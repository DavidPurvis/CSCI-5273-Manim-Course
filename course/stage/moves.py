"""The fixed vocabulary of animations that recipe cards may call."""
import json
from pathlib import Path

import numpy as np
from manim import (DOWN, LEFT, RIGHT, UP, Arrow, Circle, Create, DashedVMobject, Dot, FadeIn, FadeOut, GrowFromCenter, LaggedStart,
                   Line, MathTex, MoveAlongPath, Rectangle, RoundedRectangle, Star, Succession, Text, Transform,
                   VGroup, VMobject, Write, linear, rate_functions, AnimationGroup, DashedLine)

from .parts import (BitRow, ByteBar, Curves, Device, Fields, Grid, Ladder, Net, PacketToken, Sieve, Slots, Stack, StepWave, T, Tracks, layer_block,
                    outline, paragraph, place, zone_box)
from .theme import BG, FRAME_X, INK, LAYER, LINE, MUTED, PANEL, STATE, ZONES, zones_overlap

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = {}
_TRACES = {}


def move(name, t=1.0):
    def wrap(fn):
        REGISTRY[name] = {"fn": fn, "t": t}
        return fn
    return wrap


def resolve(value):
    """Replace "$module.key.sub" with the frozen trace value."""
    if isinstance(value, str) and value.startswith("$"):
        parts = value[1:].split(".")
        data = _TRACES.setdefault(parts[0], json.loads((ROOT / "traces" / f"{parts[0]}.json").read_text()))
        for p in parts[1:]:
            data = data[int(p)] if isinstance(data, list) else data[p]
        return data
    if isinstance(value, list):
        return [resolve(v) for v in value]
    if isinstance(value, dict):
        return {k: resolve(v) for k, v in value.items()}
    return value


class Stage:
    def __init__(self, scene):
        self.scene = scene
        self.objs, self.zone_of, self.marks = {}, {}, {}
        self.adjust = {}
        self.pause_bar = None

    def register(self, name, mob, zone=None):
        out = self.drop(name)
        if zone:
            for other, z in list(self.zone_of.items()):
                if z and zones_overlap(zone, z):
                    out += self.drop(other)
        scale = self.adjust.get("scale", {}).get(name)
        if scale:
            mob.scale(scale)
        nudge = self.adjust.get("nudge", {}).get(name)
        if nudge:
            mob.shift(np.array([nudge[0], nudge[1], 0]))
        self.objs[name] = mob
        self.zone_of[name] = zone
        return out

    def drop(self, name):
        out = []
        for key in [k for k in self.marks if k[0] == name]:
            out.append(FadeOut(self.marks.pop(key)))
        for pname, pkt in list(self.objs.items()):
            if getattr(pkt, "net_name", None) == name:
                out += self.drop(pname)
        if name in self.objs:
            mob = self.objs.pop(name)
            self.zone_of.pop(name, None)
            out.append(FadeOut(mob))
        return out

    def get(self, name):
        if name not in self.objs:
            raise KeyError(f"move refers to '{name}', which is not on stage")
        return self.objs[name]

    def set_mark(self, key, mob_or_none):
        out = []
        if key in self.marks:
            out.append(FadeOut(self.marks.pop(key)))
        if mob_or_none is not None:
            self.marks[key] = mob_or_none
            out.append(FadeIn(mob_or_none))
        return out


# General --------------------------------------------------------------------
@move("heading", 0.6)
def heading(s, text):
    m = T(text, 30, MUTED).move_to([0, 3.6, 0]).to_edge(LEFT, buff=0.35)
    return s.register("_heading", m) + [FadeIn(m)]


SPINE = ["LAN", "IP", "Forward", "Discover", "Route", "Failure", "Policy", "Groups", "Radio", "Move"]


@move("spine", 1.4)
def spine(s, current, zone="full"):
    dots, labels, links = VGroup(), VGroup(), VGroup()
    idx = SPINE.index(current)
    for i, stop in enumerate(SPINE):
        color = STATE["done"] if i < idx else STATE["now"] if i == idx else STATE["idle"]
        dots.add(Dot(radius=0.14 if i == idx else 0.09, color=color).move_to([-6.1 + i * 1.355, 0.25, 0]))
        labels.add(T(stop, 24, INK if i == idx else MUTED).move_to([-6.1 + i * 1.355, -0.25, 0]))
    for a, b in zip(dots, dots[1:]):
        links.add(Line(a.get_center(), b.get_center(), stroke_color=LINE, stroke_width=3))
    group = VGroup(links, dots, labels)
    title = T("One laptop's journey: you are here", 30, INK).next_to(group, UP, buff=0.7)
    whole = VGroup(title, group)
    place(whole, zone)
    return s.register("_spine", whole, zone) + [FadeIn(whole)]


@move("clear", 0.6)
def clear(s, keep=None):
    keep = set(keep or []) | {"_heading", "_tag"}
    out = []
    for name in list(s.objs):
        if name not in keep:
            out += s.drop(name)
    return out


@move("fade", 0.5)
def fade(s, names):
    out = []
    for n in names if isinstance(names, list) else [names]:
        out += s.drop(n)
    return out


@move("q", 1.0)
def question(s, text, zone="full", name="_q"):
    _, w, _ = zone_box(zone)
    m = paragraph(text, w - 0.4, 42, INK, center=True)
    place(m, zone)
    return s.register(name, m, zone) + [Write(m)]


@move("rule", 0.9)
def rule(s, text, name="_rule"):
    m = paragraph(text, 13.2, 30, STATE["now"], center=True)
    place(m, "rule")
    return s.register(name, m, "rule") + [FadeIn(m)]


@move("trap", 1.5)
def trap(s, wrong, right, name="_rule"):
    """The answer that sounds right, struck through, then the correction."""
    w = paragraph(wrong, 13.2, 28, STATE["error"], center=True)
    r = paragraph(right, 13.2, 28, STATE["done"], center=True)
    group = VGroup(w, r).arrange(DOWN, buff=0.1)
    place(group, "rule")
    strike = Line(w.get_left() + LEFT * 0.1, w.get_right() + RIGHT * 0.1, stroke_color=STATE["error"], stroke_width=4)
    whole = VGroup(w, r, strike)
    return s.register(name, whole, "rule") + [Succession(FadeIn(w), Create(strike), FadeIn(r))]


