import json
import subprocess
import shutil

import pytest

from course.tools.player_build import ROOT, assessment_date


def test_packaged_assessment_default():
    assert assessment_date() == "2026-11-04"


@pytest.mark.parametrize("config, expected", [({}, None), ({"assessment_date": None}, None),
    ({"assessment_date": ""}, None), ({"assessment_date": "2028-02-29"}, "2028-02-29")])
def test_optional_date(tmp_path, config, expected):
    assert assessment_date(tmp_path) is None
    (tmp_path / "sources").mkdir()
    (tmp_path / "sources/study-config.json").write_text(json.dumps(config))
    assert assessment_date(tmp_path) == expected


@pytest.mark.parametrize("value", ["2026-02-29", "20261104", "2026-11-04T12:00:00", False, 20261104])
def test_invalid_dates_fail_clearly(tmp_path, value):
    (tmp_path / "sources").mkdir()
    (tmp_path / "sources/study-config.json").write_text(json.dumps({"assessment_date": value}))
    with pytest.raises(ValueError, match="assessment_date"):
        assessment_date(tmp_path)


def test_frontend_days_left_handles_undated_and_legacy_data():
    node = shutil.which("node")
    if not node:
        pytest.skip("Node is required for the frontend function check")
    text = (ROOT / "course/player/player.js").read_text()
    function = text.split("function daysLeft() {", 1)[1].split("\n}", 1)[0]
    script = "let D = {}; function daysLeft() {" + function + "\n}\n" + """
const assert = require('node:assert/strict');
assert.equal(daysLeft(), null);
D.examDate = null; assert.equal(daysLeft(), null);
D.examDate = ''; assert.equal(daysLeft(), null);
D.examDate = 'invalid'; assert.equal(daysLeft(), null);
D.examDate = '2026-11-04'; assert.ok(Number.isFinite(daysLeft()));
"""
    subprocess.run([node, "-e", script], check=True, capture_output=True, text=True)
