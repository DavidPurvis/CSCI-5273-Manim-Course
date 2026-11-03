"""Independent checks: each compares a model with a different method or a vault answer."""
import ipaddress
import itertools
import json
import math
import random
from pathlib import Path

from course.model import bgp, convergence, discovery, ethernet, ipv4, lpm, mobile, multicast, router, routing, subnet, wireless

ROOT = Path(__file__).resolve().parents[2]


def floyd(edges):
    nodes = sorted({n for e in edges for n in e})
    d = {(a, b): 0 if a == b else math.inf for a in nodes for b in nodes}
    for (a, b), c in edges.items():
        d[a, b] = d[b, a] = c
    for k, i, j in itertools.product(nodes, nodes, nodes):
        d[i, j] = min(d[i, j], d[i, k] + d[k, j])
    return d


def test_decode_matches_stdlib_on_random_addresses():
    rng = random.Random(5273)
    for _ in range(2000):
        addr = ipaddress.IPv4Address(rng.getrandbits(32))
        p = rng.randint(1, 30)
        net = ipaddress.IPv4Network(f"{addr}/{p}", strict=False)
        got = ipv4.decode(str(addr), p)
        assert got["network"] == str(net.network_address)
        assert got["broadcast"] == str(net.broadcast_address)
        assert got["mask"] == str(net.netmask)
        assert got["total"] == net.num_addresses


def test_vault_decode_example():
    d = ipv4.decode("10.10.1.97", 23)
    assert (d["network"], d["broadcast"], d["usable"], d["first"], d["last"]) == ("10.10.0.0", "10.10.1.255", 510, "10.10.0.1", "10.10.1.254")


def test_total_length_correction():
    assert 2 ** 16 - 1 == 65535 and ipv4.trace()["max_total_length"] == 65535


def test_vlsm_with_stdlib():
    plan = subnet.vlsm("128.101.5.0", 23, subnet.DEPARTMENTS)
    parent = ipaddress.IPv4Network("128.101.4.0/23")
    nets = [ipaddress.IPv4Network(p["block"]) for p in plan]
    assert [p["block"] for p in plan] == ["128.101.4.0/24", "128.101.5.0/25", "128.101.5.128/26", "128.101.5.192/26"]
    assert sum(n.num_addresses for n in nets) == 512
    assert all(n.subnet_of(parent) for n in nets)
    assert not any(a.overlaps(b) for a, b in itertools.combinations(nets, 2))
    assert all(p["usable"] >= p["hosts"] for p in plan)
    assert 2 ** 5 - 2 < 31


def test_lpm_against_trie_and_stdlib_bruteforce():
    trie = lpm.Trie(lpm.ROUTES)
    nets = [(ipaddress.IPv4Network(f"{n}/{p}"), o) for n, p, o in lpm.ROUTES]
    rng = random.Random(1)
    samples = lpm.DESTINATIONS + [str(ipaddress.IPv4Address(rng.getrandbits(32))) for _ in range(500)]
    samples += [f"201.10.{rng.randint(0, 9)}.{rng.randint(0, 255)}" for _ in range(500)]
    for dest in samples:
        addr = ipaddress.IPv4Address(dest)
        brute = max((n for n in nets if addr in n[0]), key=lambda n: n[0].prefixlen)[1]
        assert lpm.lookup(lpm.ROUTES, dest)["output"] == brute == trie.lookup(dest)[0]
    assert [lpm.lookup(lpm.ROUTES, d)["output"] for d in lpm.DESTINATIONS] == ["B", "A", "C"]


def test_lookup_budget():
    b = lpm.lookup_budget(10e9, 64)
    assert b["packets_per_second"] == 19531250 and abs(b["ns_per_packet"] - 51.2) < 1e-9


def test_fragments_reassemble_payload():
    for total, mtu in [(4000, 1500), (3200, 1000), (9000, 576), (1500, 1500)]:
        frags = ipv4.fragment(total, 20, mtu)
        data = bytearray(total - 20)
        for f in frags:
            start = f["offset_units"] * 8
            for i in range(start, start + f["payload"]):
                assert data[i] == 0
                data[i] = 1
            assert f["total"] <= mtu
        assert all(data)
        assert [f["mf"] for f in frags] == [1] * (len(frags) - 1) + [0]
        assert all(f["payload"] % 8 == 0 for f in frags[:-1])


def test_vault_fragment_numbers():
    a = ipv4.fragment(4000, 20, 1500)
    assert [f["payload"] for f in a] == [1480, 1480, 1020] and [f["offset_units"] for f in a] == [0, 185, 370]
    b = ipv4.fragment(3200, 20, 1000)
    assert [f["payload"] for f in b] == [976, 976, 976, 252] and [f["offset_units"] for f in b] == [0, 122, 244, 366]


