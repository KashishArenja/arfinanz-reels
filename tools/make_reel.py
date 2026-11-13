"""Build a 5.1 s Instagram reel: clip in background, text boxes in front.

Design template (see WORKFLOW.md "Design-Vorlage"): Barlow Condensed Bold, one tight box per line,
styles "white" / "red" / "yellow" (legacy "blue"), small CTA line fades in at 1.5 s.

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
HERE = os.path.dirname(os.path.abspath(__file__))
# ---- AR DESIGN TEMPLATE (native Instagram text look, from our top reels + competitor hits, 10.11.2026) ----
# Condensed bold font, one tight box per text line, three colours, no shadows, no big panels.
FONT = os.path.join(HERE, "fonts", "BarlowCondensed-700.ttf")
FONT_SCALE = 1.22          # spec sizes were tuned for Poppins; the condensed font needs a bit more px
STYLES = {                 # box colour, text colour
    "white":  ((255, 255, 255, 250), (12, 12, 12, 255)),   # hook, info, CTA
    "red":    ((228, 0, 43, 250), (255, 255, 255, 255)),   # problem / "worse" side / headline accent
    "yellow": ((255, 208, 0, 250), (12, 12, 12, 255)),     # solution / "better" side / result
    "blue":   ((14, 42, 92, 245), (255, 255, 255, 255)),   # legacy (navy), avoid in new reels
}
RADIUS = 10                # small, like Instagram's text background
LPAD_X, LPAD_Y = 16, 6     # tight padding around each line
CTA_FROM = 1.5             # the last (small) block fades in at this second, like "Read the caption 👇"
YUNET = os.path.join(HERE, "yunet.onnx")
MIN_FACE_H = 110     # px in 1920 frame: only people in the foreground (crowd faces are smaller)
MAX_FACE_H = 700     # larger boxes are false positives (lights, patterns)
MIN_SCORE = 0.85
FACE_MARGIN = 45     # px clearance around each face
HEAD_MIN_SCORE = 1.0 # HOG person detections below this are ignored (false positives)
PAD, GAP = LPAD_Y, 18
CX = W / 2                                   # all text blocks centred on the frame
MAXW = 2 * (SAFE["right"] - CX)              # widest box that stays clear of the right-hand buttons
RAIL_TOP = 1100   # Instagram like/comment/share buttons start roughly here on the right
WIDE = 900        # max box width where no buttons are (above RAIL_TOP)
CARD_LOW = 2 * (W - 150 - CX)   # 780: card width below RAIL_TOP, clear of the button icons


EMOJI_FONT = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
_EMO = None


def _is_emoji(ch):
    o = ord(ch)
    return 0x1F1E6 <= o <= 0x1F1FF or 0x1F300 <= o <= 0x1FAFF or 0x2600 <= o <= 0x27BF or o in (0xFE0F, 0x200D)


def _runs(text):
    runs, cur, emo = [], "", None
    for ch in text:
        e = _is_emoji(ch)
        if emo is None or e == emo:
            cur += ch
        else:
            runs.append((emo, cur)); cur = ch
        emo = e
    if cur:
        runs.append((emo, cur))
    return runs


def _emoji_img(seq, size):
    global _EMO
    if _EMO is None:
        _EMO = ImageFont.truetype(EMOJI_FONT, 109, layout_engine=ImageFont.Layout.RAQM)
    d = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    w = int(d.textlength(seq, font=_EMO)) + 4
    im = Image.new("RGBA", (w, 140), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((2, 0), seq, font=_EMO, embedded_color=True)
    im = im.crop(im.getbbox() or (0, 0, w, 140))
    h = int(size * 0.95)
    return im.resize((max(1, int(im.width * h / im.height)), h), Image.LANCZOS)


def rich_len(d, text, font):
    """Width of text that may contain emoji flags such as 🇮🇳 🇩🇪."""
    total = 0
    for emo, seg in _runs(text):
        total += _emoji_img(seg, font.size).width + 6 if emo else d.textlength(seg, font=font)
    return total


def rich_draw(img, xy, text, font, fill):
    d = ImageDraw.Draw(img); x, y = xy
    for emo, seg in _runs(text):
        if emo:
            e = _emoji_img(seg, font.size)
            img.alpha_composite(e, (int(x + 3), int(y + font.size * 0.12)))
            x += e.width + 6
        else:
            d.text((x, y), seg, font=font, fill=fill); x += d.textlength(seg, font=font)


LATE = {"img": None}   # small CTA lines are drawn on a second layer that fades in at CTA_FROM


def paint_block(img, b, r):
    """Instagram-style text: one tight rounded box per line, centred in rect r, boxes touching."""
    target = img
    if b.get("late"):
        if LATE["img"] is None:
            LATE["img"] = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        target = LATE["img"]
    d = ImageDraw.Draw(target)
    bg, fg = STYLES.get(b["style"], STYLES["white"])
    cx = (r[0] + r[2]) / 2; y = r[1]
    widths = b.get("widths") or [rich_len(d, l, font=b["font"]) + 2 * LPAD_X for l in b["lines"]]
    for l, w in zip(b["lines"], widths):
        d.rounded_rectangle([cx - w / 2, y, cx + w / 2, y + b["lh"]], radius=RADIUS, fill=bg)
        tw = rich_len(d, l, font=b["font"])
        top = y + (b["lh"] - b["font"].size) / 2 - b["font"].size * 0.12
        rich_draw(target, (cx - tw / 2, top), l, font=b["font"], fill=fg)
        y += b["lh"]


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


def head_boxes(video):
    """Heads of people who turn their back / side to the camera (the face detector misses them).
    OpenCV's HOG person detector finds the body; the head sits in the top part of that box."""
    hog = cv2.HOGDescriptor(); hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
    cap = cv2.VideoCapture(video); out = []; i = 0
    while True:
        ok, fr = cap.read()
        if not ok:
            break
        if i % 6 == 0:
            sm = cv2.resize(fr, (W // 2, H // 2))
            rects, weights = hog.detectMultiScale(sm, winStride=(8, 8), padding=(8, 8), scale=1.05)
            for (x, y, w, h), sc in zip(rects, (weights.ravel() if len(weights) else [])):
                if sc < HEAD_MIN_SCORE:
                    continue
                x, y, w, h = 2 * x, 2 * y, 2 * w, 2 * h
                cx = x + w / 2
                out.append((cx - 0.24 * w, y + 0.04 * h, cx + 0.24 * w, y + 0.30 * h))
        i += 1
    return out


def _greedy(d, words, font, maxw):
    lines, line = [], ""
    for w in words:
        t = (line + " " + w).strip()
        if rich_len(d, t, font=font) <= maxw or not line:
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


def layout(blocks, scale, maxw=None):
    d = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    maxw = (maxw or MAXW) - 2 * PAD
    maxw = maxw - 2 * LPAD_X + 2 * PAD
    out = []
    for text, size, style in blocks:
        px = int(size * scale * FONT_SCALE)
        f = ImageFont.truetype(FONT, px)
        if size <= 46:                   # small hint lines always stay on one line
            while rich_len(d, text, font=f) > maxw and px > 26:
                px -= 2; f = ImageFont.truetype(FONT, px)
        lines = wrap_balanced(d, text, f, maxw)
        lh = int(f.size * 1.08) + 2 * LPAD_Y     # one tight box per line, boxes touch (Instagram look)
        widths = [rich_len(d, l, font=f) + 2 * LPAD_X for l in lines]
        out.append(dict(lines=lines, widths=widths, font=f, lh=lh, w=max(widths), h=len(lines) * lh, style=style, late=size <= 46))
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
    """One label above each person, same height, same width, never overlapping, inside the safe zone."""
    gap = 24
    for sz in (size, 50, 44, 40, 36):
        out = []
        for text, (x, y, w, h) in zip(labels, anchors):
            lay, th = layout([[text, sz, "white"]], scale)
            b = lay[0]
            cx = x + w / 2
            top_face = min([f[1] for f in faces if f[0] < cx < f[2]] or [y])
            out.append([b, cx, max(SAFE["top"], top_face - th - 10), th])
        bw = max(o[0]["w"] for o in out)
        # push centres apart so boxes never touch, keep the pair centred on the people
        for i in range(1, len(out)):
            need = bw + gap - (out[i][1] - out[i - 1][1])
            if need > 0:
                out[i - 1][1] -= need / 2; out[i][1] += need / 2
        # the button rail only sits on the lower right; above it labels may use the full width
        right_edge = W - 40 if max(o[2] + o[3] for o in out) < RAIL_TOP else SAFE["right"]
        lo, hi = SAFE["left"] + bw / 2, right_edge - bw / 2
        for o in out:                       # clamp each label on its own, so the others stay above their person
            o[1] = min(max(o[1], lo), hi)
        fits = out[0][1] >= lo - 1 and out[-1][1] <= hi + 1
        if fits:
            break
    y = min(o[2] for o in out)
    res = []
    for b, cx, _, th in out:
        b["w"] = bw; b["widths"] = [bw] * len(b["lines"])   # same width for every label
        res.append((b, (cx - bw / 2, y, cx + bw / 2, y + th)))
    return res

def _fit(d, texts, size, maxw, minsize=22):
    while size > minsize and max(rich_len(d, str(x), font=ImageFont.truetype(FONT, size)) for x in texts) > maxw:
        size -= 2
    return ImageFont.truetype(FONT, size)


def table_card(t, faces, min_y=None):
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
        cands = [y for y in range(int(min_y) if min_y is not None else SAFE["top"], limit - h + 1, 10)
                 if not any(overlap((CX - width / 2, y, CX + width / 2, y + h), f) for f in faces)]
        if cands:
            break
    else:
        return None, None
    if min_y is not None:      # stacked layout (hook on top): table directly under the hook
        cands = [min(cands)]
    # visually centred: as low as possible above the button rail (wide), else centred in the safe zone
    mid = (SAFE["top"] + SAFE["bottom"] - h) / 2
    y0 = max(cands) if width > MAXW else min(cands, key=lambda y: abs(y - mid))
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0)); g = ImageDraw.Draw(img)
    x0 = CX - width / 2
    g.rounded_rectangle([x0, y0, x0 + width, y0 + h], radius=28, fill=(255, 255, 255, 246))
    y = y0 + pad
    for l in title_lines:
        rich_draw(img, (CX - rich_len(g, l, font=tf) / 2, y), l, font=tf, fill=(10, 10, 10, 255)); y += 58
    y += 24
    g.rounded_rectangle([x0 + pad - 12, y - 6, x0 + width - pad + 12, y + 50], radius=RADIUS, fill=STYLES["red"][0])
    for c, hd in enumerate(t["headers"]):
        cx = x0 + pad + colw * c + colw / 2
        rich_draw(img, (cx - rich_len(g, hd, font=hf) / 2, y + 22 - hf.size / 2), hd, font=hf, fill=(255, 255, 255, 255))
    y += 56
    for r, row in enumerate(t["rows"]):
        if r == t.get("highlight"):
            g.rounded_rectangle([x0 + pad - 12, y + 6, x0 + width - pad + 12, y + rh - 6], radius=12, fill=(255, 214, 102, 255))
        elif r % 2:
            g.rectangle([x0 + pad - 12, y + 6, x0 + width - pad + 12, y + rh - 6], fill=(240, 243, 248, 255))
        for c, cell in enumerate(row):
            cx = x0 + pad + colw * c + colw / 2
            rich_draw(img, (cx - rich_len(g, str(cell), font=cf) / 2, y + rh / 2 - cf.size * 0.62), str(cell), font=cf, fill=(10, 10, 10, 255))
        y += rh
    if t.get("note"):
        rich_draw(img, (CX - rich_len(g, t["note"], font=nf) / 2, y + 10), t["note"], font=nf, fill=(90, 90, 90, 255))
    return img, (x0, y0, x0 + width, y0 + h)


