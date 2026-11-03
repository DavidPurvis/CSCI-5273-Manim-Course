"""The lecture's simplified BGP order, export rule, and valley-free classifier."""

CANDIDATES = [{"name": "A", "lp": 140, "len": 4, "igp": 50}, {"name": "B", "lp": 100, "len": 2, "igp": 5},
              {"name": "C", "lp": 100, "len": 2, "igp": 1}]


def select(routes):
    remaining, log = list(routes), []
    for key, label, better in (("lp", "local preference", max), ("len", "AS path length", min), ("igp", "internal cost", min)):
        value = better(r[key] for r in remaining)
        kept = [r for r in remaining if r[key] == value]
        log.append({"step": label, "value": value, "kept": [r["name"] for r in kept]})
        remaining = kept
        if len(remaining) == 1:
            break
    return {"winner": sorted(r["name"] for r in remaining)[0], "log": log}


def may_export(learned_from, to):
    """Would this make me carry traffic between two non-customers?"""
    if learned_from in ("own", "customer"):
        return True
    return to == "customer"


def export_table():
    kinds = ["own", "customer", "peer", "provider"]
    tos = ["customer", "peer", "provider"]
    return {"cols": ["Learned from"] + [f"To {t}" for t in tos],
            "rows": [[k] + ["yes" if may_export(k, t) else "no" for t in tos] for k in kinds]}


# customer -> provider edges and peer edges from lec12 PDF p45.
UP = [(2, 1), (3, 1), (4, 1), ("d", 2), ("d", 3), (5, 4), (6, 4), (7, "d"), (8, "d"), (8, 5)]
PEERS = [(3, 4), ("d", 5), (5, 6)]
SLIDE_PATHS = [[1, 2, "d"], [7, "d"], [5, 8, "d"], [6, 4, 3, "d"], [8, 5, "d"], [6, 5, "d"], [1, 4, 3, "d"]]


def rel(a, b):
    if (a, b) in UP:
        return "up"
    if (b, a) in UP:
        return "down"
    if (a, b) in PEERS or (b, a) in PEERS:
        return "peer"
    raise ValueError(f"no edge {a}-{b}")


def valley_free(path):
    seq = [rel(a, b) for a, b in zip(path, path[1:])]
    phase = 0  # 0 climbing, 1 descending or just peered
    for step in seq:
        if step == "up" and phase:
            return seq, False
        if step == "peer":
            if phase:
                return seq, False
            phase = 1
        if step == "down":
            phase = 1
    return seq, True


def hot_potato(costs):
    return min(costs, key=costs.get)


def resolve_next_hop(bgp, igp):
    return igp[bgp["next_hop"]]


def trace():
    return {
        "all": select(CANDIDATES),
        "a_withdrawn": select(CANDIDATES[1:]),
        "b_shorter": select([CANDIDATES[1] | {"len": 1}, CANDIDATES[2]]),
        "guide_lp": select([{"name": "customer", "lp": 100, "len": 4, "igp": 0}, {"name": "peer", "lp": 90, "len": 2, "igp": 0}]),
        "candidates": {"cols": ["Route", "Local pref", "AS length", "Exit cost"],
                       "rows": [[r["name"], r["lp"], r["len"], r["igp"]] for r in CANDIDATES]},
        "export": export_table(),
        "valley": [{"path": " → ".join(map(str, p)), "seq": ", ".join(valley_free(p)[0]),
                    "valid": valley_free(p)[1]} for p in SLIDE_PATHS],
        "valley_table": {"cols": ["Path", "Sequence", "Result"],
                         "rows": [[" → ".join(map(str, p)), ", ".join(valley_free(p)[0]),
                                   "valid" if valley_free(p)[1] else "invalid"] for p in SLIDE_PATHS]},
        "hot_west": hot_potato({"west": 4, "east": 9}), "hot_east": hot_potato({"west": 12, "east": 3}),
        "next_hop": resolve_next_hop({"prefix": "203.0.113.0/24", "next_hop": "192.0.2.9"},
                                     {"192.0.2.9": {"neighbor": "198.51.100.2", "port": 3}}),
    }
