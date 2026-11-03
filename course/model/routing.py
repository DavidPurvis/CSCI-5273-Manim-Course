"""Dijkstra, synchronous distance vector, path vector and MPLS swapping."""
import math

SMALL = {("A", "B"): 2, ("A", "C"): 5, ("B", "C"): 1, ("B", "D"): 4, ("C", "D"): 2}
SMALL_CHANGED = {**SMALL, ("B", "C"): 6}
SLIDE_26 = {("u", "v"): 4, ("u", "w"): 3, ("v", "y"): 1, ("v", "x"): 4, ("x", "w"): 1, ("x", "z"): 1,
            ("x", "t"): 5, ("y", "z"): 1, ("w", "s"): 1, ("s", "t"): 2}


SLIDE_27 = {("A", "B"): 2, ("A", "C"): 4, ("A", "D"): 5, ("B", "D"): 2, ("B", "E"): 7, ("B", "F"): 12, ("C", "D"): 1, ("C", "G"): 4,
            ("D", "E"): 4, ("D", "G"): 3, ("E", "G"): 1, ("E", "H"): 5, ("F", "H"): 3, ("G", "H"): 7}


def adjacency(edges):
    adj = {}
    for (a, b), c in edges.items():
        adj.setdefault(a, {})[b] = c
        adj.setdefault(b, {})[a] = c
    return adj


def fmt(x):
    return "∞" if x == math.inf else x


def dijkstra(edges, src):
    adj = adjacency(edges)
    dist = {n: math.inf for n in adj}
    pred = {}
    dist[src] = 0
    settled, steps = [], []
    while len(settled) < len(adj):
        w = min((n for n in adj if n not in settled), key=lambda n: (dist[n], n))
        settled.append(w)
        relaxed = []
        for v, c in sorted(adj[w].items()):
            if v not in settled and dist[w] + c < dist[v]:
                relaxed.append({"node": v, "old": fmt(dist[v]), "new": dist[w] + c, "via": w})
                dist[v] = dist[w] + c
                pred[v] = w
        steps.append({"settle": w, "relaxed": relaxed, "dist": {k: fmt(v) for k, v in dist.items()},
                      "settled": list(settled), "pred": dict(pred)})
    return {"steps": steps, "dist": dist, "pred": pred, "paths": {n: path_to(pred, src, n) for n in adj},
            "first_hop": {n: path_to(pred, src, n)[1] for n in adj if n != src}}


def path_to(pred, src, n):
    out = [n]
    while out[-1] != src:
        out.append(pred[out[-1]])
    return out[::-1]


def path_cost(edges, path):
    adj = adjacency(edges)
    return sum(adj[a][b] for a, b in zip(path, path[1:]))


def dijkstra_table(result, order):
    rows = []
    for s in result["steps"]:
        rows.append([s["settle"]] + [s["dist"][n] for n in order])
    return {"cols": ["Settled"] + [f"D({n})" for n in order], "rows": rows}


def dv_rounds(edges, node_order=None):
    """Synchronous rounds: every update reads only the previous round's vectors."""
    adj = adjacency(edges)
    nodes = node_order or sorted(adj)
    table = {n: {m: (0 if n == m else adj[n].get(m, math.inf)) for m in nodes} for n in nodes}
    rounds = [{n: dict(table[n]) for n in nodes}]
    while True:
        new = {}
        for x in nodes:
            new[x] = {}
            for y in nodes:
                new[x][y] = 0 if x == y else min(adj[x][v] + table[v][y] for v in adj[x])
        if new == table:
            return rounds
        table = new
        rounds.append({n: dict(table[n]) for n in nodes})


def bf_update(options):
    best = min(options, key=lambda o: o["link"] + o["advertised"])
    return {"via": best["via"], "total": best["link"] + best["advertised"],
            "totals": {o["via"]: o["link"] + o["advertised"] for o in options}}


def path_vector_accept(me, path):
    return me not in path


def mpls_swap(table, label):
    path = []
    for hop in table:
        entry = hop["swap"][label]
        path.append({"router": hop["router"], "in": label, "out": entry})
        label = entry
    return path


MPLS_PATH = [{"router": "R1", "swap": {17: 42}}, {"router": "R2", "swap": {42: 8}}, {"router": "R3", "swap": {8: "pop"}}]


def trace():
    small = dijkstra(SMALL, "A")
    changed = dijkstra(SMALL_CHANGED, "A")
    slide = dijkstra(SLIDE_26, "t")
    rounds = dv_rounds(SMALL)
    return {
        "small": small["steps"], "small_paths": small["paths"], "small_first_hop": small["first_hop"],
        "small_pred": small["pred"], "small_table": dijkstra_table(small, ["B", "C", "D"]),
        "changed_dist": changed["dist"], "changed_first_hop": changed["first_hop"], "changed_paths": changed["paths"],
        "slide26_path": slide["paths"]["v"], "slide26_cost": slide["dist"]["v"], "slide26_first_hop": slide["first_hop"]["v"],
        "slide26_alt_direct": path_cost(SLIDE_26, ["t", "x", "z", "y", "v"]),
        "slide26_alt_via_x": path_cost(SLIDE_26, ["t", "s", "w", "x", "v"]),
        "dv_rounds_A": [{k: fmt(v) for k, v in r["A"].items()} for r in rounds],
        "dv_table_A": {"cols": ["Round", "D(B)", "D(C)", "D(D)"],
                       "rows": [[i + 1] + [fmt(r["A"][n]) for n in "BCD"] for i, r in enumerate(rounds)]},
        "bf_first": bf_update([{"via": "B", "link": 3, "advertised": 3}, {"via": "C", "link": 2, "advertised": 5}]),
        "bf_second": bf_update([{"via": "B", "link": 3, "advertised": 10}, {"via": "C", "link": 2, "advertised": 5}]),
        "pv_reject": path_vector_accept(1, [3, 2, 1]), "pv_accept": path_vector_accept(4, [3, 2, 1]),
        "mpls": mpls_swap(MPLS_PATH, 17),
        "slide27_dist": dijkstra(SLIDE_27, "A")["dist"],
        "slide27_table": {"cols": ["Node", "B", "C", "D", "G", "E", "H", "F"],
                          "rows": [["Distance"] + [dijkstra(SLIDE_27, "A")["dist"][n] for n in "BCDGEHF"]]},
    }
