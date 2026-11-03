"""Report still stretches by beat: python -m course.tools.still_map 6.1 6.2 [--level -50] [--over 15]

A stretch counts as still when ffmpeg's freezedetect sees no frame differ from its start by more than the noise
level. Pause holds are exempt: a stretch fails only by the time it runs outside the prediction holds it covers.
"""
import argparse
import json
import re
import subprocess
import sys

from course.tools.kitchen import BUILD
from course.tools.preparation import ROOT


def freezes(video, level, least=4):
    out = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(video), "-map", "0:v:0", "-vf", f"freezedetect=n={level}dB:d={least}", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    starts = [float(x) for x in re.findall(r"freeze_start: ([\d.]+)", out)]
    ends = [float(x) for x in re.findall(r"freeze_end: ([\d.]+)", out)]
    length = re.search(r"Duration: (\d+):(\d+):([\d.]+)", out)
    total = int(length[1]) * 3600 + int(length[2]) * 60 + float(length[3])
    return [(s, ends[i] if i < len(ends) else total) for i, s in enumerate(starts)]


def beats_of(dish):
    import yaml
    timeline = json.loads((BUILD / "timelines" / f"{dish}.json").read_text())
    card = yaml.safe_load((ROOT / "recipes" / f"{dish}.yaml").read_text())
    holds = {b["id"]: b.get("hold", 0) for b in card["beats"] if b.get("stage") == "prediction"}
    t, rows = 0, []
    for b in timeline["beats"]:
        start, end = t / 30, (t + b["frames"]) / 30
        hold = None
        if holds.get(b["beat_id"]):
            hold = (end - 0.2 - holds[b["beat_id"]], end)
        rows.append((b["beat_id"].split(".", 2)[2], start, end, hold))
        t += b["frames"]
    return rows


def report(dish, level, over):
    rows = beats_of(dish)
    failures = []
    for start, end in freezes(BUILD / "dishes" / "final" / f"{dish}.mp4", level):
        exempt = sum(max(0, min(end, h[1]) - max(start, h[0])) for *_, h in rows if h)
        if end - start - exempt >= over:
            failures.append((start, end, exempt, [r[0] for r in rows if r[1] < end and r[2] > start]))
    return failures


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("dishes", nargs="+")
    parser.add_argument("--level", type=int, default=-50)
    parser.add_argument("--over", type=float, default=15)
    args = parser.parse_args()
    bad = 0
    for dish in args.dishes:
        failures = report(dish, args.level, args.over)
        bad += len(failures)
        print(f"{dish}: {'PASS' if not failures else 'FAIL'}")
        for start, end, exempt, names in failures:
            print(f"  {start:7.1f}-{end:7.1f}  {end - start:4.0f} s still, {exempt:.0f} s of it a pause hold: {', '.join(names)}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
