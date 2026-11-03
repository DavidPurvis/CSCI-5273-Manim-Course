"""Prep's ears: transcribe every narration clip locally, list what it misheard, and time every written word.

Run with .venv-speech/bin/python -m course.tools.ears. The chef never runs this; its output is narration/timing.json.
"""
import difflib
import json
import re
import sys
import time
from collections import Counter, defaultdict

import yaml

from course.stage.card import ROOT, load_manifest, narration_text
from course.tools.tts import load_rules, plain_form, spoken_form

MODEL = "mlx-community/whisper-small.en-mlx"
CACHE = ROOT / "narration" / ".heard"
OK = ROOT / "sources" / "heard-ok.yaml"
UNITS = {w: i for i, w in enumerate("zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split())}
TENS = {w: (i + 2) * 10 for i, w in enumerate("twenty thirty forty fifty sixty seventy eighty ninety".split())}


def raw_tokens(text):
    """Lowercase tokens with numbers, addresses, and punctuation in one common form."""
    t = text.lower().replace("’", "'").replace("−", " minus ").replace("→", " to ")
    t = re.sub(r"\[\[slnc \d+\]\]", " ", t)
    t = re.sub(r"(?<=\d),(?=\d{3})", "", t)
    t = re.sub(r"(?<=\d)\.(?=\d)", " dot ", t)
    t = re.sub(r"/", " slash ", t)
    t = t.replace("%", " percent ")
    t = re.sub(r"(?<=\d)(st|nd|rd|th)\b", "", t)
    t = re.sub(r"[-–—]", " ", t)
    t = re.sub(r"[^a-z0-9' ]", " ", t)
    return t.split()


def parse_number(tokens, i):
    """Read number words starting at i. Returns the value and the index after them; no number leaves the index at i."""
    total, cur, j = 0, None, i
    while j < len(tokens):
        w = tokens[j]
        if w in UNITS and (cur is None or (cur and cur % 100 == 0) or (UNITS[w] < 10 and cur % 100 >= 20 and cur % 10 == 0)):
            cur = (cur or 0) + UNITS[w]
        elif w in TENS and (cur is None or (cur and cur % 100 == 0)):
            cur = (cur or 0) + TENS[w]
        elif w == "hundred" and cur and cur < 100:
            cur *= 100
        elif w in ("thousand", "million") and cur and cur < 1000:
            total += cur * (1000 if w == "thousand" else 1000000)
            cur = None
        elif w == "and" and cur and cur % 100 == 0 and j + 1 < len(tokens) and (tokens[j + 1] in UNITS or tokens[j + 1] in TENS):
            pass
        else:
            break
        j += 1
    return total + (cur or 0), j


def fold_numbers(tokens):
    """Turn runs of number words into digits, keeping for each output token the index of the input token it came from."""
    out, src, i = [], [], 0
    while i < len(tokens):
        value, j = parse_number(tokens, i)
        if j > i:
            out.append(str(value))
            src.append(i)
            i = j
        else:
            out.append(tokens[i])
            src.append(i)
            i += 1
    return out, src


def norm_with_map(tokens_by_source):
    """Normalize a list of source tokens; return the flat tokens and, for each, its source index."""
    flat, owner = [], []
    for idx, tok in enumerate(tokens_by_source):
        for piece in raw_tokens(tok):
            flat.append(piece)
            owner.append(idx)
    folded, src = fold_numbers(flat)
    return folded, [owner[s] for s in src]


def transcribe(beat, entry):
    if entry.get('config', {}).get('engine') == 'elevenlabs':
        from course.tools.narration_pipeline import valid_clip, heard_words
        wav = ROOT / entry['wav']
        if not valid_clip(wav):
            raise ValueError(f'{beat}: missing synthesizer evidence; run kitchen align, not Whisper')
        return heard_words(json.loads(wav.with_suffix('.alignment.json').read_text()))
    import hashlib
    cached = CACHE / f"{entry['sha']}.json"
    identity=hashlib.sha256((ROOT/entry['wav']).read_bytes()).hexdigest()
    meta_path=cached.with_suffix('.meta.json')
    old_timing_path=ROOT/'narration/timing.json'
    old_timing=json.loads(old_timing_path.read_text()).get(beat,{}) if old_timing_path.exists() else {}
    metadata=json.loads(meta_path.read_text()) if meta_path.exists() else old_timing
    if cached.exists() and metadata.get('wav_hash')==identity and metadata.get('aligner')==MODEL:
        return json.loads(cached.read_text())
    evidence=ROOT/'narration/alignment-evidence';index=evidence/'manifest.json'
    if index.exists():
        record=json.loads(index.read_text()).get('clips',{}).get(entry['sha'],{})
        source=evidence/record.get('file','missing')
        if record.get('wav_hash')==identity and record.get('aligner')==MODEL and source.is_file() and hashlib.sha256(source.read_bytes()).hexdigest()==record.get('sha256'):
            return json.loads(source.read_text())
    import mlx_whisper
    result = mlx_whisper.transcribe(str(ROOT / entry["wav"]), path_or_hf_repo=MODEL, word_timestamps=True, language="en",
                                    condition_on_previous_text=False, temperature=0.0, verbose=None)
    words = [[w["word"].strip(), round(w["start"], 3), round(w["end"], 3)] for seg in result["segments"] for w in seg.get("words", [])]
    CACHE.mkdir(exist_ok=True)
    cached.write_text(json.dumps(words))
    meta_path.write_text(json.dumps({'wav_hash':identity,'aligner':MODEL},indent=2))
    return words


from dataclasses import dataclass

@dataclass
class AlignmentResult:
    times: list
    ratio: float
    mismatches: list
    provenance: list
    def __iter__(self):
        return iter((self.times, self.ratio, self.mismatches))

def align(written, heard, duration, rules):
    """A [start, end] time for each written word, plus the share of it that matched and the mismatched segments."""
    spoken_per_word = [plain_form(spoken_form(w, rules)) for w in written]
    want, want_owner = norm_with_map(spoken_per_word)
    got, got_owner = norm_with_map([w[0] for w in heard])
    matcher = difflib.SequenceMatcher(None, want, got, autojunk=False)
    starts, ends = [None] * len(written), [None] * len(written)
    for block in matcher.get_matching_blocks():
        for k in range(block.size):
            wi, hw = want_owner[block.a + k], heard[got_owner[block.b + k]]
            starts[wi] = hw[1] if starts[wi] is None else min(starts[wi], hw[1])
            ends[wi] = hw[2] if ends[wi] is None else max(ends[wi], hw[2])
    # Words the transcriber heard differently take their share of the time between their matched neighbours.
    i, n = 0, len(written)
    while i < n:
        if starts[i] is not None:
            i += 1
            continue
        j = i
        while j < n and starts[j] is None:
            j += 1
        left = ends[i - 1] if i else 0.0
        right = starts[j] if j < n else duration
        if i == 0 and heard:
            left = min(left, heard[0][1])
        weights = [max(len(w), 1) for w in written[i:j]]
        total, t = sum(weights), left
        for k, w in enumerate(weights):
            starts[i + k] = t
            t += (right - left) * w / total
            ends[i + k] = t
        i = j
    # Keep times increasing and inside the clip.
    last = 0.0
    for k in range(n):
        starts[k] = round(min(max(starts[k], last), duration), 3)
        ends[k] = round(min(max(ends[k], starts[k]), duration), 3)
        last = starts[k]
    bad = [(" ".join(want[a0:a1]), " ".join(got[b0:b1])) for tag, a0, a1, b0, b1 in matcher.get_opcodes() if tag != "equal"]
    provenance = ['interpolated'] * len(written)
    for block in matcher.get_matching_blocks():
        for k in range(block.size):
            provenance[want_owner[block.a+k]] = 'asr_aligned'
    return AlignmentResult([[s,e] for s,e in zip(starts,ends)], matcher.ratio(), bad, provenance)


def expected_differences(rules_data):
    """Differences that only reflect spelling: the transcriber wrote the real word where the script holds a respelling."""
    same = set()
    for word, spoken in {**(rules_data.get("words") or {}), **(rules_data.get("kokoro") or {})}.items():
        said = "".join(fold_numbers(raw_tokens(plain_form(spoken)))[0])
        same.add((said, "".join(fold_numbers(raw_tokens(word))[0])))
    return same


def real_differences(seen, rules_data):
    same, reviewed = expected_differences(rules_data), set()
    if OK.exists():
        reviewed = {tuple(pair) for pair in yaml.safe_load(OK.read_text()) or []}
    left = {}
    for (said, got), where in seen.items():
        a, b = said.replace(" ", ""), got.replace(" ", "")
        if a == b or (a, b) in same or (said, got) in reviewed:
            continue
        # A multi-word difference is fine when each respelling inside it accounts for what was heard.
        for x, y in same:
            a = a.replace(x, y)
        if a == b:
            continue
        left[(said, got)] = where
    return left


def main():
    only = next((a for a in sys.argv[1:] if not a.startswith("--")), None)
    manifest, texts = load_manifest(), narration_text()
    _, rules = load_rules()
    timing, ratios, seen, began = {}, {}, defaultdict(list), time.time()
    beats = [b for b in sorted(manifest) if not only or b.startswith(only)]
    for n, beat in enumerate(beats, 1):
        heard = transcribe(beat, manifest[beat])
        written = texts[beat].split()
        result = align(written, heard, manifest[beat]["duration"], rules)
        times, ratio, bad = result
        from course.tools.preparation import digest
        timing[beat] = {"sha": manifest[beat]["sha"], "t": times, "provenance": ["synthesizer_aligned" if p == "asr_aligned" and manifest[beat].get("model") else p for p in result.provenance],
                        "wav_hash": digest(ROOT / manifest[beat]["wav"]), "aligner": "elevenlabs:" + manifest[beat]["model"] if manifest[beat].get("model") else MODEL,
                        "mismatch_spans": bad, "corrections": []}
        ratios[beat] = ratio
        for said, got in bad:
            seen[(said, got)].append(beat)
        if n % 25 == 0:
            print(f"{n}/{len(beats)} clips, {time.time() - began:.0f} s", flush=True)
    if only:
        print(f"{len(beats)} clips; mean match {sum(ratios.values()) / max(len(ratios), 1):.3f}")
        for (said, got), where in sorted(seen.items(), key=lambda kv: -len(kv[1]))[:60]:
            print(f"{len(where):3}  '{said}' -> '{got}'  {where[0]}")
        return
    (ROOT / "narration" / "timing.json").write_text(json.dumps(timing, separators=(",", ":"), sort_keys=True))
    left = real_differences(seen, yaml.safe_load((ROOT / "narration" / "pronounce.yaml").read_text()))
    if "--accept" in sys.argv:
        reviewed = yaml.safe_load(OK.read_text()) if OK.exists() else []
        OK.write_text(yaml.safe_dump((reviewed or []) + [list(k) for k in sorted(left)], allow_unicode=True, width=200))
        left = {}
    lines = ["# What the transcriber heard", "",
             f"{len(beats)} clips against their spoken scripts. Mean match {sum(ratios.values()) / len(ratios):.3f}.", "",
             "ASR agreement is supporting evidence. It does not prove intelligibility, pronunciation, naturalness or exact synchronization. Spelling-only differences and explicitly accepted ASR patterns in `sources/heard-ok.yaml` are left out.", "",
             f"**{len(left)} differences left to review.**", "", "| Times | Script says | Heard | First clip |", "|---|---|---|---|"]
    lines += [f"| {len(w)} | {s} | {g} | {w[0]} |" for (s, g), w in sorted(left.items(), key=lambda kv: (-len(kv[1]), kv[0]))]
    lines += ["", "## Lowest-matching clips", "", "| Clip | Match |", "|---|---|"]
    lines += [f"| {b} | {r:.2f} |" for b, r in sorted(ratios.items(), key=lambda kv: kv[1])[:15]]
    (ROOT / "narration" / "heard.md").write_text("\n".join(lines) + "\n")
    print(f"{len(beats)} clips in {time.time() - began:.0f} s; mean match {sum(ratios.values()) / len(ratios):.3f}; {len(left)} differences left to review")


if __name__ == "__main__":
    main()
