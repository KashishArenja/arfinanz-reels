#!/usr/bin/env python3
"""Fest eingebaute Hintergrundmusik für TikTok/YouTube-Versionen der Reels.

Instagram bekommt weiter den Trend-Sound über Metricool (audioConfiguration).
TikTok/YouTube können über Metricool keinen Sound wählen -> Musik wird ins MP4 gemischt.

Usage:
  python3 tools/add_music.py in.mp4 out.mp4 [track.mp3]
Ohne track wird der nächste Track aus music/library.json rotiert (music/rotation.json).
Bibliothek: lizenzfreie Tracks aus der YouTube Audio Library (Kashish 18.11.).
"""
import json, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB = os.path.join(ROOT, "music", "library.json")
ROT = os.path.join(ROOT, "music", "rotation.json")
TARGET_LUFS = -14.0


def dur(p):
    return float(subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p]).decode())


def has_audio(p):
    out = subprocess.run(["ffmpeg", "-i", p, "-af", "volumedetect", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    for l in out.splitlines():
        if "max_volume" in l:
            return float(l.split()[-2]) > -60
    return False


def next_track():
    lib = json.load(open(LIB))
    names = sorted(lib)
    rot = json.load(open(ROT)) if os.path.exists(ROT) else {"i": 0}
    name = names[rot["i"] % len(names)]
    rot["i"] += 1
    json.dump(rot, open(ROT, "w"))
    return name, lib[name]


def main():
    src, dst = sys.argv[1], sys.argv[2]
    lib = json.load(open(LIB))
    if len(sys.argv) > 3:
        name = os.path.basename(sys.argv[3]); meta = lib[name]
    else:
        name, meta = next_track()
    if has_audio(src):
        # Talking-Head o. ä.: eigene Tonspur behalten, keine Musik drüber
        subprocess.check_call(["cp", src, dst]); print("own audio kept", dst); return
    d = dur(src)
    gain = TARGET_LUFS - meta["lufs_section"]
    fo = max(d - 0.5, 0)
    af = (f"volume={gain:.1f}dB,afade=t=in:st=0:d=0.08,afade=t=out:st={fo:.2f}:d=0.5,"
          f"alimiter=limit=0.89")
    subprocess.check_call([
        "ffmpeg", "-y", "-v", "error", "-i", src,
        "-ss", str(meta["offset"]), "-t", f"{d:.3f}", "-i", os.path.join(ROOT, "music", name),
        "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-af", af,
        "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-shortest", "-movflags", "+faststart", dst])
    print(name, dst)


if __name__ == "__main__":
    main()
