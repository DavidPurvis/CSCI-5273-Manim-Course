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

ZONES = {
    "full": (-6.8, -2.05, 6.8, 3.2), "left": (-6.8, -2.05, -0.15, 3.2), "right": (0.15, -2.05, 6.8, 3.2),
    "top": (-6.8, 0.35, 6.8, 3.2), "bottom": (-6.8, -2.05, 6.8, 0.1),
    "left_top": (-6.8, 0.35, -0.15, 3.2), "left_bottom": (-6.8, -2.05, -0.15, 0.1),
    "right_top": (0.15, 0.35, 6.8, 3.2), "right_bottom": (0.15, -2.05, 6.8, 0.1),
    "upper": (-6.8, -1.1, 6.8, 3.2), "lower": (-6.8, -2.05, 6.8, -1.3),
    "mobility_bottom": (-6.8, -2.05, 6.8, 0.75),
    "story_upper": (-6.8, -0.2, 6.8, 3.2), "story_lower": (-6.8, -2.05, 6.8, -0.45),
    "rule": (-6.8, -2.95, 6.8, -2.15),
}


def zones_overlap(a, b):
    ax0, ay0, ax1, ay1 = ZONES[a]
    bx0, by0, bx1, by1 = ZONES[b]
    return ax0 < bx1 and bx0 < ax1 and ay0 < by1 and by0 < ay1
