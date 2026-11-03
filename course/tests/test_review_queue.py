import json
import wave

import pytest
import yaml
from course.tools import review_queue as queue


@pytest.fixture
def tiny_course(tmp_path):
    root = tmp_path / 'source'
    for folder in ('recipes', 'narration/audio', 'sources', 'build/assembly', 'build/dishes/final'):
        (root / folder).mkdir(parents=True)
    beat = '1.1.explain'
    text = 'If the link fails, the sender retries because the receiver has not acknowledged the packet. Each retry uses the same sequence number so the receiver can recognize duplicates and avoid delivering the same payload twice.'
    (root / 'recipes/1.1.yaml').write_text(yaml.safe_dump({'dish': '1.1', 'title': 'Retry', 'concepts': [],
        'beats': [{'id': beat, 'pdf': ['slides.pdf', 1], 'moves': [{'packet.hop': {'to': 'B'}}]}]}))
    (root / 'narration/1.1.md').write_text(f'## {beat}\n{text}\n## 1.1.other\nA second flagged sentence.\n')
    manifest = {}
    for name in (beat, '1.1.other'):
        audio = root / f'narration/audio/{name}.wav'
        with wave.open(str(audio), 'wb') as out:
            out.setnchannels(1); out.setsampwidth(2); out.setframerate(8000)
            out.writeframes(b'\0' * 16000)
        manifest[name] = {'wav': str(audio.relative_to(root)), 'sha': name, 'duration': 1}
    (root / 'narration/manifest.json').write_text(json.dumps(manifest))
    (root / 'narration/timing.json').write_text(json.dumps({name: {'mismatch_spans': [['retry', 'try']], 'wav_hash': 'x'} for name in manifest}))
    (root / 'narration/heard.md').write_text('**1 differences left to review.**\n\n| Times | Script says | Heard | First clip |\n|---|---|---|---|\n| 2 | retry | try | 1.1.explain |\n')
    (root / 'sources/bindings.json').write_text(json.dumps({'Retry': {'primary_beats': [beat],
        'source_refs': ['Concepts/Retry.md'], 'explanation_claim': 'Retries recover loss.',
        'mechanism': {'beat': beat, 'narration_excerpt': text, 'visible_events': [beat + ':move:0']}}}))
    (root / 'sources/clarifications.yaml').write_text('- {dish: "1.1", id: correction, text: exact correction}\n')
    (root / 'recipes/predictions.json').write_text(json.dumps({'predictions': [{'prediction_beat': '1.1.predict', 'answer_beat': '1.1.answer'}]}))
    (root / 'build/assembly/main.json').write_text(json.dumps({'output_id': 'main', 'members': ['1.1', '1.2'],
        'offsets': {'1.1': 0, '1.2': 60}, 'total_frames': 90}))
    return root


def test_asr_keeps_all_occurrences_unresolved_with_audio(tiny_course):
    root = tiny_course
    rows, issues = queue.parse_asr(root, queue.read_json(root / 'narration/manifest.json'),
                                   queue.read_json(root / 'narration/timing.json'))
    assert not issues and len(rows) == 1
    row = rows[0]
    assert row['status'] == 'unresolved' and row['reviewer'] is None
    assert len(row['occurrences']) == 2 and row['occurrence_count_matches']
    assert all(o['audio'] and o['listen_range'] == [0, 1] for o in row['occurrences'])
    (root / 'narration/heard.md').write_text('**86 differences left to review.**')
    assert queue.parse_asr(root, {}, {})[1]


def test_queue_contains_hash_bound_categories_and_evidence(tiny_course):
    root = tiny_course
    video = root / 'build/dishes/final/1.1.mp4'; video.write_bytes(b'fake video')
    video.with_suffix('.receipt.json').write_text(json.dumps({'input_fingerprint': 'stage', 'media_metadata': {'duration': 2}}))
    result = queue.build_queue(root)
    dish = result['dishes'][0]
    assert set(dish['reviews']) == set(queue.CATEGORIES)
    assert all(r['result'] == 'not_reviewed' and r['reviewer'] is None
               and r['artifact_hash'] == queue.sha256(video) for r in dish['reviews'].values())
    assert dish['concepts'] == ['Retry'] and dish['corrections'] and dish['predictions']
    assert len(dish['asr_concerns']) == 1
    assert dish['sources'][0]['pdf'] == ['slides.pdf', 1]
    join = result['assemblies'][0]['joins'][0]
    assert (join['before'], join['after'], join['frame'], join['seconds']) == ('1.1', '1.2', 60, 2)
    assert join['status'] == 'unresolved'
    assert result['release_verified'] is False
    destination = root / 'build/review-queue.json'
    queue.write_queue(result, destination)
    assert json.loads(destination.read_text()) == result
    assert 'No perceptual passes' in destination.with_suffix('.md').read_text()


def test_binding_audit_reads_actual_text_and_flags_invalid_references(tiny_course):
    texts, _, beats = queue.texts_and_cards(tiny_course)
    bindings = queue.read_json(tiny_course / 'sources/bindings.json')
    bindings['Retry']['mechanism']['narration_excerpt'] = 'Invented explanation'
    bindings['Retry']['mechanism']['visible_events'] = ['nonexistent:move:99']
    audit = queue.audit_bindings(tiny_course, bindings, texts, beats)[0]
    assert audit['actual_narration'] == texts['1.1.explain']
    assert 'binding_excerpt_differs_from_actual_narration' in audit['anomalies']
    assert 'missing_or_invalid_visible_events' in audit['anomalies']
    assert audit['substantive_explanation'] == 'requires_review'
    assert audit['perceptual_review'] == 'not_reviewed'


def test_pilot_is_bounded_and_preserves_transcript_and_source_hashes(tiny_course):
    result = queue.build_queue(tiny_course)
    destination = tiny_course.parent / 'verification/elevenlabs-pilot.wav'
    record = queue.prepare_pilot(tiny_course, result, destination)
    assert len(record['clips']) == 2 and record['duration_seconds'] == 2.5
    assert record['uploaded'] is False and record['status'] == 'awaiting_user_upload'
    with wave.open(str(destination), 'rb') as wav:
        assert wav.getnframes() / wav.getframerate() == record['duration_seconds']
    assert record['sha256'] == queue.sha256(destination)
    assert 'second flagged' in destination.with_suffix('.txt').read_text()
    assert all(c['source_sha256'] == queue.sha256(tiny_course / c['source_audio']) for c in record['clips'])
    with pytest.raises(ValueError):
        queue.prepare_pilot(tiny_course, result, destination, max_seconds=91)
