"""Artifact invalidation must follow the bytes actually used by each output."""
import json
from pathlib import Path
import yaml
from course.tools import evidence


def minimal_source(root):
    for folder in ['recipes','narration/audio','course/stage','course/tools','traces']:
        (root/folder).mkdir(parents=True)
    files={'recipes/1.1.yaml':yaml.safe_dump({'beats':[{'id':'1.1.a'}]}),
           'narration/1.1.md':'A packet moves.', 'requirements.lock':'manim==0.22.1',
           'course/contracts.py':'# records', 'course/stage/player.py':'# renderer',
           'course/tools/export.py':'# exporter', 'narration/audio/a.wav':'first waveform'}
    for path,text in files.items():(root/path).write_text(text)
    (root/'sources/snapshot').mkdir(parents=True)
    (root/'sources/snapshot/manifest.json').write_text('{}')
    (root/'narration/manifest.json').write_text(json.dumps({'1.1.a':{'wav':'narration/audio/a.wav','duration':2,'sha':'a'}}))
    (root/'narration/timing.json').write_text(json.dumps({'1.1.a':{'sha':'a','t':[[0,2]]},'other':{'t':[[0,1]]}}))


def test_wav_bytes_and_profile_invalidate_the_render(tmp_path,monkeypatch):
    minimal_source(tmp_path);monkeypatch.setattr(evidence,'ROOT',tmp_path)
    before=evidence.fingerprint_dish('1.1')
    assert evidence.fingerprint_dish('1.1',{'profile':'preview'})!=before
    timing=json.loads((tmp_path/'narration/timing.json').read_text())
    timing['other']['t']=[[2,3]]
    (tmp_path/'narration/timing.json').write_text(json.dumps(timing))
    assert evidence.fingerprint_dish('1.1')==before
    (tmp_path/'narration/audio/a.wav').write_text('different waveform')
    assert evidence.fingerprint_dish('1.1')!=before


def test_export_change_invalidates_assembly_without_rerender(tmp_path,monkeypatch):
    minimal_source(tmp_path);monkeypatch.setattr(evidence,'ROOT',tmp_path)
    plan={'members':['1.1'],'offsets':{'1.1':0}}
    render_before=evidence.fingerprint_dish('1.1');assembly_before=evidence.fingerprint_assembly(plan)
    (tmp_path/'course/tools/export.py').write_text('# corrected subtitle export')
    assert evidence.fingerprint_assembly(plan)!=assembly_before
    assert evidence.fingerprint_dish('1.1')==render_before


def test_output_identity_is_portable_across_frozen_builds(tmp_path,monkeypatch):
    root=tmp_path/'source';video=root/'build/dishes/final/1.1.mp4'
    video.parent.mkdir(parents=True);video.write_bytes(b'encoded-video-bytes')
    monkeypatch.setattr(evidence,'ROOT',root)
    legacy_inside=evidence.hash_files([video]);identity=evidence.artifact_hash(video)
    frozen=tmp_path/'frozen-source';frozen.mkdir()
    monkeypatch.setattr(evidence,'ROOT',frozen)
    legacy_outside=evidence.hash_files([video])
    assert legacy_inside!=legacy_outside
    assert evidence.artifact_matches(video,legacy_inside)
    assert evidence.artifact_matches(video,legacy_outside)
    assert evidence.artifact_hash(video)==identity
    moved=tmp_path/'package/1.1.mp4';moved.parent.mkdir();moved.write_bytes(video.read_bytes())
    assert evidence.artifact_hash(moved)==identity


def test_serve_rejects_stale_chapters_before_media_work(tmp_path,monkeypatch):
    from course.tools import kitchen,assembly
    pack=tmp_path/'pack';build=tmp_path/'build'
    (pack/'video/chapters').mkdir(parents=True)
    (pack/'video/chapters/ch01-foundations.mp4').write_bytes(b'old chapter')
    (build/'chapters').mkdir(parents=True)
    (build/'chapters/1.fp').write_text('old inputs')
    monkeypatch.setattr(kitchen,'PACK',pack);monkeypatch.setattr(kitchen,'BUILD',build)
    monkeypatch.setattr(kitchen,'dishes',lambda:['1.1'])
    monkeypatch.setattr(kitchen,'is_fresh',lambda d:True)
    monkeypatch.setattr(kitchen,'group_fp',lambda members:'current inputs')
    monkeypatch.setattr(assembly,'write_plans',lambda:{})
    monkeypatch.setattr(kitchen,'run',lambda *a,**kw:(_ for _ in ()).throw(AssertionError('Media work must not begin')))
    assert kitchen.cmd_serve(None)==1
