"""The question bank: everything parsed, nothing empty, everything tied to a dish."""
from course.tools import bank

ITEMS = bank.build()


def test_counts_match_the_vault():
    kinds = {}
    for item in ITEMS:
        kinds[item["kind"]] = kinds.get(item["kind"], 0) + 1
    assert kinds["cue"] == 176
    assert kinds["lecture"] == 100
    assert kinds["midterm"] == 20


def test_every_item_has_a_question_an_answer_and_a_dish():
    for item in ITEMS:
        assert len(item["q"]) > 8, item["id"]
        assert len(item["a"]) > 1, item["id"]
        assert item["dishes"], item["id"]


def test_ids_are_unique():
    ids = [i["id"] for i in ITEMS]
    assert len(ids) == len(set(ids))


def test_no_vault_markup_survives():
    for item in ITEMS:
        for text in (item["q"], item["a"]):
            assert "[[" not in text and "**" not in text and "> [!" not in text, item["id"]


def test_every_taught_dish_has_enough_questions():
    by_concept, by_chapter = bank.recipe_maps()
    counts = {d: 0 for dishes in by_chapter.values() for d in dishes}
    for item in ITEMS:
        if item["kind"] != "midterm":
            for d in item["dishes"]:
                if d in counts:
                    counts[d] += 1
    thin = {d: n for d, n in counts.items() if n < 3 and int(d.split(".")[0]) <= 15}
    assert not thin, thin
