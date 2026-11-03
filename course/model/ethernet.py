"""Layer-2 calculations: shared-medium timing, source learning, simplified STP."""


def fixed_share(capacity_mbps, users):
    return capacity_mbps / users


def serialization_us(size_bytes, rate_mbps):
    return size_bytes * 8 / rate_mbps


def min_frame_bits(rate_bps, one_way_s):
    return 2 * one_way_s * rate_bps


def backoff(collision, rate_bps, k):
    top = 2 ** collision - 1
    if not 0 <= k <= top:
        raise ValueError("K outside the backoff range")
    slot_us = round(512 / rate_bps * 1e6, 6)
    return {"collision": collision, "k_max": top, "k": k, "slot_us": slot_us, "wait_us": round(k * slot_us, 6)}


def learning_switch(frames):
    """Compatibility view of independent learning in one forwarding VLAN."""
    if not frames:return []
    state,events={},[]
    ports=sorted({frame['in_port'] for frame in frames}|set(frames[0].get('all_ports',[])))
    config=[{'id':port,'vlans':[1],'state':'forwarding'} for port in ports]
    for frame in frames:
        src,dst,port=frame['src'],frame['dst'],frame['in_port']
        learned=state.get((1,src))!=port
        event=switch_step(state,{'src':src,'dst':dst,'in_port':port,'vlan':1},config)
        state=event['table']
        events.append({'src':src,'dst':dst,'in_port':port,'learned':learned,
                       'action':event['action'],'out_ports':event['out_ports'],
                       'table':{mac:location for (vlan,mac),location in state.items()}})
    return events


def stp(switches, edges):
    """Equal-cost simplified STP: lowest ID is root; ties prefer the lowest parent ID."""
    root = min(switches)
    adj = {s: set() for s in switches}
    for a, b in edges:
        adj[a].add(b)
        adj[b].add(a)
    dist, parent, frontier = {root: 0}, {}, [root]
    while frontier:
        nxt = []
        for node in sorted(frontier):
            for n in sorted(adj[node]):
                if n not in dist:
                    dist[n] = dist[node] + 1
                    parent[n] = node
                    nxt.append(n)
        frontier = nxt
    active = sorted(tuple(sorted((c, p))) for c, p in parent.items())
    blocked = sorted(tuple(sorted(e)) for e in edges if tuple(sorted(e)) not in active)
    return {"root": root, "dist": dist, "parent": parent, "active": active, "blocked": blocked}


def tree_path(parent, a, b):
    def up(x):
        out = [x]
        while x in parent:
            x = parent[x]
            out.append(x)
        return out
    pa, pb = up(a), up(b)
    common = next(x for x in pa if x in pb)
    return pa[: pa.index(common) + 1] + list(reversed(pb[: pb.index(common)]))


STP_SWITCHES = ["S1", "S2", "S3", "S4", "S5", "S6", "S7"]
STP_EDGES = [("S3", "S2"), ("S2", "S1"), ("S1", "S5"), ("S1", "S7"), ("S1", "S6"), ("S1", "S4"),
             ("S3", "S5"), ("S5", "S7"), ("S6", "S4")]
STP_HOSTS = {"A": "S3", "B": "S7", "C": "S4"}
LEARN_FRAMES = [
    {"src": "A", "dst": "B", "in_port": 1, "all_ports": [1, 2, 3]},
    {"src": "B", "dst": "A", "in_port": 2},
    {"src": "A", "dst": "B", "in_port": 1},
]


def trace():
    tree = stp(STP_SWITCHES, STP_EDGES)
    paths = {f"{a}-{b}": tree_path(tree["parent"], STP_HOSTS[a], STP_HOSTS[b])
             for a, b in [("A", "B"), ("A", "C"), ("B", "C")]}
    learn = learning_switch(LEARN_FRAMES)
    return {
        "fixed_share_mbps": fixed_share(12, 4),
        "serial_1500_100_us": serialization_us(1500, 100),
        "min_frame_bits": min_frame_bits(10e6, 25.6e-6),
        "backoff_m3_k5": backoff(3, 10e6, 5),
        "learning": learn,
        "learning_table": {"cols": ["Frame", "Learn", "Action"], "rows": [
            [f"{e['src']} → {e['dst']} on {e['in_port']}", f"{e['src']} → port {e['in_port']}",
             e["action"] + (" to " + ",".join(map(str, e["out_ports"])) if e["out_ports"] else "")]
            for e in learn]},
        "stp": tree, "stp_paths": paths,
        "triangle": stp(["S1", "S2", "S3"], [("S1", "S2"), ("S1", "S3"), ("S2", "S3")]),
    }


def switch_step(state, frame, ports):
    """Independent VLAN learning; ports have id, vlans, state, and optional trunk."""
    table = dict(state)
    vlan, ingress = frame['vlan'], frame['in_port']
    config = {p['id']: p for p in ports}
    accepted = ingress in config and vlan in config[ingress]['vlans'] and config[ingress].get('state', 'forwarding') == 'forwarding'
    if not accepted:
        return dict(action='discard', learned=None, out_ports=[], table=table, vlan=vlan)
    learned = (vlan, frame['src'])
    table[learned] = ingress
    eligible = sorted(p['id'] for p in ports if p['id'] != ingress and vlan in p['vlans'] and p.get('state','forwarding') == 'forwarding')
    dest = table.get((vlan, frame['dst']))
    action = 'flood' if dest is None else 'filter' if dest == ingress else 'forward'
    out = eligible if dest is None else [dest] if dest in eligible else []
    return dict(action=action, learned=learned, in_port=ingress, out_ports=out, table=table, vlan=vlan)


def derive_stp_port_states(tree, topology):
    result = []
    active = {tuple(sorted(e)) for e in tree['active']}
    for a,b in topology:
        designated = min((a,b), key=lambda n:(tree['dist'][n],n))
        for node,peer in ((a,b),(b,a)):
            forwarding = tuple(sorted((a,b))) in active or node == designated
            result.append(dict(device=node, peer=peer, state='forwarding' if forwarding else 'discarding'))
    return result
