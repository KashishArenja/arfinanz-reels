"""Build a 5.1 s Instagram reel: clip in background, text boxes in front.

Text is placed inside the Instagram safe zone and never over a face
(faces are detected on frames every 0.2 s across the whole clip).

usage: python3 make_reel.py clip.mp4 spec.json out.mp4
spec.json: {"blocks": [["text", size, "white"|"blue"], ...],
            "start": 2.0,                       # optional: where to cut into clip.mp4
            "segments": [{"clip": "a.mov", "start": 0, "dur": 2.5},
                         {"clip": "b.mov", "start": 3, "dur": 2.6}]}   # optional: combine several clips
            (with "segments" the clip argument is ignored; use "-")
            "labels": ["India", "Germany"]      # optional: one label above each person (left to right)
            "table": {"title": "...", "headers": [...], "rows": [[...]], "highlight": 1, "note": "..."}  # optional: data table (clips without people)
"""
import json, os, subprocess, sys, tempfile
import cv2
from PIL import Image, ImageDraw, ImageFont

W, H, DUR, FPS = 1080, 1920, 5.1, 30
SAFE = dict(top=250, bottom=1440, left=90, right=W - 230)
FONT = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
YUNET = os.path.join(os.path.dirname(os.path.abspath(__file__)), "yunet.onnx")
MIN_FACE_H = 110     # px in 1920 frame: only people in the foreground (crowd faces are smaller)
MAX_FACE_H = 700     # larger boxes are false positives (lights, patterns)
MIN_SCORE = 0.85
FACE_MARGIN = 45     # px clearance around each face
PAD, GAP = 26, 18
CX = W / 2                                   # all text blocks centred on the frame
MAXW = 2 * (SAFE["right"] - CX)              # widest box that stays clear of the right-hand buttons


def run(*a):
    subprocess.run(a, check=True)


