"""Write verification/deliverables-manifest.json: the exact bytes of the verified delivery."""
import datetime
import json
import re
import sys
from pathlib import Path

from course.tools.playback import sha256

ROOT = Path(__file__).resolve().parents[2]
TEXT_FOLDERS = ("captions", "transcript", "player")
TOP_FILES = ("README.md", "final-report.json", "CSCI-5273-Course-Source.zip")
MAIN = "CSCI-5273-Lectures-06-15.mp4"


def record(course, path):
    return {"path": path.relative_to(course).as_posix(), "bytes": path.stat().st_size, "sha256": sha256(path)}


def build_manifest(source, course):
    """Read evidence that other steps already wrote; never decide a state here."""
    media = json.loads((source / "build/media-audit.json").read_text())
    status = json.loads((source / "implementation-status.json").read_text())
    findings = json.loads((source / "build/release-verification.json").read_text())
    tests = re.findall(r"(\d+) passed", (course / "verification/tests.log").read_text())
    if not tests:
        raise ValueError("verification/tests.log has no passing test count")
    files = [record(course, course / name) for name in TOP_FILES]
    for folder in TEXT_FOLDERS:
        files += [record(course, p) for p in sorted((course / folder).rglob("*")) if p.is_file() and p.name != ".DS_Store"]
    main = next(a for a in media["artifacts"] if a["path"].endswith(MAIN))
    return {"created_at": datetime.datetime.now().isoformat(),
            "states": {"mise_complete": status["mise_complete"], "media_verified": status["automatic_media_verified"],
                       "release_verified": status["release_verified"]},
            "tests_passed": int(tests[-1]), "main_seconds": main["seconds"],
            "review_findings": sum(f.get("code") == "REVIEW" for f in findings),
            "source_archive_crc": "passed during atomic packaging",
            "media": media["artifacts"], "files": files}


def main():
    course = ROOT.parent
    try:
        manifest = build_manifest(ROOT, course)
    except (OSError, ValueError, KeyError, StopIteration) as exc:
        raise SystemExit(f"Cannot write the manifest ({exc!r}). Run the earlier steps under 'Hand off the deliverables' in SETUP.md.") from exc
    (course / "verification/deliverables-manifest.json").write_text(json.dumps(manifest, indent=1))
    print(f"{len(manifest['media'])} videos, {len(manifest['files'])} files, {manifest['review_findings']} reviews pending")
    return 0


if __name__ == "__main__":
    sys.exit(main())
