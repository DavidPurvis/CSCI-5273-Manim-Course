"""run, plus check, cook, taste, plate, serve, review, open: everything the chef does, and nothing the chef must decide."""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from types import SimpleNamespace

import yaml
from PIL import Image

from course.stage.card import ROOT, beat_times, load_card, load_manifest, load_timing, narration_text, timed_cues, word_times

BUILD = Path(os.environ.get("KITCHEN_BUILD", ROOT / "build"))
PACK = Path(os.environ.get("KITCHEN_PACK", ROOT.parent))  # outputs/CSCI-5273-Manim-Course
STAGES = ["question", "animation", "state", "rule", "changed_example", "prediction", "explanation"]
MIN_FREE_GIB = 8
from course.catalog import CHAPTERS, MAIN, SUPPLEMENTS, is_main
DRIFT_PER_DISH = 0.05  # A dish's container may outrun its compiled frames by this much; more means a broken render.
MAIN_CHAPTERS = 16  # Later chapters are the practice walkthrough and warm-up, which get their own video.
QUALITY = {"preview": ("1280,720", "720p30"), "final": ("1920,1080", "1080p30")}
ENV = dict(os.environ, PYTHONWARNINGS="ignore")


def dishes():
    return sorted((p.stem for p in (ROOT / "recipes").glob("*.yaml")), key=lambda d: [int(x) for x in d.split(".")])


def chapter_of(d):
    return d.split(".")[0]


def run(cmd, **kw):
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kw)


def probe_duration(path, stream=None):
    args = ["ffprobe", "-v", "error"]
    if stream:
        args += ["-select_streams", stream, "-show_entries", "stream=duration", "-of", "csv=p=0", str(path)]
    else:
        args += ["-show_entries", "format=duration", "-of", "csv=p=0", str(path)]
    return float(run(args).stdout.strip().splitlines()[0])


def free_gib():
    return shutil.disk_usage(ROOT).free / 2 ** 30


def manim(dish, res, media, *extra, env=None):
    e = dict(ENV, KITCHEN_DISH=dish, **(env or {}))
    return subprocess.run([str(ROOT / ".venv/bin/manim"), "render", "course/stage/player.py", "Dish", "--disable_caching", "-v", "ERROR",
                           "--progress_bar", "none", "-r", res, "--fps", "30", "--renderer", "cairo", "--media_dir", str(media), *extra],
                          cwd=ROOT, env=e, capture_output=True, text=True)


def dry_run(dish):
    lint = BUILD / "lint" / f"{dish}.json"
    if lint.exists():
        lint.unlink()
    r = manim(dish, "640,360", BUILD / "media" / "dry" / dish, "--dry_run")
    if not lint.exists():
        tail = [x for x in (r.stdout + r.stderr).splitlines() if x.strip()][-6:]
        return ["crashed: " + " ".join(t.strip("│ ") for t in tail)[:300]], 0
    data = json.loads(lint.read_text())
    return data["problems"], data["duration"]


def schedule_problems(only=None):
    """Catch a broken timeline before Manim draws a frame."""
    from course.stage.moves import REGISTRY
    from course.stage.timeline import compile_dish
    manifest, timing, texts = load_manifest(), load_timing(), narration_text()
    defaults = {k: v["t"] for k, v in REGISTRY.items()}
    problems = []
    for dish in dishes():
        if only and dish != only:
            continue
        try:
            compile_dish(load_card(dish), manifest, timing, texts, defaults)
        except (ValueError, KeyError) as exc:
            problems.append(f"{dish}: {exc}")
    return problems


def long_narrated_gaps(limit=20.0):
    """Narrated stretches with no authored move for limit seconds or more. Advisory: the renderer breaks
    these only with a corner-tag pulse, so they still read as still frames. Pause and reading holds are exempt."""
    from course.stage.moves import REGISTRY
    from course.stage.timeline import compile_beat
    manifest, timing, texts = load_manifest(), load_timing(), narration_text()
    defaults = {k: v["t"] for k, v in REGISTRY.items()}
    found = []
    for dish in dishes():
        card = load_card(dish)
        times, _ = beat_times(card, manifest)
        for beat, slot in zip(card["beats"], times):
            entry = manifest[beat["id"]]
            measured = word_times(beat["id"], manifest, timing)
            schedule = compile_beat(beat, entry, measured, texts[beat["id"]], card.get("pad", 2.2), defaults=defaults)
            frozen = beat["stage"] == "prediction" or bool(beat.get("reading_hold"))
            now = 0.0
            gaps = []
            for move in schedule.moves:
                start = move["start"] / 30
                if start > now:
                    gaps.append(start - now)
                now = start + move["frames"] / 30
            remaining = slot["total"] - now - slot["hold"] - (0.2 if slot["hold"] else 0.0)
            if remaining > 0.02 and not frozen:
                gaps.append(remaining)
            found += [(beat["id"], round(gap, 1)) for gap in gaps if gap >= limit]
    return found


# What a video depends on. If any of this changes, it must be cooked again.
_shared = None


def fingerprint(dish):
    from course.tools.evidence import fingerprint_dish
    return fingerprint_dish(dish)


def fp_path(dish):
    return video_path(dish, "final").with_suffix(".fp")


def taste_is_current(dish):
    """A taste file counts only when it was written after the video it claims to describe."""
    tasted = BUILD / "taste" / f"{dish}.json"
    video = video_path(dish, "final")
    if not tasted.exists() or not video.exists():
        return False
    if tasted.stat().st_mtime < video.stat().st_mtime - 1:
        return False
    return not json.loads(tasted.read_text()).get("problems")


def is_fresh(dish):
    from course.tools.evidence import artifact_matches
    video=video_path(dish, "final");receipt=video.with_suffix('.receipt.json')
    if not video.exists() or not receipt.exists():
        return False
    try:
        data=json.loads(receipt.read_text())
        return (data['profile']=='final' and data['input_fingerprint']==fingerprint(dish)
                and artifact_matches(video,data['output_hashes'].get(video.name)))
    except (ValueError,KeyError):
        return False


