import json
from pathlib import Path
import stat
from types import SimpleNamespace
import zipfile

import pytest
from course.tools import reproduction as repro


def make_zip(path, extra=None):
    with zipfile.ZipFile(path, 'w') as archive:
        for name in ('requirements.lock', 'course/stage/player.py', 'course/tools/evidence.py'):
            archive.writestr('source/' + name, 'pytest==9.2.0\n' if name.endswith('.lock') else '')
        for name, value in extra or []:
            archive.writestr(name, value)
    return path


@pytest.mark.parametrize('name', ['../escape', '/source/evil', 'source/../../escape',
    'source/../escape', 'source\\evil', 'source/C:/evil', 'source//evil', 'source/./evil'])
def test_extract_rejects_unsafe_paths_before_deleting_existing_tree(tmp_path, name):
    destination = tmp_path / 'extract'
    destination.mkdir(); (destination / 'sentinel').write_text('keep')
    archive = make_zip(tmp_path / 'candidate.zip', [(name, 'bad')])
    with pytest.raises(ValueError):
        repro.extract_candidate(archive, destination)
    assert (destination / 'sentinel').read_text() == 'keep'
    assert not (tmp_path / 'escape').exists()


def test_extract_rejects_symlinks_duplicates_and_size_limit(tmp_path):
    link = zipfile.ZipInfo('source/link')
    link.create_system = 3
    link.external_attr = (stat.S_IFLNK | 0o777) << 16
    for extra in ([(link, '../../escape')], [('source/A', 'a'), ('source/a', 'b')],
                  [('source/file', 'x'), ('source/file/child', 'y')]):
        archive = make_zip(tmp_path / 'candidate.zip', extra)
        with pytest.raises(ValueError):
            repro.extract_candidate(archive, tmp_path / 'out')
    with pytest.raises(ValueError, match='limits'):
        repro.extract_candidate(archive, tmp_path / 'out', max_bytes=1)


def test_extract_is_clean_and_checks_crc_and_required_files(tmp_path):
    archive = make_zip(tmp_path / 'candidate.zip')
    dest = tmp_path / 'out'; dest.mkdir(); (dest / 'stale').write_text('old')
    clean = repro.extract_candidate(archive, dest)
    assert (clean / 'requirements.lock').is_file()
    assert not (dest / 'stale').exists()
    with zipfile.ZipFile(archive, 'w') as zipped:
        zipped.writestr('source/incomplete', 'x')
    with pytest.raises(ValueError, match='missing'):
        repro.extract_candidate(archive, dest)
    assert not dest.exists()


def test_source_identity_survives_status_and_zip_metadata_only(tmp_path):
    root = tmp_path / 'source'; (root / 'course').mkdir(parents=True)
    code = root / 'course/a.py'; code.write_text('real input')
    original = repro.source_content_identity(root)
    (root / 'implementation-status.json').write_text('{"changed":true}')
    (root / 'docs').mkdir(); (root / 'docs/status.md').write_text('generated')
    assert repro.source_content_identity(root) == original
    code.write_text('changed runtime input')
    assert repro.source_content_identity(root) != original


def test_environment_lock_validation_and_isolation(tmp_path, monkeypatch):
    lock = tmp_path / 'requirements.lock'; lock.write_text('pytest==9.2.0\n')
    python = tmp_path / '.venv/bin/python'
    record = {'prefix': str(python.parent.parent), 'base_prefix': '/base', 'versions': {'pytest': '9.2.0'}}
    monkeypatch.setattr(repro, 'run_python', lambda *a, **k: SimpleNamespace(returncode=0, stdout=json.dumps(record)))
    assert repro.validate_environment(python, tmp_path, lock)['lock_sha256'] == repro.sha256(lock)
    record['versions']['pytest'] = '0'
    with pytest.raises(ValueError, match='differs'):
        repro.validate_environment(python, tmp_path, lock)
    lock.write_text('pytest>=9')
    with pytest.raises(ValueError, match='unpinned'):
        repro.validate_environment(python, tmp_path, lock)
    monkeypatch.setenv('PYTHONPATH', '/bad'); monkeypatch.setenv('KITCHEN_PACK', '/bad')
    assert 'PYTHONPATH' not in repro.isolated_env() and 'KITCHEN_PACK' not in repro.isolated_env()


