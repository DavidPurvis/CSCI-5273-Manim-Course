"""A clean clone has no vault or audio (see SETUP.md). Tests that read them skip there; a full checkout runs everything."""
import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
ABSENT = (ROOT / "sources/snapshot", ROOT / "narration/audio")
CLEAN_CLONE = not ABSENT[0].exists()
# These read the vault when imported, so they cannot even be collected.
collect_ignore = ["test_practice.py", "test_bank.py"] if CLEAN_CLONE else []
# Without the vault or audio these fail on an empty catalog or a clip check, not on FileNotFoundError.
NEEDS_ABSENT = {
    "test_packaged_catalog_resolves_alias",
    "test_packaged_wikilinks_and_pdf_pages_resolve",
    "test_packaged_alignment_evidence_works_without_speech_engine",
}


def pytest_report_header():
    return "clean clone: tests that need the vault or audio will skip" if CLEAN_CLONE else None


def pytest_collection_modifyitems(items):
    if CLEAN_CLONE:
        skip = pytest.mark.skip(reason="needs sources/snapshot or narration/audio, absent from a clean clone")
        for item in items:
            if "corpus" in getattr(item, "fixturenames", ()) or getattr(item, "originalname", None) in NEEDS_ABSENT:
                item.add_marker(skip)


def missing_input(exc):
    if isinstance(exc, FileNotFoundError) and isinstance(exc.filename, (str, bytes, os.PathLike)):
        path = Path(os.fsdecode(exc.filename)).absolute()
        return any(path.is_relative_to(folder) for folder in ABSENT)
    return False


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if CLEAN_CLONE and report.failed and call.excinfo and missing_input(call.excinfo.value):
        report.outcome = "skipped"
        path, line = item.reportinfo()[:2]
        report.longrepr = (str(path), None if line is None else line + 1, f"needs {call.excinfo.value.filename}, absent from a clean clone")