def group_fp(members):
    from course.tools.evidence import fingerprint_assembly
    return fingerprint_assembly({"members": members, "receipts": [json.loads(video_path(d,"final").with_suffix('.receipt.json').read_text()) for d in members]})



# check ----------------------------------------------------------------------
def check_static():
    """Everything that can be verified without running Manim."""
    errors = []
    decks = json.loads((ROOT / "sources" / "decks.json").read_text())
    concepts = json.loads((ROOT / "sources" / "concepts.json").read_text())
    clar = yaml.safe_load((ROOT / "sources" / "clarifications.yaml").read_text())
    manifest = load_manifest()
    texts = narration_text()
    used_concepts, used_clar, chapter_minutes = {}, set(), {}
    from course.stage.moves import REGISTRY, resolve
    for d in dishes():
        card = load_card(d)
        stages = [b["stage"] for b in card["beats"]]
        for st in STAGES if is_main(d) else ():
            if st not in stages and not (d == "16.1" and st == "state"):
                errors.append(f"{d}: no {st} beat")
        seen = set()
        for b in card["beats"]:
            bid = b["id"]
            if bid in seen:
                errors.append(f"{bid}: duplicate id")
            seen.add(bid)
            if bid not in manifest or not (ROOT / manifest[bid]["wav"]).exists():
                errors.append(f"{bid}: no narration audio")
            if bid not in texts:
                errors.append(f"{bid}: no narration text")
            if not b.get("pdf"):
                errors.append(f"{bid}: no PDF citation")
            else:
                deck, *pages = b["pdf"]
                if deck not in decks:
                    errors.append(f"{bid}: unknown deck {deck}")
                elif not all(1 <= p <= decks[deck]["pages"] for p in pages):
                    errors.append(f"{bid}: page {pages} outside {deck}")
            for c in b.get("concepts") or []:
                if c not in concepts:
                    errors.append(f"{bid}: unknown concept {c}")
                else:
                    used_concepts.setdefault(c, []).append(bid)
                    pages = concepts[c]["pages"]
                    lect = f"lec{concepts[c]['lecture'][1:]}"
                    if b["pdf"] and b["pdf"][0].startswith(lect) and not any(min(pages) - 4 <= cited <= max(pages) + 4 for cited in b["pdf"][1:]):
                        errors.append(f"{bid}: cites p{b['pdf'][1]} but {c} is on pp{min(pages)}-{max(pages)}")
            used_clar.update(b.get("clarifications") or [])
            for raw in b.get("moves") or []:
                name = next(k for k in raw if k not in ("when", "t", "event_id"))
                if name not in REGISTRY:
                    errors.append(f"{bid}: unknown move {name}")
                try:
                    resolve(raw[name] or {})
                except Exception as exc:
                    errors.append(f"{bid}: bad trace reference in {name}: {exc}")
        for c in card.get("concepts") or []:
            if not any(c in (b.get("concepts") or []) for b in card["beats"]):
                errors.append(f"{d}: concept {c} has no beat")
        chapter_minutes.setdefault(chapter_of(d), [0, 0])
        chapter_minutes[chapter_of(d)][0] += beat_times(card, manifest)[1] / 60
        chapter_minutes[chapter_of(d)][1] += card["target_min"]
    missing = set(concepts) - set(used_concepts)
    if missing:
        errors.append(f"unmapped concepts: {sorted(missing)}")
    for item in clar:
        if item["id"] not in used_clar:
            errors.append(f"clarification {item['id']} appears on no beat")
    if set(texts) - set(manifest):
        errors.append("narration text without audio")
    timing = load_timing()
    unmeasured = [b for b in manifest if not word_times(b, manifest, timing)]
    if unmeasured:
        errors.append(f"{len(unmeasured)} clips have no word timing, such as {unmeasured[0]}")
    pacing_path=ROOT/'sources/pacing-targets.yaml'
    pacing=yaml.safe_load(pacing_path.read_text()) if pacing_path.exists() else {}
    for ch in chapter_minutes:
        if ch in pacing:chapter_minutes[ch][1]=pacing[ch]
    for ch, (actual, target) in chapter_minutes.items():
        if abs(actual - target) > 0.1 * target:
            print(f"PACING: chapter {ch}: {actual:.1f} min vs target {target}")
    total = sum(v[0] for k, v in chapter_minutes.items() if int(k) <= MAIN_CHAPTERS)
    if not 210 <= total <= 240:
        errors.append(f"course length {total:.1f} min is outside 210-240")
    return errors, used_concepts, total, chapter_minutes


def write_coverage(used):
    concepts = json.loads((ROOT / "sources" / "concepts.json").read_text())
    lines = ["concept,lecture,dish,beats,pdf_pages"]
    for name, info in concepts.items():
        beats = used.get(name, [])
        dish = beats[0].rsplit(".", 1)[0] if beats else ""
        lines.append(f'"{name}",{info["lecture"]},{dish},"{" ".join(beats)}","{info["pages"][0]}-{info["pages"][-1]}"')
    (ROOT / "coverage.csv").write_text("\n".join(lines) + "\n")


