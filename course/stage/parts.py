"""Reusable visual components. None of them knows about any particular lecture."""
from manim import (DOWN, LEFT, ORIGIN, RIGHT, UP, Arc, Circle, DashedLine, Dot, Ellipse, Line, Polygon,
                   Rectangle, RoundedRectangle, Text, VGroup, VMobject, Arrow, DashedVMobject, MathTex, config)
import numpy as np

from .theme import BG, FONT, INK, LAYER, LINE, MIN_FONT, MUTED, PANEL, STATE, ZONES


def T(text, size=28, color=INK, weight="NORMAL"):
    m = Text(str(text), font=FONT, font_size=size, color=color, weight=weight, disable_ligatures=True)
    m.kfont, m.kheight, m.ktext = size, max(m.height, 1e-3), str(text)
    return m


def wrap_lines(text, width, size):
    lines, cur = [], ""
    for word in str(text).split():
        candidate = (cur + " " + word).strip()
        if cur and T(candidate, size).width > width:
            lines.append(cur)
            cur = word
        else:
            cur = candidate
    return lines + ([cur] if cur else [])


def paragraph(text, width, size=30, color=INK, center=False):
    group = VGroup(*[T(line, size, color) for line in wrap_lines(text, width, size)])
    group.arrange(DOWN, buff=0.14, aligned_edge=ORIGIN if center else LEFT)
    return group


def zone_box(zone):
    x0, y0, x1, y1 = ZONES[zone]
    return np.array([(x0 + x1) / 2, (y0 + y1) / 2, 0]), x1 - x0, y1 - y0


def place(mob, zone, grow=False):
    center, w, h = zone_box(zone)
    factor = min(w / max(mob.width, 1e-3), h / max(mob.height, 1e-3))
    if factor < 1 or grow:
        fonts = [m.kfont * m.height / max(m.kheight, 1e-6)
                 for m in mob.get_family() if hasattr(m, "kfont")]
        floor = MIN_FONT / min(fonts) if fonts else 0
        mob.scale(max(floor, min(factor, 1.25) if grow else factor))
        if mob.width > w + .03 or mob.height > h + .03:
            mob.layout_overflow = f"{zone}: content needs reflow or staged disclosure"
    mob.move_to(center)
    return mob


def outline(mob, state, buff=0.09):
    color = STATE[state]
    box = RoundedRectangle(corner_radius=0.08, width=mob.width + 2 * buff, height=mob.height + 2 * buff,
                           stroke_color=color, stroke_width=4, fill_opacity=0).move_to(mob)
    if state in ("candidate", "changed"):
        return DashedVMobject(box, num_dashes=28)
    return box


