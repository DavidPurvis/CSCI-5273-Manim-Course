"""Pre-generate calculation drills from the tested models. The browser only compares answers; it never does networking math."""
import itertools
import json
import math
import random

from course.model import bgp, ethernet, ipv4, lpm, multicast, routing, subnet, wireless
from course.stage.card import ROOT

PER_TYPE = 25
OUT = ROOT / "sources" / "drills.json"


def field(key, label, answer, options=None):
    f = {"key": key, "label": label, "answer": str(answer)}
    if options:
        f["options"] = options
    return f


def address_math(rng):
    prefix = rng.choice([p for p in range(17, 30) if p not in (24,)])
    addr = f"{rng.choice([10, 172, 192])}.{rng.randrange(0, 255)}.{rng.randrange(0, 255)}.{rng.randrange(1, 254)}"
    info = ipv4.decode(addr, prefix)
    host_bits = 32 - prefix
    octet = (prefix - 1) // 8
    block = 2 ** ((octet + 1) * 8 - prefix)
    value = int(addr.split(".")[octet])
    start = value // block * block
    return {"prompt": f"For {addr}/{prefix}, give the mask, network, broadcast, and conventional usable count.",
            "fields": [field("mask", "Mask", info["mask"]), field("network", "Network", info["network"]),
                       field("broadcast", "Broadcast", info["broadcast"]), field("usable", "Usable addresses", info["usable"])],
            "steps": [f"/{prefix} leaves {host_bits} host bits, so the mask is {info['mask']}.",
                      f"The boundary is in byte {octet + 1}, with a block size of {block}. {value} falls in the block starting at {start}.",
                      f"Network {info['network']}, broadcast {info['broadcast']}.",
                      f"Usable: 2^{host_bits} − 2 = {info['usable']}."],
            "given": {"address": addr, "prefix": prefix}}


def subnet_sizing(rng):
    hosts = rng.choice([rng.randrange(3, 30), rng.randrange(30, 300), rng.randrange(300, 3000), 2 ** rng.randrange(3, 11) - rng.choice([0, 1, 2, 3])])
    h = subnet.host_bits(hosts)
    return {"prompt": f"A department needs {hosts} conventional host addresses. What is the longest prefix that fits, and how many usable addresses does it give?",
            "fields": [field("prefix", "Prefix length", f"/{32 - h}"), field("usable", "Usable addresses", 2 ** h - 2)],
            "steps": [f"Find the smallest h with 2^h − 2 ≥ {hosts}.",
                      f"h = {h}, because 2^{h} − 2 = {2 ** h - 2}" + (f", while 2^{h - 1} − 2 = {2 ** (h - 1) - 2} is too small." if h > 1 else "."),
                      f"Prefix = 32 − {h} = /{32 - h}."],
            "given": {"hosts": hosts}}


def longest_match(rng):
    a, b, c = rng.randrange(1, 223), rng.randrange(0, 255), rng.randrange(0, 240)
    base = f"{a}.{b}.{c}.0"
    outs = rng.sample("ABCDE", 4)
    p1 = rng.choice([12, 14, 16])
    p2 = rng.choice([18, 19, 20])
    p3 = rng.choice([21, 22, 23, 24])
    routes = [(subnet.normalize(base, p1), p1, outs[0]), (subnet.normalize(base, p2), p2, outs[1]),
              (subnet.normalize(base, p3), p3, outs[2]), ("0.0.0.0", 0, outs[3])]
    rng.shuffle(routes)
    want = rng.choice([0, 12, 18, 21])
    # Aim the destination so that the winning prefix varies from problem to problem.
    target = next((r for r in sorted(routes, key=lambda r: r[1]) if r[1] >= want), routes[0])
    span = 2 ** (32 - target[1]) if target[1] else 2 ** 32
    start = ipv4.to_int(target[0])
    dest = None
    for _ in range(200):
        candidate = ipv4.to_dotted(start + rng.randrange(1, span - 1))
        if lpm.lookup(routes, candidate)["winner"] == f"{target[0]}/{target[1]}":
            dest = candidate
            break
    dest = dest or ipv4.to_dotted(start + 1)
    result = lpm.lookup(routes, dest)
    table = "; ".join(f"{r[0]}/{r[1]} → {r[2]}" for r in routes)
    return {"prompt": f"Routes: {table}. Which output does {dest} use?",
            "fields": [field("output", "Output", result["output"]), field("winner", "Winning prefix", result["winner"])],
            "steps": [f"{dest} matches: {', '.join(result['matches'])}.", f"The longest match is {result['winner']}, so the output is {result['output']}."],
            "given": {"routes": routes, "dest": dest}}