def cmd_check(args):
    failures = []
    import manim as _m
    if _m.__version__ != "0.22.1":
        failures.append(f"Manim is {_m.__version__}, expected 0.22.1")
    if sys.version_info[:2] != (3, 12):
        failures.append("Python is not 3.12")
    for tool in ("ffmpeg", "ffprobe", "dvisvgm"):
        if not shutil.which(tool):
            failures.append(f"{tool} is missing")
    from course.tools import sources
    try:
        from course.tools.preparation import audit, timeline_findings
        failures.extend(x.message for x in audit() + timeline_findings() if x.severity == "error")
    except SystemExit as exc:
        failures.append(str(exc))
    t = subprocess.run([sys.executable, "-W", "ignore", "-m", "pytest", "course/tests", "-q"], cwd=ROOT, capture_output=True, text=True, env=ENV)
    print(t.stdout.strip().splitlines()[-1])
    if t.returncode:
        failures.append("calculation tests failed")
    errors, used, total, minutes = check_static()
    failures += errors
    # Coverage is generated by prepare, not by check.
    print(f"{len(used)} of 176 concepts mapped; {len(dishes())} cards; {total:.1f} min")
    from concurrent.futures import ThreadPoolExecutor
    if not args.quick:
        with ThreadPoolExecutor(8) as pool:
            for d, (problems, _) in zip(dishes(), pool.map(dry_run, dishes())):
                failures += [f"{d}: {p}" for p in sorted(set(problems))]
    for f in failures[:40]:
        print("  FAIL", f)
    if failures:
        print(f"NOT READY: {len(failures)} problem(s)")
        return 1
    print("MISE COMPLETE")
    return 0


# cook -----------------------------------------------------------------------
def video_path(dish, quality):
    return BUILD / "dishes" / quality / f"{dish}.mp4"


def cmd_cook(args):
    quality = "final" if args.final else "preview"
    if free_gib() < MIN_FREE_GIB:
        print(f"STOP: only {free_gib():.1f} GiB free; report this.")
        return 1
    from course.tools.evidence import fingerprint_dish
    input_fp = fingerprint_dish(args.dish, {"profile": quality})
    problems = schedule_problems(args.dish)
    if problems:
        print("Fix these before cooking (see CHEF.md):")
        for p in problems[:30]:
            print("  ", p)
        return 1
    res, folder = QUALITY[quality]
    media = BUILD / "media" / quality / args.dish
    r = manim(args.dish, res, media)
    produced = media / "videos" / "player" / folder / "Dish.mp4"
    if r.returncode or not produced.exists():
        print((r.stdout + r.stderr)[-1500:])
        print("STOP: render failed; report this.")
        return 1
    lint = BUILD / "lint" / f"{args.dish}.json"
    if lint.exists():
        scene_problems = json.loads(lint.read_text()).get("problems") or []
        if scene_problems:
            print("Fix these before cooking (see CHEF.md):")
            for p in sorted(set(scene_problems))[:30]:
                print("  ", p)
            return 1
    if fingerprint_dish(args.dish, {"profile": quality}) != input_fp:
        print("STOP: inputs changed during rendering; keep the render cache and cook again.")
        return 1
    out = video_path(args.dish, quality)
    out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(produced, out)
    from course.tools.evidence import write_render_receipt
    write_render_receipt(out, args.dish, quality, input_fingerprint=input_fp)
    if quality == "final":
        fp_path(args.dish).write_text(fingerprint(args.dish))
    print(f"{args.dish}  {probe_duration(out) / 60:.2f} min")
    return 0


# taste ----------------------------------------------------------------------
def fmt(t, sep=","):
    millis = round(t * 1000)
    seconds, ms = divmod(millis, 1000)
    hours, rem = divmod(seconds, 3600)
    minutes, sec = divmod(rem, 60)
    return f"{hours:02}:{minutes:02}:{sec:02}{sep}{ms:03}"



def cues_for(dish, offset=0.0):
    card, manifest, texts, timing = load_card(dish), load_manifest(), narration_text(), load_timing()
    from course.stage.timeline import compile_dish
    from course.stage.moves import REGISTRY
    timeline = compile_dish(card, manifest, timing, texts, {k:v['t'] for k,v in REGISTRY.items()})
    out, frame_offset = [], round(offset*timeline.fps)
    for beat in timeline.beats:
        for i, cue in enumerate(beat.captions):
            out.append({"start": (frame_offset+cue['start'])/timeline.fps,
                        "end": (frame_offset+cue['end'])/timeline.fps,
                        "text": cue['text'], "beat": beat.beat_id, "first": i == 0})
        frame_offset += beat.frames
    return out


