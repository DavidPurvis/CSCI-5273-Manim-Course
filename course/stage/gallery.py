"""Every component and move on one reel, silent, for judging the look and the color rule."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from manim import Scene

from course.stage.moves import Stage, REGISTRY, resolve
from course.stage.theme import BG

NET = {"L": {"k": "laptop", "at": [0, 0], "l": "Laptop"}, "S": {"k": "switch", "at": [2.6, 0], "l": "Switch"},
       "R": {"k": "router", "at": [5.2, 0], "l": "Router"}, "W": {"k": "server", "at": [7.8, 0], "l": "Server"}}
REEL = [
    ("heading", {"text": "Gallery: the visual language"}),
    ("spine", {"current": "Route", "zone": "top"}), ("q", {"text": "Question cards look like this", "zone": "bottom"}),
    ("clear", {}), ("net.show", {"name": "n", "zone": "top", "nodes": NET, "links": [["L", "S"], ["S", "R"], ["R", "W"]]}),
    ("stack.show", {"name": "st", "zone": "left_bottom", "width": 5.6, "reserve": 1, "layers": [{"t": "IP stays blue", "k": "ip"}]}),
    ("packet.spawn", {"name": "p", "net": "n", "at": "L", "layers": ["ip"]}), ("packet.wrap", {"name": "p", "kind": "eth"}),
    ("stack.push", {"name": "st", "text": "Ethernet is yellow", "kind": "eth"}), ("packet.hop", {"name": "p", "to": ["S", "R"]}),
    ("packet.swap_link_header", {"name": "p"}), ("stack.set", {"name": "st", "layer": 0, "text": "A new yellow envelope", "kind": "eth"}),
    ("stack.mark", {"name": "st", "layer": 1, "state": "done"}), ("packet.peel", {"name": "p"}), ("packet.hop", {"name": "p", "to": "W"}),
    ("net.state", {"name": "n", "nodes": {"S": "now", "R": "done", "W": "candidate"}, "links": [["S", "R", "active"], ["R", "W", "failed"]]}),
    ("net.badge", {"name": "n", "node": "R", "text": "Outlines show state", "side": "up", "state": "done"}),
    ("rule", {"text": "Fills name a layer. Outlines and glows name a state."}),
    ("trap", {"wrong": "The answer that sounds right", "right": "What's actually true"}),
    ("pause", {"text": "this is the prediction banner"}),
    ("card", {"kind": "clarification", "text": "Slide clarifications appear in a card like this.", "zone": "right_bottom"}),
    ("clear", {}), ("bits.show", {"name": "b", "zone": "top", "rows": [{"label": "Address 10.10.1.97", "value": "10.10.1.97"}]}),
    ("bits.draw_mask", {"name": "b", "prefix": 23}), ("bits.add", {"name": "b", "label": "Network", "value": "10.10.0.0"}), ("bits.mark", {"name": "b", "row": 1, "start": 23, "end": 24}),
    ("table.show", {"name": "t", "zone": "left_bottom", "cols": ["MAC", "Port"], "rows": [["A", 1]], "ghost": [["Host", 9]]}),
    ("table.add", {"name": "t", "row": ["B", 2]}), ("table.set", {"name": "t", "r": 0, "c": 1, "v": 3, "state": "now"}), ("table.mark", {"name": "t", "r": 1, "state": "done"}),
    ("queue.show", {"name": "qq", "zone": "right_bottom", "items": ["to 2", "to 1"], "kind": "eth", "title": "A queue"}), ("queue.mark", {"name": "qq", "i": 1}), ("queue.pop", {"name": "qq"}),
    ("clear", {}), ("seq.show", {"name": "s", "zone": "left", "lanes": ["Client", "Server"], "steps": 3}), ("seq.msg", {"name": "s", "a": "Client", "b": "Server", "text": "Request", "kind": "ip"}),
    ("seq.msg", {"name": "s", "a": "Server", "b": "Client", "text": "ACK", "state": "done"}),
    ("tl.show", {"name": "tl", "zone": "right_top", "tracks": ["Sender", "Others"], "span": [0, 10], "ticks": [0, 5, 10]}),
    ("tl.block", {"name": "tl", "track": "Sender", "start": 0, "end": 6, "text": "DATA", "kind": "radio"}), ("tl.block", {"name": "tl", "track": "Others", "start": 3, "end": 7, "text": "defer", "state": "now"}),
    ("fields.show", {"name": "f", "zone": "right_bottom", "unit": 0.17, "rows": [[["Dest", 7], ["Source", 8], ["Tag", 6], ["CRC", 7]]]}), ("fields.mark", {"name": "f", "label": "Tag"}),
    ("clear", {}), ("net.show", {"name": "r", "zone": "full", "spread": [0.6, 1], "nodes": {"A": {"k": "ap", "at": [0, 0], "l": "AP"}, "B": {"k": "phone", "at": [4, 0], "l": "Phone"}, "C": {"k": "tower", "at": [8, 0], "l": "Tower"}, "M": {"k": "box", "at": [4, 3], "l": "MME"}, "H": {"k": "hub", "at": [0, 3], "l": "Hub"}, "N": {"k": "node", "at": [8, 3], "l": "N"}, "K": {"k": "cloud", "at": [8, -3], "l": "AS 100"}}, "links": [["A", "B", {"s": "radio"}], ["B", "C", {"s": "tunnel"}], ["M", "B", {"s": "control"}], ["H", "A", {"s": "up"}]]}),
    ("radio.zone", {"net": "r", "node": "A", "radius": 2.6, "kind": "ip", "name": "z"}), ("radio.pulse", {"net": "r", "node": "C", "radius": 2.6}), ("fx.burst", {"net": "r", "node": "B"}),
    ("net.cost", {"name": "r", "a": "A", "b": "B", "cost": 3}), ("graph.promote", {"name": "r", "node": "N"}), ("net.path", {"name": "r", "path": ["M", "B"], "style": "now"}),
    ("net.unlink", {"name": "r", "a": "A", "b": "B"}), ("net.move", {"name": "r", "node": "B", "to": [6, 0]}), ("net.relink", {"name": "r", "a": "C", "b": "B", "style": "tunnel"}),
    ("clear", {}), ("chips.show", {"name": "c", "zone": "left", "rows": [{"label": "c1", "values": [1, 1, -1, -1]}, {"label": "z", "values": [0, 2, -2, 0]}]}),
    ("plot.show", {"name": "pl", "zone": "right", "xlabel": "SNR", "ylabel": "Errors", "xr": [0, 10], "yr": [0, 10], "curves": [{"name": "a", "k": "radio", "points": [[0, 8], [4, 2], [8, 0.3]]}]}),
    ("plot.mark", {"name": "pl", "x": 4, "y": 2, "text": "works", "state": "done"}),
    ("clear", {}), ("net.show", {"name": "w", "zone": "left", "nodes": {"A": {"k": "node", "at": [0, 1], "l": "A"}, "B": {"k": "node", "at": [3, 2], "l": "B"}, "C": {"k": "node", "at": [3, 0], "l": "C"}}, "links": [["A", "B", {"c": 2}], ["A", "C", {"c": 5}], ["B", "C", {"c": 1}]]}),
    ("net.pulse", {"name": "w", "path": ["A", "B", "C"]}), ("graph.relax", {"name": "w", "via": "B", "node": "C", "text": "3", "side": "down"}), ("net.walk", {"name": "w", "path": ["A", "B", "C"], "state": "done"}),
    ("msg.send", {"name": "w", "a": "C", "b": "A", "text": "3 to Z"}), ("net.badge", {"name": "w", "node": "A", "text": "badge", "side": "left"}), ("net.unbadge", {"name": "w", "node": "A"}), ("net.unwalk", {"name": "w"}),
    ("sieve.show", {"name": "sv", "zone": "right", "rungs": ["Local pref", "AS length"], "routes": [{"name": "A", "vals": [100, 4]}, {"name": "B", "vals": [90, 2]}]}),
    ("sieve.step", {"name": "sv", "rung": 0, "keep": ["A"]}), ("sieve.win", {"name": "sv", "route": "A", "unused": [1]}),
    ("clear", {}), ("bar.show", {"name": "bb", "zone": "full", "total": 4000, "rows": 3}), ("bar.cut", {"name": "bb", "at": 1480}), ("bar.ruler", {"name": "bb"}),
    ("bar.zoom", {"name": "bb", "at": 1484, "state": "error"}), ("bar.snap", {"name": "bb", "at": 1480}),
    ("bar.slice", {"name": "bb", "i": 0, "frag": {"offset_bytes": 0, "payload": 1480, "offset_units": 0, "mf": 1}}),
    ("bar.slice", {"name": "bb", "i": 1, "frag": {"offset_bytes": 1480, "payload": 1480, "offset_units": 185, "mf": 1}, "info": False}),
    ("bar.info", {"name": "bb", "i": 1, "frag": {"offset_bytes": 1480, "payload": 1480, "offset_units": 185, "mf": 1}}),
    ("bar.join", {"name": "bb"}), ("bar.note", {"name": "bb", "text": "Nothing was lost", "state": "done"}),
    ("clear", {}), ("text", {"name": "x", "zone": "top", "lines": ["Plain text blocks"]}), ("tex", {"name": "y", "zone": "bottom", "tex": r"D(v)\leftarrow\min(D(v),\,D(w)+c(w,v))"}),
    ("bullets", {"name": "z", "zone": "bottom", "show": 1, "items": ["Bullets reveal one by one", "Like this"]}), ("reveal", {"name": "z"}),
]


class Gallery(Scene):
    def construct(self):
        self.camera.background_color = BG
        stage = Stage(self)
        for name, args in REEL:
            anims = REGISTRY[name]["fn"](stage, **resolve(dict(args)))
            if anims:
                self.play(*anims, run_time=REGISTRY[name]["t"])
                live = set()
                for mob in list(stage.objs.values()) + list(stage.marks.values()):
                    live.update(id(m) for m in mob.get_family())
                dead = [m for m in self.mobjects if id(m) not in live]
                if dead:
                    self.remove(*dead)
                self.wait(0.5)
        self.wait(1)
