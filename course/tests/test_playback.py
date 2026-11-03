"""Portable delivery and failure isolation, using disposable synthetic bundles."""
import http.client
import json
import subprocess
import sys
import threading
import zipfile
from pathlib import Path
from unittest import mock

import pytest

from course.tools import handoff, playback
from course.tools.local_server import create_server


@pytest.fixture
def candidate(tmp_path, monkeypatch):
    # Isolate the status-copy/promotion tests from production evidence calculation.
    monkeypatch.setattr(handoff,"validate_live_status",lambda source,status:None)
    course = tmp_path / "course"
    source = course / "source"
    source.mkdir(parents=True)
    for name in handoff.FOLDERS:
        (course / name).mkdir()
    for name in ("README.md", "video/dish.mp4", "captions/dish.vtt",
                 "player/index.html", "player/player.js", "player/style.css",
                 "player/tokens.css", "player/slides/slide.jpg"):
        p = course / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"0123456789")
    data = {"dishes": {"1.1": {"cooked": True, "video": "/video/dish.mp4",
            "vtt": "/captions/dish.vtt", "beats": [{"deck": "a.pdf", "slide": "slide.jpg"}]}},
            "concepts": {"a": {"note": "/notes/Concepts/A%20note.md"}}}
    (course / "player/data.json").write_text(json.dumps(data))
    status = {"revision": "test-revision", "release_verified": False,
              "perceptual_review": "not_reviewed", "remaining_work": ["Review"]}
    for path in (source / "implementation-status.json", course / "verification/implementation-status.json"):
        path.write_text(json.dumps(status))
    (course / "final-report.json").write_text(json.dumps({"release_status": status}))
    (course / "verification/deliverables-manifest.json").write_text('{"states":{"release_verified":false}}')
    with zipfile.ZipFile(course / "CSCI-5273-Course-Source.zip", "w") as z:
        z.writestr("source/implementation-status.json", json.dumps(status))
    snapshot = source / "sources/snapshot"
    records = []
    for name in ("Assets/Slides/a.pdf", "Concepts/A note.md", "Assets/Figures/a.png"):
        p = snapshot / "vault" / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"bundled-resource")
        records.append({"path": "vault/" + name, "sha256": playback.sha256(p)})
    (snapshot / "manifest.json").write_text(json.dumps({"snapshot_id": "snapshot-1", "records": records,
        "required_decks": ["vault/Assets/Slides/a.pdf"]}))
    return course, source, tmp_path / "delivered with spaces"


