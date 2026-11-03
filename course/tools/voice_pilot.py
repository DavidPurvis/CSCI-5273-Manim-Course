"""Synthesize one dish with ElevenLabs and render a preview beside the Samantha cut.

The shipped voice.yaml, narration/audio, and narration timing stay untouched.
Word times come from the synthesizer's character timestamps.
"""
import json
import os
import shutil
import subprocess
import sys

from course.stage.card import ROOT, load_card, narration_text
from course.stage.moves import REGISTRY
from course.stage.timeline import compile_dish
from course.tools.ears import align
from course.tools.preparation import digest
from course.tools.tts import CONFIG, clip_key, load_rules, render_clip, spoken_form

MODEL = "eleven_flash_v2_5"
# Matilda: American, informative educational. The other two audition takes are Alice and Daniel.
VOICE_ID = "XrExE9yKIg1WjnnlVkGX"
VOICE_NAME = "Matilda"
DISH = "1.1"


def heard_words(alignment):
    """Words and their times from ElevenLabs character timestamps, including inserted silence."""
    words = []
    for piece in alignment.get("pieces") or []:
        offset = piece["offset"]
        buf, start, end = "", None, None
        chars = piece.get("characters") or []
        starts = piece.get("starts") or []
        ends = piece.get("ends") or []
        for ch, at, stop in zip(chars, starts, ends):
            if ch.isspace():
                if buf.strip():
                    words.append([buf.strip(), round(offset + start, 4), round(offset + end, 4)])
                buf, start, end = "", None, None
                continue
            if start is None:
                start = at
            end = stop
            buf += ch
        if buf.strip():
            words.append([buf.strip(), round(offset + start, 4), round(offset + end, 4)])
    return words


def word_timing(written, alignment, duration, rules):
    """Map synthesizer times onto the written words. Scale if loudnorm changed the length."""
    raw = float(alignment.get("duration") or 0) or duration
    scale = duration / raw if raw else 1.0
    heard = [[w, s * scale, e * scale] for w, s, e in heard_words(alignment)]
    result = align(written.split(), heard, duration, rules)
    times, ratio, bad = result
    provenance = ["synthesizer_aligned" if item == "asr_aligned" else item for item in result.provenance]
    return times, provenance, ratio, bad


def synthesize_dish(dish=DISH, voice=VOICE_ID, model=MODEL):
    """One take of each beat. A second run reuses the hash cache and does not call the API."""
    if not os.environ.get("ELEVENLABS_API_KEY"):
        raise SystemExit("ELEVENLABS_API_KEY is not set. No clip was synthesized.")
    config = dict(CONFIG, engine="elevenlabs", voice=voice, model_id=model)
    _, rules = load_rules(config)
    texts = {bid: text for bid, text in narration_text().items() if bid.startswith(dish + ".")}
    if not texts:
        raise SystemExit(f"No narration beats for dish {dish}.")
    cache = ROOT / "build" / "voice-pilot" / "cache"
    cache.mkdir(parents=True, exist_ok=True)
    manifest = {}
    spoken_by_beat = {}
    for beat, text in texts.items():
        spoken = spoken_form(text, rules, config)
        spoken_by_beat[beat] = spoken
        key = clip_key(spoken, config)
        wav = cache / f"{key}.wav"
        if not wav.exists():
            render_clip(spoken, wav, config)
        dur = float(subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(wav)],
            check=True, capture_output=True, text=True).stdout.strip())
        manifest[beat] = {"sha": key, "wav": str(wav.relative_to(ROOT)), "duration": round(dur, 3),
                          "words": len(text.split()), "voice": voice, "model": model}
    return manifest, texts, rules, spoken_by_beat


def write_pilot(dish=DISH, voice=VOICE_ID, model=MODEL):
    manifest, texts, rules, _spoken = synthesize_dish(dish, voice, model)
    timing = {}
    for beat, entry in manifest.items():
        wav = ROOT / entry["wav"]
        alignment = json.loads(wav.with_suffix(".alignment.json").read_text())
        times, provenance, ratio, bad = word_timing(texts[beat], alignment, entry["duration"], rules)
        timing[beat] = {"sha": entry["sha"], "t": times, "provenance": provenance,
                        "wav_hash": digest(wav), "aligner": f"elevenlabs:{model}",
                        "mismatch_spans": bad, "corrections": [], "match": round(ratio, 3)}
        entry["match"] = round(ratio, 3)
    dest = ROOT / "build" / "voice-pilot" / dish
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True))
    (dest / "timing.json").write_text(json.dumps(timing, indent=2, sort_keys=True))
    card = load_card(dish)
    timeline = compile_dish(card, manifest, timing, texts, {k: v["t"] for k, v in REGISTRY.items()})
    print(f"{dish} {voice} {model}: {timeline.total_frames / 30 / 60:.2f} min, {len(manifest)} beats")
    for beat, entry in sorted(manifest.items()):
        anchored = sum(1 for item in timing[beat]["provenance"] if item == "synthesizer_aligned")
        print(f"  {beat}: {entry['duration']:.1f}s match {entry['match']:.2f} anchored {anchored}/{len(timing[beat]['t'])}")
    return dest, timeline


def render_preview(dish=DISH):
    """Render a 720p preview. Leaves narration/audio and the Samantha 1.1 file in place."""
    dest = ROOT / "build" / "voice-pilot" / dish
    manifest_path = dest / "manifest.json"
    timing_path = dest / "timing.json"
    if not manifest_path.exists():
        raise SystemExit("Pilot audio is missing. Synthesize it before rendering.")
    from course.tools.kitchen import manim
    media = ROOT / "build" / "voice-pilot" / "media" / dish
    result = manim(dish, "1280,720", media, env={
        "KITCHEN_MANIFEST": str(manifest_path),
        "KITCHEN_TIMING": str(timing_path),
        "KITCHEN_BUILD": str(ROOT / "build" / "voice-pilot"),
    })
    produced = media / "videos" / "player" / "720p30" / "Dish.mp4"
    if result.returncode or not produced.exists():
        tail = (result.stdout + result.stderr)[-1500:]
        secret = os.environ.get("ELEVENLABS_API_KEY")
        if secret:
            tail = tail.replace(secret, "[redacted]")
        print(tail)
        raise SystemExit("Preview render failed.")
    out = dest / f"{dish}-flash.mp4"
    shutil.copy(produced, out)
    beside = ROOT / "build" / "dishes" / "final" / f"{dish}-elevenlabs-flash.mp4"
    beside.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(produced, beside)
    samantha = ROOT / "build" / "dishes" / "final" / f"{dish}.mp4"
    print(f"preview {out}")
    print(f"beside Samantha {beside}")
    if samantha.exists():
        print(f"Samantha stays {samantha}")
    return out


def main():
    write_pilot()
    if "--render" in sys.argv:
        render_preview()


if __name__ == "__main__":
    main()