def two_lines(text, width=42):
    if len(text) <= width:
        return text
    words, a = text.split(), ""
    while words and len(a) + len(words[0]) + 1 <= max(width, (len(text) + 1) // 2):
        a = (a + " " + words.pop(0)).strip()
    return a + "\n" + " ".join(words)


def write_subs(cues, srt, vtt):
    srt.parent.mkdir(parents=True, exist_ok=True)
    s = [f"{i}\n{fmt(c['start'])} --> {fmt(c['end'])}\n{two_lines(c['text'])}\n" for i, c in enumerate(cues, 1)]
    srt.write_text("\n".join(s))
    v = ["WEBVTT\n"] + [f"{fmt(c['start'], '.')} --> {fmt(c['end'], '.')}\n{two_lines(c['text'])}\n" for c in cues]
    vtt.write_text("\n".join(v))


def caption_problems(cues):
    bad = []
    for a, b in zip(cues, cues[1:]):
        if b["start"] < a["end"] - 0.002:
            bad.append(f"{b['beat']}: caption overlaps the previous one")
    for c in cues:
        if len(two_lines(c["text"]).splitlines()) > 2:
            bad.append(f"{c['beat']}: caption is over two lines")
        from course.stage.card import MAX_CPS
        if len(c["text"]) / max(c["end"] - c["start"], 0.01) > MAX_CPS:
            bad.append(f"{c['beat']}: caption reads over 20 characters per second")
    return bad


def cmd_taste(args):
    dish = args.dish
    found = [v for v in (video_path(dish, "final"), video_path(dish, "preview")) if v.exists()]
    video = max(found, key=lambda v: v.stat().st_mtime) if found else None
    if not video:
        print("Cook the dish first.")
        return 1
    fails = []
    card, manifest = load_card(dish), load_manifest()
    times, duration = beat_times(card, manifest)
    # The render that just finished already walked the scene and wrote this lint.
    # A second Manim pass only repeats that walk.
    lint = BUILD / "lint" / f"{dish}.json"
    if getattr(args, "reuse_lint", False) and lint.exists():
        fails += sorted(set(json.loads(lint.read_text()).get("problems") or []))
    else:
        problems, duration = dry_run(dish)
        fails += sorted(set(problems))
    actual = probe_duration(video, "v:0")
    if abs(actual - duration) > 0.25:
        fails.append(f"video is {actual:.2f}s but the card's timeline is {duration:.2f}s")
    audio = probe_duration(video, "a:0")
    if audio > actual + 0.1:
        fails.append("audio runs past the video")
    if abs(audio - actual) > 0.25:
        fails.append(f"audio is {audio:.2f}s but video is {actual:.2f}s")
    srt = video.parents[2] / "media" / ("final" if "final" in str(video) else "preview") / dish / "videos" / "player"
    produced = next(srt.glob("*/Dish.srt"), None)
    mine = cues_for(dish)
    fails += sorted(set(caption_problems(mine)))
    if produced:
        starts = [m.group(1) for m in re.finditer(r"(\d\d:\d\d:\d\d,\d{3}) -->", produced.read_text())]
        def secs(s):
            h, m, rest = s.split(":")
            return int(h) * 3600 + int(m) * 60 + float(rest.replace(",", "."))
        firsts = [c["start"] for c in mine]
        if len(starts) == len(firsts):
            worst = max(abs(secs(a) - b) for a, b in zip(starts, firsts))
            if worst > 0.05:
                fails.append(f"Manim's captions differ from the beat table by {worst:.3f}s")
        else:
            fails.append("Manim's caption count differs from the beat table")
    sheet = BUILD / "taste" / f"{dish}.png"
    sheet.parent.mkdir(parents=True, exist_ok=True)
    frames = []
    with tempfile.TemporaryDirectory() as tmp:
        for i, slot in enumerate(times):
            for j, frac in enumerate((0.05, 0.5, 0.97)):
                f = Path(tmp) / f"{i:03}_{j}.png"
                subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(slot["start"] + slot["total"] * frac), "-i", str(video), "-frames:v", "1", "-vf", "scale=426:-2", str(f)], check=False)
                if f.exists():
                    frames.append(f)
        W, H = 426, 240
        rows = (len(frames) + 5) // 6
        page = Image.new("RGB", (W * 6, H * rows))
        for n, f in enumerate(frames):
            page.paste(Image.open(f).convert("RGB"), ((n % 6) * W, (n // 6) * H))
        page.save(sheet)
    from course.tools.stills import report as still_report
    still = still_report(video)
    (BUILD / "taste" / f"{dish}.json").write_text(json.dumps({"dish": dish, "problems": fails, "stills": still, "video": video.name, "quality": video.parent.name}, indent=1))
    print(f"Contact sheet: build/taste/{dish}.png  Stills: {still['over_10s']:.0%} of the dish in stretches over 10 s; longest {still['longest']:.0f} s")
    for f in fails[:30]:
        print("  FAIL", f)
    print("FAIL" if fails else "PASS")
    return 1 if fails else 0


# plate ----------------------------------------------------------------------
def concat(files, out, extra=()):
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as lst:
        for f in files:
            lst.write(f"file '{Path(f).resolve()}'\n")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst.name, *extra,
                    "-c:v", "copy", "-af", "aresample=async=1", "-c:a", "aac", "-b:a", "192k", str(out)], check=True)
    os.unlink(lst.name)


def verify_playback(path, expected=None, tolerance=None):
    fails = []
    streams = run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type", "-of", "csv=p=0", str(path)]).stdout.split()
    if "video" not in streams or "audio" not in streams:
        fails.append(f"{path.name}: missing a stream ({streams})")
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-map", "0:v", "-map", "0:a", "-f", "null", "-"], capture_output=True, text=True)
    if r.returncode or r.stderr.strip():
        fails.append(f"{path.name}: decode errors: {r.stderr[:200]}")
    d = probe_duration(path)
    for t in (0, d * 0.25, d * 0.5, d * 0.75, max(d - 2, 0)):
        r = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", str(path), "-t", "1", "-f", "null", "-"], capture_output=True, text=True)
        if r.returncode or r.stderr.strip():
            fails.append(f"{path.name}: seek failed at {t:.0f}s")
    tol = tolerance if tolerance is not None else 0.5
    if expected and abs(d - expected) > tol:
        fails.append(f"{path.name}: duration {d:.1f}s, expected {expected:.1f}s")
    return fails, d


def chapter_title(ch):
    return CHAPTERS[str(ch)]


def measured_starts(paths):
    """Where each file starts once concatenated. The concat demuxer advances by each file's container
    duration, which runs a few hundredths of a second past the compiled frames when audio overhangs video."""
    starts, t = [], 0.0
    for path in paths:
        starts.append(t)
        t += probe_duration(path)
    return starts, t


def chapter_cues(ch):
    from course.tools.assembly import course_plans
    plan=course_plans()['chapter-'+str(ch)]
    videos=[video_path(dish,"final") for dish in plan.members]
    if all(video.exists() for video in videos):
        starts,total=measured_starts(videos)
    else:
        starts,total=[plan.offsets[dish]/30 for dish in plan.members],plan.total_frames/30
    cues=[]
    for dish,start in zip(plan.members,starts):
        cues += cues_for(dish,start)
    return cues,total


def cmd_plate(args):
    ch = args.chapter
    members = [d for d in dishes() if chapter_of(d) == ch]
    missing = [d for d in members if not video_path(d, "final").exists()]
    if missing:
        print("Cook these at final quality first:", " ".join(missing))
        return 1
    stale = [d for d in members if not is_fresh(d)]
    if stale:
        print("These dishes changed after their final render. Cook them at final quality again:", " ".join(stale))
        return 1
    plate_identity = group_fp(members)
    out_dir = PACK / "video" / "chapters"
    cap_dir = PACK / "captions"
    out_dir.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "-", chapter_title(ch).lower()).strip("-")
    out = out_dir / f"ch{int(ch):02}-{slug}.mp4"
    cues, expected = chapter_cues(ch)
    srt, vtt = cap_dir / f"ch{int(ch):02}.srt", cap_dir / f"ch{int(ch):02}.vtt"
    write_subs(cues, srt, vtt)
    joined = BUILD / f"ch{ch}.joined.mp4"
    concat([video_path(d, "final") for d in members], joined)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(joined), "-i", str(srt), "-map", "0", "-map", "1", "-c", "copy", "-c:s", "mov_text",
                    "-metadata:s:s:0", "language=eng", "-movflags", "+faststart", str(out)], check=True)
    joined.unlink()
    fails, d = verify_playback(out, expected)
    fails += caption_problems(cues)
    if plate_identity != group_fp(members):
        fails.append('chapter inputs changed during assembly; replate stable inputs')
    pacing_path=ROOT/"sources/pacing-targets.yaml"
    pacing=yaml.safe_load(pacing_path.read_text()) if pacing_path.exists() else {}
    target = pacing.get(ch,sum(load_card(x)["target_min"] for x in members))
    if abs(d / 60 - target) > 0.1 * target:
        print(f"PACING: {d / 60:.1f} min vs {target} min target; see sources/pacing-decisions.json")
    for f in fails[:20]:
        print("  FAIL", f)
    if fails:
        print("FAIL")
        return 1
    (PACK / "video" / "dishes").mkdir(parents=True, exist_ok=True)
    for x in members:
        shutil.copy(video_path(x, "final"), PACK / "video" / "dishes" / f"{x}.mp4")
        write_subs(cues_for(x), cap_dir / "dishes" / f"{x}.srt", cap_dir / "dishes" / f"{x}.vtt")
        shutil.rmtree(BUILD / "media" / "final" / x, ignore_errors=True)
        shutil.rmtree(BUILD / "media" / "preview" / x, ignore_errors=True)
    (BUILD / "chapters").mkdir(exist_ok=True)
    from course.tools.assembly import course_plans
    from course.tools.evidence import write_assembly_receipt
    write_assembly_receipt(out,course_plans()['chapter-'+ch],members)
    (BUILD / "chapters" / f"{ch}.fp").write_text(group_fp(members))
    (BUILD / "served.fp").unlink(missing_ok=True)
    print(f"{out.relative_to(PACK)}  {d / 60:.1f} min")
    print("PASS")
    return 0