# Devices ------------------------------------------------------------------
def icon(kind, text=""):
    stroke = {"stroke_color": INK, "stroke_width": 3}
    fill = {"fill_color": PANEL, "fill_opacity": 1}
    if kind in ("laptop", "host"):
        screen = RoundedRectangle(corner_radius=0.05, width=0.62, height=0.42, **stroke, **fill)
        base = Polygon([-0.4, -0.3, 0], [0.4, -0.3, 0], [0.3, -0.22, 0], [-0.3, -0.22, 0], **stroke, **fill)
        return VGroup(screen, base)
    if kind == "router":
        c = Circle(radius=0.34, **stroke, **fill)
        arms = VGroup(*[Line(ORIGIN, d * 0.2, stroke_color=LAYER["ip"], stroke_width=3).shift(d * 0.05) for d in (UP, DOWN, LEFT, RIGHT)])
        return VGroup(c, arms)
    if kind == "switch":
        box = RoundedRectangle(corner_radius=0.06, width=0.86, height=0.36, **stroke, **fill)
        a = Line(LEFT * 0.26, RIGHT * 0.26, stroke_color=LAYER["eth"], stroke_width=3).shift(UP * 0.06)
        b = Line(LEFT * 0.26, RIGHT * 0.26, stroke_color=LAYER["eth"], stroke_width=3).shift(DOWN * 0.06)
        return VGroup(box, a, b)
    if kind == "hub":
        box = Rectangle(width=0.86, height=0.32, **stroke, **fill)
        dots = VGroup(*[Dot(radius=0.03, color=MUTED).shift(RIGHT * x) for x in (-0.24, -0.08, 0.08, 0.24)])
        return VGroup(box, dots)
    if kind == "server":
        return VGroup(*[RoundedRectangle(corner_radius=0.03, width=0.56, height=0.2, **stroke, **fill).shift(UP * y) for y in (0.22, 0, -0.22)])
    if kind == "ap":
        d = Dot(radius=0.07, color=LAYER["radio"])
        arcs = VGroup(*[Arc(radius=r, start_angle=np.pi / 4, angle=np.pi / 2, stroke_color=LAYER["radio"], stroke_width=3) for r in (0.18, 0.32)])
        pole = Line(ORIGIN, DOWN * 0.3, **stroke)
        return VGroup(pole, d, arcs)
    if kind == "phone":
        body = RoundedRectangle(corner_radius=0.06, width=0.34, height=0.6, **stroke, **fill)
        return VGroup(body, Dot(radius=0.025, color=INK).shift(DOWN * 0.22))
    if kind == "tower":
        mast = Polygon([-0.2, -0.36, 0], [0.2, -0.36, 0], [0, 0.18, 0], **stroke, **fill)
        arcs = VGroup(*[Arc(radius=r, start_angle=np.pi / 4, angle=np.pi / 2, stroke_color=LAYER["radio"], stroke_width=3).shift(UP * 0.16) for r in (0.16, 0.28)])
        return VGroup(mast, arcs)
    if kind == "node":
        return VGroup(Circle(radius=0.38, **stroke, **fill), T(text, 32))
    if kind == "cloud":
        label = T(text, 28)
        return VGroup(Ellipse(width=max(1.5, label.width + 0.5), height=0.78, **stroke, **fill), label)
    if kind == "box":
        label = T(text, 28)
        return VGroup(RoundedRectangle(corner_radius=0.08, width=max(label.width + 0.3, 0.9), height=0.68, **stroke, **fill), label)
    if kind == "point":
        return VGroup(Dot(radius=0.07, color=MUTED))
    raise ValueError(f"unknown device kind {kind}")


def segment_hits_box(p0, p1, center, w, h, pad=0.02):
    """Does a straight segment touch a box? Liang-Barsky clipping."""
    x0, x1, y0, y1 = center[0] - w / 2 - pad, center[0] + w / 2 + pad, center[1] - h / 2 - pad, center[1] + h / 2 + pad
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    t0, t1 = 0.0, 1.0
    for p, q in ((-dx, p0[0] - x0), (dx, x1 - p0[0]), (-dy, p0[1] - y0), (dy, y1 - p0[1])):
        if p == 0:
            if q < 0:
                return False
        elif p < 0:
            t0 = max(t0, q / p)
        else:
            t1 = min(t1, q / p)
        if t0 > t1:
            return False
    return True


INSIDE = {"node", "cloud", "box"}
GLYPH = 1.5  # Icons are drawn at unit size, then scaled; big enough to read at a glance.
DIRECTIONS = {"down": DOWN, "up": UP, "left": LEFT, "right": RIGHT}


class Device(VGroup):
    def __init__(self, kind, label="", label_side="down"):
        super().__init__()
        self.kind = kind
        self.body = icon(kind, label if kind in INSIDE else "")
        if kind not in INSIDE and kind != "point":
            self.body.scale(GLYPH)
        self.add(self.body)
        self.label = None
        self.side = label_side
        if label and kind not in INSIDE:
            self.label = T(label, 28, MUTED).next_to(self.body, DIRECTIONS[label_side], buff=0.17)
            self.add(self.label)

    def anchor(self):
        return self.body.get_center()

    def radius(self):
        return max(self.body.width, self.body.height) / 2


