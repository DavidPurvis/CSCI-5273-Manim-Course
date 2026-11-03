"""Stage, validate and promote portable deliverables, retaining the previous handoff."""
import json
import shutil
import subprocess
import sys
import tempfile
import uuid
import zipfile
from pathlib import Path

from course.tools.playback import MANIFEST, sha256, validate_assets, write_launcher

ROOT = Path(__file__).resolve().parents[2]
FOLDERS = ("video", "captions", "transcript", "player", "verification")
FILES = ("README.md", "final-report.json", "CSCI-5273-Course-Source.zip")


def clone(source, target):
    source, target = Path(source), Path(target)
    if sys.platform == "darwin":
        if subprocess.run(["cp", "-cR", str(source), str(target)], capture_output=True).returncode == 0:
            return
        # A failed clone may have left a partial tree.
        if target.is_dir():
            shutil.rmtree(target)
        elif target.exists():
            target.unlink()
    if source.is_dir():
        shutil.copytree(source, target)
    else:
        shutil.copy2(source, target)


def validate_live_status(source, status):
    from course.tools.release_status import live_proof
    if status.get('live_proof') != live_proof(source):
        raise ValueError('Release snapshot is stale against current source or review evidence; refresh and package again')


def read_status(source, course):
    """Consume refresh()'s shared status without changing release evidence."""
    status = json.loads((source / "implementation-status.json").read_text())
    verification = json.loads((course / "verification/implementation-status.json").read_text())
    report = json.loads((course / "final-report.json").read_text())
    if not status.get("revision") or status != verification or status != report.get("release_status"):
        raise ValueError("Release status snapshots differ; run release_status.refresh() and package again")
    with zipfile.ZipFile(course / "CSCI-5273-Course-Source.zip") as archive:
        failed = archive.testzip()
        if failed:
            raise ValueError(f"Source archive integrity failed: {failed}")
        archived = json.loads(archive.read("source/implementation-status.json"))
    if archived != status:
        raise ValueError("Source archive status differs from shared release status; package again")
    validate_live_status(source,status)
    return status


def validate_handoff(target, status):
    """Validate the staged copy before its name can become the destination."""
    errors = validate_assets(target)
    # Check copied bytes against the pre-existing verified delivery, not just
    # the newly generated inventory of whatever happened to be copied.
    evidence_path=target/'verification/deliverables-manifest.json'
    try:
        evidence=json.loads(evidence_path.read_text())
        records=evidence.get('media',[])+evidence.get('files',[])
        for row in records:
            path=(target/row['path']).resolve()
            if not path.is_relative_to(target.resolve()) or not path.is_file() or sha256(path)!=row['sha256']:
                errors.append(f"Verified delivery asset changed: {row['path']}")
    except (OSError,ValueError,KeyError,TypeError) as exc:
        errors.append(f'Invalid delivery manifest (run course.tools.deliverables): {exc}')

    for name in FOLDERS + FILES:
        if not (target / name).exists():
            errors.append(f"Missing deliverable: {name}")
    try:
        copies = [json.loads((target / "implementation-status.json").read_text()),
                  json.loads((target / "verification/implementation-status.json").read_text()),
                  json.loads((target / "final-report.json").read_text())["release_status"]]
        if any(copy != status for copy in copies):
            errors.append("Staged release status differs from source snapshot")
        with zipfile.ZipFile(target / "CSCI-5273-Course-Source.zip") as archive:
            if archive.testzip():
                errors.append("Staged source ZIP failed CRC validation")
            if json.loads(archive.read("source/implementation-status.json")) != status:
                errors.append("Staged source ZIP status differs from source snapshot")
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as exc:
        errors.append(f"Invalid staged evidence: {exc}")
    if errors:
        raise ValueError("Handoff validation failed:\n" + "\n".join(errors))


def promote(staged, target):
    """Rename only validated trees; retain old output and roll back a failed rename.

    Each rename is atomic on the shared filesystem. Replacing an existing nonempty
    directory takes two renames, so readers can briefly see the destination absent.
    """
    previous = None
    if target.exists():
        previous = target.with_name(f"{target.name}.previous-{uuid.uuid4().hex}")
        target.rename(previous)
    try:
        staged.rename(target)
    except BaseException:
        if previous is not None:
            previous.rename(target)
        raise
    return previous


