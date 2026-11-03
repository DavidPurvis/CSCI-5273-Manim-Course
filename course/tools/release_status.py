"""Shared release state calculated from current evidence, never assumed approvals."""
from dataclasses import dataclass,asdict
from collections import Counter
import hashlib,json
from pathlib import Path

@dataclass
class ReleaseStatus:
    revision: str
    mise_complete: bool
    automatic_media_verified: bool
    reproduction_verified: bool
    perceptual_review: str
    release_verified: bool
    finding_counts: dict
    current_render_receipts: int
    expected_render_receipts: int
    input_findings: list
    remaining_work: list


def calculate(findings, input_findings, revision, current, expected):
    codes=Counter(f['code'] for f in findings)
    preparation=not input_findings
    media=preparation and current==expected and not any(codes[c] for c in ('RENDER_RECEIPT','STALE_RENDER','MEDIA_AUDIT','STALE_MEDIA_AUDIT','MEDIA'))
    reproduction=not any(codes[c] for c in ('REPRODUCTION','STALE_REPRODUCTION'))
    reviewed=current==expected and not any(codes[c] for c in ('REVIEW','RENDER_RECEIPT','STALE_RENDER'))
    remaining=[]
    if not preparation:remaining.append('Resolve preparation findings')
    if not media:remaining.append('Verify current media and receipts')
    if not reproduction:remaining.append('Reproduce the candidate source ZIP')
    if not reviewed:remaining.append('Complete explicit artifact-bound content, visual, audio and caption reviews')
    return ReleaseStatus(revision,preparation,media,reproduction,'passed' if reviewed else 'not_reviewed',not findings and preparation and media and reproduction and reviewed,dict(codes),current,expected,input_findings,remaining)


def refresh():
    from course.tools.preparation import ROOT,audit,timeline_findings,verify_release
    from course.tools.kitchen import dishes,is_fresh
    from course.tools.kitchen import group_fp
    inputs=[asdict(f) for f in audit()+timeline_findings()]
    findings=[asdict(f) for f in verify_release()]
    members=dishes();status=asdict(calculate(findings,inputs,group_fp(members),sum(is_fresh(d) for d in members),len(members)))
    status['live_proof']=live_proof(ROOT)
    status['implementation']='release verified' if status['release_verified'] else 'release evidence incomplete; see finding_counts'
    for path in (ROOT/'implementation-status.json',ROOT.parent/'verification/implementation-status.json'):
        path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(status,indent=2))
    report=ROOT.parent/'final-report.json'
    if report.exists():
        data=json.loads(report.read_text());data['release_status']=status;report.write_text(json.dumps(data,indent=2))
    return status


def live_proof(root):
    """Bind publication to current source and review/build evidence, excluding status copies."""
    from course.tools.reproduction import source_content_identity
    paths=list((root/'build/dishes/final').glob('*.receipt.json'))
    paths += [root/p for p in ('build/review/decisions.jsonl','build/media-audit.json','build/reproduction/report.json')]
    h=hashlib.sha256()
    for p in sorted(paths):
        h.update(str(p.relative_to(root)).encode());h.update(p.read_bytes() if p.exists() else b'<missing>')
    return {'source_content_sha256':source_content_identity(root),'evidence_sha256':h.hexdigest()}