class Net(VGroup):
    """A diagram of devices and links. Coordinates are stretched to fill a zone; glyphs keep their size."""

    def __init__(self, zone, nodes, links=(), spread=None):
        super().__init__()
        self.zone = zone
        self.layout = {k: v.get("at", [0, 0]) for k, v in nodes.items()}
        xs = [p[0] for p in self.layout.values()]
        ys = [p[1] for p in self.layout.values()]
        center, w, h = zone_box(zone)
        self.cx, self.cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
        self.sx = (w - 3.0) / max(max(xs) - min(xs), 1e-3)
        self.sy = (h - 1.35) / max(max(ys) - min(ys), 1e-3)
        self.sx, self.sy = min(self.sx, 2.4), min(self.sy, 2.0)
        if spread:
            self.sx, self.sy = spread
        self.center_pt = center
        self.devices, self.links, self.link_meta, self.badges, self.marks = {}, {}, {}, {}, {}
        self.link_layer, self.device_layer = VGroup(), VGroup()
        self.add(self.link_layer, self.device_layer)
        for name, spec in nodes.items():
            self.add_device(name, spec)
        for spec in links:
            self.add_link(*spec)
        self.clear_labels()

    def on_link(self, mob):
        center, w, h = mob.get_center(), mob.width, mob.height
        return any(segment_hits_box(*self.endpoints(a, b), center, w, h) for a, b in self.links)

    def crowded(self, mob):
        others = [d.label for d in self.devices.values() if d.label is not None] + list(self.badges.values())
        return any(o is not mob and abs(o.get_x() - mob.get_x()) < (o.width + mob.width) / 2 + 0.03
                   and abs(o.get_y() - mob.get_y()) < (o.height + mob.height) / 2 + 0.03 for o in others)

    def seat(self, mob, dev, side, buff):
        """Put a label on its preferred side, or on the first side clear of links and other labels, always inside the frame."""
        def put(way):
            mob.next_to(dev.body, way, buff=buff)
            over = abs(mob.get_x()) + mob.width / 2 - 6.95
            if over > 0:
                mob.shift(LEFT * over * np.sign(mob.get_x()))
        for distance in (buff, buff+0.2, buff+0.45, buff+0.75):
            for way in (side, -side, RIGHT, LEFT, UP, DOWN, UP+RIGHT, UP+LEFT, DOWN+RIGHT, DOWN+LEFT):
                put(way)
                mob.shift(way/np.linalg.norm(way)*(distance-buff))
                x0,y0,x1,y1 = ZONES[self.zone]
                inside = mob.get_top()[1] <= y1 and mob.get_bottom()[1] >= y0 and mob.get_left()[0] >= x0 and mob.get_right()[0] <= x1
                if inside and not self.on_link(mob) and not self.crowded(mob):
                    return
        put(side)

    def clear_labels(self):
        for dev in self.devices.values():
            if dev.label is not None:
                self.seat(dev.label, dev, DIRECTIONS[dev.side], 0.17)

    def point(self, at):
        return self.center_pt + np.array([(at[0] - self.cx) * self.sx, (at[1] - self.cy) * self.sy, 0])

    def add_device(self, name, spec):
        dev = Device(spec.get("k", "node"), spec.get("l", name), spec.get("lp", "down"))
        dev.shift(self.point(spec.get("at", [0, 0])) - dev.anchor())
        self.devices[name] = dev
        self.device_layer.add(dev)
        return dev

    def _key(self, a, b):
        return (a, b) if (a, b) in self.links or (b, a) not in self.links else (b, a)

    def edge_gap(self, dev, u):
        """How far a link stops from a device's center, along direction u, so it meets the icon's edge."""
        return min(dev.body.width / 2 / max(abs(u[0]), 1e-3), dev.body.height / 2 / max(abs(u[1]), 1e-3)) + 0.03

    def endpoints(self, a, b):
        pa, pb = self.devices[a].anchor(), self.devices[b].anchor()
        v = pb - pa
        u = v / max(np.linalg.norm(v), 1e-3)
        return pa + u * self.edge_gap(self.devices[a], u), pb - u * self.edge_gap(self.devices[b], u)

    def build_link(self, a, b, style="solid", cost=None):
        start, end = self.endpoints(a, b)
        colors = {"solid": LINE, "active": STATE["done"], "tree": STATE["done"], "blocked": STATE["idle"], "failed": STATE["error"],
                  "now": STATE["now"], "dim": "#39404D", "up": LINE, "peer": LINE, "radio": LAYER["radio"], "tunnel": LAYER["tunnel"], "control": MUTED}
        width = {"active": 8, "tree": 8, "now": 8, "tunnel": 8}.get(style, 5)
        color = colors.get(style, LINE)
        if style in ("blocked", "failed", "radio", "control"):
            line = DashedLine(start, end, stroke_color=color, stroke_width=width, dash_length=0.12)
        elif style == "up":
            line = Arrow(start, end, buff=0, stroke_color=color, stroke_width=5, max_tip_length_to_length_ratio=0.2, tip_length=0.24)
        else:
            line = Line(start, end, stroke_color=color, stroke_width=width)
        group = VGroup(line)
        if cost is not None:
            n = np.array([-(end - start)[1], (end - start)[0], 0])
            n = n / max(np.linalg.norm(n), 1e-3)
            label = T(cost, 28, INK)
            label.move_to((start + end) / 2 + n * 0.24)
            group.add(VGroup(Circle(radius=max(label.width, label.height) / 2 + 0.05, fill_color=BG, fill_opacity=1, stroke_width=0).move_to(label), label))
        return group

    def add_link(self, a, b, opts=None):
        opts = opts or {}
        group = self.build_link(a, b, opts.get("s", "solid"), opts.get("c"))
        self.links[(a, b)] = group
        self.link_meta[(a, b)] = dict(opts)
        self.link_layer.add(group)
        return group


