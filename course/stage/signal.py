"""Light up what the narration names, at the moment it names it. No card asks for this; it reads the stage and the word timing."""
import re

from manim import AnimationGroup, FadeIn, UpdateFromAlphaFunc, VGroup, there_and_back_with_pause

from .parts import Fields, Grid, Ladder, Net, Slots, Stack, Tracks, scale_opacity, opacity_state, outline

FLASH = 1.2     # seconds a highlight lasts
MIN_GAP = 1.6   # seconds between highlights, so the screen doesn't flicker
AGAIN = 7.0     # seconds before the same item can light up again
SKIP = {"yes", "no", "the", "a", "an", "of", "to", "in", "on", "and", "or", "is", "it", "at", "by", "for", "?", "-", "none", "all", "one", "two", "from", "with", "as",
        "not", "but", "its", "this", "that", "be", "are", "was", "if", "so", "then", "when", "only", "each", "every", "same", "new", "old", "first", "next", "can", "may"}
# Too common in this course to identify one item by themselves.
COMMON = {"packet", "router", "route", "network", "address", "table", "frame", "layer", "state", "because", "there", "their", "which", "other", "still", "before", "after",
          "about", "would", "could", "should", "where", "through", "between", "these", "those", "using", "without"}


def tokens(text):
    out = []
    for raw in str(text).split():
        t = raw.strip(".,;:!?()\"“”'’→=+").replace(",", "")
        t = re.sub(r"['’]s$", "", t)
        if t:
            out.append(t)
    return out


def fold(tok):
    # Single capital letters name nodes, so their case matters. Plurals count as the same word.
    if len(tok) == 1:
        return tok
    low = tok.lower()
    return low[:-1] if len(low) > 3 and low.endswith("s") and not low.endswith("ss") else low


def spoken_words(text, times):
    words = []
    sentence_start = True
    for raw, (start, _) in zip(text.split(), times):
        toks = tokens(raw)
        words.append((fold(toks[0]) if toks else "", start, sentence_start))
        sentence_start = raw.endswith((".", "!", "?", ":"))
    return words


def items_on_stage(stage):
    """Everything with a name the narration might say: (text, mobject to ring)."""
    out = []
    for mob in stage.objs.values():
        if isinstance(mob, Grid):
            for r, cells in enumerate(mob.cells):
                if r < mob.knext:
                    out += [(getattr(c, "ktext", ""), c) for c in cells]
        elif isinstance(mob, Net):
            out += [(d.label.ktext, VGroup(d.body, d.label)) for d in mob.devices.values() if d.label is not None]
            out += [(d.body[1].ktext, d.body) for d in mob.devices.values() if d.kind in ("node", "box", "cloud")]
        elif isinstance(mob, Stack):
            out += [(data["t"].split(":")[0], block) for data, block in zip(mob.layers_data, mob.blocks)]
        elif isinstance(mob, Slots):
            out += [(item[1].ktext, item) for item in mob.items]
        elif isinstance(mob, Fields):
            out += [(cell[1].ktext, cell) for cell in mob.cell.values()]
        hidden = getattr(mob, "khidden", ())
        out += [(t, m) for t, m in getattr(mob, "kitems", ()) if not any(m is h for h in hidden)]
    return out


def find(words, start, end, stage, used):
    """Highlights due between two moments in the beat, as (time, mobject). used maps an item to when it last lit up."""
    found = []
    for text, mob in items_on_stage(stage):
        toks = tokens(text)
        key = [fold(t) for t in toks]
        if not key or (len(key) == 1 and (key[0] in SKIP or not key[0].isalnum())):
            continue
        hit = None
        for i in range(len(words) - len(key) + 1):
            tok, at, first = words[i]
            if start <= at <= end - FLASH and [w[0] for w in words[i:i + len(key)]] == key and not (key == ["A"] and first):
                if at - used.get(id(mob), -99) >= AGAIN:
                    hit = at
                    break
        if hit is None and len(key) > 1:
            # A longer label also answers to its most distinctive word.
            strong = [k for k in key if len(k) >= 5 and k not in SKIP and k not in COMMON]
            for tok, at, first in words:
                if start <= at <= end - FLASH and tok in strong and at - used.get(id(mob), -99) >= AGAIN:
                    hit = at
                    break
        if hit is not None:
            found.append((hit, mob))
    found.sort(key=lambda x: x[0])
    chosen, last = [], start - MIN_GAP
    for at, mob in found:
        if at - last >= MIN_GAP:
            chosen.append((at, mob))
            used[id(mob)] = at
            last = at
    return chosen


SPOTLIGHT_DIM = 0.32


def flash(mob, stage=None):
    """Ring what the narration names. Given the stage, its neighbours also step back, so one thing is bright at a time."""
    ring = outline(mob, "now", buff=0.07)
    ring.set_z_index(7)
    glow = FadeIn(ring, rate_func=there_and_back_with_pause, remover=True)
    owner = spotlight_owner(mob, stage) if stage is not None else None
    if owner is None:
        return glow
    state = opacity_state(owner, skip=mob.get_family())

    def update(_, alpha):
        # Ease down, hold, ease back up, ending at exactly the opacities it started with.
        edge = min(alpha, 1 - alpha) / 0.15
        scale_opacity(state, 1 - (1 - SPOTLIGHT_DIM) * min(1.0, max(0.0, edge)))
    return AnimationGroup(glow, UpdateFromAlphaFunc(owner, update))


def spotlight_owner(mob, stage):
    """The diagram or table on stage holding this item, if it has anything else in it."""
    parts = {id(part) for part in mob.get_family()}
    for name, other in stage.objs.items():
        if str(name).startswith("_"):
            continue
        family = other.get_family()
        if parts & {id(part) for part in family} and len(family) > len(parts):
            return other
    return None