def test_checksum_verifies_including_itself():
    words = ipv4.header_words(ttl=64)
    c = ipv4.checksum(words)
    words[5] = c
    assert ipv4.checksum(words) == 0
    words[4] = ipv4.header_words(ttl=63)[4]
    assert ipv4.checksum(words) != 0, "a stale checksum must fail after TTL changes"


def test_switch_learning_vault_trace():
    ev = ethernet.learning_switch(ethernet.LEARN_FRAMES)
    assert ev[0]["action"] == "flood" and ev[0]["table"] == {"A": 1}
    assert ev[1]["action"] == "forward" and ev[1]["out_ports"] == [1]
    assert ev[2]["action"] == "forward" and ev[2]["out_ports"] == [2]


def test_backoff_and_collision_window():
    assert ethernet.backoff(3, 10e6, 5)["wait_us"] == 256
    assert abs(ethernet.min_frame_bits(10e6, 25.6e-6) - 512) < 1e-9
    assert ethernet.serialization_us(1500, 100) == 120


def test_stp_vault_tree():
    t = ethernet.trace()
    assert t["stp"]["root"] == "S1"
    assert t["stp"]["active"] == sorted(tuple(sorted(e)) for e in [("S1", "S2"), ("S2", "S3"), ("S1", "S4"), ("S1", "S5"), ("S1", "S6"), ("S1", "S7")])
    assert len(t["stp"]["active"]) == len(ethernet.STP_SWITCHES) - 1
    assert t["stp_paths"]["A-B"] == ["S3", "S2", "S1", "S7"]
    assert t["stp_paths"]["A-C"] == ["S3", "S2", "S1", "S4"]
    assert t["stp_paths"]["B-C"] == ["S7", "S1", "S4"]


def test_dijkstra_against_floyd():
    for edges, src in [(routing.SMALL, "A"), (routing.SMALL_CHANGED, "A"), (routing.SLIDE_26, "t"), (routing.SLIDE_26, "u")]:
        d, f = routing.dijkstra(edges, src)["dist"], floyd(edges)
        assert all(d[n] == f[src, n] for n in d)


def test_vault_routing_answers():
    s = routing.dijkstra(routing.SMALL, "A")
    assert s["dist"] == {"A": 0, "B": 2, "C": 3, "D": 5} and s["first_hop"]["D"] == "B" and s["pred"]["D"] == "C"
    c = routing.dijkstra(routing.SMALL_CHANGED, "A")
    assert c["dist"]["C"] == 5 and c["dist"]["D"] == 6 and c["first_hop"] == {"B": "B", "C": "C", "D": "B"}
    t = routing.dijkstra(routing.SLIDE_26, "t")
    assert t["dist"]["v"] == 7 and t["paths"]["v"] == list("tswxzyv") and t["first_hop"]["v"] == "s"
    assert routing.path_cost(routing.SLIDE_26, list("txzyv")) == 8 and routing.path_cost(routing.SLIDE_26, list("tswxv")) == 8


def test_dv_converges_to_shortest_paths():
    for edges in (routing.SMALL, routing.SLIDE_26):
        final, f = routing.dv_rounds(edges)[-1], floyd(edges)
        assert all(final[a][b] == f[a, b] for a in final for b in final)
    r = [x["A"] for x in routing.dv_rounds(routing.SMALL)]
    assert [(x["B"], x["C"], x["D"]) for x in r] == [(2, 5, math.inf), (2, 3, 6), (2, 3, 5)]
    assert routing.bf_update([{"via": "B", "link": 3, "advertised": 3}, {"via": "C", "link": 2, "advertised": 5}])["total"] == 6


def test_path_vector_and_mpls():
    assert routing.path_vector_accept(1, [3, 2, 1]) is False
    assert [h["out"] for h in routing.mpls_swap(routing.MPLS_PATH, 17)] == [42, 8, "pop"]


def test_count_to_infinity_vault_table():
    rows = convergence.count_to_infinity(3)
    assert [(r["Y"], r["Z"]) for r in rows] == [(1, 2), (3, 2), (3, 4), (5, 4)]
    assert convergence.rip_rounds()[-1]["Y"] == 16


def test_slide_link_cost_change():
    good = convergence.link_cost_change(1)
    assert (good["final_y"], good["final_z"]) == (1, 2) and good["exchanges"] <= 2
    bad = convergence.link_cost_change(60)
    assert (bad["final_y"], bad["final_z"]) == (51, 50) and bad["exchanges"] > 20
    first = bad["rows"]
    assert (first[0]["Y"], first[0]["Z"]) == (4, 5) and first[1]["Y"] == 6 and first[2]["Z"] == 7
    f = floyd({("X", "Y"): 60, ("Y", "Z"): 1, ("X", "Z"): 50})
    assert f["Y", "X"] == 51 and f["Z", "X"] == 50