def wrapped_text(text, size, width, color=INK):
    """Wrap to a column width. A single long word stays one line and may still be wider than width."""
    raw = str(text)
    if not raw.strip():
        # A blank cell has no glyphs. One invisible point keeps placement from asking an empty curve for a box.
        mark = Dot(radius=0.01, fill_opacity=0, stroke_width=0)
        mark.text = ""
        return mark
    lines = wrap_lines(raw, width, size) or [raw]
    if len(lines) == 1:
        return T(lines[0], size, color)
    group = VGroup(*[T(line, size, color) for line in lines])
    group.arrange(DOWN, buff=0.05, aligned_edge=LEFT)
    group.text = str(text)
    return group


def column_content_widths(cols, rows, size, max_width=None):
    """Natural column widths. Extra-wide columns wrap, but never narrower than their longest word."""
    samples = [list(cols)] + [list(r) for r in rows]
    natural = [0.0] * len(cols)
    floors = [0.6] * len(cols)
    for row in samples:
        for i, cell in enumerate(row):
            natural[i] = max(natural[i], T(cell, size).width)
            words = str(cell).split() or [""]
            floors[i] = max(floors[i], max(T(word, size).width for word in words))
    pad = 0.34
    if not max_width or sum(natural) + pad * len(cols) <= max_width:
        return natural
    budget = max_width - pad * len(cols)
    widths = natural[:]
    for _ in range(24):
        extra = sum(widths) - budget
        if extra <= 0.01:
            break
        slack = [widths[i] - floors[i] for i in range(len(cols))]
        i = max(range(len(cols)), key=lambda n: slack[n])
        if slack[i] <= 0.01:
            break
        widths[i] = max(floors[i], widths[i] - extra)
    return widths


# Tables -------------------------------------------------------------------
class Grid(VGroup):
    def __init__(self, cols, rows, size=26, ghost=(), row_h=0.52, max_width=None):
        super().__init__()
        self.size = size
        self.cols, self.data = [str(c) for c in cols], [[str(c) for c in r] for r in rows]
        ghosts = [[str(c) for c in g] for g in ghost]
        self.content_w = column_content_widths(self.cols, self.data + ghosts, size, max_width)
        self.row_h = row_h
        self.widths = [w + 0.34 for w in self.content_w]
        self.total_w = sum(self.widths)
        self.head = VGroup()
        self.rows, self.cells = [], []
        self.window = 0
        self.knext = 0
        self.kzone = None
        self.bright_rows = None
        x = -self.total_w / 2
        self.xs = []
        for w in self.widths:
            self.xs.append(x + w / 2)
            x += w
        for i, c in enumerate(self.cols):
            self.head.add(wrapped_text(c, size, self.content_w[i], MUTED).move_to([self.xs[i], 0, 0]))
        rule_y = -max(self.head.height, row_h) / 2 - 0.06
        rule = Line([-self.total_w / 2, rule_y, 0], [self.total_w / 2, rule_y, 0], stroke_color=LINE, stroke_width=2)
        self.add(self.head, rule)
        self.rule = rule
        self._cursor = rule_y
        for row in self.data:
            self._make_row(row)

    def _make_row(self, row):
        cells = [wrapped_text(cell, self.size, self.content_w[i]).move_to([self.xs[i], 0, 0]) for i, cell in enumerate(row)]
        pitch = max(self.row_h, max(c.height for c in cells) + 0.16)
        y = self._cursor - pitch / 2 - 0.04
        for cell in cells:
            cell.set_y(y)
        self._cursor = y - pitch / 2
        self.row_h = max(self.row_h, pitch)
        group = VGroup(*cells)
        self.cells.append(cells)
        self.rows.append(group)
        self.add(group)
        return group


def shift_grid(grid, delta):
    """Move a table, including rows that were detached for a later reveal."""
    grid.shift(delta)
    for row in grid.rows:
        if row not in grid.submobjects:
            row.shift(delta)


