"""Colour table reel (inspo: big red hook banner + coloured 3-column table + black source box).
usage: python3 tools/color_table.py clip.mov spec.json out.mp4
spec = {"hook": "...", "headers": [a,b,c], "rows": [[..],..], "colors": ["yel","red","green"],
        "highlight": i (optional), "footer": ["line1", "line2"], "cta": "Comment HOME for a free PDF guide 👇",
        "start": 0.0, "dur": 8.0, "speed": 1.0}
Safe zones: everything between y=250 and y=1440, width <= 780 below y=1100 (button rail)."""
import json, subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

sys.path.insert(0, "/home/claude/arfinanz-reels/tools")
import make_reel as MR

W, H = 1080, 1920
F7 = "/home/claude/arfinanz-reels/tools/fonts/BarlowCondensed-700.ttf"
F = lambda s: ImageFont.truetype(F7, int(s))
COL = {"yel": ((255, 214, 64), (12, 12, 12)), "red": ((232, 64, 52), (255, 255, 255)),
       "green": ((98, 222, 120), (12, 12, 12)), "white": ((255, 255, 255), (12, 12, 12)),
       "blue": ((47, 92, 245), (255, 255, 255))}
D0 = ImageDraw.Draw(Image.new("RGBA", (4, 4)))


def tw(t, f):
    return MR.rich_len(D0, t, f)


def build(spec):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    TW = 820; X0 = (W - TW) // 2          # table x 130..950 (rail starts ~ 960)
    # --- hook banner
    bf = 66
    while True:
        f = F(bf); lines = MR.wrap_balanced(D0, spec["hook"], f, 940)
        if len(lines) <= 3 or bf <= 44:
            break
        bf -= 2
    lh = int(bf * 1.08); bh = lh * len(lines) + 40
    bw = max(tw(l, f) for l in lines) + 60
    by = 262
    ban = Image.new("RGBA", (int(bw), bh), (0, 0, 0, 0))
    ImageDraw.Draw(ban).rounded_rectangle([0, 0, bw - 1, bh - 1], radius=26, fill=(200, 24, 32, 250))
    y = 20 - bf * 0.1
    for l in lines:
        MR.rich_draw(ban, ((bw - tw(l, f)) / 2, y), l, f, (255, 255, 255, 255)); y += lh
    sh = Image.new("RGBA", (ban.width + 40, ban.height + 40), (0, 0, 0, 0))
    blk = Image.new("RGBA", ban.size, (0, 0, 0, 120)); sh.paste(blk, (20, 26)); sh = sh.filter(ImageFilter.GaussianBlur(10))
    sh.alpha_composite(ban, (20, 20)); img.alpha_composite(sh, (int((W - sh.width) / 2), by - 20))
    top = by + bh + 26
    # --- footer + cta sizes
    ff = F(30); foot = spec.get("footer", [])
    fh = 22 + 38 * len(foot) if foot else 0
    cta = spec.get("cta"); ch = 0
    if cta:
        cf = F(52); cw = tw(cta, cf) + 60; ch = 86
    bottom = 1436 - fh - (ch + 14 if cta else 0) - (12 if foot else 0)
    n = len(spec["rows"]); hdr = 62; gap = 8
    rh = min(70, int((bottom - top - hdr - gap) / n) - 7)
    cols = len(spec["headers"]); cgap = 14
    widths = spec.get("widths") or [1 / cols] * cols
    cws = [int((TW - cgap * (cols - 1)) * w) for w in widths]
    xs = [X0]
    for w in cws[:-1]:
        xs.append(xs[-1] + w + cgap)
    # headers
    hf = F(38)
    for x, w, h_ in zip(xs, cws, spec["headers"]):
        d.rounded_rectangle([x, top, x + w, top + hdr], radius=12, fill=COL["blue"][0] + (255,))
        MR.rich_draw(img, (x + (w - tw(h_, hf)) / 2, top + (hdr - 38) / 2 - 5), h_, hf, (255, 255, 255, 255))
    y = top + hdr + gap
    rf = F(min(46, rh * 0.72))
    for ri, row in enumerate(spec["rows"]):
        hl = spec.get("highlight") == ri
        for ci, (x, w, val) in enumerate(zip(xs, cws, row)):
            bg, fg = COL[spec["colors"][ci]]
            d.rounded_rectangle([x, y, x + w, y + rh], radius=10, fill=bg + (250,),
                                outline=(255, 255, 255, 255) if hl else None, width=5 if hl else 0)
            MR.rich_draw(img, (x + (w - tw(val, rf)) / 2, y + (rh - rf.size) / 2 - rf.size * 0.1), val, rf, fg + (255,))
        y += rh + 7
    y += 5
    if foot:
        d.rounded_rectangle([X0, y, X0 + TW, y + fh], radius=14, fill=(10, 10, 10, 235))
        yy = y + 11
        for l in foot:
            MR.rich_draw(img, (X0 + (TW - tw(l, ff)) / 2, yy), l, ff, (235, 235, 235, 255)); yy += 38
        y += fh + 12
    if cta:
        cx0 = (W - cw) / 2
        d.rounded_rectangle([cx0, y, cx0 + cw, y + ch], radius=40, fill=(255, 208, 0, 255))
        MR.rich_draw(img, (cx0 + 30, y + (ch - 52) / 2 - 6), cta, cf, (12, 12, 12, 255))
        y += ch
    assert y <= 1442, f"layout too tall: {y}"
    return img


def main(clip, spec_p, out):
    spec = json.load(open(spec_p))
    ov = build(spec)
    ovp = out.replace(".mp4", "_ov.png"); ov.save(ovp)
    dur = spec.get("dur", 8.0); sp = spec.get("speed", 1.0); st = spec.get("start", 0.0)
    vf = (f"[0:v]setpts=PTS/{sp},scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
          f"eq=brightness=-0.06,fps=30,trim=0:{dur},setpts=PTS-STARTPTS[bg];[bg][1:v]overlay=0:0,format=yuv420p[v]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-stream_loop", "3", "-ss", str(st), "-i", clip, "-i", ovp,
                    "-f", "lavfi", "-t", str(dur), "-i", "anullsrc=r=48000:cl=stereo",
                    "-filter_complex", vf, "-map", "[v]", "-map", "2:a", "-t", str(dur),
                    "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-c:a", "aac", "-shortest", "-movflags", "+faststart", out],
                   check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "3", "-i", out, "-frames:v", "1", "-vf", "scale=540:-1",
                    out.replace(".mp4", "_check.jpg")], check=True)
    print("ok", out)


if __name__ == "__main__":
    main(*sys.argv[1:4])
