"""Build the study player: static pages plus one data file, from the cards, narration timing, and question bank."""
import json
import math
import os
import re
import shutil
import subprocess
from datetime import date
from pathlib import Path
from urllib.parse import quote

import yaml

from course.stage.card import ROOT, beat_times, load_card, load_manifest, narration_text
from course.tools import bank, drills
from course.tools.sources import DECKS, VAULT

PACK = Path(os.environ.get("KITCHEN_PACK", ROOT.parent))
from course.catalog import CHAPTERS, COURSE_VERSION
EXPRESS = ["6.1", "7.4", "8.1", "8.2", "10.1", "10.2", "11.1", "11.2", "12.2", "12.4", "13.4", "14.4", "15.4"]
READY_LINKS = [(["6.3"], ["switch"]), (["6.3", "13.3"], []), (["7.2", "8.1"], ["addr", "size"]), (["8.2"], ["lpm"]), (["7.3", "7.4"], ["frag"]), (["9.1", "9.2"], []),
               (["10.1", "10.2"], ["dijkstra", "bf"]), (["11.1", "11.2", "11.3"], []), (["12.2", "12.4"], ["bgp"]), (["13.1", "13.2", "13.3", "13.4"], ["rpf"]), (["14.2", "14.4"], ["cdma"]),
               (["15.1", "15.3", "15.4"], [])]
# A practice question's drill with new numbers, where one exists.
PM_DRILL = {1: "switch", 3: "addr", 4: "frag", 5: "lpm", 9: "dijkstra", 10: "bf", 13: "bgp", 14: "bgp", 16: "rpf", 18: "cdma"}


def prediction_pause_time(beat, slot, pad, fps=30):
    """Absolute second when the video's prediction hold starts, on the same frame grid as compile_beat."""
    pre = round(beat.get("pre_roll", 0) * fps)
    speech_frames = math.ceil(slot["speech"] * fps)
    pad_frames = round(pad * fps)
    reading = round(beat.get("reading_hold", 0) * fps)
    return slot["start"] + (pre + speech_frames + pad_frames + reading) / fps


def assessment_date(root=ROOT):
    """Read optional study metadata; absent/null/blank means an undated player."""
    path = Path(root) / "sources/study-config.json"
    if not path.exists():
        return None
    config = json.loads(path.read_text(encoding="utf-8"))
    value = config.get("assessment_date")
    if value is None or value == "":
        return None
    if not isinstance(value, str):
        raise ValueError("assessment_date must be YYYY-MM-DD or null")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("assessment_date must be YYYY-MM-DD or null") from exc
    if parsed.isoformat() != value:
        raise ValueError("assessment_date must be YYYY-MM-DD or null")
    return value


def dish_order(d):
    return [int(x) for x in d.split(".")]


def note_url(relative):
    return "/notes/" + quote(relative)


def route(all_dishes):
    """The vault's Sunday-to-Wednesday route as a list of boxes, one thing at a time."""
    def ch(*chapters):
        return [{"kind": "dish", "id": d} for c in chapters for d in all_dishes if d.split(".")[0] == str(c)]

    def task(key, text, note=None, stop=False):
        return {"kind": "stop" if stop else "task", "id": key, "text": text, "note": note_url(note) if note else None}

    days = [
        ("Sunday", "One packet-delivery story", ch(6, 7, 8, 9) + [
            task("ex01", "From a blank page, trace joining a LAN and sending a packet. Draw the host, switch, gateway, DNS resolver, and server.", "Examples/01 - From Joining a LAN to Sending a Packet.md"),
            task("ex02", "From a blank page, calculate the subnetting, longest match, and fragmentation examples.", "Examples/02 - Subnetting LPM and Fragmentation.md"),
            task("sun", "Stop check: can you rebuild source learning, a mask calculation, a longest-match choice, and next-hop framing without looking?", "03 - Study Route to Wednesday.md", True)]),
        ("Monday", "Build and break routing state", ch(10, 11, 12) + [
            task("ex03", "Work Dijkstra, distance vector, and failure. Write distances, predecessors, and first hops separately.", "Examples/03 - Dijkstra DV and Failure.md"),
            task("ex04", "Solve BGP selection and export. Use the attribute order and export rule explicitly.", "Examples/04 - BGP Selection Export and Paths.md"),
            task("mon", "Stop check: can you compute one Dijkstra trace and one Bellman-Ford update, name the four convergence stages, and justify a BGP choice plus a permitted export?", "03 - Study Route to Wednesday.md", True)]),
        ("Tuesday", "Replication, radio, movement, then mixed practice", ch(13) + [
            task("ex05", "Solve multicast membership and trees. Draw the IGMP and PIM boundary, and compare (*,G) with (S,G).", "Examples/05 - Multicast Membership and Trees.md")] + ch(14) + [
            task("ex06", "Solve contention and CDMA. Draw hidden and exposed terminals before naming the protocol response.", "Examples/06 - Wireless Contention and CDMA.md")] + ch(15) + [
            task("ex07", "Solve tunnels and handover. Label inner and outer destinations and control and data roles.", "Examples/07 - Mobile Tunnels and Handover.md")] + ch(16) + [
            {"kind": "midterm", "id": "midterm", "text": "Take the practice midterm with the 75-minute timer, then mark it."},
            {"kind": "ready", "id": "ready", "text": "Check the readiness board and repair the few remaining gaps."}]),
        ("Wednesday", "Short reconstruction, no full reread", ch(18) + [
            task("wed", "Draw the connected packet story from memory, recompute one mask, longest match, and fragment, and recite the BGP order, export rule, dense and sparse default, and handover stages.", "03 - Study Route to Wednesday.md")]),
    ]
    return [{"day": d, "theme": t, "boxes": b} for d, t, b in days if b]