def bundle_snapshot(snapshot, source_manifest, staged):
    """Bundle vault notes and required decks; other provenance stays in the source ZIP."""
    snapshot, staged = Path(snapshot).resolve(), Path(staged).resolve()
    clone(snapshot / "vault", staged / "notes")
    records = {}
    for record in source_manifest["records"]:
        relative = Path(record["path"])
        # Review/provenance records are archived sources, not player notes.
        if relative.parts[:1] != ("vault",):
            continue
        original = (snapshot / relative).resolve()
        if relative.is_absolute() or ".." in relative.parts or not original.is_relative_to(snapshot):
            raise ValueError(f"Invalid snapshot resource: {relative}")
        if relative.as_posix() in records:
            raise ValueError(f"Duplicate snapshot resource: {relative}")
        records[relative.as_posix()] = record
        bundled = (staged / "notes" / Path(*relative.parts[1:])).resolve()
        if (not bundled.is_relative_to(staged / "notes") or not bundled.is_file()
                or sha256(bundled) != record["sha256"]):
            raise ValueError(f"Snapshot resource hash mismatch: {relative}")
    decks = staged / "decks"
    decks.mkdir()
    names = set()
    required = source_manifest["required_decks"]
    if not required:
        raise ValueError("Snapshot must list required_decks")
    for relative in required:
        record = records.get(relative)
        if record is None:
            raise ValueError(f"Required deck missing from vault snapshot records: {relative}")
        name = Path(relative).name
        if Path(relative).suffix.lower() != ".pdf" or name in names:
            raise ValueError(f"Invalid or ambiguous required deck: {relative}")
        names.add(name)
        clone(snapshot / relative, decks / name)
        if sha256(decks / name) != record["sha256"]:
            raise ValueError(f"Required deck hash mismatch: {relative}")


def build_handoff(course, source, destination):
    course, source = Path(course).resolve(), Path(source).resolve()
    target = Path(destination).absolute()
    # Never permit a destination that could rename the source or recurse into it.
    if target.is_symlink():
        raise ValueError("Handoff destination cannot be a symlink")
    target = target.resolve()
    resolved = target
    if (resolved == course or resolved.is_relative_to(course)
            or course.is_relative_to(resolved) or source.is_relative_to(resolved)
            or resolved.is_relative_to(source)):
        raise ValueError("Handoff destination must be outside the course/source tree")
    if target.exists() and not target.is_dir():
        raise ValueError("Handoff destination must be a directory")
    missing = [name for name in FOLDERS + FILES if not (course / name).exists()]
    if missing:
        raise ValueError("Missing from course folder: " + ", ".join(missing))
    status = read_status(source, course)
    snapshot = source / "sources/snapshot"
    source_manifest = json.loads((snapshot / "manifest.json").read_text())
    target.parent.mkdir(parents=True, exist_ok=True)
    staged = Path(tempfile.mkdtemp(prefix=f".{target.name}.staging-", dir=target.parent))
    try:
        for name in FOLDERS + FILES:
            clone(course / name, staged / name)
        bundle_snapshot(snapshot, source_manifest, staged)
        clone(source / "implementation-status.json", staged / "implementation-status.json")
        write_launcher(staged)
        for stray in staged.rglob(".DS_Store"):
            stray.unlink()
        (staged / "video/CSCI-5273-Full-Course.mp4").unlink(missing_ok=True)
        # Inventory the delivered bytes, including generated launchers and resources.
        records = {p.relative_to(staged).as_posix(): sha256(p)
                   for p in sorted(staged.rglob("*")) if p.is_file()
                   and p != staged / "verification/deliverables-manifest.json"}
        manifest = dict(schema_version=1, revision=status["revision"],
                        snapshot_id=source_manifest["snapshot_id"], files=records)
        (staged / MANIFEST).write_text(json.dumps(manifest, indent=2) + "\n")
        evidence_path = staged / "verification/deliverables-manifest.json"
        evidence = json.loads(evidence_path.read_text()) if evidence_path.exists() else {}
        evidence["handoff"] = manifest
        evidence_path.write_text(json.dumps(evidence, indent=2) + "\n")
        validate_handoff(staged, status)
        # Catch a concurrent refresh/package while the copy was being constructed.
        if read_status(source, course) != status:
            raise ValueError("Release status changed during handoff; retry from one snapshot")
        previous = promote(staged, target)
    finally:
        if staged.exists():
            shutil.rmtree(staged)
    return target, previous


def main(destination=None):
    course = ROOT.parent
    target = Path(destination) if destination else course.parent / f"{course.name}-handoff"
    try:
        target, previous = build_handoff(course, ROOT, target)
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as exc:
        raise SystemExit(str(exc)) from exc
    print(target)
    if previous:
        print(f"Previous handoff preserved: {previous}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else None))
