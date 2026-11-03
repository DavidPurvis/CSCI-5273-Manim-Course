"""The study player's design system: tokens mirror the course palette, components take colour from tokens, text is readable."""
import re
from pathlib import Path

from course.stage import theme

PLAYER = Path(__file__).resolve().parents[1] / "player"
HEX = re.compile(r"#[0-9A-Fa-f]{3,8}\b")

MIRRORED = {
    "blue": theme.LAYER["ip"],
    "orange": theme.STATE["now"],
    "green": theme.STATE["done"],
    "red": theme.STATE["error"],
    "grey": theme.STATE["idle"],
    "ink": theme.INK,
    "ink-muted": theme.MUTED,
    "page": theme.BG,
    "card": theme.PANEL,
}
TEXT_PAIRS = [("ink", "page"), ("ink-muted", "page"), ("ink", "card"), ("ink-muted", "card"), ("ink", "raised"),
              ("ink-muted", "raised"), ("page", "orange"), ("orange", "raised"), ("blue", "page"), ("blue", "card"),
              ("green", "card"), ("red", "card"), ("red", "page"), ("page", "green")]
CONTROL_PAIRS = [("grey", "page"), ("grey", "raised"), ("blue", "page"), ("blue", "card")]


def tokens():
    text = (PLAYER / "tokens.css").read_text()
    block = re.search(r":root\s*\{(.*?)\n\}", text, re.S).group(1)
    return {name: value.strip() for name, value in re.findall(r"--([\w-]+)\s*:\s*([^;]+);", block)}


def luminance(hex_colour):
    digits = hex_colour.lstrip("#")
    channels = [int(digits[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    linear = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast(a, b):
    hi, lo = sorted((luminance(a), luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def test_palette_mirrors_course_theme():
    palette = tokens()
    for name, value in MIRRORED.items():
        assert palette[name].upper() == value.upper(), f"--{name} has drifted from course/stage/theme.py"


def test_components_take_colour_from_tokens():
    assert not HEX.search((PLAYER / "style.css").read_text()), "raw hex colour in style.css"
    assert not HEX.search((PLAYER / "player.js").read_text()), "raw hex colour in player.js"
    assert not re.search(r"rgba?\(", (PLAYER / "style.css").read_text()), "raw rgb colour in style.css"


def test_text_meets_aa_contrast():
    palette = tokens()
    for fg, bg in TEXT_PAIRS:
        assert contrast(palette[fg], palette[bg]) >= 4.5, f"--{fg} on --{bg} is below 4.5:1"


def test_controls_meet_non_text_contrast():
    palette = tokens()
    for fg, bg in CONTROL_PAIRS:
        assert contrast(palette[fg], palette[bg]) >= 3.0, f"--{fg} on --{bg} is below 3:1"


def test_no_native_dialogs():
    assert not re.search(r"\b(alert|confirm)\(", (PLAYER / "player.js").read_text())


def test_tokens_load_before_components():
    html = (PLAYER / "index.html").read_text()
    assert html.index("tokens.css") < html.index("style.css")