@move("keep", 0.6)
def keep_awake(s):
    """Pulse the corner tag. It adds motion during a narrated still without changing the diagram."""
    tag = s.objs.get("_tag")
    if tag is None:
        return []
    from course.stage.signal import flash
    return [flash(tag)]


@move("pause", 0.6)
def pause(s, text, long=False):
    words = paragraph(("Pause the video and work it out: " if long else "Pause and predict: ") + text, 13.2, 30, INK, center=True)
    place(words, "rule")
    bar = Rectangle(width=13.2, height=0.07, stroke_width=0, fill_color=STATE["now"], fill_opacity=1).move_to([0, -3.92, 0])
    group = VGroup(words, bar)
    s.pause_bar = bar
    return s.register("_rule", group, "rule") + [FadeIn(group)]


@move("text", 0.9)
def text_block(s, name, zone, lines, size=30, color=None):
    _, w, _ = zone_box(zone)
    col = color and (STATE.get(color) or LAYER.get(color)) or INK
    group = VGroup(*[paragraph(l, w - 0.3, size, col) for l in lines]).arrange(DOWN, buff=0.28, aligned_edge=LEFT)
    place(group, zone)
    group.kitems = list(zip(lines, group))
    return s.register(name, group, zone) + [FadeIn(group)]


@move("bullets", 0.8)
def bullets(s, name, zone, items, show=1, size=30, gap=0.24):
    _, w, _ = zone_box(zone)
    rows = []
    for it in items:
        dot = Dot(radius=0.06, color=STATE["now"])
        p = paragraph(it, w - 0.75, size)
        dot.next_to(p[0], LEFT, buff=0.18)
        rows.append(VGroup(dot, p))
    group = VGroup(*rows).arrange(DOWN, buff=gap, aligned_edge=LEFT)
    place(group, zone)
    group.kitems = list(zip(items, rows))
    hidden = list(group[show:])
    for r in hidden:
        group.remove(r)
    group.khidden = hidden
    return s.register(name, group, zone) + ([FadeIn(group)] if show else [])


@move("reveal", 0.7)
def reveal(s, name, n=1):
    group = s.get(name)
    out = []
    for _ in range(n):
        row = group.khidden.pop(0)
        group.add(row)
        out.append(FadeIn(row, shift=UP * 0.1))
    return out


@move("card", 0.9)
def card(s, kind, text, zone="right_bottom", name="_card"):
    color = {"clarification": STATE["now"], "assumption": LAYER["transport"], "correction": STATE["error"], "note": LAYER["ip"]}[kind]
    _, w, _ = zone_box(zone)
    head = T({"clarification": "Slide clarification", "assumption": "Assumption", "correction": "Slide correction", "note": "Note"}[kind], 26, color)
    body = paragraph(text, w - 0.5, 28)
    content = VGroup(head, body).arrange(DOWN, buff=0.16, aligned_edge=LEFT)
    box = RoundedRectangle(corner_radius=0.1, width=content.width + 0.36, height=content.height + 0.32, stroke_color=color, stroke_width=3, fill_color=PANEL, fill_opacity=1).move_to(content)
    group = VGroup(box, content)
    place(group, zone)
    return s.register(name, group, zone) + [FadeIn(group)]


@move("tex", 1.0)
def tex(s, name, zone, tex, size=44, color=None):
    m = MathTex(tex, font_size=size, color=(color and STATE.get(color)) or INK)
    m.kfont, m.kheight = 48, m.height
    place(m, zone)
    return s.register(name, m, zone) + [Write(m)]


# Network diagrams -----------------------------------------------------------
@move("net.show", 1.3)
def net_show(s, name, zone, nodes, links=(), spread=None):
    n = Net(zone, nodes, links, spread)
    n.kname = name
    return s.register(name, n, zone) + [FadeIn(n.link_layer), FadeIn(n.device_layer)]


@move("net.add", 0.8)
def net_add(s, name, nodes=None, links=()):
    n, out = s.get(name), []
    for key, spec in (nodes or {}).items():
        out.append(FadeIn(n.add_device(key, spec)))
    for spec in links:
        out.append(Create(n.add_link(*spec)))
    n.clear_labels()
    return out


def relink(net, key, style):
    old = net.links[key]
    meta = net.link_meta[key]
    new = net.build_link(key[0], key[1], style or meta.get("s", "solid"), meta.get("c"))
    if style:
        meta["s"] = style
    net.link_layer.remove(old)
    net.link_layer.add(new)
    net.links[key] = new
    return AnimationGroup(FadeOut(old), FadeIn(new))


def find_link(net, a, b):
    if (a, b) in net.links:
        return (a, b)
    if (b, a) in net.links:
        return (b, a)
    raise KeyError(f"no link {a}-{b} in {net.kname}")


@move("net.state", 0.7)
def net_state(s, name, nodes=None, links=()):
    n, out = s.get(name), []
    for node, state in (nodes or {}).items():
        body = n.devices[node].body
        out += s.set_mark((name, "node", node), outline(body, state) if state else None)
    for a, b, style in links:
        out.append(relink(n, find_link(n, a, b), style))
    return out


@move("net.path", 0.9)
def net_path(s, name, path, style="now"):
    n = s.get(name)
    return [relink(n, find_link(n, a, b), style) for a, b in zip(path, path[1:])]


@move("net.badge", 0.5)
def net_badge(s, name, node, text, side="right", state=None):
    n = s.get(name)
    dev = n.devices[node]
    color = STATE.get(state, INK) if state else INK
    new = T(text, 26, color)
    n.seat(new, dev, {"right": RIGHT, "left": LEFT, "up": UP, "down": DOWN}[side], 0.2)
    old = n.badges.get(node)
    n.badges[node] = new
    n.add(new)
    if old is not None:
        n.remove(old)
        return [FadeOut(old), FadeIn(new)]
    return [FadeIn(new)]


