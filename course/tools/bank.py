"""Turn the vault's questions into one bank, each tied to the dishes that teach it."""
import json
import re

import yaml

from course.stage.card import ROOT
from course.tools.sources import VAULT

CHAPTER = {"L06": "6", "L07": "7", "L08": "8", "L09": "9", "L10": "10", "L11": "11", "L12": "12", "L13": "13", "L14": "14", "L15": "15"}
OUT = ROOT / "sources" / "bank.json"


def clean(text):
    text = re.sub(r"\[\[[^\]|]*\|([^\]]+)\]\]", r"\1", text)
    text = re.sub(r"\[\[([^\]]+)\]\]", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\(https?://[^)]*\)", r"\1", text)
    text = text.replace("**", "").replace("`", "")
    return re.sub(r"\s+", " ", text).strip()


def links(text):
    return [m.split("|")[0].split("#")[0] for m in re.findall(r"\[\[([^\]]+)\]\]", text)]


def recipe_maps():
    """Which dishes teach each concept, and the dishes of each chapter."""
    by_concept, by_chapter = {}, {}
    for path in (ROOT / "recipes").glob("*.yaml"):
        card = yaml.safe_load(path.read_text())
        by_chapter.setdefault(card["dish"].split(".")[0], []).append(card["dish"])
        for beat in card["beats"]:
            for c in beat.get("concepts") or []:
                dishes = by_concept.setdefault(c, [])
                if card["dish"] not in dishes:
                    dishes.append(card["dish"])
    return by_concept, by_chapter


def tie(concepts, text, chapter, by_concept, by_chapter, names):
    """Linked concepts first, then concept names found in the text, then the whole chapter."""
    found = [c for c in concepts if c in by_concept]
    if not found:
        lowered = text.lower()
        found = [n for n in names if n.lower() in lowered]
    dishes = []
    for c in found:
        for d in by_concept[c]:
            if d not in dishes and (chapter is None or d.split(".")[0] == chapter):
                dishes.append(d)
    return found, dishes or list(by_chapter.get(chapter, []))


def exam_cues(by_concept, by_chapter, names):
    items = []
    concepts = json.loads((ROOT / "sources" / "concepts.json").read_text())
    for name in names:
        text = (VAULT / "Concepts" / f"{name}.md").read_text()
        m = re.search(r"> \[!question\]- (.+)\n((?:> .*\n?)+)", text)
        answer = " ".join(line[2:] for line in m.group(2).splitlines())
        items.append({"id": f"cue:{name}", "kind": "cue", "lecture": concepts[name]["lecture"], "q": clean(m.group(1)), "a": clean(answer),
                      "concepts": [name], "dishes": list(by_concept[name])})
    return items


def lecture_questions(by_concept, by_chapter, names):
    items = []
    for path in sorted((VAULT / "Lectures").glob("L*.md")):
        lecture = path.name[:3]
        body = path.read_text().split("## Potential Exam Questions", 1)[1].split("\n## ", 1)[0]
        section = ""
        for line in body.splitlines():
            if line.startswith("### "):
                section = line[4:].strip()
            m = re.match(r"(\d+)\. \*\*(.+?)\*\*\s*(.*)$", line)
            if m:
                q, a = clean(m.group(2)), clean(m.group(3))
                found, dishes = tie(links(line), q + " " + a, CHAPTER[lecture], by_concept, by_chapter, names)
                items.append({"id": f"{lecture}.{m.group(1)}", "kind": "lecture", "lecture": lecture, "section": section, "q": q, "a": a,
                              "concepts": found, "dishes": dishes})
    return items


def practice_midterm(by_concept, by_chapter, names):
    answers = {}
    for block in re.split(r"\n## ", (VAULT / "Practice" / "02 - Model Answers.md").read_text())[1:]:
        head, _, rest = block.partition("\n")
        m = re.match(r"(\d+)\. ", head)
        if m:
            answers[int(m.group(1))] = rest.strip()
    items = []
    lecture = None
    for line in (VAULT / "Practice" / "01 - Practice Midterm.md").read_text().splitlines():
        m = re.match(r"## Lecture (\d+):", line)
        if m:
            lecture = f"L{int(m.group(1)):02}"
        m = re.match(r"\*\*(\d+)\. (.+?)\.\*\* (.+)$", line)
        if m:
            n = int(m.group(1))
            raw = answers[n]
            found, dishes = tie(links(raw), clean(m.group(3)), CHAPTER[lecture], by_concept, by_chapter, names)
            items.append({"id": f"PM.{n}", "kind": "midterm", "n": n, "lecture": lecture, "title": clean(m.group(2)), "q": clean(m.group(3)),
                          "a": clean(raw), "concepts": found, "dishes": dishes, "points": 5})
    return items


def build():
    by_concept, by_chapter = recipe_maps()
    concepts = json.loads((ROOT / "sources" / "concepts.json").read_text())
    names = sorted(concepts, key=len, reverse=True)
    items = exam_cues(by_concept, by_chapter, sorted(concepts)) + lecture_questions(by_concept, by_chapter, names) + practice_midterm(by_concept, by_chapter, names)
    for extra in yaml.safe_load((ROOT / "sources" / "extra_questions.yaml").read_text()):
        items.append(dict(extra, kind="extra"))
    return items


def main():
    items = build()
    OUT.write_text(json.dumps(items, indent=0, ensure_ascii=False))
    counts = {}
    for i in items:
        counts[i["kind"]] = counts.get(i["kind"], 0) + 1
    print(counts)


if __name__ == "__main__":
    main()
