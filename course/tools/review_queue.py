"""Build artifact-bound review work without assigning reviewers or inventing passes.

The binding audit inspects source text and choreography references only. Its
heuristics flag candidates for substantive review, never certify understanding.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import wave

import yaml
from course.tools.reproduction import ROOT, sha256

CATEGORIES = ('content', 'visual', 'audio', 'captions')


def read_json(path, default=None):
    return json.loads(path.read_text()) if path.exists() else default


def texts_and_cards(root):
    texts, cards, beats = {}, {}, {}
    for path in sorted((root / 'recipes').glob('[0-9]*.yaml')):
        card = yaml.safe_load(path.read_text())
        cards[str(card['dish'])] = card
        for beat in card['beats']:
            beats[beat['id']] = beat
    for path in sorted((root / 'narration').glob('[0-9]*.md')):
        current = None
        for line in path.read_text().splitlines():
            if line.startswith('## '):
                current = line[3:].strip()
                texts[current] = ''
            elif current and line.strip():
                texts[current] = (texts[current] + ' ' + line.strip()).strip()
    return texts, cards, beats


def parse_asr(root, manifest, timing):
    path = root / 'narration/heard.md'
    if not path.exists():
        return [], ['Missing narration/heard.md']
    rows, issues = [], []
    for line in path.read_text().splitlines():
        if not re.match(r'^\|\s*\d+\s*\|', line):
            continue
        columns = [x.strip() for x in line.strip().strip('|').split('|')]
        if len(columns) != 4:
            issues.append('Malformed ASR table row: ' + line)
            continue
        count, script, heard, first = columns
        occurrences = []
        for beat, entry in sorted(timing.items()):
            for index, span in enumerate(entry.get('mismatch_spans', [])):
                if list(span) == [script, heard]:
                    audio = manifest.get(beat, {})
                    occurrences.append({'beat': beat, 'mismatch_index': index,
                        'audio': audio.get('wav'), 'wav_sha256': entry.get('wav_hash'),
                        'alignment_evidence': f"narration/alignment-evidence/{audio.get('sha')}.json",
                        'listen_range': [0, audio.get('duration')],
                        'range_note': 'Whole clip; mismatch spans have no exact ASR timestamp bounds.'})
        if not occurrences:
            audio = manifest.get(first, {})
            occurrences = [{'beat': first, 'audio': audio.get('wav'),
                            'listen_range': [0, audio.get('duration')],
                            'range_note': 'First clip from report; timing occurrence unavailable.'}]
        row_id = hashlib.sha256(json.dumps([script, heard]).encode()).hexdigest()[:16]
        rows.append({'id': 'asr-' + row_id, 'status': 'unresolved', 'reviewer': None,
                     'script_says': script, 'asr_heard': heard, 'reported_occurrences': int(count),
                     'first_clip': first, 'occurrences': occurrences,
                     'occurrence_count_matches': len(occurrences) == int(count),
                     'source': 'narration/heard.md',
                     'decision': None, 'independent_transcription': None})
    match = re.search(r'\*\*(\d+) differences left to review', path.read_text())
    if match and int(match[1]) != len(rows):
        issues.append(f'ASR report declares {match[1]} differences but parsed {len(rows)}')
    return rows, issues


def audit_bindings(root, bindings, texts, beats):
    """Inspect every binding against actual narration and move IDs, conservatively."""
    shared = Counter(v.get('mechanism', {}).get('beat') for v in bindings.values())
    results = []
    for concept, binding in bindings.items():
        mechanism = binding.get('mechanism', {})
        beat_id = mechanism.get('beat')
        beat = beats.get(beat_id, {})
        text = texts.get(beat_id, '')
        events = mechanism.get('visible_events', [])
        actual_events = {f'{beat_id}:move:{i}' for i in range(len(beat.get('moves', [])))}
        flags = []
        if not text:
            flags.append('missing_actual_narration')
        if text != mechanism.get('narration_excerpt', ''):
            flags.append('binding_excerpt_differs_from_actual_narration')
        if not events or not set(events).issubset(actual_events):
            flags.append('missing_or_invalid_visible_events')
        if len(text.split()) < 35:
            flags.append('short_explanation_requires_review')
        if not re.search(r'\b(because|if|when|therefore|so|means|instead|only|each|until|which|by)\b', text, re.I):
            flags.append('weak_mechanism_signal')
        # Shared beats often teach related concepts, but require separate coverage checks.
        if shared[beat_id] > 1:
            flags.append('shared_mechanism_requires_concept_specific_review')
        words = set(re.findall(r'[a-z0-9]+', concept.lower())) - {'a', 'the', 'and', 'of', 'in', 'ip'}
        if words and not words.intersection(re.findall(r'[a-z0-9]+', text.lower())):
            flags.append('concept_name_not_in_mechanism_check_equivalence')
        source_refs = binding.get('source_refs', [])
        if not source_refs or any(not (root / 'sources/snapshot/vault' / ref).is_file() for ref in source_refs):
            flags.append('source_reference_missing')
        if not binding.get('explanation_claim'):
            flags.append('missing_explanation_claim')
        results.append({'concept': concept, 'beat': beat_id, 'status': 'unresolved',
            'audit_kind': 'agent_source_content_inspection', 'reviewer': None,
            'explanation_claim': binding.get('explanation_claim'), 'actual_narration': text,
            'word_count': len(text.split()), 'visible_events': events,
            'move_names': [next(iter(move)) for move in beat.get('moves', [])],
            'source_refs': source_refs, 'pdf': mechanism.get('pdf'),
            'prediction_pairs': binding.get('prediction_pairs', []), 'anomalies': flags,
            'substantive_explanation': 'requires_review', 'perceptual_review': 'not_reviewed'})
    return results


def pending_reviews(artifact_hash):
    return {category: {'result': 'not_reviewed', 'status': 'unresolved',
                       'reviewer': None, 'artifact_hash': artifact_hash, 'decision': None}
            for category in CATEGORIES}


def artifact_info(path, receipt=None):
    receipt = receipt or {}
    return {'path': str(path), 'exists': path.is_file(),
            'sha256': sha256(path) if path.is_file() else None,
            'duration_seconds': receipt.get('media_metadata', {}).get('duration'),
            'input_fingerprint': receipt.get('input_fingerprint')}


def build_queue(root=ROOT):
    root = Path(root)
    texts, cards, beats = texts_and_cards(root)
    bindings = read_json(root / 'sources/bindings.json', {})
    manifest = read_json(root / 'narration/manifest.json', {})
    timing = read_json(root / 'narration/timing.json', {})
    predictions = read_json(root / 'recipes/predictions.json', {}).get('predictions', [])
    corrections_path = root / 'sources/clarifications.yaml'
    corrections = yaml.safe_load(corrections_path.read_text()) if corrections_path.exists() else []
    asr, issues = parse_asr(root, manifest, timing)
    audits = audit_bindings(root, bindings, texts, beats)
    dishes = []
    for dish, card in sorted(cards.items(), key=lambda kv: tuple(map(int, kv[0].split('.')))):
        path = root / 'build/dishes/final' / f'{dish}.mp4'
        info = artifact_info(path, read_json(path.with_suffix('.receipt.json'), {}))
        associated = [a for a in audits if dish in ['.'.join(b.split('.')[:2]) for b in
                      bindings[a['concept']].get('primary_beats', []) + bindings[a['concept']].get('supporting_beats', [])]]
        dish_asr = [a['id'] for a in asr if any(o['beat'].startswith(dish + '.') for o in a['occurrences'])]
        dishes.append({'dish': dish, 'title': card['title'], 'artifact': info,
            'reviews': pending_reviews(info['sha256']),
            'concepts': sorted(set(card.get('concepts', [])) | {a['concept'] for a in associated}),
            'sources': [{'beat': b['id'], 'pdf': b.get('pdf')} for b in card['beats']],
            'corrections': [c for c in corrections or [] if str(c.get('dish')) == dish],
            'predictions': [p for p in predictions if p['prediction_beat'].startswith(dish + '.')],
            'asr_concerns': dish_asr,
            'content_anomalies': [{'concept': a['concept'], 'anomalies': a['anomalies']} for a in associated if a['anomalies']]})
    assemblies = []
    for path in sorted((root / 'build/assembly').glob('*.json')):
        plan = read_json(path)
        name = plan['output_id']
        if name in ('main', 'supplements'):
            video = root.parent / 'video' / ('CSCI-5273-Lectures-06-15.mp4' if name == 'main' else 'CSCI-5273-Practice-and-Warm-up.mp4')
        else:
            candidates = sorted((root.parent / 'video/chapters').glob(f'ch{int(name.split("-")[-1]):02}-*.mp4'))
            video = candidates[0] if len(candidates) == 1 else root.parent / 'video/chapters' / (name + '.missing.mp4')
        info = artifact_info(video, read_json(video.with_suffix('.receipt.json'), {}))
        fps = plan.get('fps', 30)
        info['duration_seconds'] = info['duration_seconds'] or plan['total_frames'] / fps
        joins = [{'before': a, 'after': b, 'frame': plan['offsets'][b],
                  'seconds': plan['offsets'][b] / fps, 'status': 'unresolved', 'reviewer': None,
                  'reviews': pending_reviews(info['sha256'])}
                 for a, b in zip(plan['members'], plan['members'][1:])]
        assemblies.append({'assembly': name, 'artifact': info, 'members': plan['members'],
                           'reviews': pending_reviews(info['sha256']), 'joins': joins,
                           'duration_basis': 'assembly plan when receipt has no duration'})
    if len(dishes) != 64:
        issues.append(f'Expected 64 dishes; found {len(dishes)}')
    if len(audits) != 176:
        issues.append(f'Expected 176 concept bindings; found {len(audits)}')
    return {'schema_version': 1, 'reviewer': None, 'release_verified': False,
            'perceptual_review': 'not_reviewed', 'categories': list(CATEGORIES),
            'limitations': ['Source text and event inspection is not a perceptual or substantive coverage pass.',
                'ASR differences require listening and adjudication; agreement alone cannot pass audio review.',
                'Review queue assigns no reviewer and records no decisions; existing decision logs are not modified.',
                'Duration from receipt/assembly plan is evidence, not a new media probe.'],
            'issues': issues, 'summary': {'dishes': len(dishes), 'bindings_inspected': len(audits),
                'bindings_flagged': sum(bool(a['anomalies']) for a in audits),
                'asr_differences': len(asr), 'assemblies': len(assemblies),
                'joins': sum(len(a['joins']) for a in assemblies)},
            'dishes': dishes, 'assemblies': assemblies, 'binding_audit': audits, 'asr_adjudication': asr}


def write_queue(queue, destination):
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(queue, indent=2) + '\n')
    lines = ['# Review queue', '', 'Reviewer unspecified. All decisions unresolved. No perceptual passes.', '',
             '```json', json.dumps(queue['summary'], indent=2), '```', '', *queue['limitations'], '',
             '## Dishes', '', '| Dish | Title | Seconds | SHA-256 | ASR concerns |', '|---|---|---|---|---|']
    lines += [f"| {d['dish']} | {d['title']} | {d['artifact']['duration_seconds']} | {d['artifact']['sha256']} | {len(d['asr_concerns'])} |" for d in queue['dishes']]
    lines += ['', '## Assembly joins', '']
    for assembly in queue['assemblies']:
        lines += [f"- {assembly['assembly']}: {len(assembly['joins'])} unresolved joins; SHA-256 {assembly['artifact']['sha256']}"]
    lines += ['', '## Agent content inspection anomalies', '']
    for audit in queue['binding_audit']:
        if audit['anomalies']:
            lines += [f"- **{audit['concept']}** ({audit['beat']}): {', '.join(audit['anomalies'])}"]
    lines += ['', '## ASR adjudication', '', '| ID | Script | ASR | First clip | Status |', '|---|---|---|---|---|']
    lines += [f"| {a['id']} | {a['script_says']} | {a['asr_heard']} | {a['first_clip']} | unresolved |" for a in queue['asr_adjudication']]
    lines += ['', 'Exact source excerpts, event IDs, audio references, corrections, predictions, hashes and all join times are in the adjacent JSON.', '']
    destination.with_suffix('.md').write_text('\n'.join(lines))


def prepare_pilot(root, queue, destination, max_seconds=90):
    """Concatenate complete flagged clips with silence; never upload anything."""
    if not 0 < max_seconds <= 90:
        raise ValueError('Pilot limit must be between 0 and 90 seconds')
    root, destination = Path(root), Path(destination)
    texts, _, _ = texts_and_cards(root)
    clips, seen, frames, audio_format = [], set(), [], None
    total = 0
    # Prefer potentially consequential numeric/technical substitutions, then others.
    concerns = sorted(queue['asr_adjudication'], key=lambda a: (not bool(re.search(r'\d', a['script_says'])), a['id']))
    for concern in concerns:
        for occurrence in concern['occurrences']:
            beat = occurrence['beat']
            if beat in seen or not occurrence.get('audio'):
                continue
            path = root / occurrence['audio']
            if not path.is_file():
                continue
            with wave.open(str(path), 'rb') as wav:
                fmt = (wav.getnchannels(), wav.getsampwidth(), wav.getframerate(), wav.getcomptype())
                if fmt[3] != 'NONE' or (audio_format and fmt != audio_format):
                    continue
                n = wav.getnframes()
                gap = round(fmt[2] * .5) if clips else 0
                if (total + gap + n) / fmt[2] > max_seconds:
                    continue
                audio_format = fmt
                frames.append(b'\x00' * (gap * fmt[0] * fmt[1]))
                start = total + gap
                frames.append(wav.readframes(n))
                total = start + n
                clips.append({'beat': beat, 'source_audio': occurrence['audio'],
                    'source_sha256': sha256(path), 'pilot_start_seconds': start / fmt[2],
                    'pilot_end_seconds': total / fmt[2], 'expected_transcript': texts.get(beat, ''),
                    'asr_concern_ids': [a['id'] for a in queue['asr_adjudication']
                        if any(o['beat'] == beat for o in a['occurrences'])]})
                seen.add(beat)
            if len(clips) >= 5:
                break
        if len(clips) >= 5:
            break
    if len(clips) < 2:
        raise ValueError('Need at least two compatible flagged WAV clips for a pilot')
    destination.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(destination), 'wb') as wav:
        wav.setnchannels(audio_format[0]); wav.setsampwidth(audio_format[1]); wav.setframerate(audio_format[2])
        wav.writeframes(b''.join(frames))
    record = {'status': 'awaiting_user_upload', 'uploaded': False, 'reviewer': None,
              'purpose': 'Independent ElevenLabs transcription evidence; all audio reviews remain unresolved.',
              'wav': str(destination), 'sha256': sha256(destination),
              'duration_seconds': total / audio_format[2], 'clips': clips}
    destination.with_suffix('.json').write_text(json.dumps(record, indent=2) + '\n')
    destination.with_suffix('.txt').write_text('\n\n'.join(c['expected_transcript'] for c in clips) + '\n')
    return record


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--pilot', action='store_true')
    args = parser.parse_args(argv)
    queue = build_queue(args.root)
    write_queue(queue, args.output or args.root / 'build/review-queue.json')
    if args.pilot:
        prepare_pilot(args.root, queue, args.root.parent / 'verification/elevenlabs-pilot.wav')
    print(json.dumps(queue['summary'], indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
