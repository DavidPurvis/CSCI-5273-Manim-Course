"""Synthesize every narration beat in the chosen voice, cached by content hash, and measure it."""
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import wave
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml

from course.stage.card import ROOT, narration_text

OUT = ROOT / "narration" / "audio"
CONFIG = yaml.safe_load((ROOT / "narration" / "voice.yaml").read_text())
KOKORO_MODEL = "mlx-community/Kokoro-82M-bf16"
_kokoro = None


def load_rules(config=CONFIG):
    data = yaml.safe_load((ROOT / "narration" / "pronounce.yaml").read_text())
    rules = [(re.compile(r), v) for r, v in (data.get("patterns") or {}).items()]
    words = dict(data.get("words") or {})
    if config["engine"] == "kokoro":
        special = data.get("kokoro") or {}
        words.update(special)
        words.update({k.capitalize(): v.replace(f"[{k}]", f"[{k.capitalize()}]") for k, v in special.items() if k[0].islower()})
    # Longest first, so "Dijkstra's" gets its own rule before "Dijkstra" can claim it.
    for word, spoken in sorted(words.items(), key=lambda kv: -len(kv[0])):
        rules.append((re.compile(r"(?<![\w/.-])" + re.escape(word) + r"(?![\w/-])"), spoken))
    return data.get("version", 1), rules


def spoken_form(text, rules, config=CONFIG):
    for pattern, value in rules:
        text = pattern.sub(value, text)
    text = re.sub(r"(?<=[.!?])\s+", f" [[slnc {config['sentence_pause']}]] ", text)
    return re.sub(r"(?<=[;:])\s+", f" [[slnc {config['clause_pause']}]] ", text)


def plain_form(spoken):
    """Remove Kokoro's phoneme notation, leaving the word."""
    return re.sub(r"\[([^\]]+)\]\(/[^)]*/\)", r"\1", spoken)


def clip_key(spoken, config=CONFIG):
    if config["engine"] == "say":
        label = f"{config['voice']}|{config['rate']}"
    elif config["engine"] == "elevenlabs":
        label = json.dumps(dict(config, processing_version="pcm-loudnorm-v2"), sort_keys=True)
    else:
        label = f"{config['engine']}|{config['voice']}|{config['speed']}"
    return hashlib.sha256(f"{label}|{config['sentence_pause']}|{config['clause_pause']}|{spoken}".encode()).hexdigest()[:20]


def pause_pieces(spoken):
    """Split say/Kokoro pause marks into text and silence. ElevenLabs does not speak those marks."""
    pieces = []
    for i, piece in enumerate(re.split(r"\[\[slnc (\d+)\]\]", spoken)):
        if i % 2:
            pieces.append(("silence", int(piece)))
        elif piece.strip():
            pieces.append(("text", piece.strip()))
    return pieces


def raw_say(spoken, path, config):
    with tempfile.TemporaryDirectory() as tmp:
        txt = Path(tmp) / "t.txt"
        txt.write_text(spoken)
        subprocess.run(["say", "-v", config["voice"], "-r", str(config["rate"]), "-f", str(txt), "-o", str(path)], check=True)


def raw_kokoro(spoken, path, config):
    """Kokoro speaks each stretch between pause marks; the pauses go in as silence."""
    global _kokoro
    import mlx.core as mx
    import numpy as np
    from mlx_audio.tts.utils import load_model
    if _kokoro is None:
        # espeak's packaged data path is broken on this Mac, and our dictionary covers every word Kokoro's lexicon lacks.
        import types
        import mlx_audio.tts.models.kokoro.pipeline as pipeline

        def no_espeak(british):
            raise RuntimeError("not used")
        pipeline._get_misaki_espeak = lambda: types.SimpleNamespace(EspeakFallback=no_espeak)
        _kokoro = load_model(KOKORO_MODEL)
    rate, chunks = 24000, []
    for i, piece in enumerate(re.split(r"\[\[slnc (\d+)\]\]", spoken)):
        if i % 2:
            chunks.append(np.zeros(int(rate * int(piece) / 1000)))
        elif piece.strip():
            for result in _kokoro.generate(text=piece.strip(), voice=config["voice"], speed=config["speed"], lang_code="a", split_pattern=None):
                chunks.append(np.array(result.audio))
    audio = np.clip(np.concatenate(chunks), -1, 1)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes((audio * 32767).astype(np.int16).tobytes())


def raw_elevenlabs(spoken, path, config):
    """Speak with ElevenLabs timestamps. Pause marks become silence so they are not read aloud."""
    from course.tools.narration_pipeline import raw_provider
    raw_provider(spoken, path, config)


def render_clip(spoken, wav, config=CONFIG):
    """Speak the text, then bring it to the course's level and format."""
    engines = {"say": raw_say, "kokoro": raw_kokoro, "elevenlabs": raw_elevenlabs}
    with tempfile.TemporaryDirectory() as tmp:
        raw = Path(tmp) / ("t.aiff" if config["engine"] == "say" else "t.wav")
        engines[config["engine"]](spoken, raw, config)
        part = Path(wav).with_suffix(".part.wav")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(raw), "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
                        "-ar", "48000", "-ac", "1", "-c:a", "pcm_s16le", str(part)], check=True)
        sidecar = raw.with_suffix(".alignment.json")
        if sidecar.exists():
            Path(wav).with_suffix(".alignment.json").write_bytes(sidecar.read_bytes())
        duration = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(part)], check=True, capture_output=True, text=True).stdout.strip()
        if duration == "N/A" or float(duration) <= 0:
            part.unlink(missing_ok=True)
            raise RuntimeError("Speech synthesis produced empty audio; no cached asset was published")
        part.rename(wav)


def synth(job):
    beat, spoken, key = job
    wav = OUT / f"{key}.wav"
    if not wav.exists():
        render_clip(spoken, wav)
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(wav)],
                               check=True, capture_output=True, text=True).stdout)
    return beat, {"sha": key, "wav": f"narration/audio/{key}.wav", "duration": round(dur, 3)}


def main(only=None):
    OUT.mkdir(parents=True, exist_ok=True)
    version, rules = load_rules()
    texts = narration_text()
    jobs = []
    for beat, text in texts.items():
        if only and not beat.startswith(only):
            continue
        spoken = spoken_form(text, rules)
        jobs.append((beat, spoken, clip_key(spoken)))
    with ThreadPoolExecutor(6 if CONFIG["engine"] == "say" else 1) as pool:
        results = dict(pool.map(synth, jobs))
    mpath = ROOT / "narration" / "manifest.json"
    manifest = json.loads(mpath.read_text()) if mpath.exists() and only else {}
    manifest.update(results)
    for beat, entry in manifest.items():
        entry["words"] = len(texts[beat].split())
    mpath.write_text(json.dumps(manifest, indent=0, sort_keys=True))
    # Retain alternate voices for rollback.
    print(f"{len(results)} clips; {sum(e['duration'] for e in results.values()) / 60:.1f} min of speech")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
