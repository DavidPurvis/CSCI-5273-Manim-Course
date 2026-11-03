"""Every drill answer, re-solved by a method that shares no code with the models."""
import ipaddress
import itertools
import math

from course.tools import drills

ITEMS = drills.build()


def answers(item):
    return {f["key"]: f["answer"] for f in item["fields"]}


def of_type(key):
    return [i for i in ITEMS if i["type"] == key]


def test_ten_types_of_twenty_five():
    assert len({i["type"] for i in ITEMS}) == 10
    assert len(ITEMS) == 250
    assert len({i["id"] for i in ITEMS}) == 250
    assert len({i["prompt"] for i in ITEMS}) == 250


def test_address_math_against_stdlib():
    for item in of_type("addr"):
        g, a = item["given"], answers(item)
        net = ipaddress.ip_network(f"{g['address']}/{g['prefix']}", strict=False)
        assert a["mask"] == str(net.netmask)
        assert a["network"] == str(net.network_address)
        assert a["broadcast"] == str(net.broadcast_address)
        assert int(a["usable"]) == net.num_addresses - 2


def test_subnet_sizing_by_brute_force():
    for item in of_type("size"):
        hosts, a = item["given"]["hosts"], answers(item)
        best = max(p for p in range(1, 31) if 2 ** (32 - p) - 2 >= hosts)
        assert a["prefix"] == f"/{best}"
        assert int(a["usable"]) == 2 ** (32 - best) - 2


def test_longest_match_by_brute_force():
    for item in of_type("lpm"):
        g, a = item["given"], answers(item)
        dest = ipaddress.ip_address(g["dest"])
        fits = [(ipaddress.ip_network(f"{n}/{p}"), out) for n, p, out in g["routes"] if dest in ipaddress.ip_network(f"{n}/{p}")]
        net, out = max(fits, key=lambda x: x[0].prefixlen)
        assert a["output"] == out
        assert a["winner"] == str(net)


def test_fragments_reassemble():
    for item in of_type("frag"):
        g, a = item["given"], answers(item)
        data = g["total"] - 20
        step = (g["mtu"] - 20) - (g["mtu"] - 20) % 8
        assert int(a["step"]) == step
        count = math.ceil(data / step)
        assert int(a["count"]) == count
        assert int(a["offset"]) == (count - 1) * step // 8
        assert int(a["last"]) == data - (count - 1) * step


def test_switch_learning_by_replay():
    ports = {h: i + 1 for i, h in enumerate("ABCD")}
    for item in of_type("switch"):
        table = {}
        a = answers(item)
        for i, (src, dst) in enumerate(item["given"]["frames"]):
            table[src] = ports[src]
            assert a[f"f{i}"] == (str(table[dst]) if dst in table else "flood")


def test_dijkstra_against_floyd_warshall():
    for item in of_type("dijkstra"):
        edges, a = item["given"]["edges"], answers(item)
        nodes = "ABCDE"
        d = {(x, y): 0 if x == y else math.inf for x in nodes for y in nodes}
        for x, y, c in edges:
            d[x, y] = d[y, x] = c
        for k, i, j in itertools.product(nodes, nodes, nodes):
            d[i, j] = min(d[i, j], d[i, k] + d[k, j])
        for n in "BCDE":
            assert int(a[f"d{n}"]) == d["A", n]
        far = next(f["label"][-1] for f in item["fields"] if f["key"] == "pred")
        w = {(x, y): c for x, y, c in edges} | {(y, x): c for x, y, c in edges}
        assert w[a["pred"], far] + d["A", a["pred"]] == d["A", far]
        assert w["A", a["hop"]] + d[a["hop"], far] == d["A", far]


def test_bellman_ford_by_minimum():
    for item in of_type("bf"):
        a = answers(item)
        totals = {o["via"]: o["link"] + o["advertised"] for o in item["given"]["options"]}
        assert int(a["dist"]) == min(totals.values())
        assert totals[a["hop"]] == min(totals.values())


def test_bgp_by_sorted_tuple_and_export_table():
    allowed = {("customer", "customer"), ("customer", "peer"), ("customer", "provider"), ("peer", "customer"), ("provider", "customer")}
    for item in of_type("bgp"):
        g, a = item["given"], answers(item)
        ordered = sorted(g["routes"], key=lambda r: (-r["lp"], r["len"], r["igp"]))
        assert a["winner"] == ordered[0]["name"]
        assert a["export"] == ("yes" if (g["learned"], g["to"]) in allowed else "no")


def test_cdma_recovers_bits():
    for item in of_type("cdma"):
        g, a = item["given"], answers(item)
        z = [int(x) for x in a["z"].split(",")]
        assert z == [g["d1"] * x + g["d2"] * y for x, y in zip(g["c1"], g["c2"])]
        assert int(a["r1"]) == g["d1"] and int(a["r2"]) == g["d2"]
        assert sum(x * y for x, y in zip(g["c1"], g["c2"])) == 0


def test_rpf_by_comparison():
    for item in of_type("rpf"):
        g, a = item["given"], answers(item)
        if g["expected"] == g["arrival"]:
            assert a["act"] == "forward"
            assert a["ports"] == ",".join(map(str, g["interested"]))
        else:
            assert a["act"] == "drop" and a["ports"] == "none"