@move("net.cost", 0.5)
def net_cost(s, name, a, b, cost):
    n = s.get(name)
    key = find_link(n, a, b)
    n.link_meta[key]["c"] = cost
    return [relink(n, key, None)]


@move("net.move", 1.4)
def net_move(s, name, node, to):
    n = s.get(name)
    dev = n.devices[node]
    delta = n.point(to) - dev.anchor()
    anims = []
    dev.shift(delta)
    fresh = {}
    for key in [k for k in n.links if node in k]:
        meta = n.link_meta[key]
        fresh[key] = n.build_link(key[0], key[1], meta.get("s", "solid"), meta.get("c"))
    dev.shift(-delta)
    anims.append(dev.animate.shift(delta))
    if n.badges.get(node) is not None:
        anims.append(n.badges[node].animate.shift(delta))
    for key, new in fresh.items():
        anims.append(Transform(n.links[key], new))
    for mark_key, mark_mob in s.marks.items():
        if mark_key[:3] == (name, "node", node):
            anims.append(mark_mob.animate.shift(delta))
    return anims


@move("net.relink", 0.5)
def net_relink(s, name, a, b, style="solid"):
    """Redraw a link after its endpoint has moved, or add it if new."""
    n = s.get(name)
    if (a, b) in n.links or (b, a) in n.links:
        key = find_link(n, a, b)
        return [relink(n, key, style)]
    return [Create(n.add_link(a, b, {"s": style}))]


@move("net.unlink", 0.4)
def net_unlink(s, name, a, b):
    n = s.get(name)
    key = find_link(n, a, b)
    old = n.links.pop(key)
    n.link_meta.pop(key)
    n.link_layer.remove(old)
    return [FadeOut(old)]


@move("net.unbadge", 0.4)
def net_unbadge(s, name, node):
    n = s.get(name)
    old = n.badges.pop(node, None)
    if old is None:
        return []
    n.remove(old)
    return [FadeOut(old)]


@move("net.pulse", 0.9)
def net_pulse(s, name, path, state="now"):
    """A signal runs along links."""
    n = s.get(name)
    pts = [n.devices[a].anchor() for a in path]
    dot = Dot(pts[0], radius=0.13, color=STATE[state]).set_z_index(6)
    route = VMobject().set_points_as_corners(pts)
    return [Succession(MoveAlongPath(dot, route, rate_func=rate_functions.smooth), FadeOut(dot, run_time=0.15))]


@move("net.walk", 1.0)
def net_walk(s, name, path, state="now"):
    """Trace a path hop by hop, in the direction data travels. It stays until the next walk."""
    n = s.get(name)
    arrows = VGroup()
    for a, b in zip(path, path[1:]):
        start, end = n.endpoints(a, b)
        arrows.add(Arrow(start, end, buff=0, stroke_color=STATE[state], stroke_width=8, tip_length=0.24, max_tip_length_to_length_ratio=0.3, max_stroke_width_to_length_ratio=30))
    out = s.set_mark((name, "walk"), None)
    s.marks[(name, "walk")] = arrows
    return out + [Succession(*[Create(a, rate_func=linear) for a in arrows])]


@move("net.unwalk", 0.4)
def net_unwalk(s, name):
    return s.set_mark((name, "walk"), None)


@move("msg.send", 1.3)
def msg_send(s, name, a, b, text, kind="label"):
    """A message with readable contents travels along a link."""
    n = s.get(name)
    label = T(text, 26)
    color = LAYER.get(kind, STATE.get(kind, LAYER["data"]))
    box = RoundedRectangle(corner_radius=0.08, width=label.width + 0.28, height=label.height + 0.2, stroke_color=color, stroke_width=3, fill_color=PANEL, fill_opacity=1)
    tag = VGroup(box, label).set_z_index(6).move_to(n.devices[a].anchor())
    return [Succession(FadeIn(tag, run_time=0.25), tag.animate(run_time=1).move_to(n.devices[b].anchor()), FadeOut(tag, run_time=0.25))]


# Packets --------------------------------------------------------------------
def dock(dev):
    """Where a packet rests: on the icon, or just above a labelled box so the label stays readable."""
    if dev.kind in ("box", "node", "cloud"):
        return dev.anchor() + UP * (dev.body.height / 2 + 0.2)
    return dev.anchor()


@move("packet.spawn", 0.5)
def packet_spawn(s, name, net, at, layers=("eth", "ip")):
    n = s.get(net)
    token = PacketToken(list(layers))
    token.move_to(dock(n.devices[at]))
    token.net_name, token.at = net, at
    token.set_z_index(5)
    return s.register(name, token) + [GrowFromCenter(token)]


@move("packet.hop", 1.1)
def packet_hop(s, name, to):
    token = s.get(name)
    n = s.get(token.net_name)
    stops = to if isinstance(to, list) else [to]
    token.at = stops[-1]
    if len(stops) == 1:
        return [token.animate.move_to(dock(n.devices[stops[0]]))]
    path = VMobject().set_points_as_corners([token.get_center()] + [dock(n.devices[a]) for a in stops])
    return [MoveAlongPath(token, path, rate_func=rate_functions.smooth)]


@move("packet.both", 1.1)
def packet_both(s, moves):
    """Several packets move at the same moment."""
    out = []
    for m in moves:
        out += packet_hop(s, m["name"], m["to"])
    return out


@move("packet.peel", 0.6)
def packet_peel(s, name):
    token = s.get(name)
    shell = token.shells.pop(0)
    token.remove(shell)
    return [FadeOut(shell, shift=UP * 0.45)]


@move("packet.wrap", 0.6)
def packet_wrap(s, name, kind="eth"):
    token = s.get(name)
    color = LAYER.get(kind, LAYER["data"])
    inner = token.shells[0]
    box = RoundedRectangle(corner_radius=0.05, width=inner.width + 0.3, height=inner.height + 0.24, stroke_color=color, stroke_width=4, fill_color=color, fill_opacity=0.25).move_to(inner)
    box.set_z_index(4)
    token.shells.insert(0, box)
    token.add_to_back(box)
    return [FadeIn(box, scale=1.6)]


