"""Regression checks for the fixes made after the lectures 6-15 review notes."""
import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
SLIDES = ROOT / "sources/snapshot/vault/Assets/Slides"

# What each chapter 12 beat's cited slide must mention.
CH12_KEYWORDS = {
    "question": "day in the life",
    "story1": "dhcp",
    "story2": "self learning",
    "story3": "convergence delay",
    "pitfall": "layering",
    "p1": "subnet mask",
    "a1": "subnet mask",
    "p2": "infinity",
    "a2": "infinity",
    "p3": "local preference",
    "a3": "local preference",
    "p5": "mtu",
    "a5": "mtu",
    "p6": "group-specific",
    "a6": "group-specific",
    "p4": "tunnel",
    "predict": "tunnel",
    "a4": "tunnel",
}


def _chapter16_beats():
    doc = next(d for d in yaml.safe_load_all((ROOT / "authoring/ch16.yaml").read_text()) if d)
    return doc, doc["beats"]


def test_chapter16_cites_the_lecture_each_beat_draws_on():
    from pypdf import PdfReader

    doc, beats = _chapter16_beats()
    decks = json.loads((ROOT / "sources/decks.json").read_text())
    cited = set()
    for beat in beats:
        deck = beat.get("deck", doc["deck"])
        page = beat["pdf"]
        cited.add(deck)
        assert deck in decks, f"{beat['id']}: unknown deck {deck}"
        assert 1 <= page <= decks[deck]["pages"], f"{beat['id']}: page {page} is outside {deck}"
        text = PdfReader(SLIDES / deck).pages[page - 1].extract_text().lower()
        assert CH12_KEYWORDS[beat["id"]] in text, f"{beat['id']}: {deck} p{page} does not mention {CH12_KEYWORDS[beat['id']]!r}"
    assert len(cited) >= 8, "the synthesis chapter should draw on many lectures, not one"


def test_chapter16_ending_points_to_the_next_step():
    _, beats = _chapter16_beats()
    last = beats[-1]["say"]
    assert "Thanks for watching" not in last
    assert "chapter 13" in last and "study player" in last


def test_study_player_reports_import_errors_inline():
    source = (ROOT / "course/player/player.js").read_text()
    assert "alert(" not in source
    assert "progress export" in source


def test_viewing_guide_covers_the_whole_package():
    from course.tools.kitchen import guide

    text = guide([("6", "Lecture 6: LANs and switching", "00:00:00", "21.8 min")], 14100)
    for needle in ("Practice-and-Warm-up", "kitchen open", "supplements.md", "SETUP.md", "Lectures 6–15", "not the instructor's exam"):
        assert needle in text, needle
    assert "stops with a progress bar" not in text
    assert "study explanations and constructed examples" in text


def test_final_report_counts_pending_reviews():
    from course.tools.kitchen import dishes, pending_reviews

    pending = pending_reviews()
    assert isinstance(pending, int) and 0 <= pending <= 4 * len(dishes())
    source = (ROOT / "course/tools/kitchen.py").read_text()
    assert 'course.tools.release_status import refresh' in source and '"reviews_pending"' in source


def test_chapter_one_excised_for_midterm_two_scope():
    assert not (ROOT / "authoring/ch01.yaml").exists()
    assert not (ROOT / "recipes/1.1.yaml").exists()
    assert not (ROOT / "recipes/1.2.yaml").exists()


def test_practice_headings_say_practice_midterm():
    text = (ROOT / "authoring/ch17.yaml").read_text()
    assert "Generated practice, question" not in text
    assert len(re.findall(r"Practice midterm, question \d+", text)) == 20
