"""Prep aid: run dishes without rendering, save each beat's end frame, and build contact sheets."""
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]


def run(dish, sheet=True):
    snap = ROOT / "build" / "snap" / dish
    for old in snap.glob("*.png") if snap.exists() else []:
        old.unlink()
    env = dict(os.environ, KITCHEN_DISH=dish, KITCHEN_SNAP=str(snap) if sheet else "", PYTHONWARNINGS="ignore")
    if not sheet:
        env.pop("KITCHEN_SNAP")
    lint = ROOT / "build" / "lint" / f"{dish}.json"
    if lint.exists():
        lint.unlink()
    r = subprocess.run([str(ROOT / ".venv/bin/manim"), "render", "course/stage/player.py", "Dish", "--dry_run", "--disable_caching",
                        "-v", "ERROR", "-r", "640,360", "--media_dir", f"build/media/dry/{dish}"], cwd=ROOT, env=env, capture_output=True, text=True)
    if not lint.exists():
        tail = [l for l in (r.stdout + r.stderr).splitlines() if l.strip()][-14:]
        return dish, ["CRASH: " + "\n".join(tail)], 0
    data = json.loads(lint.read_text())
    if sheet:
        # Order frames by the card, not the file name.
        import yaml
        ids = [b["id"] for b in yaml.safe_load((ROOT / "recipes" / f"{dish}.yaml").read_text())["beats"]]
        files = [snap / f"{i}.png" for i in ids if (snap / f"{i}.png").exists()]
        W, H, cols = 560, 315, 4
        rows = (len(files) + cols - 1) // cols
        page = Image.new("RGB", (cols * W, rows * H))
        for i, f in enumerate(files):
            page.paste(Image.open(f).convert("RGB").resize((W, H)), ((i % cols) * W, (i // cols) * H))
        page.save(ROOT / "build" / "snap" / f"{dish}.sheet.png")
    return dish, data["problems"], data["duration"]


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    sheet = "--nosheet" not in sys.argv
    if args == ["all"]:
        args = sorted((p.stem for p in (ROOT / "recipes").glob("*.yaml")), key=lambda d: [int(x) for x in d.split(".")])
    totals = {}
    with ThreadPoolExecutor(8) as pool:
        for dish, problems, duration in pool.map(lambda d: run(d, sheet), args):
            totals[dish.split(".")[0]] = totals.get(dish.split(".")[0], 0) + duration
            if problems:
                print(f"{dish}: {duration / 60:.1f} min, {len(problems)} problem(s)")
                for p in sorted(set(x.split(": ", 1)[1] for x in problems))[:8]:
                    print("   ", p[:150])
    print({k: round(v / 60, 1) for k, v in totals.items()}, "total", round(sum(totals.values()) / 60, 1))
    still_report(args)


def still_report(dishes):
    """Where the picture stays still, estimated from every animation's scheduled time."""
    lines, grand, over10, over20, worst = [], 0.0, 0.0, 0.0, []
    for d in dishes:
        data = json.loads((ROOT / "build" / "lint" / f"{d}.json").read_text())
        cursor, gaps = 0.0, []
        for a, b in sorted(data.get("moving", [])):
            if a - cursor > 0.05:
                gaps.append((a - cursor, cursor))
            cursor = max(cursor, b)
        if data["duration"] - cursor > 0.05:
            gaps.append((data["duration"] - cursor, cursor))
        total = data["duration"] or 1
        o10 = sum(g for g, _ in gaps if g > 10)
        grand += total
        over10 += o10
        over20 += sum(g for g, _ in gaps if g > 20)
        worst += [(round(g, 1), d, round(at, 1)) for g, at in gaps]
        lines.append(f"{d}:{100 * o10 / total:.0f}%")
    if grand:
        print(f"Stills over 10 s: {100 * over10 / grand:.0f}%  over 20 s: {100 * over20 / grand:.0f}%")
        print(" ".join(lines))
        print("Longest:", sorted(worst, reverse=True)[:14])


if __name__ == "__main__":
    main()