@move("packet.swap_link_header", 1.2)
def packet_swap(s, name, kind="eth"):
    token = s.get(name)
    old = token.shells.pop(0)
    token.remove(old)
    inner = token.shells[0]
    color = LAYER.get(kind, LAYER["data"])
    box = RoundedRectangle(corner_radius=0.05, width=old.width, height=old.height, stroke_color=color, stroke_width=4, fill_color=color, fill_opacity=0.25).move_to(inner)
    box.set_z_index(4)
    token.shells.insert(0, box)
    token.add_to_back(box)
    return [Succession(FadeOut(old, shift=UP * 0.45), FadeIn(box, scale=1.6))]


@move("packet.flood", 1.3)
def packet_flood(s, name, to, keep=False):
    token = s.get(name)
    n = s.get(token.net_name)
    out = []
    for dest in to:
        copy = token.copy()
        copy.set_z_index(5)
        target = dock(n.devices[dest])
        out.append(Succession(copy.animate.move_to(target), FadeOut(copy)))
    return out


@move("packet.drop", 0.8)
def packet_drop(s, name):
    token = s.objs.pop(name)
    s.zone_of.pop(name, None)
    x = VGroup(Line(UP * 0.2 + LEFT * 0.2, DOWN * 0.2 + RIGHT * 0.2, stroke_color=STATE["error"], stroke_width=6),
               Line(UP * 0.2 + RIGHT * 0.2, DOWN * 0.2 + LEFT * 0.2, stroke_color=STATE["error"], stroke_width=6)).move_to(token).set_z_index(6)
    return [Succession(FadeIn(x), AnimationGroup(FadeOut(x), FadeOut(token)))]


@move("packet.fade", 0.4)
def packet_fade(s, name):
    return s.drop(name)


# Named teaching moves --------------------------------------------------------
@move("switch.learn_source", 0.9)
def switch_learn(s, table, mac, port, net=None, node=None):
    out = table_add(s, table, [mac, port], state="changed")
    if net:
        out += s.set_mark((net, "node", node), outline(s.get(net).devices[node].body, "now"))
    return out


@move("graph.promote", 0.8)
def graph_promote(s, name, node, via=None):
    n = s.get(name)
    out = s.set_mark((name, "node", node), outline(n.devices[node].body, "done"))
    if via:
        out.append(relink(n, find_link(n, via, node), "tree"))
    return out


@move("graph.relax", 1.0)
def graph_relax(s, name, via, node, text, side="right", state="now"):
    """Try a route through a settled node: a signal crosses the edge, and the neighbor's distance updates."""
    n = s.get(name)
    dev = n.devices[node]
    dot = Dot(n.devices[via].anchor(), radius=0.13, color=STATE["now"]).set_z_index(6)
    new = T(text, 28, STATE.get(state, INK))
    old = n.badges.get(node)
    if old is not None:
        n.remove(old)
        n.badges.pop(node)
    n.seat(new, dev, {"right": RIGHT, "left": LEFT, "up": UP, "down": DOWN}[side], 0.2)
    n.badges[node] = new
    n.add(new)
    out = [Succession(dot.animate(run_time=1).move_to(dev.anchor()), FadeOut(dot, run_time=0.15)), FadeIn(new)]
    return out + ([FadeOut(old)] if old is not None else [])


@move("tunnel.reencapsulate", 1.0)
def tunnel_re(s, stack, outer, kind="tunnel"):
    return stack_set(s, stack, 0, outer, kind)


# Radio ----------------------------------------------------------------------
@move("radio.zone", 0.8)
def radio_zone(s, net, node, radius=1.6, name=None, kind="radio"):
    n = s.get(net)
    c = Circle(radius=radius, stroke_color=LAYER.get(kind, LAYER["radio"]), stroke_width=2, fill_color=LAYER.get(kind, LAYER["radio"]), fill_opacity=0.07).move_to(n.devices[node].anchor())
    c.set_z_index(-1)
    c.net_name = net
    return s.register(name or f"_zone_{net}_{node}", c) + [GrowFromCenter(c)]


@move("radio.pulse", 1.0)
def radio_pulse(s, net, node, radius=1.8, kind="radio"):
    n = s.get(net)
    c = Circle(radius=0.15, stroke_color=LAYER.get(kind, LAYER["radio"]), stroke_width=5).move_to(n.devices[node].anchor())
    return [Succession(c.animate.scale(radius / 0.15).set_stroke(opacity=0.3), FadeOut(c, run_time=0.1))]


@move("fx.burst", 0.7)
def burst(s, net, node=None, between=None):
    n = s.get(net)
    pt = n.devices[node].anchor() if node else (n.devices[between[0]].anchor() + n.devices[between[1]].anchor()) / 2
    star = Star(n=9, outer_radius=0.42, inner_radius=0.2, fill_color=STATE["error"], fill_opacity=0.9, stroke_width=0).move_to(pt).set_z_index(6)
    return [Succession(GrowFromCenter(star), FadeOut(star))]


# Tables ---------------------------------------------------------------------
@move("table.show", 0.9)
def table_show(s, name, zone, data=None, cols=None, rows=None, show=None, size=30, ghost=(), row_h=0.52):
    if data:
        cols, rows = data["cols"], data["rows"]
    grid = Grid(cols, rows or [], size, ghost, row_h)
    before = grid.height
    place(grid, zone)
    grid.kscale = grid.height / max(before, 1e-3)
    grid.knext = len(grid.rows)
    if show is not None:
        for row in grid.rows[show:]:
            grid.remove(row)
        grid.knext = show
    return s.register(name, grid, zone) + [FadeIn(grid)]


@move("table.reveal", 0.6)
def table_reveal(s, name, n=1):
    grid = s.get(name)
    out = []
    for _ in range(n):
        row = grid.rows[grid.knext]
        grid.knext += 1
        grid.add(row)
        out.append(FadeIn(row, shift=DOWN * 0.08))
    return out


