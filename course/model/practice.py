"""The generated practice midterm and warm-up, worked by the course's own models. This is practice, not the instructor's exam."""
from . import bgp, convergence, ethernet, ipv4, lpm, multicast, routing, wireless

Q5_ROUTES = [("10.0.0.0", 8, "A"), ("10.4.0.0", 16, "B"), ("10.4.8.0", 21, "C"), ("0.0.0.0", 0, "D")]
Q5_DESTS = ["10.4.9.7", "10.4.20.1", "10.8.1.2", "192.0.2.8"]
Q9_EDGES = {("A", "B"): 2, ("A", "C"): 6, ("B", "C"): 1, ("B", "D"): 5, ("C", "D"): 2}
Q18_C1, Q18_C2 = (1, 1, -1, -1), (1, -1, 1, -1)
WARM_ROUTES = [("192.168.0.0", 16, "A"), ("192.168.32.0", 21, "B"), ("192.168.36.0", 24, "C"), ("0.0.0.0", 0, "D")]


def trace():
    q1 = ethernet.learning_switch([{"src": "A", "dst": "B", "in_port": 1, "all_ports": [1, 2, 3]}, {"src": "B", "dst": "A", "in_port": 2}, {"src": "C", "dst": "B", "in_port": 3}])
    q3 = ipv4.decode("172.16.5.130", 22)
    q4 = ipv4.fragment(2600, 20, 1000)
    q5 = [lpm.lookup(Q5_ROUTES, d) for d in Q5_DESTS]
    q9 = routing.dijkstra(Q9_EDGES, "A")
    z = wireless.cdma_sum([(-1, Q18_C1), (1, Q18_C2)])
    warm = ipv4.decode("192.168.37.200", 21)
    warm_frags = ipv4.fragment(1800, 20, 600)
    warm_lookup = lpm.lookup(WARM_ROUTES, "192.168.37.200")
    return {
        "q1": q1,
        "q3": dict(q3, same_subnet=ipv4.decode("172.16.7.12", 22)["network"] == q3["network"]),
        "q4": q4, "q4_table": ipv4.frag_table(q4),
        "q5": q5, "q5_routes": {"cols": ["Prefix", "Output"], "rows": [[f"{n}/{p}", o] for n, p, o in Q5_ROUTES]},
        "q5_table": {"cols": ["Destination", "Matches", "Output"], "rows": [[r["dest"], ", ".join("/" + m.split("/")[1] for m in r["matches"]), r["output"]] for r in q5]},
        "q6_growth": 20 - 10,
        "q9": {"steps": q9["steps"], "dist": q9["dist"], "pred": q9["pred"], "first_hop": q9["first_hop"], "table": routing.dijkstra_table(q9, ["B", "C", "D"])},
        "q10_first": routing.bf_update([{"via": "V", "link": 2, "advertised": 7}, {"via": "W", "link": 4, "advertised": 2}]),
        "q10_second": routing.bf_update([{"via": "V", "link": 2, "advertised": 7}, {"via": "W", "link": 4, "advertised": 9}]),
        "q11": convergence.count_to_infinity(3),
        "q11_table": {"cols": ["Event", "Y to X", "Z to X"], "rows": [[r["event"], r["Y"], r["Z"]] for r in convergence.count_to_infinity(3)]},
        "q13_first": bgp.select([{"name": "A", "lp": 150, "len": 5, "igp": 20}, {"name": "B", "lp": 100, "len": 2, "igp": 1}]),
        "q13_second": bgp.select([{"name": "A", "lp": 100, "len": 5, "igp": 20}, {"name": "B", "lp": 100, "len": 2, "igp": 1}]),
        "q14": {"to_customer": bgp.may_export("provider", "customer"), "to_peer": bgp.may_export("provider", "peer")},
        "q15": {"unicast": multicast.link_load(10, 3, False), "multicast": multicast.link_load(10, 3, True)},
        "q18": {"c1": list(Q18_C1), "c2": list(Q18_C2), "minus_c1": [-c for c in Q18_C1], "z": z,
                "corr1": wireless.products(z, Q18_C1), "corr2": wireless.products(z, Q18_C2),
                "d1": wireless.cdma_decode(z, Q18_C1), "d2": wireless.cdma_decode(z, Q18_C2)},
        "warm": warm, "warm_frags": warm_frags, "warm_frag_table": ipv4.frag_table(warm_frags), "warm_lookup": warm_lookup,
        "warm_routes": {"cols": ["Prefix", "Output"], "rows": [[f"{n}/{p}", o] for n, p, o in WARM_ROUTES]},
    }