def seat_grid(grid, zone, pin_top=False):
    """Put a table in its zone without scaling it. Overflow stays a finding."""
    center, w, h = zone_box(zone)
    if pin_top:
        delta = np.array([center[0] - grid.get_center()[0], (center[1] + h / 2 - 0.08) - grid.get_top()[1], 0])
    else:
        delta = np.array([center[0] - grid.get_center()[0], center[1] - grid.get_center()[1], 0])
    shift_grid(grid, delta)
    if grid.width > w + 0.03 or grid.height > h + 0.03:
        grid.layout_overflow = f"{zone}: content needs reflow or staged disclosure"
    return grid


def scroll_grid(grid, zone):
    """Drop the oldest visible data rows until the table sits inside the zone. Positions update immediately."""
    center, _, h = zone_box(zone)
    bottom = center[1] - h / 2 + 0.06
    dropped = []
    for _ in range(len(grid.rows) + 1):
        if grid.get_bottom()[1] >= bottom:
            break
        if grid.window >= grid.knext - 1:
            grid.layout_overflow = f"{zone}: content needs reflow or staged disclosure"
            break
        oldest = grid.rows[grid.window]
        successor = grid.rows[grid.window + 1]
        gap = oldest.get_y() - successor.get_y()
        if gap <= 0.01:
            grid.layout_overflow = f"{zone}: content needs reflow or staged disclosure"
            break
        grid.window += 1
        if oldest in grid.submobjects:
            grid.remove(oldest)
            dropped.append(oldest)
        for later in grid.rows[grid.window:]:
            later.shift(UP * gap)
    return dropped


# Address bits -------------------------------------------------------------
class BitRow(VGroup):
    def __init__(self, label, dotted):
        super().__init__()
        self.title = T(label, 26, MUTED)
        octets = [f"{int(o):08b}" for o in dotted.split(".")]
        self.bits = []
        self.cells = VGroup()
        x = 0.0
        w = 0.36
        for o, octet in enumerate(octets):
            for bit in octet:
                box = Rectangle(width=w, height=0.46, stroke_color=LINE, stroke_width=1.5, fill_color=PANEL, fill_opacity=1).move_to([x, 0, 0])
                digit = T(bit, 26).move_to(box)
                cell = VGroup(box, digit)
                self.bits.append(cell)
                self.cells.add(cell)
                x += w
            x += 0.12
        self.title.next_to(self.cells, UP, buff=0.08, aligned_edge=LEFT)
        self.add(self.title, self.cells)


# Sequence diagrams --------------------------------------------------------
class Ladder(VGroup):
    def __init__(self, zone, lanes, steps=6):
        super().__init__()
        center, w, h = zone_box(zone)
        n = len(lanes)
        self.steps, self.used = steps, 0
        gap = (w - 2.4) / max(n - 1, 1)
        x0, top, self.bottom = center[0] - gap * (n - 1) / 2, center[1] + h / 2 - 0.3, center[1] - h / 2 + 0.05
        self.top = top - 0.35
        self.x = {}
        for i, lane in enumerate(lanes):
            x = x0 + gap * i
            self.x[lane] = x
            self.add(T(lane, 26, INK).move_to([x, top, 0]))
            self.add(Line([x, top - 0.25, 0], [x, self.bottom, 0], stroke_color=LINE, stroke_width=2))

    def slot(self):
        y = self.top - (self.top - self.bottom) * (self.used + 0.7) / self.steps
        self.used += 1
        return y


# Timelines ----------------------------------------------------------------
class Tracks(VGroup):
    def __init__(self, zone, tracks, span, ticks=None):
        super().__init__()
        center, w, h = zone_box(zone)
        self.t0, self.t1 = span
        labels = [T(t, 26, MUTED) for t in tracks]
        pad = max(l.width for l in labels) + 0.25
        self.x0, self.x1 = center[0] - w / 2 + pad, center[0] + w / 2 - 0.15
        self.row = {}
        rh = min((h - 0.5) / len(tracks), 0.9)
        top = center[1] + rh * len(tracks) / 2
        for i, (name, label) in enumerate(zip(tracks, labels)):
            y = top - rh * (i + 0.5)
            self.row[name] = (y, rh * 0.72)
            label.move_to([self.x0 - pad / 2, y, 0])
            self.add(label, Line([self.x0, y, 0], [self.x1, y, 0], stroke_color="#303746", stroke_width=2))
        self.axis_y = top - rh * len(tracks)
        self.add(Line([self.x0, self.axis_y, 0], [self.x1, self.axis_y, 0], stroke_color=LINE, stroke_width=2))
        for tick in ticks or []:
            x = self.x_of(tick)
            self.add(Line([x, self.axis_y - 0.05, 0], [x, self.axis_y + 0.05, 0], stroke_color=LINE), T(tick, 24, MUTED).move_to([x, self.axis_y - 0.26, 0]))

    def x_of(self, t):
        return self.x0 + (t - self.t0) / (self.t1 - self.t0) * (self.x1 - self.x0)