# serve ----------------------------------------------------------------------
def transcript(chapter_start, output_id="main"):
    clar = {c["id"]: c for c in yaml.safe_load((ROOT / "sources" / "clarifications.yaml").read_text())}
    texts = narration_text()
    manifest = load_manifest()
    lines = ["# CSCI 5273 Lectures 6-15: Transcript", "",
             f"Timecodes are positions in the {output_id} video. Page numbers are 1-based instructor PDF pages.", ""]
    current = None
    t = 0.0
    for d in dishes():
        card = load_card(d)
        ch = chapter_of(d)
        if ch not in chapter_start:
            continue
        t = chapter_start[ch] + sum(beat_times(load_card(x), manifest)[1] for x in dishes() if chapter_of(x) == ch and [int(n) for n in x.split(".")] < [int(n) for n in d.split(".")])
        if ch != current:
            current = ch
            lines += [f"## Chapter {ch}: {chapter_title(ch)}", ""]
        lines += [f"### {d} {card['title']}", ""]
        times, total = beat_times(card, manifest)
        for b, slot in zip(card["beats"], times):
            deck, *pages = b["pdf"]
            tag = f"[{fmt(t + slot['start'] + slot.get('pre_roll',0), '.')[:8]}] ({deck} p{','.join(map(str, pages))})"
            notes = "".join(f" **Clarification:** {clar[c]['text']}" for c in b.get("clarifications") or [])
            lines += [f"{tag} {texts[b['id']]}{notes}", ""]
        t += total
    if output_id != "main":
        lines[0] = "# CSCI 5273 Supplement Transcript"
    return "\n".join(lines)


def pending_reviews():
    """Explicit category reviews still missing for the current final renders: four per dish."""
    from course.tools.evidence import artifact_hash
    review = BUILD / "review" / "decisions.jsonl"
    decisions = [json.loads(line) for line in review.read_text().splitlines() if line.strip()] if review.exists() else []
    pending = 0
    for dish in dishes():
        video = BUILD / "dishes" / "final" / f"{dish}.mp4"
        sha = artifact_hash(video) if video.exists() else None
        for category in ("content", "visual", "audio", "captions"):
            matching = [x for x in decisions if x["artifact_hash"] == sha and x["category"] == category]
            if not matching or matching[-1]["result"] != "passed":
                pending += 1
    return pending


def guide(rows, total):
    table = "\n".join(f"| {n} | {title} | {start} | {length} |" for n, title, start, length in rows)
    return f"""# CSCI 5273 Lectures 6-15: Viewing Guide

A narrated course of {total / 60:.0f} minutes. Watch `video/CSCI-5273-Lectures-06-15.mp4` straight through, or use a single chapter from `video/chapters/`.

| Chapter | Topic | Starts at | Length |
|---|---|---|---|
{table}

The corner tags name slides from the instructor's PDFs (Lectures 6–15). The page number is the page of the instructor's PDF.

**Captions.** Chapter and combined MP4s carry selectable English caption tracks. Individual study segments use the supplied sidecar captions in the study player. Subtitle files are also available as `.srt` and `.vtt` in `captions/`.

**Chapter markers.** The combined video has 11 embedded markers. A player with MP4 chapter support can jump between them.

**Prediction pauses.** The video holds on each prediction prompt with a progress bar and a "Pause" length label, so you can answer before the explanation. The study player goes further: it waits on the prompt until you press Continue.

**Transcript.** `transcript/transcript.md` has every narrated beat with its timecode and instructor PDF page.

**Practice video.** `video/CSCI-5273-Practice-and-Warm-up.mp4` holds chapter 17 (Practice midterm walkthrough) and chapter 18 (Wednesday warm-up), with two chapter markers. Its questions are generated practice, not the instructor's exam.

**Standalone playback.** In the delivered handoff, double-click `Play Course.command` or run `python3 play.py`. Only Python is required for playback.

**Study player for developers.** Run `./kitchen open` from `source/` to start the study player; if you only have this delivered folder, unpack `CSCI-5273-Course-Source.zip` first. The player pauses at each prediction until you continue, and it saves your progress in this browser. Transcript supplement for the practice video: `transcript/supplements.md`.

**Rebuilding.** Everything needed is in `source/`, which is also packaged as `CSCI-5273-Course-Source.zip`. The steps are in `source/SETUP.md`.

**Status.** Current preparation, media, reproduction and review results are recorded in `verification/implementation-status.json`. Only a current `release_verified: true` represents a fully reviewed release.

These are study explanations and constructed examples, not an official exam outline.
"""


