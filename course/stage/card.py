"""Loading a recipe card with its measured narration, and computing its timeline."""
import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
SENTENCE = re.compile(r"(?<=[.!?:;])\s+")
MAX_CPS = 19.5  # Captions must stay readable.


def load_card(dish):
    return yaml.safe_load((ROOT / "recipes" / f"{dish}.yaml").read_text())


def load_manifest():
    import os
    path = Path(os.environ["KITCHEN_MANIFEST"]) if os.environ.get("KITCHEN_MANIFEST") else ROOT / "narration" / "manifest.json"
    return json.loads(path.read_text()) if path.exists() else {}


def split_cues(text, max_chars=84):
    """Break a beat's written text into caption cues of at most two lines."""
    chunks, cues = SENTENCE.split(text.strip()), []
    for chunk in chunks:
        words, cur = chunk.split(), ""
        for w in words:
            if cur and len(cur) + 1 + len(w) > max_chars:
                cues.append(cur)
                cur = w
            else:
                cur = (cur + " " + w).strip()
        if cur:
            cues.append(cur)
    return cues


def load_timing():
    import os
    path = Path(os.environ["KITCHEN_TIMING"]) if os.environ.get("KITCHEN_TIMING") else ROOT / "narration" / "timing.json"
    return json.loads(path.read_text()) if path.exists() else {}


def word_times(beat_id, manifest, timing):
    """Measured [start, end] for each written word, or None if this exact clip hasn't been measured."""
    import hashlib
    entry = timing.get(beat_id)
    asset=manifest.get(beat_id,{})
    if not entry or asset.get('sha')!=entry.get('sha'):
        raise ValueError(f'{beat_id}: missing or stale narration alignment')
    wav=ROOT/asset['wav']
    if entry.get('wav_hash')!=hashlib.sha256(wav.read_bytes()).hexdigest():
        raise ValueError(f'{beat_id}: waveform bytes changed; rebuild word alignment')
    return entry['t']


def phrase_time(text, phrase, speech, times):
    """When the narration reaches a phrase of the written text, or None if the phrase isn't there."""
    at = text.find(phrase)
    if at < 0:
        return None
    if times:
        index = len(text[:at].split())
        if at and not text[at - 1].isspace():
            index -= 1
        if index < len(times):
            return times[index][0]
    return speech * at / max(len(text), 1)


def timed_cues(text, speech, times):
    """Caption cues as (text, offset, duration). A cue stays up until the next one starts."""
    cues = split_cues(text)
    if times and len(times) == len(text.split()):
        from course.stage.captioning import aligned_cues
        return aligned_cues(text,speech,times)
    chars = sum(len(c) for c in cues) or 1
    out, offset = [], 0.0
    for cue in cues:
        dur = speech * len(cue) / chars
        out.append((cue, offset, dur))
        offset += dur
    return out


def beat_times(card, manifest):
    """Beats play back to back: narration, then the dish's pad, then any beat-specific hold."""
    import math
    fps_snap = lambda t: math.ceil(t * 30) / 30
    pad = card.get("pad", 2.2)
    t, out = 0.0, []
    for beat in card["beats"]:
        adj = beat.get("adjust") or {}
        speech = manifest[beat["id"]]["duration"] if beat["id"] in manifest else 0.0
        hold = beat.get("hold", 0) + adj.get("hold", 0)
        total = (round(beat.get("pre_roll", 0) * 30) + __import__("math").ceil(speech * 30) + round(pad * 30) + round(hold * 30) + round(beat.get("reading_hold", 0) * 30) + (6 if hold else 0)) / 30
        out.append({"id": beat["id"], "start": round(t, 4), "speech": speech, "pre_roll": beat.get("pre_roll", 0), "hold": hold, "total": total})
        t = round(t + total, 4)
    return out, t


def narration_text():
    texts = {}
    for path in (ROOT / "narration").glob("[0-9]*.md"):
        beat = None
        for line in path.read_text().splitlines():
            if line.startswith("## "):
                beat = line[3:].strip()
                texts[beat] = []
            elif beat and line.strip():
                texts[beat].append(line.strip())
    return {k: " ".join(v) for k, v in texts.items()}