# Header stacks ------------------------------------------------------------
def layer_block(text, kind, width=4.6, height=0.62):
    color = LAYER.get(kind, LAYER["data"])
    box = RoundedRectangle(corner_radius=0.06, width=width, height=height, stroke_color=color, stroke_width=3, fill_color=color, fill_opacity=0.22)
    return VGroup(box, T(text, 26).move_to(box))


class Stack(VGroup):
    def __init__(self, layers, width=None):
        super().__init__()
        self.layers_data = [dict(l) for l in layers]
        self.block_w = width or max([T(l["t"], 26).width for l in layers] + [3.0]) + 0.6
        self.blocks = VGroup(*[layer_block(l["t"], l.get("k", "data"), self.block_w) for l in layers])
        self.blocks.arrange(DOWN, buff=0.08)
        self.add(self.blocks)


class Fields(VGroup):
    """A header drawn by rows, with cells sized by their share of the row."""

    def __init__(self, rows, unit=0.2, row_h=0.56):
        super().__init__()
        self.cell = {}
        y = 0
        for row in rows:
            x = 0
            for label, span in row:
                w = span * unit
                box = Rectangle(width=w, height=row_h, stroke_color=LINE, stroke_width=2, fill_color=PANEL, fill_opacity=1).move_to([x + w / 2, y, 0])
                text = T(label, 24).move_to(box)
                if text.width > w - 0.08:
                    raise ValueError(f"field '{label}' is too wide for its cell")
                cell = VGroup(box, text)
                self.cell[label] = cell
                self.add(cell)
                x += w
            y -= row_h


class Slots(VGroup):
    """A FIFO drawn left to right; the head is on the right."""

    def __init__(self, items, kind="data", title=None, cell_w=1.0):
        super().__init__()
        self.kind, self.cell_w = kind, cell_w
        self.items = VGroup()
        for it in items:
            self.items.add(self.make(it))
        self.items.arrange(RIGHT, buff=0.08)
        self.title = T(title, 26, MUTED) if title else None
        self.add(self.items)
        if self.title:
            self.title.next_to(self.items, UP, buff=0.14)
            self.add(self.title)

    def make(self, text, kind=None):
        color = LAYER.get(kind or self.kind, LAYER["data"])
        box = RoundedRectangle(corner_radius=0.05, width=self.cell_w, height=0.58, stroke_color=color, stroke_width=3, fill_color=color, fill_opacity=0.22)
        return VGroup(box, T(text, 26).move_to(box))


class StepWave(VGroup):
    """Chip values drawn as a step signal, for code-division sums."""

    def __init__(self, label, values, top=2, chip=0.95, unit=0.34):
        super().__init__()
        self.values, self.chip = values, chip
        axis = Line(LEFT * 0, RIGHT * chip * len(values), stroke_color=LINE, stroke_width=2)
        pts, x = [], 0
        for v in values:
            pts += [[x, v * unit, 0], [x + chip, v * unit, 0]]
            x += chip
        wave = VMobject(stroke_color=LAYER["radio"], stroke_width=5).set_points_as_corners(np.array(pts))
        nums = VGroup(*[T(v, 24).move_to([chip * (i + 0.5), (v * unit) + (0.24 if v >= 0 else -0.24), 0]) for i, v in enumerate(values)])
        name = T(label, 26, MUTED).next_to(axis, LEFT, buff=0.22)
        self.axis, self.wave = axis, wave
        self.add(axis, wave, nums, name)
        self.natural_w = self.get_width()


