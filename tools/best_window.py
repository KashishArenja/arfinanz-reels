#!/usr/bin/env python3
"""Find the most dynamic continuous window of a clip (Kashish 18.11.: beste, schnellste Stelle, 5,1 s).
usage: best_window.py clip [dur=5.1] [top=3] -> prints start times, best first"""
import sys, subprocess, numpy as np
clip = sys.argv[1]; dur = float(sys.argv[2]) if len(sys.argv) > 2 else 5.1; top = int(sys.argv[3]) if len(sys.argv) > 3 else 3
fps = 10; w, h = 72, 128
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", clip, "-vf", f"fps={fps},scale={w}:{h},format=gray", "-f", "rawvideo", "-"],
                     capture_output=True).stdout
f = np.frombuffer(raw, np.uint8).reshape(-1, h, w).astype(np.float32)
mot = np.r_[0, np.abs(np.diff(f, axis=0)).mean(axis=(1, 2))]
n = int(round(dur * fps))
if len(mot) <= n:
    print(0.0); sys.exit()
scores = np.convolve(mot, np.ones(n), "valid") / n
order = np.argsort(-scores)
picked = []
for i in order:
    if all(abs(i - j) >= fps for j in picked):
        picked.append(i)
    if len(picked) == top:
        break
print(" ".join(f"{i / fps:.1f}" for i in picked))
