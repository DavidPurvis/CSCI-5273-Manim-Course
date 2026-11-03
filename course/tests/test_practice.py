"""Practice values come from the models, and must agree with the vault's model answers, which were written separately."""
import re

from course.model import practice
from course.tools.sources import VAULT

ANSWERS = (VAULT / "Practice" / "02 - Model Answers.md").read_text()
T = practice.trace()


def answer(n):
    return re.split(r"\n## ", ANSWERS.split(f"## {n}. ", 1)[1], maxsplit=1)[0]


def test_q1_switch():
    e = T["q1"]
    assert [x["action"] for x in e] == ["flood", "forward", "forward"]
    assert e[0]["out_ports"] == [2, 3] and e[1]["out_ports"] == [1] and e[2]["out_ports"] == [2]
    assert "flood 2 and 3" in answer(1) and "A1,B2,C3" in answer(1)
    assert e[2]["table"] == {"A": 1, "B": 2, "C": 3}


def test_q3_prefix():
    q, a = T["q3"], answer(3)
    for value in (q["mask"], q["network"], q["broadcast"], str(q["usable"])):
        assert value in a
    assert q["same_subnet"] is True


def test_q4_fragments():
    a = answer(4)
    assert "976,976,628" in a and "996,996,648" in a and "0,122,244" in a and "1,1,0" in a
    assert [f["payload"] for f in T["q4"]] == [976, 976, 628]
    assert [f["total"] for f in T["q4"]] == [996, 996, 648]
    assert [f["offset_units"] for f in T["q4"]] == [0, 122, 244]
    assert [f["mf"] for f in T["q4"]] == [1, 1, 0]


def test_q5_lpm():
    assert [r["output"] for r in T["q5"]] == ["C", "B", "A", "D"]
    assert "C,B,A,D" in answer(5)


def test_q9_dijkstra():
    q, a = T["q9"], answer(9)
    assert "Final B2,C3,D5" in a
    assert q["dist"]["B"] == 2 and q["dist"]["C"] == 3 and q["dist"]["D"] == 5
    assert q["pred"]["D"] == "C" and q["first_hop"]["D"] == "B"


def test_q10_bellman_ford():
    a = answer(10)
    assert "=6 via W" in a and "=9 via V" in a
    assert T["q10_first"]["total"] == 6 and T["q10_first"]["via"] == "W"
    assert T["q10_second"]["total"] == 9 and T["q10_second"]["via"] == "V"


def test_q11_counting():
    rows = T["q11"]
    assert rows[1]["Y"] == 3 and rows[2]["Z"] == 4 and rows[3]["Y"] == 5


def test_q13_selection():
    assert T["q13_first"]["winner"] == "A" and T["q13_second"]["winner"] == "B"
    assert T["q13_first"]["log"][-1]["step"] == "local preference"
    assert T["q13_second"]["log"][-1]["step"] == "AS path length"


def test_q14_export():
    assert T["q14"]["to_customer"] is True and T["q14"]["to_peer"] is False


def test_q15_rates():
    a = answer(15)
    assert "30 Mb/s" in a and "10 Mb/s" in a
    assert T["q15"]["unicast"] == 30 and T["q15"]["multicast"] == 10


def test_q18_cdma():
    q, a = T["q18"], answer(18)
    assert "(0,−2,2,0)" in a
    assert q["z"] == [0, -2, 2, 0] and q["d1"] == -1 and q["d2"] == 1


def test_warm_up_values_checked_by_hand():
    w = T["warm"]
    assert (w["mask"], w["network"], w["broadcast"], w["usable"]) == ("255.255.248.0", "192.168.32.0", "192.168.39.255", 2046)
    assert [f["payload"] for f in T["warm_frags"]] == [576, 576, 576, 52]
    assert [f["offset_units"] for f in T["warm_frags"]] == [0, 72, 144, 216]
    assert T["warm_lookup"]["output"] == "B"