def slide_name(deck, page):
    return f"{deck[:-4]}-p{page:03}.jpg"


def render_slides(needed, folder):
    folder.mkdir(parents=True, exist_ok=True)
    made = 0
    for deck, page in sorted(needed):
        out = folder / slide_name(deck, page)
        if out.exists():
            continue
        stem = out.with_suffix("")
        subprocess.run(["pdftoppm", "-jpeg", "-jpegopt", "quality=78", "-r", "96", "-f", str(page), "-l", str(page), "-singlefile", str(DECKS / deck), str(stem)], check=True)
        made += 1
    return made


def readiness():
    lines = (VAULT / "04 - Readiness Check.md").read_text().splitlines()
    rows = [re.match(r"- \[ \] \*\*(.+?):\*\* (.+)", line) for line in lines]
    rows = [m for m in rows if m]
    out = []
    for m, (dishes_, drill_types) in zip(rows, READY_LINKS):
        out.append({"title": m.group(1), "text": bank.clean(m.group(2)), "dishes": dishes_, "drills": drill_types})
    return out


def build_data():
    from course.tools.kitchen import is_fresh
    manifest, texts = load_manifest(), narration_text()
    all_dishes = sorted((p.stem for p in (ROOT / "recipes").glob("*.yaml")), key=dish_order)
    concepts_meta = json.loads((ROOT / "sources" / "concepts.json").read_text())
    dishes, needed, first_beat = {}, set(), {}
    for d in all_dishes:
        card = load_card(d)
        times, total = beat_times(card, manifest)
        beats, pauses = [], []
        for b, slot in zip(card["beats"], times):
            deck, *pages = b["pdf"]
            needed.add((deck, pages[0]))
            beats.append({"id": b["id"], "t": slot["start"], "stage": b["stage"], "deck": deck, "pages": pages, "slide": slide_name(deck, pages[0]),
                          "text": texts[b["id"]], "concepts": b.get("concepts") or []})
            if b["stage"] == "prediction":
                pauses.append({"t": round(prediction_pause_time(b, slot, card.get("pad", 2.2)), 2), "resume": round(slot["start"] + slot["total"], 2), "prompt": texts[b["id"]]})
            for c in b.get("concepts") or []:
                first_beat.setdefault(c, (d, b["id"], slot["start"]))
        chapter = d.split(".")[0]
        dishes[d] = {"id": d, "title": card["title"], "chapter": chapter, "chapterTitle": CHAPTERS[chapter], "minutes": round(total / 60, 1), "seconds": round(total, 1),
                     "video": f"/video/dishes/{d}.mp4", "vtt": f"/captions/dishes/{d}.vtt", "cooked": (PACK / "video" / "dishes" / f"{d}.mp4").exists() and is_fresh(d),
                     "concepts": card.get("concepts") or [], "beats": beats, "pauses": pauses}
    concepts = {}
    for name, meta in concepts_meta.items():
        where = first_beat.get(name)
        concepts[name] = {"lecture": meta["lecture"], "definition": bank.clean(meta["definition"]), "note": note_url(f"Concepts/{name}.md"),
                          "dish": where[0] if where else None, "t": where[2] if where else 0}
    items = json.loads((ROOT / "sources" / "bank.json").read_text()) if (ROOT / "sources" / "bank.json").exists() else bank.build()
    problems = json.loads((ROOT / "sources" / "drills.json").read_text()) if (ROOT / "sources" / "drills.json").exists() else drills.build()
    walkthroughs = {int(d.split(".")[1]): d for d in all_dishes if d.startswith("17.")}
    for item in items:
        if item["kind"] == "midterm":
            item["walkthrough"] = walkthroughs.get(item["n"])
            item["drill"] = PM_DRILL.get(item["n"])
    types = []
    for key, title, dish, _ in drills.TYPES:
        types.append({"key": key, "title": title, "dish": dish})
    return {"dishes": dishes, "order": all_dishes, "route": route(all_dishes), "express": [d for d in EXPRESS if d in dishes], "concepts": concepts, "bank": items,
            "drills": problems, "drillTypes": types, "ready": readiness(), "examDate": assessment_date()}, needed


def main():
    out = PACK / "player"
    out.mkdir(parents=True, exist_ok=True)
    for f in (ROOT / "course" / "player").iterdir():
        if f.is_file():
            shutil.copy(f, out / f.name)
    data, needed = build_data()
    made = render_slides(needed, out / "slides")
    data["courseVersion"] = COURSE_VERSION
    (out / "data.json").write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")))
    print(f"Player built: {len(data['dishes'])} dishes, {len(data['bank'])} questions, {len(data['drills'])} drills, {len(needed)} slides ({made} new)")


if __name__ == "__main__":
    main()
