"""Title, diagram, and rule bands stay apart, and a wide table wraps instead of shrinking."""
from course.stage.theme import TITLE_TAG_SLOT, ZONES, zones_overlap


def test_title_diagram_and_rule_bands_stay_apart():
    assert not zones_overlap("title", "full")
    assert not zones_overlap("title", "top")
    assert not zones_overlap("rule", "full")
    assert not zones_overlap("rule", "bottom")
    assert not zones_overlap("title", "rule")
    assert ZONES["title"][1] > ZONES["full"][3]
    assert ZONES["rule"][3] < ZONES["full"][1]


def test_title_clears_the_source_tag_and_the_diagram():
    from manim import LEFT, RIGHT
    from course.stage.moves import drawn_title
    from course.stage.parts import T, paragraph
    assert drawn_title("Lecture 6: sharing a wire") == "sharing a wire"
    assert drawn_title("Exam warm-up: the packet story") == "Exam warm-up: the packet story"
    x0, y0, x1, y1 = ZONES["title"]
    title = paragraph(drawn_title("Lecture 6: sharing a wire"), (x1 - TITLE_TAG_SLOT) - x0 - 0.35, 36)
    title.align_to([x0 + 0.2, 0, 0], LEFT)
    title.set_y((y0 + y1) / 2)
    tag = T("Lecture 18 · p. 120", 24)
    tag.set_y((y0 + y1) / 2)
    tag.align_to([x1 - 0.2, 0, 0], RIGHT)
    assert title.get_right()[0] < tag.get_left()[0] - 0.08
    assert title.get_bottom()[1] > ZONES["full"][3]
    assert tag.get_bottom()[1] > ZONES["full"][3]
    assert title.get_top()[1] < y1 + 0.02


def test_spine_sits_on_the_top_of_its_zone_and_the_prompt_clears_the_duration():
    from course.stage.moves import Stage, pause, spine
    from course.stage.parts import T
    stage = Stage(None)
    spine(stage, "LAN", "top")
    strip = stage.objs["_spine"]
    assert strip.get_top()[1] > ZONES["top"][3] - 0.12
    assert strip.get_bottom()[1] >= ZONES["top"][1] - 0.02
    assert getattr(strip, "layout_overflow", None) is None
    pause(stage, "who talks, and when?")
    prompt = stage.objs["_rule"][0]
    _, _, x1, _ = ZONES["rule"]
    label_left = x1 - 0.25 - T("Pause: 40.2 s", 24).width
    assert prompt.get_right()[0] < label_left - 0.08
    assert abs(stage.pause_bar.get_y() - (-3.78)) < 0.02


def test_ipv4_header_fits_the_top_band():
    from course.stage.moves import Stage, fields_show
    from course.stage.parts import zone_box
    rows = [
        [["Version", 4], ["IHL", 4], ["Type of service", 8], ["Total length", 16]],
        [["Identification", 16], ["Flags", 3], ["Fragment offset", 13]],
        [["TTL", 8], ["Protocol", 8], ["Header checksum", 16]],
        [["Source address", 32]],
        [["Destination address", 32]],
    ]
    stage = Stage(None)
    fields_show(stage, "h", "top", rows, unit=0.38)
    header = stage.objs["h"]
    _, _, height = zone_box("top")
    assert header.height <= height + 0.03
    assert getattr(header, "layout_overflow", None) is None


def test_band_check_skips_an_object_with_no_area_and_still_catches_a_real_hit():
    import numpy as np
    from manim import VGroup
    from course.stage.parts import T
    from course.stage.player import Dish
    dish = Dish.__new__(Dish)
    dish.stage_ = type("Stage", (), {})()
    ghost = VGroup()
    ghost.points = np.array([])
    title = T("Lecture 6", 36).move_to([0, 3.5, 0])
    dish.stage_.objs = {"_heading": title, "ghost": ghost}
    assert dish.band_problems("8.3.parts") == []
    intruder = T("Fabric", 28).move_to(title)
    dish.stage_.objs["ghost"] = intruder
    assert dish.band_problems("8.3.parts") == ["8.3.parts: title band intersects the diagram"]


def test_blank_table_cell_still_forms_a_row():
    from course.stage.parts import Grid
    grid = Grid(["Planned", "Unplanned"], [["", "failed software"]], 30)
    assert len(grid.rows) == 1
    assert grid.width > 1
    assert grid.get_bottom()[1] < grid.get_top()[1]


def test_walk_keeps_the_path_bright():
    from course.stage.moves import DIM, net_emphasis
    from course.stage.parts import Net
    net = Net("full", {
        "a": {"k": "host", "at": [0, 0]},
        "b": {"k": "host", "at": [1, 0]},
        "c": {"k": "host", "at": [2, 0]},
    }, [["a", "b"], ["b", "c"]])
    opacity = net_emphasis(net, ["a", "b"])
    assert opacity[("node", "a")] == 1
    assert opacity[("node", "b")] == 1
    assert opacity[("node", "c")] == DIM
    assert opacity[("link", ("a", "b"))] == 1
    assert opacity[("link", ("b", "c"))] == DIM


def test_valley_table_wraps_and_scrolls_inside_the_right_zone():
    from course.model.bgp import trace
    from course.stage.parts import Grid, scroll_grid, seat_grid, zone_box
    data = trace()["valley_table"]
    center, width, height = zone_box("right")
    grid = Grid(data["cols"], data["rows"], 26, max_width=width - 0.24)
    assert grid.width <= width + 0.03
    for row in grid.rows:
        grid.remove(row)
    grid.knext = 0
    seat_grid(grid, "right", pin_top=True)
    assert getattr(grid, "layout_overflow", None) is None
    for _ in data["rows"]:
        grid.add(grid.rows[grid.knext])
        grid.knext += 1
        scroll_grid(grid, "right")
    assert grid.get_bottom()[1] >= center[1] - height / 2 - 0.02
    assert grid.get_top()[1] <= center[1] + height / 2 + 0.08
    assert getattr(grid, "layout_overflow", None) is None