@move("table.add", 0.6)
def table_add(s, name, row, state=None):
    grid = s.get(name)
    r = len(grid.rows)
    anchor = grid.rule.get_center()
    spacing = grid.row_h * grid.kscale
    cells = []
    for i, cell in enumerate(row):
        t = T(cell, grid.size).scale(grid.kscale)
        x = anchor[0] + (grid.xs[i]) * grid.kscale
        t.move_to([x, anchor[1] - spacing * (r + 0.5), 0])
        cells.append(t)
    group = VGroup(*cells)
    grid.cells.append(cells)
    grid.rows.append(group)
    grid.add(group)
    grid.knext = len(grid.rows)
    out = [FadeIn(group, shift=DOWN * 0.08)]
    if state:
        out += s.set_mark((name, "row", r), outline(group, state))
    return out


@move("table.set", 0.6)
def table_set(s, name, r, c, v, state=None):
    grid = s.get(name)
    old = grid.cells[r][c]
    color = STATE.get(state, INK) if state else INK
    new = T(v, grid.size, color).scale(grid.kscale).move_to(old)
    grid.cells[r][c] = new
    grid.rows[r].remove(old)
    grid.rows[r].add(new)
    return [FadeOut(old), FadeIn(new)]


@move("table.mark", 0.5)
def table_mark(s, name, r, state="now"):
    grid = s.get(name)
    return s.set_mark((name, "row", r), outline(grid.rows[r], state) if state else None)


@move("table.flash", 0.6)
def table_flash(s, name, rows, state="candidate"):
    """Mark several rows in the same instant, the way parallel hardware compares them."""
    grid = s.get(name)
    out = []
    for r in rows:
        out += s.set_mark((name, "row", r), outline(grid.rows[r], state) if state else None)
    return out


# Bits -----------------------------------------------------------------------
@move("bits.show", 1.0)
def bits_show(s, name, zone, rows, reserve=None):
    group = VGroup(*[BitRow(r["label"], r["value"]) for r in rows])
    ghosts = [BitRow("Reserved result row", "0.0.0.0") for _ in range(max(0,(reserve or len(rows))-len(rows)))]
    group.add(*ghosts).arrange(DOWN, buff=0.3, aligned_edge=LEFT)
    place(group, zone)
    group.remove(*ghosts)
    return s.register(name, group, zone) + [FadeIn(group)]


@move("bits.add", 0.8)
def bits_add(s, name, label, value):
    group = s.get(name)
    row = BitRow(label, value)
    ratio = group[0].cells.width / row.cells.width
    row.scale(ratio)
    row.next_to(group[-1], DOWN, buff=0.3, aligned_edge=LEFT)
    group.add(row)
    return [FadeIn(row, shift=DOWN * 0.1)]


@move("bits.draw_mask", 1.2)
def bits_mask(s, name, prefix, rows=None):
    group = s.get(name)
    out = []
    for i, row in enumerate(group):
        if rows is not None and i not in rows:
            continue
        for b, cell in enumerate(row.bits):
            color = LAYER["ip"] if b < prefix else "#39404D"
            out.append(cell[0].animate.set_fill(color, opacity=0.55 if b < prefix else 1))
    ref = group[0]
    a = ref.bits[prefix - 1][0].get_right()
    b = ref.bits[prefix][0].get_left() if prefix < 32 else a
    x = (a[0] + b[0]) / 2
    line = Line([x, group.get_top()[1] + 0.05, 0], [x, group.get_bottom()[1] - 0.05, 0], stroke_color=STATE["now"], stroke_width=5)
    out += s.set_mark((name, "boundary"), line)
    return out


@move("bits.scan", 1.8)
def bits_scan(s, name, label, value):
    """Work out a new row one bit at a time: a line sweeps across, and each result bit lands under it."""
    group = s.get(name)
    row = BitRow(label, value)
    row.scale(group[0].cells.width / row.cells.width)
    row.next_to(group[-1], DOWN, buff=0.3, aligned_edge=LEFT)
    group.add(row)
    top, bottom = group.get_top()[1] + 0.05, group.get_bottom()[1] - 0.05
    x0, x1 = row.cells.get_left()[0], row.cells.get_right()[0]
    line = Line([x0, top, 0], [x0, bottom, 0], stroke_color=STATE["now"], stroke_width=5).set_z_index(6)
    return [FadeIn(row.title), LaggedStart(*[FadeIn(b, shift=DOWN * 0.15) for b in row.bits], lag_ratio=0.06),
            Succession(line.animate.shift(RIGHT * (x1 - x0)), FadeOut(line, run_time=0.1))]


@move("bits.mark", 0.6)
def bits_mark(s, name, row, start, end, state="now"):
    cells = s.get(name)[row].bits[start:end]
    return s.set_mark((name, "range", row), outline(VGroup(*cells), state, buff=0.02) if state else None)


# Sequence and timelines ------------------------------------------------------
@move("seq.show", 0.9)
def seq_show(s, name, zone, lanes, steps=6):
    m = Ladder(zone, lanes, steps)
    return s.register(name, m, zone) + [FadeIn(m)]


@move("seq.msg", 0.9)
def seq_msg(s, name, a, b, text, kind="ip", state=None):
    lad = s.get(name)
    y = lad.slot()
    color = STATE.get(state) if state else LAYER.get(kind, LAYER["data"])
    arrow = Arrow([lad.x[a], y, 0], [lad.x[b], y, 0], buff=0.03, stroke_color=color, stroke_width=4, tip_length=0.18, max_stroke_width_to_length_ratio=20)
    label = T(text, 24).move_to([(lad.x[a] + lad.x[b]) / 2, y + 0.2, 0])
    bg = Rectangle(width=label.width + 0.12, height=label.height + 0.06, fill_color=BG, fill_opacity=0.85, stroke_width=0).move_to(label)
    group = VGroup(arrow, bg, label)
    lad.add(group)
    lad.kitems = getattr(lad, "kitems", []) + [(text, VGroup(arrow, label))]
    return [Create(arrow), FadeIn(bg), FadeIn(label)]


@move("tl.show", 0.9)
def tl_show(s, name, zone, tracks, span, ticks=None):
    m = Tracks(zone, tracks, span, ticks)
    return s.register(name, m, zone) + [FadeIn(m)]