def test_zip_run_preserves_release_fields_and_rejects_missing_video(tmp_path, monkeypatch):
    archive = make_zip(tmp_path / 'candidate.zip')
    root = tmp_path / 'work'; root.mkdir()
    base = root / 'build/reproduction'
    monkeypatch.setattr(repro, 'validate_environment', lambda *a: {'locked': True})
    monkeypatch.setattr(repro, 'fingerprints', lambda *a: {'6.1': 'one', '7.4': 'three'})
    calls = []
    def run(python, clean, code, **kwargs):
        calls.append((clean, code))
        return SimpleNamespace(returncode=0, stdout='', stderr='')
    monkeypatch.setattr(repro, 'run_python', run)
    rows = repro.reproduce(archive, root=root, base=base)
    assert len(rows) == 3
    assert rows[0]['test'] == 'fresh environment tests'
    assert rows[0]['candidate_sha256'] == repro.sha256(archive)
    assert all(clean == base / 'extracted/source' for clean, _ in calls)
    assert rows[0]['tested_candidate_zip'] == str(base / 'candidate.zip')
    assert repro.sha256(base / 'candidate.zip') == rows[0]['candidate_sha256']
    for row in rows[1:]:
        assert {'dish', 'exit_code', 'video', 'exists', 'input_fingerprint', 'source_unchanged'} <= row.keys()
        assert not row['exists']
        assert row['source_unchanged']
    assert repro.main(['--zip', str(archive), '--base', str(base)]) == 1


def test_setup_failure_replaces_old_success_report(tmp_path):
    base = tmp_path / 'reproduction'; base.mkdir()
    (base / 'report.json').write_text('[{"exit_code":0}]')
    rows = repro.reproduce(tmp_path / 'missing.zip', root=tmp_path, base=base)
    assert rows[-1]['exit_code'] == 1
    assert json.loads((base / 'report.json').read_text()) == rows


def test_report_backward_compatibility_with_verify_release(tmp_path, monkeypatch):
    # Invoke the real consumer, isolating unrelated render/media acceptance checks.
    from course.tools import preparation, kitchen, evidence, assembly
    root = tmp_path / 'source'; base = root / 'build/reproduction'; base.mkdir(parents=True)
    rows = [{'test': 'fresh environment tests', 'exit_code': 0, 'candidate_sha256': 'zip',
             'tested_candidate_zip': str(base / 'candidate.zip'), 'source_content_matches': True,
             'source_content_sha256': repro.source_content_identity(root)}]
    rows += [{'test': 'fresh render', 'dish': d, 'exit_code': 0, 'exists': True,
              'input_fingerprint': d, 'source_unchanged': True, 'source_content_sha256': 'inputs'} for d in repro.DISHES]
    (base / 'report.json').write_text(json.dumps(rows))
    monkeypatch.setattr(preparation, 'ROOT', root)
    monkeypatch.setattr(preparation, 'audit', lambda: [])
    monkeypatch.setattr(preparation, 'timeline_findings', lambda: [])
    monkeypatch.setattr(kitchen, 'dishes', lambda: [])
    monkeypatch.setattr(evidence, 'fingerprint_dish', lambda d, context=None: d)
    monkeypatch.setattr(assembly, 'course_plans', lambda: {})
    codes = {f.code for f in preparation.verify_release()}
    assert not {'REPRODUCTION', 'STALE_REPRODUCTION'} & codes
    (root/'requirements.in').write_text('changed after reproduction')
    assert 'STALE_REPRODUCTION' in {f.code for f in preparation.verify_release()}
    (root/'requirements.in').unlink()
    rows[0]['source_content_matches'] = False
    (base / 'report.json').write_text(json.dumps(rows))
    assert 'REPRODUCTION' in {f.code for f in preparation.verify_release()}
    rows[0]['source_content_matches'] = True
    rows[-1]['input_fingerprint'] = 'stale'
    (base / 'report.json').write_text(json.dumps(rows))
    assert 'STALE_REPRODUCTION' in {f.code for f in preparation.verify_release()}


def test_repackaging_original_zip_does_not_invalidate_frozen_candidate(tmp_path, monkeypatch):
    archive = make_zip(tmp_path / 'candidate.zip')
    original_hash = repro.sha256(archive)
    root = tmp_path / 'root'; root.mkdir()
    base = root / 'build/reproduction'
    monkeypatch.setattr(repro, 'validate_environment', lambda *a: {})
    monkeypatch.setattr(repro, 'fingerprints', lambda *a: {'6.1': 'one', '7.4': 'three'})
    def run(python, clean, code, **kwargs):
        archive.write_bytes(b'new delivery packaging status')
        for dish in repro.DISHES:
            video = base / 'renders' / dish / 'videos/player/720p30/Dish.mp4'
            video.parent.mkdir(parents=True, exist_ok=True)
            video.write_bytes(b'render')
        return SimpleNamespace(returncode=0, stdout='', stderr='')
    monkeypatch.setattr(repro, 'run_python', run)
    rows = repro.reproduce(archive, root=root, base=base)
    assert all(row['exit_code'] == 0 for row in rows)
    assert rows[0]['candidate_sha256'] == original_hash
    assert repro.sha256(base / 'candidate.zip') == original_hash
    assert repro.sha256(archive) != original_hash


def test_cli_rejects_source_content_mismatch(monkeypatch):
    monkeypatch.setattr(repro,'reproduce',lambda *a,**k:[{'exit_code':0,'source_content_matches':False}])
    assert repro.main([])==1