def cmd_serve(args):
    from course.tools.assembly import write_plans
    assembly_plans=write_plans()
    missing = []
    every = sorted({chapter_of(d) for d in dishes()}, key=int)
    unknown = set(every) - set(CHAPTERS)
    if unknown:
        print("STOP: chapters outside the course catalog:", sorted(unknown))
        return 1
    chapters = [c for c in every if c in MAIN]
    extras = [c for c in every if c in SUPPLEMENTS]
    files, extra_files = [], []
    for ch in every:
        found = sorted((PACK / "video" / "chapters").glob(f"ch{int(ch):02}-*.mp4"))
        if not found:
            missing.append(ch)
        else:
            (files if ch in chapters else extra_files).append(found[0])
    if missing:
        print("Plate these chapters first:", " ".join(missing))
        return 1
    from course.tools.evidence import artifact_hash,artifact_matches
    for ch,path in zip(chapters+extras,files+extra_files):
        members=[d for d in dishes() if chapter_of(d)==ch]
        mark=BUILD/'chapters'/f'{ch}.fp'
        receipt=path.with_suffix('.receipt.json')
        if (not all(is_fresh(d) for d in members) or not mark.exists()
                or mark.read_text()!=group_fp(members) or not receipt.exists()
                or not artifact_matches(path,json.loads(receipt.read_text()).get('artifact_hash'))):
            print(f"STOP: chapter {ch} is stale; plate it before serving")
            return 1
    source_identity=group_fp(dishes())
    chapter_identities={str(p):artifact_hash(p) for p in files+extra_files}
    fails = []
    meta = [";FFMETADATA1", "title=CSCI 5273 Lectures 6-15"]
    all_cues, starts, rows, t = [], {}, [], 0.0
    for ch, f in zip(chapters, files):
        d = probe_duration(f)
        if not matches_plan(d, assembly_plans["chapter-"+ch]):
            print(f"STOP: chapter {ch} does not match its compiled timeline")
            return 1
        starts[ch] = t
        meta += ["[CHAPTER]", "TIMEBASE=1/1000", f"START={int(t * 1000)}", f"END={int((t + d) * 1000)}", f"title={chapter_title(ch)}"]
        cues, _ = chapter_cues(ch)
        all_cues += [dict(c, start=c["start"] + t, end=c["end"] + t) for c in cues]
        rows.append((ch, chapter_title(ch), fmt(round(t))[:8], f"{d / 60:.1f} min"))
        t += d
    meta_path = BUILD / "chapters.ffmeta"
    meta_path.write_text("\n".join(meta) + "\n")
    caps = PACK / "captions"
    write_subs(all_cues, caps / "combined.srt", caps / "combined.vtt")
    fails += caption_problems(all_cues)
    joined = BUILD / "combined.joined.mp4"
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as lst:
        for f in files:
            lst.write(f"file '{Path(f).resolve()}'\n")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst.name,
                    "-c:v", "copy", "-af", "aresample=async=1", "-c:a", "aac", "-b:a", "192k", str(joined)], check=True)
    os.unlink(lst.name)
    combined = PACK / "video" / "CSCI-5273-Lectures-06-15.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(joined), "-i", str(meta_path), "-i", str(caps / "combined.srt"), "-map", "0", "-map", "2",
                    "-map_metadata", "1", "-c", "copy", "-c:s", "mov_text", "-metadata:s:s:0", "language=eng", "-movflags", "+faststart", str(combined)], check=True)
    joined.unlink()
    pf, dur = verify_playback(combined, t)
    fails += pf
    probe = run(["ffprobe", "-v", "error", "-show_chapters", "-show_streams", "-of", "json", str(combined)]).stdout
    data = json.loads(probe)
    if len(data["chapters"]) != 11:
        fails.append(f"combined video has {len(data['chapters'])} chapter markers")
    if not any(s["codec_type"] == "subtitle" for s in data["streams"]):
        fails.append("combined video has no caption track")
    if not 210 <= dur / 60 <= 240:
        fails.append(f"combined length {dur / 60:.1f} min is outside 210-240")
    if extras:
        fails += second_video(extras, extra_files, caps)
    (PACK / "transcript").mkdir(exist_ok=True)
    (PACK / "transcript" / "transcript.md").write_text(transcript(starts))
    if extras:
        extra_starts = {}
        extra_time = 0.0
        for ch, path in zip(extras, extra_files):
            extra_starts[ch] = extra_time
            extra_time += probe_duration(path)
        (PACK / "transcript" / "supplements.md").write_text(transcript(extra_starts, "supplements"))
    (PACK / "README.md").write_text(guide(rows, dur))
    fails += reproduce()
    tastes = [json.loads(f.read_text()) for f in (BUILD / "taste").glob("*.json")]
    stills = {x["dish"]: x["stills"] for x in tastes if x["dish"] in dishes()}
    if source_identity!=group_fp(dishes()) or any(artifact_hash(Path(p))!=identity for p,identity in chapter_identities.items()):
        fails.append('assembly inputs changed during serve; rebuild from stable inputs')
    report = {"length_min": round(dur / 60, 1), "chapters": rows, "problems": fails, "stills": stills, "reviews_pending": pending_reviews()}
    if stills:
        seconds = sum(v["seconds"] for v in stills.values()) or 1
        report["stills_over_10s"] = round(sum(v["over_10s"] * v["seconds"] for v in stills.values()) / seconds, 3)
        report["longest_still"] = max(v["longest"] for v in stills.values())
    (PACK / "final-report.json").write_text(json.dumps(report, indent=1))
    from course.tools.evidence import write_assembly_receipt
    write_assembly_receipt(combined,assembly_plans['main'],assembly_plans['main'].members,fails)
    if extras:
        write_assembly_receipt(PACK/'video/CSCI-5273-Practice-and-Warm-up.mp4',assembly_plans['supplements'],assembly_plans['supplements'].members,fails)
    from course.tools.release_status import refresh
    refresh()
    if not fails:
        (BUILD / "served.fp").write_text(group_fp(dishes()))
    for f in fails[:30]:
        print("  FAIL", f)
    print("Report: final-report.json")
    print("FAIL" if fails else "PASS")
    return 1 if fails else 0