@move("tl.block", 0.7)
def tl_block(s, name, track, start, end, text="", kind="data", state=None):
    tl = s.get(name)
    y, h = tl.row[track]
    x0, x1 = tl.x_of(start), tl.x_of(end)
    color = STATE.get(state) if state else LAYER.get(kind, LAYER["data"])
    box = Rectangle(width=max(x1 - x0, 0.03), height=h, stroke_color=color, stroke_width=2, fill_color=color, fill_opacity=0.35).move_to([(x0 + x1) / 2, y, 0])
    group = VGroup(box)
    if text != "":
        group.add(T(text, 24).move_to(box))
        tl.kitems = getattr(tl, "kitems", []) + [(text, group)]
    tl.add(group)
    return [FadeIn(group)]


# Sieve: a decision, step by step --------------------------------------------
@move("sieve.show", 1.0)
def sieve_show(s, name, zone, rungs, routes, size=30):
    m = Sieve(zone, rungs, routes, size)
    return s.register(name, m, zone) + [FadeIn(m)]


@move("sieve.step", 0.9)
def sieve_step(s, name, rung, keep):
    """Compare one row. Whoever loses stops being considered."""
    m = s.get(name)
    out = s.set_mark((name, "row"), outline(m.rows[rung], "now", buff=0.08))
    for route in list(m.alive):
        if route not in keep:
            col = m.cols[route]
            strike = Line(col[0].get_left() + LEFT * 0.08, col[0].get_right() + RIGHT * 0.08, stroke_color=STATE["error"], stroke_width=5)
            m.add(strike)
            out += [col.animate.set_opacity(0.3), Create(strike)]
    m.alive = [r for r in m.alive if r in keep]
    return out


@move("sieve.win", 0.7)
def sieve_win(s, name, route, unused=()):
    """The survivor wins. Later rows never get looked at."""
    m = s.get(name)
    out = s.set_mark((name, "row"), None) + s.set_mark((name, "win"), outline(m.cols[route], "done", buff=0.1))
    for rung in unused:
        out.append(m.rows[rung].animate.set_opacity(0.3))
    return out


# Byte bars: fragmentation ---------------------------------------------------
@move("bar.show", 1.0)
def bar_show(s, name, zone, total, header=20, unit=8, rows=3):
    m = ByteBar(zone, total, header, unit, rows)
    return s.register(name, m, zone) + [FadeIn(m)]


@move("bar.ruler", 0.9)
def bar_ruler(s, name):
    m = s.get(name)
    m.comb = m.make_comb()
    label = T(f"Each tick: {m.unit} bytes", 26, MUTED).move_to([0, m.top_y - m.bar_h / 2 - 0.34, 0])
    label.align_to([m.right, 0, 0], RIGHT)
    m.add(m.comb, label)
    return [FadeIn(m.comb), FadeIn(label)]


def bar_cut_mark(m, at, color):
    x = m.x_of(at)
    return Line([x, m.top_y + 0.42, 0], [x, m.top_y - 0.42, 0], stroke_color=color, stroke_width=7)


@move("bar.cut", 1.1)
def bar_cut(s, name, at, state="now"):
    """A cut sweeps along the data and lands at a byte position."""
    m = s.get(name)
    line = bar_cut_mark(m, at, STATE[state])
    done = [c.get_x() for c in m.cuts.values()]
    start = max(done) if done else m.x0
    line.shift(LEFT * (line.get_x() - start))
    m.cuts[at] = line
    m.add(line)
    return [line.animate.move_to([m.x_of(at), m.top_y, 0])]


@move("bar.zoom", 1.0)
def bar_zoom(s, name, at, state="now"):
    m = s.get(name)
    m.zoom = m.make_zoom(at, STATE[state])
    m.add(m.zoom)
    return [FadeIn(m.zoom)]


@move("bar.snap", 0.9)
def bar_snap(s, name, at, state="done"):
    """The zoomed cut moves to a legal position."""
    m = s.get(name)
    new = m.zoom_mark(at, STATE[state], m.zoom_y)
    old = m.zoom_marker
    m.zoom.remove(old)
    m.zoom.add(new)
    m.zoom_marker = new
    return [FadeOut(old), FadeIn(new)]


def bar_info_text(m, i, frag):
    seg = m.slices[i]
    info = T(f"offset {frag['offset_units']}, MF {frag['mf']}", 26)
    info.move_to([seg.get_x(), m.row_y(i) - m.bar_h / 2 - 0.2, 0])
    if info.get_right()[0] > m.right:
        info.shift(LEFT * (info.get_right()[0] - m.right))
    if info.get_left()[0] < m.left:
        info.shift(RIGHT * (m.left - info.get_left()[0]))
    return info


@move("bar.slice", 1.2)
def bar_slice(s, name, i, frag, info=True):
    """One fragment drops out of the original and gains its own header."""
    m = s.get(name)
    out = []
    if m.zoom is not None:
        m.remove(m.zoom)
        out.append(FadeOut(m.zoom))
        m.zoom = None
    if len(m.body) > 1:
        label = m.body[1]
        m.body.remove(label)
        out.append(FadeOut(label))
    start, size = frag["offset_bytes"], frag["payload"]
    if start + size < m.data and start + size not in m.cuts:
        line = bar_cut_mark(m, start + size, STATE["now"])
        m.cuts[start + size] = line
        m.add(line)
        out.append(FadeIn(line))
    y = m.row_y(i)
    seg = m.segment(start, size, m.top_y, f"{size} bytes")
    chip = m.header_chip(m.x_of(start) - 0.03, y)
    m.slices[i], m.chips[i] = seg, chip
    m.add(seg, chip)
    m.kitems.append((str(size), seg))
    out += [seg.animate.move_to([seg.get_x(), y, 0]), FadeIn(chip, shift=RIGHT * 0.35)]
    if info:
        # The fragment is still moving, so place its text from where it will land.
        text = bar_info_text(m, i, frag)
        m.infos[i] = text
        m.add(text)
        m.kitems.append((str(frag["offset_units"]), text))
        out.append(FadeIn(text))
    return out


@move("bar.info", 0.5)
def bar_info(s, name, i, frag):
    m = s.get(name)
    text = bar_info_text(m, i, frag)
    m.infos[i] = text
    m.add(text)
    m.kitems.append((str(frag["offset_units"]), text))
    return [FadeIn(text)]


