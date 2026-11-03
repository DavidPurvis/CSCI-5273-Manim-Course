"""One palette and one set of zones for the whole course."""
FONT = "Helvetica Neue"
BG = "#11141B"
PANEL = "#1B2029"
LINE = "#5B667A"
INK = "#F2F4F8"
MUTED = "#A9B3C4"

# Fills name a layer. They stay the same in every chapter.
LAYER = {"ip": "#4A9EFF", "eth": "#F5C542", "transport": "#B18CFF", "tunnel": "#FF6FB5",
         "label": "#39D0C3", "data": "#C9D1DE", "radio": "#7EE081", "vlan": "#FFA8D9"}
# Outlines and glows name a state.
STATE = {"now": "#FF8A3D", "done": "#4CD07D", "error": "#FF5A5A", "idle": "#6B7588",
         "candidate": "#FFFFFF", "changed": "#FFFFFF"}

MIN_FONT = 24
FRAME_X, FRAME_Y = 7.11, 4.0

# Three bands, with a gap between each so a title, a diagram, and a takeaway cannot touch.
# Title also keeps its right side free for the source tag.
ZONES = {
    "title": (-6.9, 3.12, 6.9, 3.86),
    "context": (-6.8, 2.76, 6.8, 3.10),
    "full": (-6.8, -2.28, 6.8, 2.72), "left": (-6.8, -2.28, -0.15, 2.72), "right": (0.15, -2.28, 6.8, 2.72),
    "top": (-6.8, 0.20, 6.8, 2.72), "bottom": (-6.8, -2.28, 6.8, 0.0),
    "left_top": (-6.8, 0.20, -0.15, 2.72), "left_bottom": (-6.8, -2.28, -0.15, 0.0),
    "right_top": (0.15, 0.20, 6.8, 2.72), "right_bottom": (0.15, -2.28, 6.8, 0.0),
    "upper": (-6.8, -1.30, 6.8, 2.72), "lower": (-6.8, -2.28, 6.8, -1.40),
    "mobility_bottom": (-6.8, -2.28, 6.8, 0.70),
    "story_upper": (-6.8, -0.30, 6.8, 2.72), "story_lower": (-6.8, -2.28, 6.8, -0.50),
    "rule": (-6.8, -3.52, 6.8, -2.48),
}
# These lessons' tables need the full height, so they keep it and go without the context strip.
FULL_HEIGHT_LESSONS = frozenset({"6.4", "7.1", "14.2", "17.1", "17.20"})


def use_full_height():
    for zone, (x0, y0, x1, y1) in ZONES.items():
        if y1 == 2.72:
            ZONES[zone] = (x0, y0, x1, 2.96)


# Countdown sits under the rule band, clear of the prompt.
PAUSE_Y = -3.78
TITLE_TAG_SLOT = 3.45


def zones_overlap(a, b):
    ax0, ay0, ax1, ay1 = ZONES[a]
    bx0, by0, bx1, by1 = ZONES[b]
    return ax0 < bx1 and bx0 < ax1 and ay0 < by1 and by0 < ay1
