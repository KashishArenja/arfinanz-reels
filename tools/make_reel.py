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


def layout(blocks, scale):
    d = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    maxw = SAFE["right"] - SAFE["left"] - 2 * PAD
    out = []
    for text, size, style in blocks:
        f = ImageFont.truetype(FONT, int(size * scale))
        lines, line = [], ""
        for w in text.split():
            t = (line + " " + w).strip()
            if d.textlength(t, font=f) <= maxw:
                line = t
            else:
                lines.append(line); line = w
        lines.append(line)
        lh = int(f.size * 1.25)
        bw = max(d.textlength(l, font=f) for l in lines) + 2 * PAD
        out.append(dict(lines=lines, font=f, lh=lh, w=bw, h=len(lines) * lh + 2 * PAD, style=style))
    total = sum(b["h"] for b in out) + GAP * (len(out) - 1)
    return out, total


def rects_at(lay, y0):
    cx = (SAFE["left"] + SAFE["right"]) / 2
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
        out.append((b, (cx - b["w"] / 2, yl, cx + b["w"] / 2, yl + th)))
    return out


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
    else:
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
