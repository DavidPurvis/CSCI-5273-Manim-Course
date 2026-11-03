"""Exercise real corpus export and isolated missing/stale/tampered variants."""
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

from course.tools import gemini


@pytest.fixture
def corpus(tmp_path):
    root = tmp_path / "pack/source"
    for label, text in gemini.source_documents():
        if label.startswith("course/"):
            path = root / label.removeprefix("course/")
        elif label.startswith("vault/"):
            path = root / "sources/snapshot" / label
        elif label.startswith("companion/transcript/"):
            path = root.parent / label.removeprefix("companion/")
        elif label.startswith("companion/model-traces/"):
            path = root / "traces" / Path(label).name
        else:
            path = root / "sources" / Path(label).name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text.encode("utf-8"))
    for name in ("gemini-research-brief.md", "teaching-bindings.yaml"):
        (root / "sources" / name).write_bytes((gemini.ROOT / "sources" / name).read_bytes())
    return root


def test_reproducible_export_and_complete_current_corpus(corpus):
    output = gemini.export(corpus)
    first = output.read_bytes()
    assert output == gemini.default_output(corpus)
    assert len(gemini.DOCUMENT.findall(first.decode())) == 230
    assert gemini.validate_freshness(corpus) == []
    gemini.export(corpus)
    assert output.read_bytes() == first
    assert gemini.render(corpus) == gemini.render()  # portable: no absolute paths/timestamps


@pytest.mark.parametrize("change", ["missing", "duplicate", "concepts", "bindings", "stale", "brief"])
def test_input_failures_and_staleness_are_auditable(corpus, change):
    output = gemini.export(corpus)
    original = output.read_bytes()
    if change == "missing":
        (corpus / "traces/bgp.json").unlink()
    elif change == "duplicate":
        (corpus / "sources/concepts.json").write_text('{"x": {}, "x": {}}')
    elif change == "concepts":
        path = corpus / "sources/concepts.json"
        data = json.loads(path.read_text()); data.pop(next(iter(data)))
        path.write_text(json.dumps(data))
    elif change == "bindings":
        with (corpus / "sources/teaching-bindings.yaml").open("a") as stream:
            stream.write("\nextra-concept: {}\n")
    elif change == "brief":
        with (corpus / "sources/gemini-research-brief.md").open("a") as stream:
            stream.write("A new research requirement.\n")
    else:
        with (corpus / "traces/bgp.json").open("a") as stream:
            stream.write("\n")
    assert gemini.validate_freshness(corpus)
    assert output.read_bytes() == original  # audit is read-only
    if change in ("missing", "duplicate", "concepts", "bindings"):
        with pytest.raises((ValueError, OSError)):
            gemini.export(corpus)
        assert output.read_bytes() == original


@pytest.mark.parametrize("change", ["duplicate", "missing", "hash", "index", "footer"])
def test_tampered_export_is_rejected(corpus, change):
    output = gemini.export(corpus)
    text = output.read_text()
    match = gemini.DOCUMENT.search(text)
    if change == "duplicate":
        text += "\n" + match.group()
    elif change == "missing":
        text = text.replace(match.group(), "", 1)
    elif change == "hash":
        text = text[:match.start(2)] + "tampered" + text[match.end(2):]
    elif change == "index":
        text = text.replace("1. `course/sources/concepts.json`", "1. `wrong.json`", 1)
    else:
        text = text.replace("# END OF CONTEXT PACKAGE", "# wrong footer")
    output.write_text(text)
    assert gemini.validate_freshness(corpus)


def test_scope_refresh_does_not_change_revision_or_freshness(corpus):
    output = gemini.export(corpus)
    before = gemini.render(corpus)
    (corpus / "sources/verification-scope.json").write_text('{"release_verified": false, "status": "refreshed"}\n')
    assert gemini.validate_freshness(corpus) == []
    after = gemini.render(corpus)
    assert before != after
    revision = lambda text: json.loads(text.split('```json\n', 1)[1].split('\n```', 1)[0])["revision"]
    assert revision(before) == revision(after)
    gemini.export(corpus)
    assert output.read_text() == after
    assert gemini.validate_freshness(corpus) == []


def test_missing_export_returns_diagnostic(corpus):
    assert "validation" in gemini.validate_freshness(corpus)[0]


def test_clean_zip_export_and_audit_without_parent_outputs(corpus, tmp_path):
    # Exercise the original parent location first, then ship only source/.
    external = corpus.parent.parent / "CSCI-5273-Gemini-Handoff" / gemini.HANDOFF
    external.parent.mkdir()
    assert gemini.export(corpus) == external
    assert external.read_bytes() == gemini.packaged_output(corpus).read_bytes()
    tool = corpus / "course/tools/gemini.py"
    tool.parent.mkdir(parents=True)
    shutil.copyfile(gemini.__file__, tool)
    archive = tmp_path / "standalone-source.zip"
    with zipfile.ZipFile(archive, "w") as bundle:
        for path in sorted(corpus.rglob("*")):
            if path.is_file():
                bundle.write(path, "source/" + path.relative_to(corpus).as_posix())
    extracted = tmp_path / "clean"
    with zipfile.ZipFile(archive) as bundle:
        bundle.extractall(extracted)
    root = extracted / "source"
    shutil.rmtree(corpus.parent)
    shutil.rmtree(external.parent)
    assert not (root.parent / "transcript").exists()
    assert gemini.default_output(root) == gemini.packaged_output(root)
    assert gemini.validate_freshness(root) == []
    before = gemini.packaged_output(root).read_bytes()
    # Run the extracted module, not the original module's ROOT.
    for args in (("--check",), (), ("--check",)):
        result = subprocess.run([sys.executable, "-m", "course.tools.gemini", *args],
                                cwd=root, capture_output=True, text=True)
        assert result.returncode == 0, result.stdout + result.stderr
    assert gemini.packaged_output(root).read_bytes() == before
    assert len(gemini.DOCUMENT.findall(before.decode())) == 230  # no self-inclusion


@pytest.mark.parametrize("kind", ["transcript", "handoff"])
def test_present_but_incomplete_parent_does_not_use_fallback(corpus, kind):
    gemini.export(corpus)
    if kind == "transcript":
        (corpus.parent / "transcript/transcript.md").unlink()
    else:
        external = corpus.parent.parent / "CSCI-5273-Gemini-Handoff"
        external.mkdir()
        assert gemini.default_output(corpus).parent == external
    assert gemini.validate_freshness(corpus)


@pytest.mark.parametrize("kind", ["transcript", "manifest", "context"])
def test_packaged_artifact_drift_detected_even_with_current_parent(corpus, kind):
    external = corpus.parent.parent / "CSCI-5273-Gemini-Handoff"
    external.mkdir()
    gemini.export(corpus)
    if kind == "context":
        gemini.packaged_output(corpus).write_text("broken")
    elif kind == "manifest":
        (corpus / "sources/gemini-inputs/manifest.json").write_text("{}")
    else:
        (corpus / "sources/gemini-inputs/transcript/transcript.md").write_text("stale")
    assert gemini.validate_freshness(corpus)
    gemini.export(corpus)
    assert gemini.validate_freshness(corpus) == []
