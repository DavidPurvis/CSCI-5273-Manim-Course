"""Anycast selection, membership timing, tree objectives, RPF and SPT switchover."""
from .routing import dijkstra

TRIANGLE = {("A", "B"): 1, ("B", "C"): 1, ("A", "C"): 1.5}
ANYCAST = [{"via": "192.168.0.1", "distance": 1, "instance": "A"}, {"via": "192.168.0.2", "distance": 2, "instance": "B"}]


def anycast_pick(routes, failed=()):
    live = [r for r in routes if r["instance"] not in failed]
    return min(live, key=lambda r: r["distance"])["instance"]


def link_load(stream_mbps, receivers, multicast):
    return stream_mbps * (1 if multicast else receivers)


def suppression(delays):
    first = min(delays, key=delays.get)
    return {"reporter": first, "at": delays[first], "suppressed": sorted(h for h in delays if h != first)}


def membership_timers(query=125, response=10, robustness=2):
    return {"slide_formula": robustness * (query + response), "rfc2236": robustness * query + response}


def prim(edges, start):
    nodes = {n for e in edges for n in e}
    tree, chosen = {start}, []
    while tree != nodes:
        e = min((e for e in edges if (e[0] in tree) != (e[1] in tree)), key=lambda e: (edges[e], e))
        chosen.append(e)
        tree |= set(e)
    return chosen


def kruskal(edges):
    parent = {n: n for e in edges for n in e}

    def find(x):
        while parent[x] != x:
            x = parent[x]
        return x
    chosen = []
    for e in sorted(edges, key=lambda e: (edges[e], e)):
        a, b = find(e[0]), find(e[1])
        if a != b:
            parent[a] = b
            chosen.append(e)
    return chosen


def rpf(expected_port, arrival_port):
    return expected_port == arrival_port


def prune_recursive(children, interested, node):
    """Keep a branch only when it, or some descendant, has interest."""
    kept = [c for c in children.get(node, []) if prune_recursive(children, interested, c)]
    return node in interested or bool(kept)


def spt_saving(s_rp, rp_r, s_r):
    return {"shared": s_rp + rp_r, "source": s_r, "saving": s_rp + rp_r - s_r}


def trace():
    return {
        "anycast_normal": anycast_pick(ANYCAST), "anycast_failover": anycast_pick(ANYCAST, ["A"]),
        "unicast_10": link_load(10, 3, False), "multicast_10": link_load(10, 3, True),
        "suppress": suppression({"H1": 2, "H2": 6}), "suppress3": suppression({"H1": 2, "H2": 5, "H3": 8}),
        "timers": membership_timers(),
        "prim": ["".join(e) for e in prim(TRIANGLE, "A")], "kruskal": ["".join(e) for e in kruskal(TRIANGLE)],
        "mst_total": sum(TRIANGLE[e] for e in kruskal(TRIANGLE)),
        "spt_to_c": dijkstra(TRIANGLE, "A")["dist"]["C"], "spt_path": dijkstra(TRIANGLE, "A")["paths"]["C"],
        "rpf_pass": rpf(1, 1), "rpf_fail": rpf(1, 3),
        "switchover": spt_saving(8, 7, 4),
        "group_range": "224.0.0.0/4",
    }