def normalize(segments, dst):
    """segments: [{"clip": path, "start": s, "dur": d}, ...] (one or more cuts).
    Each cut: autorotate, fill 9:16, 30 fps. Cuts are joined, total exactly 5.1 s, silent stereo."""
    args, chains = [], []
    for i, sg in enumerate(segments):
        args += ["-ss", str(sg.get("start", 0)), "-t", str(sg.get("dur", DUR)), "-i", sg["clip"]]
        chains.append(f"[{i}:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},"
                      f"setsar=1,format=yuv420p,setpts=PTS-STARTPTS[s{i}]")
    n = len(segments)
    join = "".join(f"[s{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0[c]"
    tail = (f"[c]tpad=stop_mode=clone:stop_duration={DUR},trim=duration={DUR},setpts=PTS-STARTPTS[v]")
    fc = ";".join(chains + [join, tail])
    run("ffmpeg", "-v", "error", "-y", *args, "-f", "lavfi", "-t", str(DUR), "-i", "anullsrc=r=44100:cl=stereo",
        "-filter_complex", fc, "-map", "[v]", "-map", f"{n}:a",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-c:a", "aac", "-t", str(DUR), dst)


def face_boxes(video):
    det = cv2.FaceDetectorYN.create(YUNET, "", (W, H), MIN_SCORE)
    cap = cv2.VideoCapture(video)
    boxes, i = [], 0
    step = int(FPS * 0.2)
    while True:
        ok, fr = cap.read()
        if not ok:
            break
        if i % step == 0:
            _, f = det.detect(fr)
            if f is not None:
                for x, y, w, h in f[:, :4]:
                    if MIN_FACE_H <= h <= MAX_FACE_H:
                        boxes.append((x - FACE_MARGIN, y - FACE_MARGIN, x + w + FACE_MARGIN, y + h + FACE_MARGIN))
        i += 1
    return boxes


def _greedy(d, words, font, maxw):
    lines, line = [], ""
    for w in words:
        t = (line + " " + w).strip()
        if d.textlength(t, font=font) <= maxw or not line:
            line = t
        else:
            lines.append(line); line = w
    lines.append(line)
    return lines


def wrap_balanced(d, text, font, maxw):
    """Fewest lines possible, and those lines as even as possible (no lone last word).
    Use "~" to glue words that must stay together, e.g. "at~30"."""
    words = [w.replace("~", " ") for w in text.split()]
    n = len(_greedy(d, words, font, maxw))
    lo, hi = 1, int(maxw)
    while lo < hi:                       # narrowest width that still gives n lines
        mid = (lo + hi) // 2
        if len(_greedy(d, words, font, mid)) <= n:
            hi = mid
        else:
            lo = mid + 1
    return _greedy(d, words, font, lo)


def layout(blocks, scale):
    d = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    maxw = MAXW - 2 * PAD
    out = []
    for text, size, style in blocks:
        px = int(size * scale)
        f = ImageFont.truetype(FONT, px)
        if size <= 46:                   # small hint lines always stay on one line
            while d.textlength(text, font=f) > maxw and px > 26:
                px -= 2; f = ImageFont.truetype(FONT, px)
        lines = wrap_balanced(d, text, f, maxw)
        lh = int(f.size * 1.25)
        bw = max(d.textlength(l, font=f) for l in lines) + 2 * PAD
        out.append(dict(lines=lines, font=f, lh=lh, w=bw, h=len(lines) * lh + 2 * PAD, style=style))
    total = sum(b["h"] for b in out) + GAP * (len(out) - 1)
    return out, total


def rects_at(lay, y0):
    cx = CX
    rs, y = [], y0
    for b in lay:
        rs.append((cx - b["w"] / 2, y, cx + b["w"] / 2, y + b["h"])); y += b["h"] + GAP
    return rs


def overlap(r, f):
    return max(0, min(r[2], f[2]) - max(r[0], f[0])) * max(0, min(r[3], f[3]) - max(r[1], f[1]))


def place(blocks, faces, prefer="upper"):
    """Return (layout, y0) with no face overlap; prefer upper-middle, shrink text if needed."""
    pref = SAFE["top"] + 180 if prefer == "upper" else SAFE["bottom"]
    tries = [(blocks, s) for s in (1.0, 0.88, 0.76, 0.68)]
    if len(blocks) > 2:  # last resort: drop the small hint line
        tries += [(blocks[:-1], s) for s in (1.0, 0.88, 0.76, 0.68)]
    for bl, scale in tries:
        lay, total = layout(bl, scale)
        if total > SAFE["bottom"] - SAFE["top"]:
            continue
        cands = range(SAFE["top"], SAFE["bottom"] - total + 1, 10)
        free = [y for y in cands if not any(overlap(r, f) for r in rects_at(lay, y) for f in faces)]
        if free:
            return lay, min(free, key=lambda y: abs(y - pref)), (scale, len(bl))
    # no free spot: least overlap at full size
    lay, total = layout(blocks, 0.76)
    y = min(range(SAFE["top"], SAFE["bottom"] - total + 1, 10),
            key=lambda y: sum(overlap(r, f) for r in rects_at(lay, y) for f in faces))
    return lay, y, None


def place_split(blocks, faces):
    """Hook at the top, the rest at the bottom of the safe zone; both clear of faces."""
    for scale in (1.0, 0.9, 0.8, 0.7):
        top, th = layout(blocks[:1], scale); bot, bh = layout(blocks[1:], scale)
        ok = lambda lay, y: not any(overlap(r, f) for r in rects_at(lay, y) for f in faces)
        ty = [y for y in range(SAFE["top"], SAFE["bottom"] - th + 1, 10) if ok(top, y)]
        by = [y for y in range(SAFE["top"], SAFE["bottom"] - bh + 1, 10) if ok(bot, y)]
        for yt in sorted(ty):                     # top block as high as possible
            cand = [y for y in by if y >= yt + th + 120]   # visible gap between the two
            if cand:
                return [(top, yt), (bot, max(cand))], scale  # bottom block as low as possible
    return None, None


def person_anchors(video, n):
    """Median face box per person (left to right) across the clip, foreground faces only."""
    det = cv2.FaceDetectorYN.create(YUNET, "", (W, H), MIN_SCORE)
    cap = cv2.VideoCapture(video); per = []; i = 0
    while True:
        ok, fr = cap.read()
        if not ok:
            break
        if i % 6 == 0:
            _, f = det.detect(fr)
            fs = [] if f is None else sorted([r[:4] for r in f if MIN_FACE_H <= r[3] <= MAX_FACE_H], key=lambda r: r[0])
            if len(fs) == n:
                per.append(fs)
        i += 1
    if not per:
        return None
    import statistics as st
    return [tuple(st.median(fr[k][j] for fr in per) for j in range(4)) for k in range(n)]


def place_labels(labels, anchors, faces, scale=1.0, size=56):
    """One label box above each person's head, inside the safe zone, clear of all faces."""
    out = []
    for text, (x, y, w, h) in zip(labels, anchors):
        lay, th = layout([[text, size, "white"]], scale)
        b = lay[0]
        cx = min(max(x + w / 2, SAFE["left"] + b["w"] / 2), SAFE["right"] - b["w"] / 2)
        top_face = min(f[1] for f in faces if f[0] < cx < f[2]) if any(f[0] < cx < f[2] for f in faces) else y
        yl = max(SAFE["top"], top_face - th - 10)
        out.append((b, cx, yl, th))
    y = min(o[2] for o in out)                 # one shared line, above the higher head
    bw = max(o[0]["w"] for o in out)           # same width for every label
    res = []
    for b, cx, _, th in out:
        b["w"] = bw
        cx = min(max(cx, SAFE["left"] + bw / 2), SAFE["right"] - bw / 2)
        res.append((b, (cx - bw / 2, y, cx + bw / 2, y + th)))
    return res


RAIL_TOP = 1100   # Instagram's like/comment/share buttons start roughly here on the right


def _fit(d, texts, size, maxw, minsize=22):
    while size > minsize and max(d.textlength(str(x), font=ImageFont.truetype(FONT, size)) for x in texts) > maxw:
        size -= 2
    return ImageFont.truetype(FONT, size)


def table_card(t, faces):
    """Clean table card, centred. t = {"title","headers","rows","highlight"(row index),"note"}
    Wide (900 px) when it sits above the button rail, otherwise narrow enough to clear it."""
    d = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    cols = len(t["headers"]); pad, rh = 36, 76
    for width in (900, MAXW):
        inner = width - 2 * pad; colw = inner / cols
        tf = ImageFont.truetype(FONT, 46)
        title_lines = wrap_balanced(d, t["title"], tf, inner)
        hf = _fit(d, t["headers"], 30, colw - 16)
        cfs = [_fit(d, [r[c] for r in t["rows"]], 44, colw - 16) for c in range(cols)]
        cf = min(cfs, key=lambda f: f.size)   # one size for all cells keeps it clean
        nf = _fit(d, [t.get("note", "")], 24, inner)
        th = len(title_lines) * 58
        h = pad + th + 24 + 56 + rh * len(t["rows"]) + (44 if t.get("note") else 0) + pad
        limit = RAIL_TOP if width > MAXW else SAFE["bottom"]
        cands = [y for y in range(SAFE["top"], limit - h + 1, 10)
                 if not any(overlap((CX - width / 2, y, CX + width / 2, y + h), f) for f in faces)]
        if cands:
            break
    else:
        return None, None
    # visually centred: as low as possible above the button rail (wide), else centred in the safe zone
    mid = (SAFE["top"] + SAFE["bottom"] - h) / 2
    y0 = max(cands) if width > MAXW else min(cands, key=lambda y: abs(y - mid))
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0)); g = ImageDraw.Draw(img)
    x0 = CX - width / 2
    g.rounded_rectangle([x0, y0, x0 + width, y0 + h], radius=28, fill=(255, 255, 255, 246))
    y = y0 + pad
    for l in title_lines:
        g.text((CX - g.textlength(l, font=tf) / 2, y), l, font=tf, fill=(10, 10, 10, 255)); y += 58
    y += 24
    g.rounded_rectangle([x0 + pad - 12, y - 6, x0 + width - pad + 12, y + 50], radius=12, fill=(14, 42, 92, 255))
    for c, hd in enumerate(t["headers"]):
        cx = x0 + pad + colw * c + colw / 2
        g.text((cx - g.textlength(hd, font=hf) / 2, y + 22 - hf.size / 2), hd, font=hf, fill=(255, 255, 255, 255))
    y += 56
    for r, row in enumerate(t["rows"]):
        if r == t.get("highlight"):
            g.rounded_rectangle([x0 + pad - 12, y + 6, x0 + width - pad + 12, y + rh - 6], radius=12, fill=(255, 214, 102, 255))
        elif r % 2:
            g.rectangle([x0 + pad - 12, y + 6, x0 + width - pad + 12, y + rh - 6], fill=(240, 243, 248, 255))
        for c, cell in enumerate(row):
            cx = x0 + pad + colw * c + colw / 2
            g.text((cx - g.textlength(str(cell), font=cf) / 2, y + rh / 2 - cf.size * 0.62), str(cell), font=cf, fill=(10, 10, 10, 255))
        y += rh
    if t.get("note"):
        g.text((CX - g.textlength(t["note"], font=nf) / 2, y + 10), t["note"], font=nf, fill=(90, 90, 90, 255))
    return img, (x0, y0, x0 + width, y0 + h)