def test_slide27_distances_match_vault():
    d = routing.dijkstra(routing.SLIDE_27, "A")["dist"]
    assert d == {"A": 0, "B": 2, "C": 4, "D": 4, "G": 7, "E": 8, "H": 13, "F": 14}
    f = floyd(routing.SLIDE_27)
    assert all(d[n] == f["A", n] for n in d)


def test_spp_slide_answers_and_gadgets():
    sols = convergence.solve_spp(convergence.SLIDE_30)
    assert len(sols) == 1
    s = sols[0]
    assert s[1] == (1, 3, 0) and s[2] == (2, 0) and s[3] == (3, 0) and s[4] == (4, 2, 0) and s[5] is None
    assert len(convergence.solve_spp(convergence.DISAGREE)) == 2
    assert convergence.solve_spp(convergence.BAD_GADGET) == []


def _bgp_independent(routes):
    return sorted(routes, key=lambda r: (-r["lp"], r["len"], r["igp"], r["name"]))[0]["name"]


def test_bgp_selection_matches_sort_key():
    cand = bgp.CANDIDATES
    for subset in (cand, cand[1:], [cand[1] | {"len": 1}, cand[2]]):
        assert bgp.select(subset)["winner"] == _bgp_independent(subset)
    assert bgp.select(cand)["winner"] == "A" and bgp.select(cand[1:])["winner"] == "C"
    assert bgp.select([cand[1] | {"len": 1}, cand[2]])["winner"] == "B"


def _valley_regex(seq):
    import re
    return bool(re.fullmatch(r"(up )*(peer )?(down )*", "".join(s + " " for s in seq)))


def test_valley_free_matches_regex_and_vault():
    expected = [True, True, False, True, True, False, False]
    for path, ok in zip(bgp.SLIDE_PATHS, expected):
        seq, got = bgp.valley_free(path)
        assert got == ok == _valley_regex(seq)


def test_export_rule():
    t = bgp.export_table()["rows"]
    assert t[2] == ["peer", "yes", "no", "no"] and t[3] == ["provider", "yes", "no", "no"] and t[1][1:] == ["yes"] * 3
    assert bgp.hot_potato({"west": 4, "east": 9}) == "west"


def test_multicast_values():
    assert multicast.link_load(10, 3, False) == 30 and multicast.link_load(10, 3, True) == 10
    assert multicast.membership_timers() == {"slide_formula": 270, "rfc2236": 260}
    assert multicast.suppression({"H1": 2, "H2": 6})["suppressed"] == ["H2"]
    assert multicast.spt_saving(8, 7, 4)["saving"] == 11
    assert multicast.anycast_pick(multicast.ANYCAST) == "A" and multicast.anycast_pick(multicast.ANYCAST, ["A"]) == "B"
    assert multicast.rpf(1, 1) and not multicast.rpf(1, 3)


def test_mst_is_minimum_by_enumeration_and_differs_from_shortest_path():
    edges = multicast.TRIANGLE
    best = min(sum(edges[e] for e in c) for c in itertools.combinations(edges, 2))
    assert sum(edges[e] for e in multicast.kruskal(edges)) == best == sum(edges[e] for e in multicast.prim(edges, "A")) == 2
    assert routing.dijkstra(edges, "A")["dist"]["C"] == 1.5


def test_rpf_expected_port_is_the_shortest_path_toward_source():
    d = routing.dijkstra(routing.SMALL, "D")
    assert routing.path_to(d["pred"], "D", "A")[-2] == "B", "A's reverse path toward D must leave via B"


def test_prune_recursive():
    children = {"R": ["X", "Y"], "X": ["L1", "L2"], "Y": ["L3"]}
    assert multicast.prune_recursive(children, {"L3"}, "X") is False
    assert multicast.prune_recursive(children, {"L3"}, "Y") is True


def test_cdma_orthogonality_and_round_trip():
    assert wireless.dot(wireless.C1, wireless.C2) == 0
    for d1, d2 in itertools.product((1, -1), repeat=2):
        z = wireless.cdma_sum([(d1, wireless.C1), (d2, wireless.C2)])
        assert wireless.cdma_decode(z, wireless.C1) == d1 and wireless.cdma_decode(z, wireless.C2) == d2
    assert wireless.cdma_sum([(1, wireless.C1), (-1, wireless.C2)]) == [0, 2, -2, 0]
    assert wireless.cdma_sum([(-1, wireless.C1), (-1, wireless.C2)]) == [-2, 0, 0, 2]


def test_wireless_small_values():
    assert abs(wireless.snr_db(100) - 20) < 1e-9
    assert [e["counter"] for e in wireless.backoff_counter(4, ["idle", "idle", "busy", "idle", "idle"])] == [3, 2, 2, 1, 0]
    assert wireless.hidden_pair("A", "C", "B") is True


