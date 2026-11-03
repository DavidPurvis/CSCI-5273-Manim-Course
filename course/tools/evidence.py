"""Content-addressed render and assembly evidence; never infers perceptual review."""
from pathlib import Path
import hashlib,json
from dataclasses import asdict
from course.contracts import RenderReceipt
ROOT=Path(__file__).resolve().parents[2]


def hash_files(paths):
    h=hashlib.sha256()
    for p in sorted(set(Path(x) for x in paths)):
        h.update(str(p.relative_to(ROOT) if p.is_relative_to(ROOT) else p.name).encode());h.update(p.read_bytes())
    return h.hexdigest()


def fingerprint_dish(dish_id,context=None):
    import yaml
    profile=(context or {}).get('profile','final')
    p=ROOT/'recipes'/f'{dish_id}.yaml'
    card=yaml.safe_load(p.read_text())
    manifest=json.loads((ROOT/'narration/manifest.json').read_text())
    timing=json.loads((ROOT/'narration/timing.json').read_text())
    paths=[p,ROOT/'narration'/f'{dish_id}.md',ROOT/'requirements.lock',ROOT/'course/contracts.py']
    paths+=list((ROOT/'course/stage').glob('*.py'))+list((ROOT/'traces').glob('*.json'))
    paths += [ROOT/manifest[b['id']]['wav'] for b in card['beats']]
    identity={'schema_version':2,'profile':profile,'fps':30,'renderer':'cairo',
              'resolution':[1920,1080] if profile=='final' else [1280,720],
              'narration':{b['id']:manifest[b['id']] for b in card['beats']},
              'timing':{b['id']:timing.get(b['id']) for b in card['beats']}}
    return hashlib.sha256((hash_files(paths)+json.dumps(identity,sort_keys=True)).encode()).hexdigest()


def fingerprint_assembly(plan,context=None):
    paths=list((ROOT/'course/tools').glob('*.py'))+[ROOT/'sources/snapshot/manifest.json']
    for relative in ('recipes/predictions.json','sources/bindings.json','sources/proposal-decisions.yaml'):
        if (ROOT/relative).exists():paths.append(ROOT/relative)
    data=asdict(plan) if hasattr(plan,'__dataclass_fields__') else plan
    return hashlib.sha256((json.dumps(data,sort_keys=True)+hash_files(paths)).encode()).hexdigest()


def write_render_receipt(video,dish,profile,findings=(),input_fingerprint=None):
    from course.tools.kitchen import probe_duration
    video=Path(video)
    receipt=RenderReceipt(input_fingerprint or "unknown: render began without an input snapshot",profile,{video.name:artifact_hash(video)},{'duration':probe_duration(video)},list(findings))
    video.with_suffix('.receipt.json').write_text(json.dumps(asdict(receipt),indent=2))
    return receipt


def write_assembly_receipt(video,plan,members,findings=()):
    """Record the ordered render receipts separately from the assembled output."""
    from course.tools.kitchen import run,video_path
    video=Path(video)
    member_receipts=[json.loads(video_path(d,'final').with_suffix('.receipt.json').read_text()) for d in members]
    identity={'plan':asdict(plan),'member_receipts':member_receipts}
    metadata=json.loads(run(['ffprobe','-v','error','-show_format','-show_streams','-show_chapters','-of','json',str(video)]).stdout)
    record={'schema_version':1,'input_fingerprint':fingerprint_assembly(identity),
            'assembly_inputs':identity,'artifact_hash':artifact_hash(video),
            'media_metadata':metadata,'findings':list(findings)}
    video.with_suffix('.receipt.json').write_text(json.dumps(record,indent=2))
    return record


def artifact_hash(path):
    """An output's identity is its bytes, independent of build or package location."""
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def artifact_matches(path,recorded):
    """Read schema-1 path-salted receipts while writing portable SHA-256 identities."""
    path=Path(path)
    if artifact_hash(path)==recorded or hash_files([path])==recorded:return True
    for old_prefix in (path.name,'build/dishes/final/'+path.name):
        h=hashlib.sha256(old_prefix.encode())
        with path.open('rb') as stream:
            for chunk in iter(lambda:stream.read(1024*1024),b''):h.update(chunk)
        if h.hexdigest()==recorded:return True
    return False