def matches_plan(seconds, plan):
    return abs(seconds - plan.total_frames/30) <= DRIFT_PER_DISH * len(plan.members) + 1/30


def second_video(chapters, files, caps):
    """The practice walkthrough and warm-up, in their own file with their own markers and captions."""
    meta = [";FFMETADATA1", "title=CSCI 5273 Practice and Warm-up"]
    cues_all, t = [], 0.0
    for ch, f in zip(chapters, files):
        d = probe_duration(f)
        meta += ["[CHAPTER]", "TIMEBASE=1/1000", f"START={int(t * 1000)}", f"END={int((t + d) * 1000)}", f"title={chapter_title(ch)}"]
        cues, _ = chapter_cues(ch)
        cues_all += [dict(c, start=c["start"] + t, end=c["end"] + t) for c in cues]
        t += d
    meta_path = BUILD / "extra.ffmeta"
    meta_path.write_text("\n".join(meta) + "\n")
    write_subs(cues_all, caps / "practice.srt", caps / "practice.vtt")
    joined = BUILD / "extra.joined.mp4"
    concat(files, joined, ("-map", "0:v", "-map", "0:a"))
    out = PACK / "video" / "CSCI-5273-Practice-and-Warm-up.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(joined), "-i", str(meta_path), "-i", str(caps / "practice.srt"), "-map", "0", "-map", "2",
                    "-map_metadata", "1", "-c", "copy", "-c:s", "mov_text", "-metadata:s:s:0", "language=eng", "-movflags", "+faststart", str(out)], check=True)
    joined.unlink()
    fails, _ = verify_playback(out, t)
    return fails + caption_problems(cues_all)


def reproduce(dish="6.1"):
    """Render a dish from a clean copy of the package, using only supplied source and audio."""
    fails = []
    with tempfile.TemporaryDirectory(dir=BUILD) as tmp:
        clean = Path(tmp) / "source"
        shutil.copytree(ROOT, clean, ignore=shutil.ignore_patterns(".venv", ".venv-speech", "build", "__pycache__", ".pytest_cache"))
        clean_env = dict(ENV, KITCHEN_DISH=dish)
        r = subprocess.run([str(Path(os.environ.get("KITCHEN_REPRO_PYTHON", ROOT / "build/reproduction/.venv/bin/python"))), "-m", "manim", "render", "course/stage/player.py", "Dish", "--disable_caching", "-v", "ERROR", "--progress_bar", "none",
                            "-r", "1280,720", "--fps", "30", "--media_dir", str(clean / "m")], cwd=clean, env=clean_env, capture_output=True, text=True)
        out = clean / "m" / "videos" / "player" / "720p30" / "Dish.mp4"
        if r.returncode or not out.exists():
            return [f"clean-copy render failed: {(r.stdout + r.stderr)[-300:]}"]
        expected = beat_times(load_card(dish), load_manifest())[1]
        if abs(probe_duration(out, "v:0") - expected) > 0.25:
            fails.append("clean-copy render has the wrong duration")
        same = json.loads((clean / "narration" / "manifest.json").read_text()) == load_manifest()
        if not same:
            fails.append("clean-copy narration manifest differs")
    print("Clean-copy render: " + ("failed" if fails else "matches"))
    return fails


# run ------------------------------------------------------------------------
def stop(where):
    print(f"\nSTOP at {where}. See \"If it stops\" in CHEF.md. Run ./kitchen run again after that; finished dishes aren't redone.")
    return 1


