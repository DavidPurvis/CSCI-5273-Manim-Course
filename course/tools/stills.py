"""Measure how long a video's picture stays still, from its real frames."""
import subprocess
import sys

import numpy as np

FPS, W, H = 10, 320, 180
LEVEL, PIXELS = 14, 3  # A frame counts as changed when at least PIXELS pixels move by more than LEVEL of 255.


def stretches(video):
    """Every still stretch as (start seconds, length seconds)."""
    proc = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(video), "-an", "-vf", f"fps={FPS},scale={W}:{H},format=gray", "-f", "rawvideo", "-"],
                            stdout=subprocess.PIPE)
    size = W * H
    prev, frame, start, out = None, 0, 0, []
    while True:
        raw = proc.stdout.read(size)
        if len(raw) < size:
            break
        cur = np.frombuffer(raw, dtype=np.uint8).astype(np.int16)
        if prev is not None and (np.abs(cur - prev) > LEVEL).sum() >= PIXELS:
            if frame > start:
                out.append((start / FPS, (frame - start) / FPS))
            start = frame
        prev = cur
        frame += 1
    proc.wait()
    if frame > start:
        out.append((start / FPS, (frame - start) / FPS))
    return out, frame / FPS


def report(video):
    runs, total = stretches(video)
    total = max(total, 1e-3)
    longest = max(runs, key=lambda r: r[1], default=(0, 0))
    return {"seconds": round(total, 1),
            "over_10s": round(sum(d for _, d in runs if d > 10) / total, 3),
            "over_20s": round(sum(d for _, d in runs if d > 20) / total, 3),
            "longest": round(longest[1], 1), "longest_at": round(longest[0], 1)}


if __name__ == "__main__":
    for path in sys.argv[1:]:
        print(path, report(path))