def test_tunnel_invariants():
    for coa in (mobile.COA, mobile.COA2):
        rows = mobile.tunnel_headers(coa)
        assert len({r["inner"] for r in rows}) == 1, "inner identity must never change"
        assert all(coa in r["outer"] for r in rows if r["outer"])
    assert mobile.tunnel_headers(mobile.COA)[1]["outer"] != mobile.tunnel_headers(mobile.COA2)[1]["outer"]
    assert mobile.encapsulated(1480) == 1500
    assert mobile.triangle(40, 50, 10)["saving"] == 80 and mobile.triangle(60, 70, 5)["indirect"] == 130


def test_handover_states():
    h = mobile.handover_states()
    assert [s["path"] for s in h] == [["S-GW", "A", "UE"], ["S-GW", "A", "B", "UE"], ["S-GW", "B", "UE"]]
    assert all(s["path"][0] == "S-GW" and s["path"][-1] == "UE" for s in h)


def test_journey_vault_table():
    j = discovery.journey()
    assert [h["ttl"] for h in j] == [64, 63, 62]
    assert [h["eth_dst"] for h in j] == ["R1-near", "R2-middle", "server"]
    assert [h["arp_for"] for h in j] == ["192.0.2.1", "198.51.100.2", "203.0.113.80"]
    assert len({h["ip_dst"] for h in j}) == 1
    assert discovery.next_hop("192.0.2.10", "198.51.100.53", 24, "192.0.2.1") == "192.0.2.1"
    assert discovery.next_hop("192.0.2.10", "192.0.2.53", 24, "192.0.2.1") == "192.0.2.53"


def test_dns_cache_rules():
    assert discovery.dns_lookup()["queries_out"] == 3
    assert discovery.dns_lookup(cache={"www.example.test": "x"})["queries_out"] == 0
    assert discovery.cache_valid(0, 300, 240) and not discovery.cache_valid(0, 300, 300)


def test_queue_timing():
    q = router.output_queue(3, 1500, 12e6)
    assert [p["done_ms"] for p in q] == [1, 2, 3] and [p["wait_ms"] for p in q] == [0, 1, 2]
    assert router.backlog_bytes(8e6, 4e6, 0.01) == 5000
    h = router.hol_round({"B": [1], "C": [1, 2]})
    assert h["blocked"][0]["input"] == "C" and h["idle_outputs"] == [2]


def test_frozen_traces_match_models():
    mods = dict(ethernet=ethernet, ipv4=ipv4, subnet=subnet, lpm=lpm, router=router, discovery=discovery, routing=routing,
                convergence=convergence, bgp=bgp, multicast=multicast, wireless=wireless, mobile=mobile)
    for name, mod in mods.items():
        fresh = json.loads(json.dumps(mod.trace(), ensure_ascii=False, default=str, sort_keys=True))
        assert fresh == json.loads((ROOT / "traces" / f"{name}.json").read_text()), name


def test_vlan_fixture_and_discard_admission():
    ports=[dict(id=i,vlans=[10] if i in (1,2,6) else [20] if i in (3,4) else [10,20],state='discarding' if i==6 else 'forwarding') for i in range(1,7)]
    state={}
    for src,dst,port,vlan,want in [('A','B',1,10,[2,5]),('A','B',3,20,[4,5]),('B','A',2,10,[1]),('B','A',4,20,[3])]:
        event=ethernet.switch_step(state,dict(src=src,dst=dst,in_port=port,vlan=vlan),ports)
        assert event['out_ports']==want
        state=event['table']
    assert state[(10,'A')]==1 and state[(20,'A')]==3
    rejected=ethernet.switch_step(state,dict(src='C',dst='A',in_port=6,vlan=10),ports)
    assert rejected['action']=='discard' and rejected['table']==state


def test_stp_discard_endpoints():
    ports=ethernet.derive_stp_port_states(ethernet.stp(ethernet.STP_SWITCHES,ethernet.STP_EDGES),ethernet.STP_EDGES)
    assert {(p['device'],p['peer']) for p in ports if p['state']=='discarding'}=={('S3','S5'),('S7','S5'),('S6','S4')}


def test_fragment_rejects_zero_step():
    import pytest
    with pytest.raises(ValueError):ipv4.fragment(4000,20,20)


def test_already_fitting_ipv4_datagram_is_not_fragmented():
    # MTU payload capacity 980 is not divisible by eight. Alignment must not
    # fragment a 999-byte datagram which already fits the 1000-byte link.
    from course.model.ipv4 import fragment
    assert fragment(999,20,1000)==[{'payload':979,'total':999,'offset_units':0,'offset_bytes':0,'mf':0}]
    assert fragment(20,20,20)==[{'payload':0,'total':20,'offset_units':0,'offset_bytes':0,'mf':0}]
    assert fragment(27,20,27)[0]['payload']==7
