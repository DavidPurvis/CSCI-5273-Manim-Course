"""Freeze the meaning of referenced events, including legacy positional IDs."""
import hashlib,json
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parents[2]


def collect(root=ROOT):
    events={}
    for p in (root/'recipes').glob('*.yaml'):
        for beat in yaml.safe_load(p.read_text())['beats']:
            for i,move in enumerate(beat.get('moves',[])):
                eid=move.get('event_id',f"{beat['id']}:move:{i}")
                events[eid]=hashlib.sha256(json.dumps(move,sort_keys=True).encode()).hexdigest()
    refs=set()
    for b in json.loads((root/'sources/bindings.json').read_text()).values():refs.update(b.get('mechanism',{}).get('visible_events',[]))
    for c in json.loads((root/'recipes/predictions.json').read_text())['predictions']:refs.update(c['answer_events'])
    return {key:events.get(key) for key in sorted(refs)}


def validate_reference_integrity(root=ROOT):
    path=root/'sources/event-reference-baseline.json'
    if not path.exists():return ['Missing reviewed event-reference baseline']
    expected=json.loads(path.read_text())['events'];actual=collect(root)
    return [f'{eid}: referenced event changed or moved; explicitly remap and review the baseline' for eid in sorted(set(expected)|set(actual)) if expected.get(eid)!=actual.get(eid) or actual.get(eid) is None]
