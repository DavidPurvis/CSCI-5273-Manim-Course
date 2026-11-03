"""Longest prefix match, a bitwise trie, and the per-packet lookup budget."""
from .ipv4 import mask, to_int

ROUTES = [("201.10.0.0", 21, "A"), ("201.10.6.0", 23, "B"), ("0.0.0.0", 0, "C")]
DESTINATIONS = ["201.10.6.17", "201.10.4.8", "203.0.113.8"]


def matches(routes, dest):
    d = to_int(dest)
    return [r for r in routes if d & mask(r[1]) == to_int(r[0]) & mask(r[1])]


def lookup(routes, dest):
    found = matches(routes, dest)
    best = max(found, key=lambda r: r[1])
    return {"dest": dest, "matches": [f"{r[0]}/{r[1]}" for r in found], "winner": f"{best[0]}/{best[1]}", "output": best[2]}


class Trie:
    def __init__(self, routes):
        self.root = {}
        for net, plen, out in routes:
            bits, node = f"{to_int(net):032b}"[:plen], self.root
            for b in bits:
                node = node.setdefault(b, {})
            node["route"] = out

    def lookup(self, dest):
        node, best, depth = self.root, self.root.get("route"), 0
        for b in f"{to_int(dest):032b}":
            if b not in node:
                break
            node = node[b]
            depth += 1
            if "route" in node:
                best = node["route"]
        return best, depth


def lookup_budget(rate_bps, packet_bytes):
    pps = rate_bps / (8 * packet_bytes)
    return {"packets_per_second": pps, "ns_per_packet": 1e9 / pps}


def trace():
    res = [lookup(ROUTES, d) for d in DESTINATIONS]
    return {
        "routes": {"cols": ["Prefix", "Output"], "rows": [[f"{n}/{p}", o] for n, p, o in ROUTES]},
        "lookups": res,
        "lookup_table": {"cols": ["Destination", "Matches", "Output"],
                         "rows": [[r["dest"], ", ".join(m.split("/")[1].join(["/", ""]) for m in r["matches"]), r["output"]] for r in res]},
        "budget": lookup_budget(10e9, 64),
    }