def fragmentation(rng):
    mtu = rng.choice([576, 620, 1000, 1006, 1280, 1500])
    total = rng.randrange(mtu + 100, mtu * 4, 4)
    frags = ipv4.fragment(total, 20, mtu)
    last = frags[-1]
    step = (mtu - 20) // 8 * 8
    return {"prompt": f"A {total}-byte IPv4 datagram with a 20-byte header crosses a link with MTU {mtu}. Give the fragment count, the largest nonfinal payload, and the last fragment's payload and offset.",
            "fields": [field("count", "Fragments", len(frags)), field("step", "Largest nonfinal payload", step),
                       field("last", "Last payload", last["payload"]), field("offset", "Last offset (8-byte units)", last["offset_units"])],
            "steps": [f"Data = {total} − 20 = {total - 20} bytes.", f"Nonfinal payload = ⌊({mtu} − 20) / 8⌋ × 8 = {step}.",
                      "Payloads: " + ", ".join(str(f["payload"]) for f in frags) + ".",
                      "Offsets: " + ", ".join(str(f["offset_units"]) for f in frags) + ". Only the last has MF = 0."],
            "given": {"total": total, "mtu": mtu}}


def switch_learning(rng):
    hosts = {h: i + 1 for i, h in enumerate("ABCD")}
    frames = []
    for _ in range(4):
        src, dst = rng.sample("ABCD", 2)
        frames.append({"src": src, "dst": dst, "in_port": hosts[src]})
    frames[0]["all_ports"] = [1, 2, 3, 4]
    events = ethernet.learning_switch(frames)
    fields, steps = [], []
    for i, e in enumerate(events):
        answer = "flood" if e["action"] == "flood" else e["out_ports"][0]
        fields.append(field(f"f{i}", f"{e['src']}→{e['dst']} goes to", answer))
        steps.append(f"{e['src']}→{e['dst']}: learn {e['src']} on port {e['in_port']}. " +
                     (f"{e['dst']} unknown, flood ports {', '.join(map(str, e['out_ports']))}." if e["action"] == "flood" else f"{e['dst']} known, forward to port {e['out_ports'][0]}."))
    return {"prompt": "A switch starts empty. A, B, C, D are on ports 1, 2, 3, 4. Frames arrive in this order: " +
                      ", ".join(f"{e['src']}→{e['dst']}" for e in events) + ". For each, type flood or the output port.",
            "fields": fields, "steps": steps, "given": {"frames": [(e["src"], e["dst"]) for e in events]}}


def _shortest_paths_unique(edges, src):
    adj = routing.adjacency(edges)
    result = routing.dijkstra(edges, src)
    for n in adj:
        if n == src:
            continue
        ways = sum(1 for m, c in adj[n].items() if result["dist"].get(m, math.inf) + c == result["dist"][n])
        if ways != 1:
            return False
    return True


def dijkstra(rng):
    nodes = "ABCDE"
    while True:
        edges = {(a, b): rng.randrange(1, 10) for a, b in itertools.combinations(nodes, 2) if rng.random() < 0.65}
        if len({n for e in edges for n in e}) < 5:
            continue
        try:
            result = routing.dijkstra(edges, "A")
        except KeyError:
            continue
        if math.inf in result["dist"].values() or not _shortest_paths_unique(edges, "A"):
            continue
        break
    far = max("BCDE", key=lambda n: (len(result["paths"][n]), n))
    listing = ", ".join(f"{a}–{b}={c}" for (a, b), c in sorted(edges.items()))
    fields = [field(f"d{n}", f"Distance to {n}", result["dist"][n]) for n in "BCDE"]
    fields += [field("pred", f"Predecessor of {far}", result["pred"][far]), field("hop", f"A's first hop toward {far}", result["first_hop"][far])]
    steps = [f"Settle {s['settle']}: " + ("; ".join(f"{r['node']} {r['old']}→{r['new']}" for r in s["relaxed"]) or "no change") for s in result["steps"]]
    steps.append(f"Path to {far}: {'–'.join(result['paths'][far])}.")
    return {"prompt": f"Undirected edges: {listing}. Run Dijkstra from A.", "fields": fields, "steps": steps, "given": {"edges": [[a, b, c] for (a, b), c in edges.items()]}}


def bellman_ford(rng):
    names = rng.sample("KLMNPQ", 3)
    while True:
        options = [{"via": v, "link": rng.randrange(1, 12), "advertised": rng.randrange(1, 15)} for v in names]
        totals = [o["link"] + o["advertised"] for o in options]
        if totals.count(min(totals)) == 1:
            break
    result = routing.bf_update(options)
    listing = "; ".join(f"neighbor {o['via']}: link {o['link']}, advertises {o['advertised']}" for o in options)
    return {"prompt": f"Router X hears about destination Z. {listing}. What are X's distance and next hop?",
            "fields": [field("dist", "Distance", result["total"]), field("hop", "Next hop", result["via"])],
            "steps": ["Add each link cost to that neighbor's advertised distance: " + ", ".join(f"via {k} = {v}" for k, v in result["totals"].items()) + ".",
                      f"The minimum is {result['total']} via {result['via']}. X trusts what its neighbors advertise; it doesn't see the path behind them."],
            "given": {"options": options}}