def test_standalone_without_source_or_dependencies(candidate, tmp_path):
    course, source, target = candidate
    handoff.build_handoff(course, source, target)
    course.rename(course.with_name("unavailable"))
    result = subprocess.run([sys.executable, "-S", str(target / "play.py"), "--check"],
                            cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert (target / playback.COMMAND).stat().st_mode & 0o111
    assert (target / "notes/Assets/Figures/a.png").is_file()
    manifest = json.loads((target / playback.MANIFEST).read_text())
    assert {"play.py", "local_server.py", playback.COMMAND, "decks/a.pdf",
            "notes/Concepts/A note.md"} <= manifest["files"].keys()
    assert json.loads((target / "verification/deliverables-manifest.json").read_text())["handoff"] == manifest
    (target / "decks/a.pdf").write_bytes(b"changed")
    assert any("hash mismatch: decks/a.pdf" in e for e in playback.validate_assets(target))


def test_replacement_preserves_previous(candidate):
    course, source, target = candidate
    target.mkdir()
    (target / "old").write_text("keep")
    out, previous = handoff.build_handoff(course, source, target)
    assert out == target
    assert (previous / "old").read_text() == "keep"
    assert not list(target.parent.glob(".*.staging-*"))


@pytest.mark.parametrize("failure", ["copy", "validation", "status", "snapshot", "archive"])
def test_failure_preserves_old_output(candidate, failure):
    course, source, target = candidate
    target.mkdir()
    (target / "old").write_text("keep")
    if failure == "status":
        (course / "verification/implementation-status.json").write_text('{}')
    if failure == "snapshot":
        (source / "sources/snapshot/vault/Concepts/A note.md").write_text("changed")
    if failure == "archive":
        (course / "CSCI-5273-Course-Source.zip").write_bytes(b"broken")
    patch = (mock.patch.object(handoff, "clone", side_effect=OSError("copy interrupted")) if failure == "copy"
             else mock.patch.object(handoff, "validate_handoff", side_effect=ValueError("invalid")) if failure == "validation"
             else mock.patch.object(handoff, "ROOT", source))
    with patch, pytest.raises((OSError, ValueError, zipfile.BadZipFile)):
        handoff.build_handoff(course, source, target)
    assert (target / "old").read_text() == "keep"
    assert not list(target.parent.glob(".*.staging-*"))
    assert not list(target.parent.glob("*.previous-*"))


def test_promotion_failure_restores_previous(tmp_path):
    target, staged = tmp_path / "destination", tmp_path / "staged"
    target.mkdir()
    staged.mkdir()
    (target / "old").write_text("keep")
    rename = Path.rename
    def interrupted(path, destination):
        if path == staged:
            raise OSError("promotion interrupted")
        return rename(path, destination)
    with mock.patch.object(Path, "rename", interrupted), pytest.raises(OSError):
        handoff.promote(staged, target)
    assert (target / "old").read_text() == "keep"


def test_missing_assets_and_traversal(candidate):
    course, source, target = candidate
    handoff.build_handoff(course, source, target)
    (target / "player/slides/slide.jpg").unlink()
    assert any("Missing or empty asset: /slides/slide.jpg" in e for e in playback.validate_assets(target))
    with pytest.raises(ValueError):
        playback.asset_path(target, "/notes/%2e%2e/final-report.json")
    with pytest.raises(ValueError):
        playback.asset_path(target, "https://example.com/a.pdf")


def test_port_fallback_range_head_and_mount_security(tmp_path):
    player = tmp_path / "player"
    player.mkdir()
    (player / "clip.mp4").write_bytes(b"0123456789")
    secret = tmp_path / "secret"
    secret.write_text("private")
    (player / "escape").mkdir()
    (player / "escape/index.html").symlink_to(secret)
    occupied = create_server({"/": player}, port=0)
    server = create_server({"/": player}, port=occupied.server_port)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        assert server.server_port != occupied.server_port
        assert server.server_address[0] == "127.0.0.1"
        client = http.client.HTTPConnection(*server.server_address)
        try:
            client.connect()
        except PermissionError:
            pytest.skip("Local socket connection not permitted in sandbox environment")
        client.request("GET", "/clip.mp4", headers={"Range": "bytes=2-5"})
        response = client.getresponse()
        assert response.status == 206
        assert response.getheader("Content-Range") == "bytes 2-5/10"
        assert response.read() == b"2345"
        for byte_range, status, expected in (("bytes=-3", 206, b"789"),
                                              ("bytes=8-", 206, b"89"),
                                              ("bytes=99-", 416, b"")):
            client.request("GET", "/clip.mp4", headers={"Range": byte_range})
            response = client.getresponse()
            assert response.status == status
            assert response.read() == expected
        client.request("HEAD", "/clip.mp4")
        response = client.getresponse()
        assert response.getheader("Content-Length") == "10"
        assert response.read() == b""
        for url in ("/escape/", "/%2e%2e/secret"):
            client.request("GET", url)
            response = client.getresponse()
            assert response.status == 404
            response.read()
        client.close()
    finally:
        server.shutdown()
        thread.join()
        server.server_close()
        occupied.server_close()


def test_destination_inside_source_rejected(candidate):
    course, source, target = candidate
    with pytest.raises(ValueError, match="outside"):
        handoff.build_handoff(course, source, source / "delivery")


def test_missing_referenced_asset_blocks_promotion(candidate):
    course, source, target = candidate
    (course / "player/slides/slide.jpg").unlink()
    with pytest.raises(ValueError, match="Missing or empty asset"):
        handoff.build_handoff(course, source, target)
    assert not target.exists()
    assert not list(target.parent.glob(".*.staging-*"))


def test_archived_status_must_match(candidate):
    course, source, target = candidate
    with zipfile.ZipFile(course / "CSCI-5273-Course-Source.zip", "w") as archive:
        archive.writestr("source/implementation-status.json", '{"revision":"stale"}')
    with pytest.raises(ValueError, match="archive status differs"):
        handoff.build_handoff(course, source, target)
    assert not target.exists()


def test_concurrent_status_refresh_blocks_promotion(candidate):
    course, source, target = candidate
    original = handoff.read_status(course=course, source=source)
    changed = {**original, "revision": "next"}
    with mock.patch.object(handoff, "read_status", side_effect=[original, changed]):
        with pytest.raises(ValueError, match="changed during handoff"):
            handoff.build_handoff(course, source, target)
    assert not target.exists()
    assert not list(target.parent.glob(".*.staging-*"))


def test_launcher_serves_bundled_resources(candidate):
    course, source, target = candidate
    handoff.build_handoff(course, source, target)
    course.rename(course.with_name("unavailable"))
    server = create_server(playback.mounts(target), port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        client = http.client.HTTPConnection(*server.server_address)
        try:
            client.connect()
        except PermissionError:
            pytest.skip("Local socket connection not permitted in sandbox environment")
        for url in ("/data.json", "/video/dish.mp4", "/captions/dish.vtt",
                    "/decks/a.pdf", "/notes/Concepts/A%20note.md"):
            client.request("GET", url)
            response = client.getresponse()
            assert response.status == 200, url
            assert response.read()
        client.close()
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


@pytest.mark.parametrize("relative", ["review.txt", "vault-source-manifest.json"])
def test_nonvault_snapshot_records_stay_in_source_archive(candidate, relative):
    course, source, target = candidate
    snapshot = source / "sources/snapshot"
    asset = snapshot / relative
    asset.write_bytes(b"frozen-provenance")
    path = snapshot / "manifest.json"
    manifest = json.loads(path.read_text())
    manifest["records"].append({"path": relative, "sha256": playback.sha256(asset)})
    path.write_text(json.dumps(manifest))
    archive_name = "source/sources/snapshot/" + relative
    with zipfile.ZipFile(course / "CSCI-5273-Course-Source.zip", "a") as archive:
        archive.write(asset, archive_name)
    handoff.build_handoff(course, source, target)
    assert not (target / "notes" / relative).exists()
    with zipfile.ZipFile(target / "CSCI-5273-Course-Source.zip") as archive:
        assert archive.read(archive_name) == asset.read_bytes()


@pytest.mark.parametrize("failure", ["missing", "hash"])
def test_invalid_required_deck_blocks_promotion(candidate, failure):
    course, source, target = candidate
    path = source / "sources/snapshot/manifest.json"
    manifest = json.loads(path.read_text())
    if failure == "missing":
        manifest["required_decks"].append("foundation/missing.pdf")
    else:
        manifest["records"][0]["sha256"] = "invalid"
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError):
        handoff.build_handoff(course, source, target)
    assert not target.exists()
    assert not list(target.parent.glob(".*.staging-*"))


def test_current_snapshot_all_records_and_eleven_decks(tmp_path):
    snapshot = handoff.ROOT / "sources/snapshot"
    manifest = json.loads((snapshot / "manifest.json").read_text())
    staged = tmp_path / "snapshot-only"
    staged.mkdir()
    handoff.bundle_snapshot(snapshot, manifest, staged)
    assert len(manifest["required_decks"]) == 10
    assert len(list((staged / "decks").glob("*.pdf"))) == 10
    assert (staged / "decks/lec06-lan.pdf").is_file()
    for record in manifest["records"]:
        relative = Path(record["path"])
        if relative.parts[0] == "vault":
            bundled = staged / "notes" / Path(*relative.parts[1:])
            assert playback.sha256(bundled) == record["sha256"]


def test_delivered_status_is_one_snapshot(candidate):
    course, source, target = candidate
    expected = json.loads((source / "implementation-status.json").read_text())
    handoff.build_handoff(course, source, target)
    assert json.loads((target / "implementation-status.json").read_text()) == expected
    assert json.loads((target / "verification/implementation-status.json").read_text()) == expected
    with zipfile.ZipFile(target / "CSCI-5273-Course-Source.zip") as archive:
        assert json.loads(archive.read("source/implementation-status.json")) == expected
    assert json.loads((target / "final-report.json").read_text())["release_status"] == expected
    assert json.loads((target / playback.MANIFEST).read_text())["revision"] == expected["revision"]


def test_handoff_rejects_asset_changed_since_verified_manifest(candidate):
    course,source,target=candidate
    p=course/'video/dish.mp4'
    (course/'verification/deliverables-manifest.json').write_text(json.dumps({'media':[{'path':'video/dish.mp4','sha256':playback.sha256(p)}]}))
    p.write_bytes(b'corrupted after verification')
    with pytest.raises(ValueError,match='Verified delivery asset changed'):
        handoff.build_handoff(course,source,target)
    assert not target.exists()