@move("bar.join", 1.2)
def bar_join(s, name):
    """The data slides back together, proving nothing was lost. The extra headers stay behind."""
    m = s.get(name)
    out = [FadeOut(info) for info in m.infos.values()]
    m.remove(*m.infos.values())
    m.infos.clear()
    return out + [seg.animate.move_to([seg.get_x(), m.top_y, 0]) for seg in m.slices.values()] + s.set_mark((name, "whole"), outline(m.body, "done"))


@move("bar.mark", 0.5)
def bar_mark(s, name, what, state="now"):
    """Outline the headers, the whole data bar, or one row's header."""
    m = s.get(name)
    if what == "chips":
        out = []
        for i, chip in m.chips.items():
            out += s.set_mark((name, "chip", i), outline(chip, state) if state else None)
        return out
    return s.set_mark((name, "whole"), outline(m.body, state) if state else None)


@move("bar.span", 0.9)
def bar_span(s, name, to, text):
    """A measure from the start of the data to a byte position: this is what an offset means."""
    m = s.get(name)
    y = m.top_y - m.bar_h / 2 - 0.34
    arrow = Arrow([m.x0, y, 0], [m.x_of(to), y, 0], buff=0, stroke_color=STATE["now"], stroke_width=5, tip_length=0.2, max_tip_length_to_length_ratio=0.2)
    label = T(text, 28, STATE["now"]).next_to(arrow, RIGHT, buff=0.14)
    group = VGroup(arrow, label)
    m.add(group)
    return [Create(arrow), FadeIn(label)]


@move("bar.note", 0.7)
def bar_note(s, name, tex=None, text=None, side="center", state=None):
    m = s.get(name)
    color = STATE.get(state, INK) if state else INK
    if tex:
        note = MathTex(tex, font_size=38, color=color)
        note.kfont, note.kheight = 48, note.height
    else:
        note = T(text, 30, color)
    note.move_to([{"left": -3.4, "right": 3.4, "center": 0}[side], m.note_y, 0])
    m.add(note)
    return [Write(note) if tex else FadeIn(note)]


@move("tl.ghost", 0.7)
def tl_ghost(s, name, track, start, end, text="", state="error"):
    """A trial block, which a later tl.slide can move."""
    tl = s.get(name)
    y, h = tl.row[track]
    x0, x1 = tl.x_of(start), tl.x_of(end)
    color = STATE[state]
    box = Rectangle(width=x1 - x0, height=h, stroke_color=color, stroke_width=3, fill_color=color, fill_opacity=0.25).move_to([(x0 + x1) / 2, y, 0])
    group = VGroup(box, T(text, 24).move_to(box)) if text != "" else VGroup(box)
    tl.ghost = group
    tl.add(group)
    return [FadeIn(group)]


@move("tl.slide", 1.0)
def tl_slide(s, name, start, end, text="", state="done"):
    """The trial block slides to where it belongs."""
    tl = s.get(name)
    y, h = tl.row[next(k for k, v in tl.row.items() if abs(v[0] - tl.ghost.get_y()) < 0.01)]
    x0, x1 = tl.x_of(start), tl.x_of(end)
    color = STATE[state]
    new = VGroup(Rectangle(width=x1 - x0, height=h, stroke_color=color, stroke_width=3, fill_color=color, fill_opacity=0.25).move_to([(x0 + x1) / 2, y, 0]))
    if text != "":
        new.add(T(text, 24).move_to(new[0]))
    tl.remove(tl.ghost)
    tl.add(new)
    old, tl.ghost = tl.ghost, new
    return [old.animate.move_to(new).set_opacity(0), FadeIn(new)]


# Stacks, fields, queues, chips, plots ---------------------------------------
@move("stack.show", 0.9)
def stack_show(s, name, zone, layers, width=None, reserve=0):
    """reserve leaves room above for layers that will be pushed later."""
    m = Stack(layers, width)
    before = m.height
    place(m, zone)
    m.kscale = m.height / max(before, 1e-3)
    m.shift(DOWN * reserve * 0.35 * m.kscale)
    return s.register(name, m, zone) + [FadeIn(m)]


@move("stack.set", 0.8)
def stack_set(s, name, layer, text, kind=None):
    m = s.get(name)
    old = m.blocks[layer]
    k = kind or m.layers_data[layer].get("k", "data")
    new = layer_block(text, k, m.block_w).scale(m.kscale).move_to(old)
    m.layers_data[layer] = {"t": text, "k": k}
    m.blocks.submobjects[layer] = new
    return [FadeOut(old), FadeIn(new)]


@move("stack.push", 0.8)
def stack_push(s, name, text, kind="eth"):
    m = s.get(name)
    new = layer_block(text, kind, m.block_w).scale(m.kscale).next_to(m.blocks[0], UP, buff=0.08 * m.kscale)
    m.blocks.submobjects.insert(0, new)
    m.layers_data.insert(0, {"t": text, "k": kind})
    return [FadeIn(new, shift=DOWN * 0.2)]


@move("stack.pop", 0.7)
def stack_pop(s, name):
    m = s.get(name)
    old = m.blocks.submobjects.pop(0)
    m.layers_data.pop(0)
    return [FadeOut(old, shift=UP * 0.3)]


@move("stack.mark", 0.5)
def stack_mark(s, name, layer, state="now"):
    m = s.get(name)
    return s.set_mark((name, "layer", layer), outline(m.blocks[layer], state) if state else None)


@move("fields.show", 1.0)
def fields_show(s, name, zone, rows, unit=0.2):
    m = Fields(rows, unit)
    place(m, zone)
    return s.register(name, m, zone) + [FadeIn(m)]


@move("fields.mark", 0.5)
def fields_mark(s, name, label, state="now"):
    m = s.get(name)
    return s.set_mark((name, "field", label), outline(m.cell[label], state, buff=0.02) if state else None)


@move("queue.show", 0.8)
def queue_show(s, name, zone, items, kind="data", title=None, cell_w=1.0):
    m = Slots(items, kind, title, cell_w)
    before = m.items.width if len(m.items) else 1
    place(m, zone)
    m.kscale = (m.items.width / before) if len(m.items) else 1
    return s.register(name, m, zone) + [FadeIn(m)]