def bgp_selection(rng):
    while True:
        routes = [{"name": n, "lp": rng.choice([80, 100, 100, 120, 150]), "len": rng.randrange(1, 6), "igp": rng.randrange(1, 30)} for n in "ABC"]
        result = bgp.select(routes)
        key = sorted((-r["lp"], r["len"], r["igp"]) for r in routes)
        if key[0] != key[1]:
            break
    deciding = result["log"][-1]["step"]
    learned = rng.choice(["customer", "peer", "provider"])
    to = rng.choice(["customer", "peer", "provider"])
    allowed = "yes" if bgp.may_export(learned, to) else "no"
    listing = "; ".join(f"{r['name']}: local pref {r['lp']}, AS length {r['len']}, internal cost {r['igp']}" for r in routes)
    steps = [f"{s['step'].capitalize()}: best is {s['value']}, keeps {', '.join(s['kept'])}." for s in result["log"]]
    steps.append(f"Export: a route learned from a {learned} " + ("may" if allowed == "yes" else "may not") + f" go to a {to}. Customer routes go everywhere; peer and provider routes go only to customers.")
    return {"prompt": f"Routes to one prefix. {listing}. Which wins, and what decides it? Separately, may a route learned from a {learned} be exported to a {to}?",
            "fields": [field("winner", "Winner", result["winner"]),
                       field("step", "Deciding attribute", deciding, ["local preference", "AS path length", "internal cost"]),
                       field("export", "Export allowed?", allowed, ["yes", "no"])],
            "steps": steps, "given": {"routes": routes, "learned": learned, "to": to}}


WALSH = [(1, 1, 1, 1), (1, 1, -1, -1), (1, -1, 1, -1), (1, -1, -1, 1)]


def cdma(rng):
    c1, c2 = rng.sample(WALSH, 2)
    s1, s2 = rng.choice([1, -1]), rng.choice([1, -1])
    c1, c2 = tuple(s1 * x for x in c1), tuple(s2 * x for x in c2)
    d1, d2 = rng.choice([1, -1]), rng.choice([1, -1])
    z = wireless.cdma_sum([(d1, c1), (d2, c2)])
    r1, r2 = wireless.cdma_decode(z, c1), wireless.cdma_decode(z, c2)
    return {"prompt": f"c1 = {c1}, c2 = {c2}, d1 = {d1:+d}, d2 = {d2:+d}. Give the summed chip vector and recover both bits by correlation.",
            "fields": [field("z", "z (comma separated)", ",".join(map(str, z))), field("r1", "Recovered d1", f"{int(r1):+d}"), field("r2", "Recovered d2", f"{int(r2):+d}")],
            "steps": [f"z = d1·c1 + d2·c2 = {z}.", f"d1 = (z·c1)/(c1·c1) = {wireless.dot(z, c1)}/4 = {int(r1):+d}.", f"d2 = (z·c2)/(c2·c2) = {wireless.dot(z, c2)}/4 = {int(r2):+d}."],
            "given": {"c1": c1, "c2": c2, "d1": d1, "d2": d2}}


def reverse_path(rng):
    ports = [1, 2, 3, 4, 5]
    expected = rng.choice(ports)
    arrival = rng.choice([expected, expected, rng.choice(ports)])
    others = [p for p in ports if p != arrival]
    interested = sorted(rng.sample(others, rng.randrange(1, 4)))
    passed = multicast.rpf(expected, arrival)
    out = ",".join(map(str, interested)) if passed else "none"
    return {"prompt": f"A multicast router's route back to source S uses port {expected}. A packet from S arrives on port {arrival}. Ports {', '.join(map(str, interested))} have interested receivers. Forward or drop, and to which ports? (Type none if dropped.)",
            "fields": [field("act", "Decision", "forward" if passed else "drop", ["forward", "drop"]), field("ports", "Output ports", out)],
            "steps": [f"The packet arrived on port {arrival}, and the unicast route to S uses port {expected}.",
                      f"Reverse path check {'passes' if passed else 'fails'}: " + (f"forward on {out}." if passed else "drop it as a likely duplicate.")],
            "given": {"expected": expected, "arrival": arrival, "interested": interested}}


TYPES = [("addr", "Address math", "7.2", address_math), ("size", "Subnet sizing", "8.1", subnet_sizing), ("lpm", "Longest prefix match", "8.2", longest_match),
         ("frag", "Fragmentation", "7.4", fragmentation), ("switch", "Switch learning", "6.3", switch_learning), ("dijkstra", "Dijkstra", "10.1", dijkstra),
         ("bf", "Bellman-Ford update", "10.2", bellman_ford), ("bgp", "BGP selection and export", "12.2", bgp_selection), ("cdma", "CDMA", "14.2", cdma),
         ("rpf", "Reverse path forwarding", "13.4", reverse_path)]


def build():
    out = []
    for key, title, dish, make in TYPES:
        rng = random.Random(f"csci5273-{key}")
        seen = set()
        n = 0
        while n < PER_TYPE:
            p = make(rng)
            if p["prompt"] in seen:
                continue
            seen.add(p["prompt"])
            n += 1
            out.append(dict(p, id=f"{key}-{n:02}", type=key, title=title, dish=dish))
    return out


def main():
    items = build()
    OUT.write_text(json.dumps(items, indent=0, ensure_ascii=False, default=list))
    print(f"{len(items)} problems in {len(TYPES)} types")


if __name__ == "__main__":
    main()
