"""Every model behind the PS2 drills must first reproduce PS2's own answers."""
import yaml
from pathlib import Path

from course.model import ps2

ROOT = Path(__file__).resolve().parents[2]
INF = ps2.INF


def test_transcription_has_all_questions_and_points():
    data = yaml.safe_load((ROOT / "sources/ps2.yaml").read_text())["questions"]
    assert [q["n"] for q in data] == list(range(1, 19))
    assert sum(q["points"] for q in data) == 100
    for q in data:
        if q.get("figure"):
            assert (ROOT / "sources/ps2" / q["figure"]).is_file() and q["alt"]


def test_q1_q3():
    assert ps2.valid_host("10.72.0.255", "255.255.254.0")
    assert ps2.same_subnet("192.168.2.0/23", "192.168.3.0/23")


def test_q2_carve():
    got = ps2.carve("10.72.0.0/16", [8192] * 5 + [2048] * 8 + [128] * 10)
    assert got[:5] == ["10.72.0.0/19", "10.72.32.0/19", "10.72.64.0/19", "10.72.96.0/19", "10.72.128.0/19"]
    assert got[5:13] == [f"10.72.{x}.0/21" for x in range(160, 224, 8)]
    assert got[13:] == ["10.72.224.0/25", "10.72.224.128/25", "10.72.225.0/25", "10.72.225.128/25", "10.72.226.0/25", "10.72.226.128/25", "10.72.227.0/25", "10.72.227.128/25", "10.72.228.0/25", "10.72.228.128/25"]


def test_q4_departments():
    assert ps2.departments("192.168.0.0/23", [130, 120, 60, 31]) == ["192.168.0.0/24", "192.168.1.0/25", "192.168.1.128/26", "192.168.1.192/26"]


def test_q8_q9_q10_cost_jump():
    rounds = ps2.cost_jump(4, 1, 50, 100)
    assert rounds[0] == {"y_via_x": 100, "y_via_z": 8, "z_via_x": 50, "z_via_y": 7}
    assert rounds[1] == {"y_via_x": 100, "y_via_z": 10, "z_via_x": 50, "z_via_y": 9}
    assert ps2.updates_until_settled(4, 1, 50, 100) == 23


def test_q11_one_exchange():
    expected = {"A": "0A 5B 2C 7B 4C ∞-", "B": "5A 0B 7A 2D ∞- 6D", "C": "2A 7A 0C 8D 2E 6E", "D": "7B 2B 8C 0D 8F 4F", "E": "4C ∞- 2C 8F 0E 4F", "F": "∞- 6D 6E 4D 4E 0F"}
    got = ps2.dv_round(ps2.GRID)
    for node, row in expected.items():
        assert " ".join(ps2.show(got[node][d][0]) + got[node][d][1] for d in "ABCDEF") == row, node


def test_q12_link_state():
    got = ps2.link_state(ps2.GRID, "D")
    assert {d: got[d] for d in "ABCEF"} == {"A": (7, "B"), "B": (2, "B"), "C": (8, "C"), "E": (8, "F"), "F": (4, "F")}


def test_q13_headers():
    assert ps2.hop_headers("B", "C") == [
        ("B to R3", "0D:23:42:AC:EE:FC", "AF:0C:EF:11:22:11", "22.1.23.45", "33.2.2.18"),
        ("R3 to R2", "AA:BB:CC:AF:2F:11", "AF:CC:1F:11:EE:10", "22.1.23.45", "33.2.2.18"),
        ("R2 to R4", "0C:32:56:90:09:EF", "89:98:AF:FF:FF:0C", "22.1.23.45", "33.2.2.18"),
        ("R4 to C", "00:1C:AA:FE:F1:1A", "00:0C:EA:17:98:32", "22.1.23.45", "33.2.2.18")]


def test_q16_mpls():
    t = ps2.mpls_tables()
    assert t["R3"] == [(1, 4, "A", 1), (2, 3, "C", 0)] and t["R6"] == (5, "-", "A", 0) and t["R4"] == (3, "-", "C", 0) and t["R5"] == (4, 5, "A", 0)


def test_q18_visible_rows():
    rows = {"1 3 d": False, "1 4 d": True, "8 d": True, "6 d": True, "4 d": True, "7 5 d": True, "7 5 3 d": True}
    assert {p: ps2.valley(p.split()) for p in rows} == rows


def test_drills_are_well_formed_and_new():
    drills = ps2.drills()
    kinds = {key for key, _, _ in ps2.TYPES}
    assert {d["type"] for d in drills} == kinds
    assert len({d["id"] for d in drills}) == len(drills)
    assert all(d["fields"] and d["steps"] and all(f["answer"] != "" for f in d["fields"]) for d in drills)
    prompts = " ".join(d["prompt"] for d in drills)
    assert "10.72.0.255/255.255.254.0" not in prompts and "128.96.34.250" not in prompts
    assert all((ROOT / "sources/ps2" / d["figure"]).is_file() for d in drills if d.get("figure"))
    assert ps2.drills() == drills