def compare_card(c, faces, avoid=(), reserve=0, min_y=None):
    """Two-column comparison in the native Instagram look (like our Ehegattenschaukel hit):
    c = {"left": {"title": "🇮🇳 India", "points": [...], "style": "red", "point_style": "white"},
         "right": {"title": "🇩🇪 Germany", "points": [...], "style": "yellow"}}
    Each side: a header box, then one tight box per point. Defaults: left red, right yellow,
    points in the header colour. Placed clear of faces, right under the hook, centred."""
    d = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    gap, vgap = 24, 8
    sides = ("left", "right")
    style = {"left": c["left"].get("style", "red"), "right": c["right"].get("style", "yellow")}
    pstyle = {k: c[k].get("point_style", style[k]) for k in sides}
    for width in (WIDE, CARD_LOW):
        colw = (width - gap) / 2
        tf = _fit(d, [c[k]["title"] for k in sides], int(52 * FONT_SCALE), colw - 2 * LPAD_X)
        pf = _fit(d, [p for k in sides for p in c[k]["points"]], int(40 * FONT_SCALE), colw - 2 * LPAD_X, minsize=34)
        th = int(tf.size * 1.08) + 2 * LPAD_Y
        plh = int(pf.size * 1.08) + 2 * LPAD_Y
        wrapped = {k: [wrap_balanced(d, p, pf, colw - 2 * LPAD_X) for p in c[k]["points"]] for k in sides}
        body = max(sum(len(x) * plh for x in wrapped[k]) + vgap * len(wrapped[k]) for k in sides)
        h = th + vgap + body
        limit = RAIL_TOP if width > CARD_LOW else SAFE["bottom"] - reserve
        blocked = list(faces) + list(avoid)
        start = int(min_y) if min_y is not None else SAFE["top"]
        cands = [y for y in range(start, limit - h + 1, 10)
                 if not any(overlap((CX - width / 2, y, CX + width / 2, y + h), f) for f in blocked)]
        if cands:
            break
    else:
        return None, None
    y0 = min(cands) if min_y is not None else max(cands)   # reading order: right under the hook
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    x0 = CX - width / 2
    for i, k in enumerate(sides):
        cx = x0 + colw / 2 + i * (colw + gap)
        hb = dict(lines=[c[k]["title"]], font=tf, lh=th, style=style[k])
        paint_block(img, hb, (cx - colw / 2, y0, cx + colw / 2, y0 + th))
        y = y0 + th + vgap
        for pl in wrapped[k]:
            pb = dict(lines=pl, font=pf, lh=plh, style=pstyle[k])
            paint_block(img, pb, (cx - colw / 2, y, cx + colw / 2, y + len(pl) * plh))
            y += len(pl) * plh + vgap
    return img, (x0, y0, x0 + width, y0 + h)