class Curves(VGroup):
    def __init__(self, zone, xlabel, ylabel, curves, xr=(0, 1), yr=(0, 1)):
        super().__init__()
        center, w, h = zone_box(zone)
        self.x0, self.x1 = center[0] - w / 2 + 0.75, center[0] + w / 2 - 0.2
        self.y0, self.y1 = center[1] - h / 2 + 0.65, center[1] + h / 2 - 0.2
        self.xr, self.yr = xr, yr
        self.add(Line([self.x0, self.y0, 0], [self.x1, self.y0, 0], stroke_color=LINE, stroke_width=3),
                 Line([self.x0, self.y0, 0], [self.x0, self.y1, 0], stroke_color=LINE, stroke_width=3))
        self.add(T(xlabel, 26, MUTED).move_to([(self.x0 + self.x1) / 2, self.y0 - 0.35, 0]))
        yl = T(ylabel, 26, MUTED).rotate(np.pi / 2).move_to([self.x0 - 0.38, (self.y0 + self.y1) / 2, 0])
        self.add(yl)
        self.curves = {}
        for c in curves:
            pts = np.array([self.map(*p) for p in c["points"]])
            line = VMobject(stroke_color=LAYER.get(c.get("k", "ip")), stroke_width=4).set_points_smoothly(pts)
            self.curves[c["name"]] = line
            self.add(line)
            if c.get("label"):
                self.add(T(c["label"], 24, LAYER.get(c.get("k", "ip"))).next_to(pts[-1], LEFT + UP, buff=0.04))

    def map(self, x, y):
        return [self.x0 + (x - self.xr[0]) / (self.xr[1] - self.xr[0]) * (self.x1 - self.x0),
                self.y0 + (y - self.yr[0]) / (self.yr[1] - self.yr[0]) * (self.y1 - self.y0), 0]


# A decision as a sieve -----------------------------------------------------
class Sieve(VGroup):
    """Candidates in columns, decision steps in rows. A candidate drops out at the first row it loses."""

    def __init__(self, zone, rungs, routes, size=30):
        super().__init__()
        center, w, h = zone_box(zone)
        self.row_h = 0.68
        labels = [T(r, size, MUTED) for r in rungs]
        label_w = max(m.width for m in labels) + 0.5
        widths = [max([T(r["name"], size).width] + [T(v, size).width for v in r["vals"]]) + 0.6 for r in routes]
        total = label_w + sum(widths)
        x = center[0] - total / 2
        top = center[1] + (len(rungs) + 1) * self.row_h / 2 - self.row_h / 2
        self.rows, self.cols, self.cells = [], {}, {}
        self.alive = [r["name"] for r in routes]
        for i, label in enumerate(labels):
            label.move_to([x + 0.1 + label.width / 2, top - (i + 1) * self.row_h, 0])
            self.rows.append(VGroup(label))
            self.add(label)
        cx = x + label_w
        for route, width in zip(routes, widths):
            head = T(route["name"], size, INK, weight="BOLD").move_to([cx + width / 2, top, 0])
            col = VGroup(head)
            for i, v in enumerate(route["vals"]):
                cell = T(v, size).move_to([cx + width / 2, top - (i + 1) * self.row_h, 0])
                self.cells[(i, route["name"])] = cell
                self.rows[i].add(cell)
                col.add(cell)
            self.cols[route["name"]] = col
            self.add(col)
            cx += width
        self.add(Line([x, top - self.row_h / 2, 0], [x + total, top - self.row_h / 2, 0], stroke_color=LINE, stroke_width=2))
        self.kitems = [(r["name"], self.cols[r["name"]][0]) for r in routes]