def render(lay, y0, path):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    for b, r in zip(lay, rects_at(lay, y0)):
        bg, fg = ((255, 255, 255, 245), (10, 10, 10, 255)) if b["style"] == "white" else ((14, 42, 92, 240), (255, 255, 255, 255))
        d.rounded_rectangle(r, radius=22, fill=bg)
        ty = r[1] + PAD
        for l in b["lines"]:
            d.text((r[0] + (b["w"] - d.textlength(l, font=b["font"])) / 2, ty), l, font=b["font"], fill=fg); ty += b["lh"]
    img.save(path)


def render_parts(parts, path):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    for lay, y0 in parts:
        for b, r in zip(lay, rects_at(lay, y0)):
            bg, fg = ((255, 255, 255, 245), (10, 10, 10, 255)) if b["style"] == "white" else ((14, 42, 92, 240), (255, 255, 255, 255))
            d.rounded_rectangle(r, radius=22, fill=bg)
            ty = r[1] + PAD
            for l in b["lines"]:
                d.text((r[0] + (b["w"] - d.textlength(l, font=b["font"])) / 2, ty), l, font=b["font"], fill=fg); ty += b["lh"]
    img.save(path)


def main(clip, spec, out):
    sp = json.load(open(spec)); blocks = sp["blocks"]
    segments = sp.get("segments") or [{"clip": clip, "start": sp.get("start", 0), "dur": DUR}]
    tmp = tempfile.mkdtemp()
    base = os.path.join(tmp, "base.mp4"); ov = os.path.join(tmp, "ov.png")
    normalize(segments, base)
    faces = face_boxes(base)
    labels = sp.get("labels")
    if sp.get("table"):
        img, rect = table_card(sp["table"], faces)
        if img is None:
            sys.exit("table does not fit without covering a face - use a clip without people")
        if blocks:   # short hint below the table, e.g. the keyword ask
            lay, yb, _ = place(blocks, faces + [rect], prefer="bottom")
            d = ImageDraw.Draw(img)
            for b, r in zip(lay, rects_at(lay, yb)):
                bg, fg = ((255, 255, 255, 245), (10, 10, 10, 255)) if b["style"] == "white" else ((14, 42, 92, 240), (255, 255, 255, 255))
                d.rounded_rectangle(r, radius=22, fill=bg); ty = r[1] + PAD
                for l in b["lines"]:
                    d.text((r[0] + (b["w"] - d.textlength(l, font=b["font"])) / 2, ty), l, font=b["font"], fill=fg); ty += b["lh"]
        img.save(ov); y0 = rect[1]; scale = None; parts = "done"; labels = None
    if labels:
        anchors = person_anchors(base, len(labels))
        if anchors:
            lab = place_labels(labels, anchors, faces)
            lab_rects = [r for _, r in lab]
            # remaining text goes to the free area below, clear of faces and labels
            lay, y0, scale = place(blocks, faces + lab_rects, prefer="bottom")
            img = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
            for b, r in lab + list(zip(lay, rects_at(lay, y0))):
                bg, fg = ((255, 255, 255, 245), (10, 10, 10, 255)) if b["style"] == "white" else ((14, 42, 92, 240), (255, 255, 255, 255))
                d.rounded_rectangle(r, radius=22, fill=bg); ty = r[1] + PAD
                for l in b["lines"]:
                    d.text((r[0] + (b["w"] - d.textlength(l, font=b["font"])) / 2, ty), l, font=b["font"], fill=fg); ty += b["lh"]
            img.save(ov); y0 = {"labels": [r[1] for r in lab_rects], "text": y0}; parts = "done"
        else:
            print("warning: could not find", len(labels), "people consistently; labels skipped", file=sys.stderr)
            parts = None; scale = None
    elif not sp.get("table"):
        parts = None
    if parts == "done":
        pass
    elif len(blocks) > 1 and (parts := place_split(blocks, faces)[0]):
        scale = None
        y0 = [y for _, y in parts]
        render_parts(parts, ov)
    else:
        lay, y0, scale = place(blocks, faces)
        render(lay, y0, ov)
    run("ffmpeg", "-v", "error", "-y", "-i", base, "-i", ov, "-filter_complex",
        "[0:v][1:v]overlay=0:0:format=auto,format=yuv420p[v]", "-map", "[v]", "-map", "0:a",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-profile:v", "high", "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart", out)
    # contact sheet for checking: 5 frames
    sheet = out.rsplit(".", 1)[0] + "_check.jpg"
    run("ffmpeg", "-v", "error", "-y", "-i", out, "-vf", "fps=1,scale=270:-1,tile=5x1", "-frames:v", "1", sheet)
    print(json.dumps(dict(out=out, faces=len(faces), text_y=y0, scale=scale, sheet=sheet), default=float))


if __name__ == "__main__":
    main(*sys.argv[1:4])