@move("queue.pop", 0.7)
def queue_pop(s, name):
    m = s.get(name)
    head = m.items.submobjects.pop(-1)
    return [FadeOut(head, shift=RIGHT * 1.0)]


@move("queue.mark", 0.5)
def queue_mark(s, name, i, state="error"):
    m = s.get(name)
    return s.set_mark((name, "slot", i), outline(m.items[i], state) if state else None)


@move("chips.show", 1.1)
def chips_show(s, name, zone, rows, show=None):
    """Chip signals, one row each. Rows past show are placed now and appear later."""
    group = VGroup(*[StepWave(r["label"], r["values"], unit=0.22) for r in rows]).arrange(DOWN, buff=0.16, aligned_edge=RIGHT)
    place(group, zone)
    group.kall = list(group)
    if show is not None:
        group.khidden = list(group[show:])
        for row in group.khidden:
            group.remove(row)
    return s.register(name, group, zone) + ([FadeIn(group)] if len(group) else [])


@move("chips.reveal", 0.8)
def chips_reveal(s, name):
    group = s.get(name)
    row = group.khidden.pop(0)
    group.add(row)
    return [FadeIn(row, shift=DOWN * 0.1)]


@move("chips.flip", 0.9)
def chips_flip(s, name, row, values, label):
    """A sender's bit of minus one turns its code upside down."""
    group = s.get(name)
    old = group.kall[row]
    new = StepWave(label, values, unit=0.22)
    new.scale(old.get_width() / new.get_width()).move_to(old)
    new.shift(RIGHT * (old.get_right()[0] - new.get_right()[0]))
    group.submobjects[group.submobjects.index(old)] = new
    group.kall[row] = new
    return [FadeOut(old), FadeIn(new)]


@move("chips.sum", 1.3)
def chips_sum(s, name):
    """On the air the signals simply add: the waves slide together into the next row."""
    group = s.get(name)
    row = group.khidden.pop(0)
    sources = [r for r in group]
    group.add(row)
    out = [FadeIn(row)]
    for src in sources:
        ghost = src.wave.copy().set_z_index(5)
        out.append(ghost.animate.move_to(row.wave).set_stroke(opacity=0))
    return out


@move("chips.dot", 3.0)
def chips_dot(s, name, a, b, products, total, result):
    """Correlate two rows: walk the chips, multiply each pair, add them up, divide by the code length."""
    group = s.get(name)
    ra, rb = group.kall[a], group.kall[b]
    chip = ra.chip * ra.get_width() / ra.natural_w
    x0 = ra.axis.get_left()[0]
    top, bottom = max(ra.get_top()[1], rb.get_top()[1]), min(ra.get_bottom()[1], rb.get_bottom()[1])
    ring = Rectangle(width=chip, height=top - bottom + 0.08, stroke_color=STATE["now"], stroke_width=4).move_to([x0 + chip / 2, (top + bottom) / 2, 0]).set_z_index(6)
    terms = VGroup()
    y = (rb.get_y() + ra.get_y()) / 2
    x = ra.get_right()[0] + 0.5
    pieces = []
    for i, p in enumerate(products):
        t = T(f"{p:+d}" if i else f"{p}", 30)
        pieces.append(t)
    equals = T(f"= {total}, and {total} ÷ {len(products)} = {result}", 30, STATE["done"])
    row = VGroup(*pieces, equals).arrange(RIGHT, buff=0.18)
    row.move_to([x + row.width / 2, y, 0])
    if row.get_right()[0] > 6.85:
        row.scale((6.85 - x) / row.width).move_to([(x + 6.85) / 2, y, 0])
    # A mark stays on stage, but enters the scene only when each piece fades in.
    s.marks[(name, "dot", b)] = row
    steps = [FadeIn(ring, run_time=0.2), FadeIn(pieces[0], run_time=0.5)]
    for i in range(1, len(products)):
        steps += [ring.animate(run_time=0.4).shift(RIGHT * chip), FadeIn(pieces[i], run_time=0.4)]
    steps += [FadeOut(ring, run_time=0.2), FadeIn(equals, run_time=0.5)]
    return [Succession(*steps)]


@move("plot.show", 1.1)
def plot_show(s, name, zone, xlabel, ylabel, curves, xr=(0, 1), yr=(0, 1)):
    m = Curves(zone, xlabel, ylabel, curves, tuple(xr), tuple(yr))
    return s.register(name, m, zone) + [FadeIn(m)]


@move("plot.mark", 0.6)
def plot_mark(s, name, x, y, text="", state="now"):
    m = s.get(name)
    pt = np.array(m.map(x, y))
    group = VGroup(Dot(pt, radius=0.09, color=STATE[state]))
    if text:
        group.add(T(text, 24).next_to(pt, UP + RIGHT, buff=0.08))
    m.add(group)
    return [FadeIn(group)]


@move("net.port_state", 0.5)
def net_port_state(s, name, device, peer, state):
    n = s.get(name)
    a, b = n.devices[device].anchor(), n.devices[peer].anchor()
    point = a + (b-a)*0.28
    marker = T("×" if state == "discarding" else "→", 26, STATE["error"] if state == "discarding" else STATE["done"]).move_to(point)
    marker.set_z_index(8)
    return s.set_mark((name, "port", device, peer), marker)


def observe_stage(stage):
    result={}
    for name,m in stage.objs.items():
        result[name]={'bounds':[float(m.get_left()[0]),float(m.get_bottom()[1]),float(m.get_right()[0]),float(m.get_top()[1])], 'text':getattr(m,'ktext',None), 'at':getattr(m,'at',None)}
    return result


def check_stage(observation,assertions):
    from course.contracts import Finding
    out=[]
    for a in assertions:
        value=observation.get(a['object'])
        passed=value is None if a['kind']=='absent' else value is not None
        if passed and a['kind']=='equals':passed=value.get(a['field'])==a['value']
        if not passed:out.append(Finding('VISUAL_STATE','error',a['object'],'stage','state assertion failed','Correct scene events'))
    return out