# A datagram as a bar of bytes ----------------------------------------------
class ByteBar(VGroup):
    """A datagram drawn to scale. Slices keep their place under the original, so an offset is visibly a distance."""

    def __init__(self, zone, total, header=20, unit=8, rows=3):
        super().__init__()
        center, w, h = zone_box(zone)
        self.total, self.header, self.unit, self.rows, self.data = total, header, unit, rows, total - header
        self.chip_w, self.bar_h = 0.7, 0.58
        self.left, self.right = center[0] - w / 2 + 0.05, center[0] + w / 2 - 0.05
        self.x0 = self.left + self.chip_w + 0.03
        self.k = (self.right - self.x0) / self.data
        self.top_y = center[1] + h / 2 - 0.8
        low = center[1] - h / 2 + 0.75
        self.gap = min((self.top_y - 1.05 - low) / max(rows - 1, 1), 1.2)
        self.note_y = center[1] - h / 2 + 0.35
        self.chip = self.header_chip(self.x0 - 0.03, self.top_y)
        self.body = self.segment(0, self.data, self.top_y, f"{self.data} bytes of data")
        self.title = T(f"IP datagram, {total} bytes: a {header}-byte header (blue), then the data", 28, MUTED).next_to(VGroup(self.chip, self.body), UP, buff=0.12, aligned_edge=LEFT)
        self.add(self.title, self.chip, self.body)
        self.cuts, self.slices, self.chips, self.infos = {}, {}, {}, {}
        self.zoom, self.comb = None, None
        self.kitems = [(str(header), self.chip), (str(self.data), self.body)]

    def x_of(self, byte):
        return self.x0 + byte * self.k

    def row_y(self, i):
        return self.top_y - 1.05 - i * self.gap

    def segment(self, start, size, y, text=None):
        x0, x1 = self.x_of(start), self.x_of(start + size)
        color = LAYER["data"]
        box = Rectangle(width=x1 - x0, height=self.bar_h, stroke_color=color, stroke_width=3, fill_color=color, fill_opacity=0.22).move_to([(x0 + x1) / 2, y, 0])
        label = T(text or size, 26)
        if label.width > x1 - x0 - 0.1:
            label = T(size, 26)
        return VGroup(box, label.move_to(box))

    def header_chip(self, right, y):
        color = LAYER["ip"]
        box = Rectangle(width=self.chip_w, height=self.bar_h, stroke_color=color, stroke_width=3, fill_color=color, fill_opacity=0.35).move_to([right - self.chip_w / 2, y, 0])
        return VGroup(box, T(self.header, 26).move_to(box))

    def make_comb(self):
        """One tick per offset unit, under the data."""
        comb = VMobject(stroke_color=MUTED, stroke_width=1.5)
        y = self.top_y - self.bar_h / 2 - 0.02
        for n in range(self.data // self.unit + 1):
            x = self.x_of(n * self.unit)
            comb.start_new_path(np.array([x, y, 0]))
            comb.add_line_to(np.array([x, y - 0.11, 0]))
        return comb

    def make_zoom(self, at, color):
        """A magnified stretch of the ruler, where one byte position is easy to see."""
        cx, y = (self.left + self.right) / 2, self.top_y - 2.45
        base = at // self.unit * self.unit
        mid = base if at % self.unit == 0 else base + self.unit // 2
        spacing = 2.0
        self.zx = lambda b: cx + (b - mid) / self.unit * spacing
        panel = VGroup()
        panel.add(Line([cx - 5.2, y, 0], [cx + 5.2, y, 0], stroke_color=LINE, stroke_width=3))
        ticks = [base + k * self.unit for k in (-2, -1, 0, 1, 2)] + ([base + 3 * self.unit] if at % self.unit else [])
        for b in ticks:
            panel.add(Line([self.zx(b), y - 0.14, 0], [self.zx(b), y + 0.14, 0], stroke_color=INK, stroke_width=3))
            panel.add(T(f"{b}", 26, MUTED).move_to([self.zx(b), y - 0.42, 0]))
        cut_x = self.x_of(at)
        bar_y = self.top_y - self.bar_h / 2 - 0.14
        panel.add(DashedLine([cut_x, bar_y, 0], [cx - 5.2, y + 0.75, 0], stroke_color=LINE, stroke_width=2, dash_length=0.1),
                  DashedLine([cut_x, bar_y, 0], [cx + 5.2, y + 0.75, 0], stroke_color=LINE, stroke_width=2, dash_length=0.1))
        panel.add(T(f"Zoomed in: every tick is a multiple of {self.unit} bytes", 26, MUTED).move_to([cx, y - 1.0, 0]))
        self.zoom_marker = self.zoom_mark(at, color, y)
        panel.add(self.zoom_marker)
        self.zoom_y = y
        return panel

    def zoom_mark(self, at, color, y):
        return VGroup(Line([self.zx(at), y - 0.26, 0], [self.zx(at), y + 0.3, 0], stroke_color=color, stroke_width=7), T(f"{at}", 30, color).move_to([self.zx(at), y + 0.56, 0]))


# Packet token -------------------------------------------------------------
class PacketToken(VGroup):
    def __init__(self, layers):
        super().__init__()
        self.shells = []
        w, h = 0.56, 0.34
        core = None
        for i, kind in enumerate(reversed(layers)):
            color = LAYER.get(kind, LAYER["data"])
            box = RoundedRectangle(corner_radius=0.05, width=w + i * 0.3, height=h + i * 0.24, stroke_color=color, stroke_width=4, fill_color=color, fill_opacity=0.9 if i == 0 else 0.25)
            self.shells.insert(0, box)
            self.add_to_back(box)
