"""Reproduce the delivered ZIP in a clean tree using a separate locked environment.

No dependency installation is implicit. Prepare build/reproduction/.venv from the
candidate's requirements.lock first; every run verifies that environment again.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[2]
DISHES = ('6.1', '7.4')


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def source_content_identity(root):
    """Hash packaged authored/runtime inputs, excluding generated status and docs.

    Archive bytes identify the exact candidate tested; this independent identity
    survives ZIP timestamps, compression and generated documentation changes.
    """
    root = Path(root)
    included = ('course', 'recipes', 'narration', 'sources', 'traces', 'authoring', 'distribution')
    files = []
    for directory in included:
        files.extend(p for p in (root / directory).rglob('*') if p.is_file()
                     and not any(x in ('__pycache__', '.heard', '.pytest_cache') for x in p.parts))
    files.extend(root / p for p in ('requirements.lock', 'requirements-speech.lock',
                                   'requirements.in', 'setup.sh', 'kitchen') if (root / p).is_file())
    digest = hashlib.sha256()
    for path in sorted(files):
        name = path.relative_to(root).as_posix().encode()
        digest.update(len(name).to_bytes(4, 'big'))
        digest.update(name)
        digest.update(bytes.fromhex(sha256(path)))
    return digest.hexdigest()


def extract_candidate(archive, destination, *, max_bytes=20 * 1024**3, max_members=50000):
    """Validate all members before extracting; accept only a source/ rooted ZIP.

    Reject traversal, Windows paths, symlinks/devices, duplicates, encrypted
    entries and excessive expanded size. Never overlay an earlier source tree.
    """
    destination = Path(destination)
    if destination.is_symlink():
        raise ValueError('Extraction destination must not be a symlink')
    with zipfile.ZipFile(archive) as zipped:
        members = zipped.infolist()
        if len(members) > max_members or sum(i.file_size for i in members) > max_bytes:
            raise ValueError('ZIP exceeds extraction limits')
        seen = set()
        for info in members:
            name = info.filename
            parts = PurePosixPath(name).parts
            mode = info.external_attr >> 16
            kind = stat.S_IFMT(mode)
            if (not parts or parts[0] != 'source' or name.startswith('/')
                    or '\\' in name or ':' in name or '\x00' in name
                    or any(p in ('..', '.') for p in name.rstrip('/').split('/'))
                    or '' in name.rstrip('/').split('/')
                    or kind not in (0, stat.S_IFREG, stat.S_IFDIR)
                    or info.flag_bits & 1):
                raise ValueError(f'Unsafe ZIP member: {name!r}')
            # Case-fold to reject aliases on the default macOS filesystem too.
            key = '/'.join(parts).casefold()
            if key in seen:
                raise ValueError(f'Duplicate ZIP member: {name!r}')
            seen.add(key)
        files = {i.filename.rstrip("/").casefold() for i in members if not i.is_dir()}
        for info in members:
            parts = PurePosixPath(info.filename).parts
            for n in range(1, len(parts)):
                prefix = '/'.join(parts[:n]).casefold()
                if prefix in files:
                    raise ValueError(f'ZIP file/directory conflict: {info.filename!r}')
        if destination.exists():
            shutil.rmtree(destination)
        destination.mkdir(parents=True)
        try:
            # Explicit writes, not extractall: archive permissions are never restored.
            for info in members:
                target = destination.joinpath(*PurePosixPath(info.filename).parts)
                if info.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with zipped.open(info) as source, target.open('xb') as out:
                        shutil.copyfileobj(source, out)
            source_root = destination / 'source'
            for required in ('requirements.lock', 'course/stage/player.py', 'course/tools/evidence.py'):
                if not (source_root / required).is_file():
                    raise ValueError(f'Candidate missing {required}')
            return source_root
        except Exception:
            shutil.rmtree(destination)
            raise


def isolated_env():
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(('PYTHON', 'KITCHEN')) and k not in ('VIRTUAL_ENV', 'CONDA_PREFIX')}
    env['PYTHONWARNINGS'] = 'ignore'
    return env


def run_python(python, root, code, *, env=None):
    # -I excludes ambient site packages and PYTHONPATH. Only the chosen tree is added.
    bootstrap = f'import sys; sys.path.insert(0, {str(root)!r}); ' + code
    return subprocess.run([str(python), '-I', '-c', bootstrap], cwd=root,
                          env=env or isolated_env(), capture_output=True, text=True)


def validate_environment(python, root, lock):
    pins = {}
    for line in Path(lock).read_text().splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        match = re.fullmatch(r'([A-Za-z0-9_.-]+)==([^\s;]+)', line)
        if not match:
            raise ValueError(f'Unsupported unpinned lock entry: {line}')
        pins[match[1]] = match[2]
    if not pins:
        raise ValueError('Empty dependency lock')
    code = ('import importlib.metadata as m, json; '
            'print(json.dumps({"prefix":sys.prefix,"base_prefix":sys.base_prefix,'
            '"versions":{name:m.version(name) for name in ' + repr(pins) + '}}))')
    result = run_python(python, root, code)
    if result.returncode:
        raise RuntimeError('Cannot inspect locked environment: ' + result.stderr)
    record = json.loads(result.stdout)
    if Path(record['prefix']).resolve() != Path(python).parent.parent.resolve() or record['prefix'] == record['base_prefix']:
        raise ValueError('Reproduction requires a separate virtual environment')
    mismatch = {k: {'expected': v, 'actual': record['versions'].get(k)}
                for k, v in pins.items() if record['versions'].get(k) != v}
    if mismatch:
        raise ValueError(f'Environment differs from candidate lock: {mismatch}')
    record['lock_sha256'] = sha256(lock)
    return record


def fingerprints(python, root):
    result = run_python(python, root,
        'import json; from course.tools.evidence import fingerprint_dish; '
        f'print(json.dumps({{d:fingerprint_dish(d,{{"profile":"preview"}}) for d in {DISHES!r}}}))')
    if result.returncode:
        raise RuntimeError('Fingerprint inspection failed: ' + result.stderr)
    return json.loads(result.stdout)


def reproduce(archive=None, *, root=ROOT, base=None, python=None):
    root = Path(root).resolve()
    base = Path(base or root / 'build/reproduction').absolute()
    archive = Path(archive or root.parent / 'CSCI-5273-Course-Source.zip').resolve()
    python = Path(python or base / '.venv/bin/python').absolute()
    # Do not resolve the Python executable itself: venv executables can be symlinks.
    if python.parent.parent.resolve() == (root / '.venv').resolve():
        raise ValueError('Cannot reuse the working-tree environment')
    base.mkdir(parents=True, exist_ok=True)
    results = []
    candidate_hash = None
    try:
        # Freeze exact bytes tested; later status packaging may replace the delivery ZIP.
        candidate = base / 'candidate.zip'
        if archive != candidate.resolve():
            shutil.copyfile(archive, candidate.with_suffix('.zip.part'))
            candidate.with_suffix('.zip.part').replace(candidate)
        candidate_hash = sha256(candidate)
        clean = extract_candidate(candidate, base / 'extracted')
        content_identity = source_content_identity(clean)
        working_identity = source_content_identity(root)
        environment = validate_environment(python, clean, clean / 'requirements.lock')
        expected = fingerprints(python, root)
        extracted = fingerprints(python, clean)
        if expected != extracted:
            raise ValueError('Candidate ZIP fingerprints differ from current source inputs')
        env = isolated_env()
        env['KITCHEN_BUILD'] = str(base / 'checks')
        check = run_python(python, clean,
            'import runpy; sys.argv=["pytest","course/tests","-q","-p","no:cacheprovider"]; '
            'runpy.run_module("pytest",run_name="__main__")', env=env)
        (base / 'tests.log').write_text(check.stdout + check.stderr)
        results.append(dict(test='fresh environment tests', exit_code=check.returncode,
                            candidate_zip=str(archive), tested_candidate_zip=str(candidate),
                            candidate_sha256=candidate_hash, extracted_source=str(clean), environment=environment,
                            source_content_sha256=content_identity,
                            working_source_content_sha256=working_identity,
                            source_content_matches=content_identity == working_identity))
        for dish in DISHES:
            render_dir = base / 'renders' / dish
            if render_dir.exists():
                shutil.rmtree(render_dir)
            env['KITCHEN_DISH'] = dish
            args = ['manim', 'render', 'course/stage/player.py', 'Dish', '--renderer', 'cairo',
                    '--disable_caching', '--progress_bar', 'none', '-v', 'ERROR',
                    '-r', '1280,720', '--fps', '30', '--media_dir', str(render_dir)]
            rendered = run_python(python, clean,
                f'import runpy; sys.argv={args!r}; runpy.run_module("manim",run_name="__main__")', env=env)
            (base / f'{dish}.log').write_text(rendered.stdout + rendered.stderr)
            video = render_dir / 'videos/player/720p30/Dish.mp4'
            results.append(dict(test='fresh render', dish=dish,
                exit_code=rendered.returncode or (0 if video.is_file() else 1),
                render_exit_code=rendered.returncode,
                video=str(video.relative_to(root) if video.is_relative_to(root) else video),
                exists=video.is_file(), input_fingerprint=expected[dish],
                extracted_input_fingerprint=extracted[dish],
                source_unchanged=(fingerprints(python, root)[dish] == expected[dish]
                                  and fingerprints(python, clean)[dish] == extracted[dish]),
                artifact_sha256=sha256(video) if video.is_file() else None,
                candidate_sha256=candidate_hash, source_content_sha256=content_identity))
        if source_content_identity(clean) != content_identity:
            raise ValueError('Extracted source content changed during reproduction')
        if sha256(candidate) != candidate_hash:
            raise ValueError('Frozen candidate ZIP changed during reproduction')
    except Exception as error:
        results.append(dict(test='ZIP reproduction setup or integrity', exit_code=1,
                            candidate_zip=str(archive), candidate_sha256=candidate_hash,
                            error=f'{type(error).__name__}: {error}'))
    (base / 'report.json').write_text(json.dumps(results, indent=2) + '\n')
    return results


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--zip', type=Path, dest='archive')
    parser.add_argument('--base', type=Path)
    parser.add_argument('--python', type=Path)
    args = parser.parse_args(argv)
    results = reproduce(args.archive, base=args.base, python=args.python)
    print(json.dumps(results, indent=2))
    return int(any(r['exit_code'] or not r.get('source_unchanged', True)
                   or not r.get('exists', True) or not r.get('source_content_matches',True) for r in results))


if __name__ == '__main__':
    raise SystemExit(main())