def list_card(lst, faces, reserve=0):
    """Inspo format (finanzherzen 11.11.): big red banner headline at the top, then a long
    left-aligned list, one tight white box per item with an emoji in front. The list sits on the
    side of the frame that is free of faces (default left).
    lst = {"title": "🚨 ...", "items": ["🪪 Passport", ...], "side": "left"|"right"}"""
    d = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    # 1) banner
    for size in range(int(76 * FONT_SCALE), 40, -2):
        tf = ImageFont.truetype(FONT, size)
        lines = wrap_balanced(d, lst["title"], tf, WIDE - 2 * 28)
        if len(lines) <= 2:
            break
    lh = int(tf.size * 1.05)
    bh = lh * len(lines) + 2 * 22
    bw = max(rich_len(d, l, tf) for l in lines) + 2 * 34
    by = SAFE["top"]
    d2 = ImageDraw.Draw(img)
    d2.rounded_rectangle([CX - bw / 2, by, CX + bw / 2, by + bh], radius=28, fill=STYLES["red"][0])
    y = by + 22 - tf.size * 0.12
    for l in lines:
        tw = rich_len(d, l, tf)
        rich_draw(img, (CX - tw / 2, y), l, tf, STYLES["red"][1])
        y += lh
    banner = (CX - bw / 2, by, CX + bw / 2, by + bh)
    # 2) list
    items = lst["items"]; side = lst.get("side", "left"); x_margin = 36
    top = by + bh + 40; bottom = SAFE["bottom"] - reserve
    for size in range(int(50 * FONT_SCALE), 26, -2):
        f = ImageFont.truetype(FONT, size)
        ih = int(f.size * 1.08) + 2 * LPAD_Y
        total = len(items) * ih + (len(items) - 1) * 4
        widths = [rich_len(d, it, f) + 2 * LPAD_X for it in items]
        if total > bottom - top or max(widths) > W * 0.62:
            continue
        y0 = top + (bottom - top - total) // 3
        rects = []
        yy = y0
        for w in widths:
            x0 = x_margin if side == "left" else W - 230 - w
            rects.append((x0, yy, x0 + w, yy + ih)); yy += ih + 4
        if not any(overlap(r, fc) for r in rects for fc in faces):
            break
    else:
        return None, None
    for it, r in zip(items, rects):
        d2.rounded_rectangle(r, radius=RADIUS, fill=STYLES["white"][0])
        rich_draw(img, (r[0] + LPAD_X, r[1] + (ih - f.size) / 2 - f.size * 0.12), it, f, STYLES["white"][1])
    return img, (min(r[0] for r in rects), banner[1], max(r[2] for r in rects), rects[-1][3])