def cook_everything():
    problems = schedule_problems()
    if problems:
        print("Fix these before rendering:")
        for p in problems[:30]:
            print("  ", p)
        return stop("the schedule check")
    gaps = long_narrated_gaps()
    if gaps:
        print(f"Note: {len(gaps)} narrated stretches have no authored move for 20 s or more; longest {max(g for _, g in gaps):.1f} s")
    all_dishes=dishes()
    chapters=sorted({chapter_of(d) for d in all_dishes},key=int)
    completed=[]
    def progress(state,chapter=None,dish=None):
        (BUILD/'production-progress.json').write_text(json.dumps({
            'state':state,'chapter':chapter,'dish':dish,'completed_chapters':completed,
            'current_final_dishes':sum(is_fresh(d) for d in all_dishes),
            'total_dishes':len(all_dishes),'updated_at':time.time()},indent=2))
    for ch in chapters:
        members=[d for d in all_dishes if chapter_of(d)==ch]
        for d in members:
            if not is_fresh(d):
                progress('rendering',ch,d)
                print(f"Rendering {d}: {load_card(d)['title']}",flush=True)
                if cmd_cook(SimpleNamespace(dish=d,final=True,preview=False)):
                    progress('stopped',ch,d);return stop(d)
                if cmd_taste(SimpleNamespace(dish=d, reuse_lint=True)):
                    progress('stopped',ch,d);return stop(d)
            else:
                # A taste file left over from the previous video must not clear the new one.
                if not taste_is_current(d):
                    if cmd_taste(SimpleNamespace(dish=d, reuse_lint=True)):
                        progress('stopped',ch,d);return stop(d)
        mark=BUILD/'chapters'/f'{ch}.fp'
        if not mark.exists() or mark.read_text()!=group_fp(members):
            progress('assembling chapter',ch)
            print(f"Assembling chapter {ch}",flush=True)
            if cmd_plate(SimpleNamespace(chapter=ch)):
                progress('stopped',ch);return stop(f'chapter {ch}')
        completed.append(ch);progress('chapter ready',ch)
        print(f"Chapter {ch} ready",flush=True)
    mark=BUILD/'served.fp'
    if not mark.exists() or mark.read_text()!=group_fp(all_dishes):
        progress('assembling course')
        if cmd_serve(SimpleNamespace()):
            progress('stopped');return stop('serve')
    from course.tools import player_build
    player_build.main()
    progress('media built; perceptual review pending')
    print('Media built. Run ./kitchen review and ./kitchen verify-release for review evidence.',flush=True)
    return 0


def freeze():
    """Cook from a snapshot, so prep can keep working while a release cooks."""
    frozen = BUILD / "frozen"
    shutil.rmtree(frozen, ignore_errors=True)
    frozen.mkdir(parents=True)
    for item in ROOT.iterdir():
        if item.name in (".venv", ".venv-speech", "build", "__pycache__", ".pytest_cache"):
            continue
        if subprocess.run(["cp", "-cRp", str(item), str(frozen)], capture_output=True).returncode:
            subprocess.run(["cp", "-Rp", str(item), str(frozen)], check=True)
    (frozen / ".venv").symlink_to(ROOT / ".venv")
    return frozen


def cmd_run(args):
    if args.here:
        return cook_everything()
    print("Checking the kitchen", flush=True)
    if cmd_check(SimpleNamespace(quick=False)):
        return stop("the kitchen check")
    frozen = freeze()
    env = dict(ENV, KITCHEN_BUILD=str(BUILD), KITCHEN_PACK=str(PACK), KITCHEN_REPRO_PYTHON=os.environ.get("KITCHEN_REPRO_PYTHON", str(ROOT / "build/reproduction/.venv/bin/python")))
    code = subprocess.run([sys.executable, "-W", "ignore", "-m", "course.tools.kitchen", "run", "--here"], cwd=frozen, env=env).returncode
    if code == 0:
        shutil.rmtree(frozen, ignore_errors=True)
    return code


# review and open ------------------------------------------------------------
def cmd_review(args):
    from course.tools.local_server import serve
    from course.tools.review_page import build, save_notes
    if not build(BUILD, PACK, [d for d in dishes() if is_fresh(d)], load_card, lambda d: __import__("course.tools.evidence", fromlist=["artifact_hash"]).artifact_hash(video_path(d, "final")) if video_path(d, "final").exists() else ""):
        print("Nothing is cooked yet. Run ./kitchen run first.")
        return 1
    serve({"/": BUILD}, "/review/", lambda _, data: save_notes(data, ROOT / "review-notes.md", BUILD), open_browser=not args.no_browser)
    return 0


def cmd_open(args):
    from course.tools.local_server import serve
    player = PACK / "player"
    if not (player / "index.html").exists():
        print("The player isn't built yet. Run ./kitchen run first.")
        return 1
    from course.tools.sources import DECKS
    serve({"/": player, "/video/": PACK / "video", "/captions/": PACK / "captions", "/decks/": DECKS, "/notes/": ROOT / "sources/snapshot/vault"}, open_browser=not args.no_browser)
    return 0


def main():
    p = argparse.ArgumentParser(prog="kitchen")
    sub = p.add_subparsers(dest="cmd", required=True)
    from course.tools.preparation import cmd_prepare, cmd_audit, cmd_verify
    c = sub.add_parser("prepare")
    c.add_argument("--vault", type=Path)
    c.set_defaults(fn=cmd_prepare)
    c = sub.add_parser("audit")
    c.set_defaults(fn=cmd_audit)
    c = sub.add_parser("verify-release")
    c.set_defaults(fn=cmd_verify)
    c = sub.add_parser("run", help="cook everything that changed, then assemble it all")
    c.add_argument("--here", action="store_true", help=argparse.SUPPRESS)
    c.set_defaults(fn=cmd_run)
    c = sub.add_parser("review", help="see every cooked dish on one page")
    c.add_argument("--no-browser", action="store_true")
    c.set_defaults(fn=cmd_review)
    c = sub.add_parser("open", help="start the study player")
    c.add_argument("--no-browser", action="store_true")
    c.set_defaults(fn=cmd_open)
    c = sub.add_parser("check")
    c.add_argument("--quick", action="store_true", help="skip scene rendering checks")
    c.set_defaults(fn=cmd_check)
    c = sub.add_parser("cook")
    c.add_argument("dish")
    g = c.add_mutually_exclusive_group(required=True)
    g.add_argument("--preview", action="store_true")
    g.add_argument("--final", action="store_true")
    c.set_defaults(fn=cmd_cook)
    c = sub.add_parser("taste")
    c.add_argument("dish")
    c.set_defaults(fn=cmd_taste)
    c = sub.add_parser("plate")
    c.add_argument("chapter")
    c.set_defaults(fn=cmd_plate)
    c = sub.add_parser("serve")
    c.set_defaults(fn=cmd_serve)
    from course.tools.narration_pipeline import add_commands
    add_commands(sub)
    args = p.parse_args()
    sys.exit(args.fn(args))


if __name__ == "__main__":
    main()
