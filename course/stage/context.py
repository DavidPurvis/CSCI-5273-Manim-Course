"""What the context strip says: the lesson's question and the current step. Pure data, no drawing."""

STEP_LABELS = {"question": "The question", "animation": "See it", "state": "Track the state", "changed_example": "What changed",
               "rule": "The rule", "prediction": "Your turn", "explanation": "Why"}


def lesson_question(card):
    """The first question the lesson asks, or None for lessons that don't open with one."""
    for beat in card["beats"]:
        for move in beat.get("moves") or []:
            if "q" in move:
                return str(move["q"]["text"])
    return None


def last_sentence(text):
    """The shortest form of a question that still asks it, for when the whole thing won't fit."""
    parts = [p.strip() for p in text.replace("? ", "?|").replace(". ", ".|").split("|") if p.strip()]
    return parts[-1] if parts else text


def step_name(stage):
    """A label, not a count: lessons return to earlier stages, so numbering would run backwards."""
    return STEP_LABELS[stage]