def render(lay, y0, path):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    for b, r in zip(lay, rects_at(lay, y0)):
        paint_block(img, b, r)
    img.save(path)


def render_parts(parts, path):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    for lay, y0 in parts:
        for b, r in zip(lay, rects_at(lay, y0)):
            paint_block(img, b, r)
    img.save(path)


def main(clip, spec, out):
    sp = json.load(open(spec)); blocks = sp["blocks"]
    segments = sp.get("segments") or [{"clip": clip, "start": sp.get("start", 0), "dur": DUR}]
    tmp = tempfile.mkdtemp()
    base = os.path.join(tmp, "base.mp4"); ov = os.path.join(tmp, "ov.png")
    normalize(segments, base)
    faces = face_boxes(base)
    # people seen from behind/side: keep their head free too; plus manual zones from spec "avoid": [[x0,y0,x1,y1], ...]
    if sp.get("avoid_heads", True):
        faces += head_boxes(base)
    faces += [tuple(r) for r in sp.get("avoid", [])]
    labels = sp.get("labels")
    if sp.get("compare"):
        # hook on top (clear of faces), comparison card below the faces, small hint at the bottom
        hook, rest = blocks[:1], blocks[1:]
        reserve = (layout(rest, 1.0)[1] + 18) if rest else 0
        # 1) hook at the top (wide, the top of the frame has no buttons), clear of faces
        lay = yh = None
        for sc in (1.0, 0.9, 0.8):
            lay, th = layout(hook, sc, maxw=WIDE)
            free = [y for y in range(SAFE["top"], SAFE["bottom"] - th + 1, 10)
                    if not any(overlap(r, f) for r in rects_at(lay, y) for f in faces)]
            if free:
                yh = min(free); break
        hook_rect = (0, yh, W, yh + th)
        # 2) comparison right under the hook, clear of faces
        img, rect = compare_card(sp["compare"], faces, avoid=[hook_rect], reserve=reserve, min_y=yh + th + 18)
        if img is None:
            sys.exit("comparison card does not fit without covering a face")
        parts = [(lay, yh)]
        # 3) hint right under the comparison
        if rest:
            lr, rh_ = layout(rest, 1.0)
            yr = int(rect[3]) + 18
            if yr + rh_ > SAFE["bottom"] or any(overlap(r, f) for r in rects_at(lr, yr) for f in faces):
                lr, yr, _ = place(rest, faces + [rect, hook_rect], prefer="bottom")
            parts.append((lr, yr))
        d = ImageDraw.Draw(img)
        for lay_, y_ in parts:
            for b, r in zip(lay_, rects_at(lay_, y_)):
                paint_block(img, b, r)
        img.save(ov); y0 = {"hook": yh, "card": rect[1]}; scale = None; parts = "done"; labels = None
    if sp.get("list"):
        reserve = (layout(blocks, 1.0)[1] + 30) if blocks else 0
        img, rect = list_card(sp["list"], faces, reserve=reserve)
        if img is None:
            sys.exit("list does not fit without covering a face")
        if blocks:
            lay, yb, _ = place(blocks, faces + [rect], prefer="bottom")
            for b, r in zip(lay, rects_at(lay, yb)):
                paint_block(img, b, r)
        img.save(ov); y0 = rect[1]; scale = None; parts = "done"; labels = None
    if sp.get("table") and sp.get("table_hook"):
        # stacked: big hook on top -> table right under it -> extra lines + hint right under the table
        hook, rest = blocks[:1], blocks[1:]
        for sc in (1.0, 0.9, 0.8):
            lay, th = layout(hook, sc, maxw=WIDE)
            free = [y for y in range(SAFE["top"], SAFE["bottom"] - th + 1, 10)
                    if not any(overlap(r, f) for r in rects_at(lay, y) for f in faces)]
            if free:
                yh = min(free); break
        img, rect = table_card(sp["table"], faces, min_y=yh + th + 14)
        if img is None:
            sys.exit("table does not fit under the hook without covering a face")
        for b, r in zip(lay, rects_at(lay, yh)):
            paint_block(img, b, r)
        if rest:
            lr, rh_ = layout(rest, 1.0, maxw=800)   # 800 px centred stays clear of the right button rail
            yr = int(rect[3]) + 14
            if yr + rh_ > SAFE["bottom"] or any(overlap(r, f) for r in rects_at(lr, yr) for f in faces):
                print("warning: lines under the table overlap a head/face", file=sys.stderr)
            for b, r in zip(lr, rects_at(lr, yr)):
                paint_block(img, b, r)
        img.save(ov); y0 = {"hook": yh, "table": rect[1]}; scale = None; parts = "done"; labels = None
    elif sp.get("table"):
        img, rect = table_card(sp["table"], faces)
        if img is None:
            sys.exit("table does not fit without covering a face - use a clip without people")
        if blocks:   # short hint below the table, e.g. the keyword ask
            lay, yb, _ = place(blocks, faces + [rect], prefer="bottom")
            d = ImageDraw.Draw(img)
            for b, r in zip(lay, rects_at(lay, yb)):
                paint_block(img, b, r)
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
                paint_block(img, b, r)
            img.save(ov); y0 = {"labels": [r[1] for r in lab_rects], "text": y0}; parts = "done"
        else:
            print("warning: could not find", len(labels), "people consistently; labels skipped", file=sys.stderr)
            parts = None; scale = None
    elif not sp.get("table") and not sp.get("compare") and not sp.get("list"):
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
    if LATE["img"] is not None:          # CTA layer fades in at CTA_FROM (like "Read the caption 👇")
        ov2 = os.path.join(tmp, "late.png"); LATE["img"].save(ov2)
        inputs = ["-i", base, "-i", ov, "-loop", "1", "-t", str(DUR), "-i", ov2]
        fc = ("[0:v][1:v]overlay=0:0:format=auto[a];"
              f"[2:v]format=rgba,fade=t=in:st={CTA_FROM}:d=0.3:alpha=1[l];"
              "[a][l]overlay=0:0:format=auto:shortest=1,format=yuv420p[v]")
    else:
        inputs = ["-i", base, "-i", ov]
        fc = "[0:v][1:v]overlay=0:0:format=auto,format=yuv420p[v]"
    run("ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", fc, "-map", "[v]", "-map", "0:a",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-profile:v", "high", "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart", out)
    # contact sheet for checking: 5 frames
    sheet = out.rsplit(".", 1)[0] + "_check.jpg"
    run("ffmpeg", "-v", "error", "-y", "-i", out, "-vf", "fps=1,scale=270:-1,tile=5x1", "-frames:v", "1", sheet)
    print(json.dumps(dict(out=out, faces=len(faces), text_y=y0, scale=scale, sheet=sheet), default=float))


if __name__ == "__main__":
    main(*sys.argv[1:4])
