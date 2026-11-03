"""Failure dynamics: count to infinity, poison reverse, and stable-path solving."""
import itertools


def count_to_infinity(steps=4, poison=False, infinity=None):
    """X-Y-Z chain after X-Y fails. Y and Z alternate, believing each other's stale value."""
    y, z = 1, 2
    rows = [{"event": "before cut", "Y": y, "Z": z, "depends": "Z on Y"}]
    if poison:
        import math
        distance = {'Y': y, 'Z': z}
        next_hop = {'Y': 'X', 'Z': 'Y'}
        advertised = math.inf if next_hop['Z'] == 'Y' else distance['Z']
        distance['Y'] = 1 + advertised
        rows.append({"event": "Y hears Z say ∞", "Y": "∞" if distance['Y'] == math.inf else distance['Y'], "Z": distance['Z'], "depends": "Y has no route", "sender": "Z", "recipient": "Y", "advertised": "∞", "dependency": "Z via Y"})
        distance['Z'] = 1 + distance['Y']
        rows.append({"event": "Z hears Y say ∞", "Y": "∞", "Z": "∞" if distance['Z'] == math.inf else distance['Z'], "depends": "none: both know", "sender": "Y", "recipient": "Z", "advertised": "∞", "dependency": "no valid route"})
        return rows
    for i in range(steps):
        if i % 2 == 0:
            y = z + 1
            event, dep = f"Y hears Z={z}", "Y on Z"
        else:
            z = y + 1
            event, dep = f"Z hears Y={y}", "Z on Y"
        ey, ez = y, z
        if infinity:
            ey, ez = min(y, infinity), min(z, infinity)
        rows.append({"event": event, "Y": ey, "Z": ez, "depends": dep})
        if infinity and min(y, z) >= infinity:
            break
    return rows


def rip_rounds():
    return count_to_infinity(steps=40, infinity=16)


def link_cost_change(new_xy, xy=4, yz=1, xz=50):
    """Slide topology: distances to X for Y and Z, updating alternately after X-Y changes."""
    y, z = xy, yz + xy
    rows = [{"Y": y, "Z": z}]
    steps = 0
    while True:
        new_y = min(new_xy, yz + z)
        changed = new_y != y
        y = new_y
        rows.append({"Y": y, "Z": z})
        new_z = min(xz, yz + y)
        changed = changed or new_z != z
        z = new_z
        rows.append({"Y": y, "Z": z})
        steps += 1
        if not changed:
            return {"rows": rows[:-2] if len(rows) > 3 else rows, "exchanges": steps - 1, "final_y": y, "final_z": z}


def convergence_total(stages):
    return sum(stages.values())


EXPLORATION = [(2, 0), (2, 1, 0), (2, 3, 0), (2, 1, 3, 0), None]


def path_available(node, path, chosen):
    """A permitted path is available only if the next hop has chosen exactly its suffix."""
    if len(path) == 2:
        return True
    return chosen.get(path[1]) == path[1:]


def is_stable(permitted, chosen):
    for node, ranked in permitted.items():
        best = next((p for p in ranked if path_available(node, p, chosen)), None)
        if chosen.get(node) != best:
            return False
    return True


def solve_spp(permitted):
    """Exhaustive search over every path assignment, including 'no path'."""
    nodes = sorted(permitted)
    options = [list(permitted[n]) + [None] for n in nodes]
    return [dict(zip(nodes, combo)) for combo in itertools.product(*options)
            if is_stable(permitted, dict(zip(nodes, combo)))]


def s(*x):
    return tuple(x)


SLIDE_30 = {1: [s(1, 3, 0), s(1, 0)], 2: [s(2, 1, 0), s(2, 0)], 3: [s(3, 0)],
            4: [s(4, 2, 0), s(4, 3, 0)], 5: [s(5, 2, 1, 0)]}
DISAGREE = {1: [s(1, 2, 0), s(1, 0)], 2: [s(2, 1, 0), s(2, 0)]}
BAD_GADGET = {1: [s(1, 3, 0), s(1, 0)], 2: [s(2, 1, 0), s(2, 0)], 3: [s(3, 2, 0), s(3, 0)]}


def label(path):
    return "none" if path is None else "".join(str(x) for x in path)


def trace():
    sol = solve_spp(SLIDE_30)
    return {
        "stages_ms": {"detect": 30, "propagate": 10, "compute": 5, "install": 15},
        "stages_total": convergence_total({"detect": 30, "propagate": 10, "compute": 5, "install": 15}),
        "cti": count_to_infinity(4), "poison": count_to_infinity(poison=True),
        "cti_table": {"cols": ["Event", "Y to X", "Z to X", "Depends"],
                      "rows": [[r["event"], r["Y"], r["Z"], r["depends"]] for r in count_to_infinity(4)]},
        "poison_table": {"cols": ["Event", "Y to X", "Z to X"],
                         "rows": [[r["event"], r["Y"], r["Z"]] for r in count_to_infinity(poison=True)]},
        "rip_final": rip_rounds()[-1],
        "good_news": link_cost_change(1), "bad_news_final": {k: v for k, v in link_cost_change(60).items() if k != "rows"},
        "bad_news_start": [r for r in link_cost_change(60)["rows"][:6]],
        "exploration": [label(p) for p in EXPLORATION],
        "slide30_solutions": [{k: label(v) for k, v in x.items()} for x in sol],
        "disagree_solutions": [{k: label(v) for k, v in x.items()} for x in solve_spp(DISAGREE)],
        "bad_gadget_solutions": [{k: label(v) for k, v in x.items()} for x in solve_spp(BAD_GADGET)],
    }
