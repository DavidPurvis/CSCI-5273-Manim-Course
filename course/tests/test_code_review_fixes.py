"""Regressions for the code-review fixes: caption offsets, the write endpoint, the freeze report, the manifest."""
import http.client
import json
import threading
from types import SimpleNamespace
from unittest import mock

import pytest

from course.tools import deliverables, kitchen
from course.tools.local_server import create_server
from course.tools.review_page import save_notes


def test_offsets_follow_container_durations_not_compiled_frames():
    with mock.patch.object(kitchen, "probe_duration", side_effect=[10.03, 20.03, 5.03]):
        starts, total = kitchen.measured_starts(["a", "b", "c"])
    assert starts == pytest.approx([0.0, 10.03, 30.06])
    assert total == pytest.approx(35.09)


def test_duration_tolerance_grows_with_the_number_of_dishes():
    plan = mock.Mock(total_frames=30_000, members=list(range(60)))
    assert kitchen.matches_plan(1002.5, plan)
    assert not kitchen.matches_plan(1004.0, plan)


def test_release_check_expects_the_markers_the_audit_expects():
    source = (kitchen.ROOT / "course/tools/preparation.py").read_text()
    assert "video/CSCI-5273-Lectures-06-15.mp4',True,11)" in source
    assert "markers=11 if path.name=='CSCI-5273-Lectures-06-15.mp4'" in (kitchen.ROOT / "course/tools/media_audit.py").read_text()


@pytest.fixture
def server():
    calls = []
    srv = create_server({"/": "."}, lambda path, data: calls.append(data) or json.loads(data), port=0)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield srv.server_port, calls
    srv.shutdown()
    srv.server_close()


def post(port, headers, body=b"[]"):
    conn = http.client.HTTPConnection("127.0.0.1", port)
    conn.request("POST", "/notes", body=body, headers=headers)
    status = conn.getresponse().status
    conn.close()
    return status


def test_other_sites_cannot_write(server):
    port, calls = server
    assert post(port, {"Origin": "https://evil.example", "Content-Type": "application/json"}) == 403
    assert post(port, {"Origin": f"http://127.0.0.1:{port}", "Content-Type": "text/plain"}) == 403
    assert post(port, {"Host": "evil.example", "Content-Type": "application/json"}) == 403
    assert calls == []


def test_own_page_can_write_and_bad_json_is_rejected(server):
    port, calls = server
    assert post(port, {"Origin": f"http://127.0.0.1:{port}", "Content-Type": "application/json"}) == 200
    assert post(port, {"Content-Type": "application/json"}, b"not json") == 400
    assert len(calls) == 2


def test_decisions_must_name_a_current_video(tmp_path):
    (tmp_path / "review").mkdir()
    (tmp_path / "review/artifacts.json").write_text(json.dumps(["real"]))
    entry = {"reviewer": "A", "dish": "6.1", "note": "", "fp": "made-up", "reviews": {"content": "passed"}}
    assert "error" in save_notes(json.dumps([entry]), tmp_path / "notes.md", tmp_path)
    assert not (tmp_path / "review/decisions.jsonl").exists()
    entry["fp"] = "real"
    assert "error" not in save_notes(json.dumps([entry]), tmp_path / "notes.md", tmp_path)
    assert (tmp_path / "review/decisions.jsonl").exists()


def test_long_gap_report_flags_only_long_narrated_gaps():
    beats = [{"id": "long", "stage": "animation"}, {"id": "short", "stage": "animation"}, {"id": "hold", "stage": "prediction"}]
    moves = {"long": [{"start": 25 * 30, "frames": 30}, {"start": 27 * 30, "frames": 30}], "short": [{"start": 5 * 30, "frames": 30}], "hold": []}
    slots = [{"total": 60.0, "hold": 0}, {"total": 10.0, "hold": 0}, {"total": 40.0, "hold": 39.0}]
    with mock.patch.object(kitchen, "dishes", return_value=["d"]), mock.patch.object(kitchen, "load_card", return_value={"beats": beats}), \
            mock.patch.object(kitchen, "load_manifest", return_value={b["id"]: {} for b in beats}), mock.patch.object(kitchen, "load_timing", return_value={}), \
            mock.patch.object(kitchen, "narration_text", return_value={b["id"]: "" for b in beats}), mock.patch.object(kitchen, "beat_times", return_value=(slots, 110.0)), \
            mock.patch.object(kitchen, "word_times", return_value=[]), \
            mock.patch("course.stage.timeline.compile_beat", side_effect=lambda beat, *a, **k: SimpleNamespace(moves=moves[beat["id"]])):
        assert kitchen.long_narrated_gaps(limit=20.0) == [("long", 25.0), ("long", 32.0)]


def test_notes_survive_a_stale_review_page(tmp_path):
    (tmp_path / "review").mkdir()
    (tmp_path / "review/artifacts.json").write_text(json.dumps(["current"]))
    unreviewed = {c: "not_reviewed" for c in ("content", "visual", "audio", "captions")}
    entry = {"reviewer": "", "dish": "6.1", "note": "first note", "fp": "old-build", "reviews": unreviewed}
    assert save_notes(json.dumps([entry]), tmp_path / "notes.md", tmp_path) == {"notes": 1}
    entry.update(reviewer="A", note="second note", reviews={**unreviewed, "visual": "passed"})
    reply = save_notes(json.dumps([entry]), tmp_path / "notes.md", tmp_path)
    assert reply["notes"] == 1 and "not current" in reply["error"]
    assert "first note" in (tmp_path / "notes.md").read_text() and "second note" in (tmp_path / "notes.md").read_text()
    assert not (tmp_path / "review/decisions.jsonl").exists()


def test_manifest_explains_missing_evidence(tmp_path):
    with mock.patch.object(deliverables, "ROOT", tmp_path / "source"), pytest.raises(SystemExit, match="SETUP.md"):
        deliverables.main()


def test_setup_creates_the_manifest_evidence_first():
    setup = (kitchen.ROOT / "SETUP.md").read_text()
    order = [setup.index(step) for step in ("course.tools.package", "tee ../verification/tests.log", "./kitchen verify-release\n.venv", "course.tools.deliverables\n", "course.tools.handoff\n")]
    assert order == sorted(order)


def test_manifest_reads_existing_evidence(tmp_path):
    course = tmp_path / "course"
    source = course / "source"
    (source / "build").mkdir(parents=True)
    (course / "verification").mkdir()
    (source / "build/media-audit.json").write_text(json.dumps({"artifacts": [{"path": f"video/{deliverables.MAIN}", "seconds": 9.5, "sha256": "x"}]}))
    (source / "implementation-status.json").write_text(json.dumps({"mise_complete": True, "automatic_media_verified": True, "release_verified": False}))
    (source / "build/release-verification.json").write_text(json.dumps([{"code": "REVIEW"}, {"code": "OTHER"}]))
    (course / "verification/tests.log").write_text("12 passed in 1s\n")
    for name in deliverables.TOP_FILES + ("captions/a.vtt", "transcript/t.md", "player/p.js", "player/.DS_Store"):
        path = course / name
        path.parent.mkdir(exist_ok=True)
        path.write_text("x")
    manifest = deliverables.build_manifest(source, course)
    assert manifest["states"]["release_verified"] is False
    assert (manifest["tests_passed"], manifest["review_findings"], manifest["main_seconds"]) == (12, 1, 9.5)
    assert {f["path"] for f in manifest["files"]} >= {"README.md", "captions/a.vtt", "player/p.js"}
    assert not any(".DS_Store" in f["path"] for f in manifest["files"])


def test_player_validates_imports_and_asks_first():
    source = (kitchen.ROOT / "course/player/player.js").read_text()
    body = source[source.index("function importProgress"):]
    body = body[:body.index("\nfunction ", 10)]
    assert "isProgressExport(saved)" in body and "confirmFirst(" in body
    assert "Object.assign(defaults(), JSON.parse" not in body
