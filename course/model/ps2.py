"""Models for the student's Problem Set 2, and drills that ask its questions with new numbers. test_ps2 proves each model reproduces PS2's answers."""
import heapq
import ipaddress
import itertools
import math
import random

INF = math.inf
GRID = {("A", "C"): 2, ("C", "E"): 2, ("A", "B"): 5, ("C", "D"): 8, ("E", "F"): 4, ("B", "D"): 2, ("D", "F"): 4}
UP = [("2", "1"), ("3", "1"), ("1", "4"), ("2", "5"), ("5", "3"), ("3", "d"), ("4", "d"), ("4", "6"), ("7", "5"), ("8", "5"), ("8", "d")]
PEER = [("3", "4"), ("5", "d"), ("d", "6")]
HOST = {"A": ("79:AA:EF:AC:11:21", "123.123.123.111"), "B": ("0D:23:42:AC:EE:FC", "22.1.23.45"),
        "C": ("00:0C:EA:17:98:32", "33.2.2.18"), "D": ("0A:FE:CC:AB:CD:17", "33.2.2.208")}
# Each link as (from, to): the sender's interface MAC and the receiver's interface MAC.
HOPS = {("A", "R1"): ("79:AA:EF:AC:11:21", "0C:AF:10:00:1E:1C"), ("R1", "A"): ("0C:AF:10:00:1E:1C", "79:AA:EF:AC:11:21"),
        ("R1", "R2"): ("74:29:9C:EF:AC:55", "89:00:CC:1F:2C:1F"), ("R2", "R1"): ("89:00:CC:1F:2C:1F", "74:29:9C:EF:AC:55"),
        ("R2", "R3"): ("AF:CC:1F:11:EE:10", "AA:BB:CC:AF:2F:11"), ("R3", "R2"): ("AA:BB:CC:AF:2F:11", "AF:CC:1F:11:EE:10"),
        ("B", "R3"): ("0D:23:42:AC:EE:FC", "AF:0C:EF:11:22:11"), ("R3", "B"): ("AF:0C:EF:11:22:11", "0D:23:42:AC:EE:FC"),
        ("R2", "R4"): ("0C:32:56:90:09:EF", "89:98:AF:FF:FF:0C"), ("R4", "R2"): ("89:98:AF:FF:FF:0C", "0C:32:56:90:09:EF"),
        ("R4", "C"): ("00:1C:AA:FE:F1:1A", "00:0C:EA:17:98:32"), ("C", "R4"): ("00:0C:EA:17:98:32", "00:1C:AA:FE:F1:1A"),
        ("R4", "D"): ("00:1C:AA:FE:F1:1A", "0A:FE:CC:AB:CD:17"), ("D", "R4"): ("0A:FE:CC:AB:CD:17", "00:1C:AA:FE:F1:1A")}
GATEWAY = {"A": "R1", "B": "R3", "C": "R4", "D": "R4"}
SUBNETS = [("128.96.34.0/25", "128.96.34.1"), ("128.96.34.128/25", None), ("128.96.33.0/24", "128.96.33.1")]
SOURCES = {"H1": ("128.96.34.15", "128.96.34.0/25", "128.96.34.1"), "H3": ("128.96.33.14", "128.96.33.0/24", "128.96.33.1")}


def net_of(address, mask):
    return ipaddress.ip_interface(f"{address}/{mask}").network


def valid_host(address, mask):
    net = net_of(address, mask)
    ip = ipaddress.ip_address(address)
    return ip not in (net.network_address, net.broadcast_address)


def same_subnet(a, b):
    return ipaddress.ip_interface(a).network == ipaddress.ip_interface(b).network


def carve(parent, sizes):
    """Continuous blocks from the start of parent, in the order given. Each size is a count of addresses."""
    at = int(ipaddress.ip_network(parent).network_address)
    out = []
    for size in sizes:
        prefix = 32 - int(math.log2(size))
        if at % size:
            at += size - at % size
        out.append(f"{ipaddress.ip_address(at)}/{prefix}")
        at += size
    return out


def block_for_hosts(hosts):
    """The smallest block with enough usable addresses, leaving out network and broadcast."""
    size = 4
    while size - 2 < hosts:
        size *= 2
    return size


def departments(parent, hosts):
    return carve(parent, [block_for_hosts(h) for h in hosts])


def cost_jump(xy, yz, xz, new):
    """The triangle after link X-Y jumps to new: Y and Z's tables to X after each exchange, ending when Y's distance settles."""
    y_via_z, z_via_y = yz + (xy + yz if xy + yz < xz else xz), xy + yz
    rounds = []
    while True:
        y_best = min(new, y_via_z)
        z_via_y = y_best + yz
        z_best = min(xz, z_via_y)
        y_next = z_best + yz
        rounds.append({"y_via_x": new, "y_via_z": y_next, "z_via_x": xz, "z_via_y": z_via_y})
        if y_next == y_via_z or min(new, y_next) == y_best:
            y_via_z = y_next
            break
        y_via_z = y_next
    return rounds


def updates_until_settled(xy, yz, xz, new):
    """How many times Y's distance through Z changes before it stops."""
    rounds = cost_jump(xy, yz, xz, new)
    return sum(1 for r, before in zip(rounds, [None] + rounds) if before is None or r["y_via_z"] != before["y_via_z"])


def neighbors(edges):
    out = {}
    for (a, b), cost in edges.items():
        out.setdefault(a, {})[b] = cost
        out.setdefault(b, {})[a] = cost
    return out


def dv_round(edges):
    """Each node's (cost, first hop) to every node, after one exchange of its direct-neighbor table."""
    near = neighbors(edges)
    start = {n: {d: (0, n) if d == n else (near[n][d], d) if d in near[n] else (INF, "-") for d in near} for n in near}
    out = {}
    for n in near:
        out[n] = {}
        for d in near:
            best = start[n][d]
            for via, cost in sorted(near[n].items()):
                total = cost + start[via][d][0]
                if total < best[0]:
                    best = (total, via)
            out[n][d] = best
    return out


def link_state(edges, source):
    """Each destination's (cost, first hop) from source."""
    near = neighbors(edges)
    done = {}
    heap = [(0, source, source)]
    while heap:
        cost, node, first = heapq.heappop(heap)
        if node in done:
            continue
        done[node] = (cost, first)
        for other, weight in sorted(near[node].items()):
            if other not in done:
                heapq.heappush(heap, (cost + weight, other, other if node == source else first))
    return done


def valley(path):
    """Valid when it climbs, crosses at most one peer link, then descends."""
    state = "up"
    for a, b in zip(path, path[1:]):
        if (a, b) in UP:
            step = "up"
        elif (b, a) in UP:
            step = "down"
        elif (a, b) in PEER or (b, a) in PEER:
            step = "peer"
        else:
            raise ValueError(f"no link {a}-{b}")
        if state == "up":
            state = {"up": "up", "peer": "after", "down": "after"}[step]
        elif step != "down":
            return False
    return True


def hop_headers(src, dst):
    """(src MAC, dst MAC, src IP, dst IP) on each hop. Source and destination IP stay put; the MACs change at every hop."""
    first, last = GATEWAY[src], GATEWAY[dst]
    middle = [] if first == last else ["R2"]
    stops = [src, first, *middle, last, dst]
    return [(f"{a} to {b}", *HOPS[(a, b)], HOST[src][1], HOST[dst][1]) for a, b in zip(stops, stops[1:])]


def mpls_tables(r1_out=1, r2_out=2, r3_a=4, r3_c=3, r5_out=5):
    return {"R1": ("-", r1_out, "A", 0), "R2": ("-", r2_out, "C", 0), "R3": [(r1_out, r3_a, "A", 1), (r2_out, r3_c, "C", 0)],
            "R4": (r3_c, "-", "C", 0), "R5": (r3_a, r5_out, "A", 0), "R6": (r5_out, "-", "A", 0)}


def show(value):
    return "∞" if value == INF else str(value)


def field(key, label, answer):
    return {"key": key, "label": label, "answer": str(answer)}


def problem(kind, n, prompt, fields, steps, figure=None):
    out = {"prompt": prompt, "fields": fields, "steps": steps, "given": {}, "id": f"{kind}-{n}", "type": kind, "source": "ps2"}
    if figure:
        out["figure"] = figure
    return out


def host_drills(rng):
    out = []
    while len(out) < 5:
        prefix = rng.randint(20, 26)
        net = ipaddress.ip_network(f"10.{rng.randint(1, 250)}.{rng.randint(0, 255)}.0/{prefix}", strict=False)
        hosts = net.num_addresses
        address = net.network_address + rng.choice([0, hosts - 1, rng.randint(1, hosts - 2)])
        answer = "True" if valid_host(str(address), net.netmask) else "False"
        out.append(problem("ps2host", len(out), f"True or false: Is {address}/{net.netmask} a valid IP address for a host?",
                           [dict(field("v", "Answer", answer), options=["True", "False"])],
                           [f"The mask is /{prefix}, so this network runs from {net.network_address} to {net.broadcast_address}.",
                            "Only the network and broadcast addresses can't be hosts."]))
    while len(out) < 10:
        prefix = rng.randint(20, 26)
        a = ipaddress.ip_network(f"192.168.{rng.randint(0, 255)}.{rng.randint(0, 255)}/{prefix}", strict=False)
        other = int(a.network_address) + rng.choice([1, a.num_addresses - 1, a.num_addresses, 2 * a.num_addresses])
        first, second = f"{a.network_address}/{prefix}", f"{ipaddress.ip_address(other)}/{prefix}"
        answer = "True" if same_subnet(first, second) else "False"
        out.append(problem("ps2host", len(out), f"True or false: Is {first} and {second} representing the same subnet?",
                           [dict(field("v", "Answer", answer), options=["True", "False"])],
                           [f"Apply /{prefix} to each: {ipaddress.ip_interface(first).network} and {ipaddress.ip_interface(second).network}."]))
    return out


def carve_drills(rng):
    out = []
    while len(out) < 5:
        second = rng.randint(1, 250)
        groups = [("A", rng.randint(3, 6), 2 ** rng.choice([12, 13])), ("B", rng.randint(4, 8), 2 ** rng.choice([10, 11])), ("C", rng.randint(4, 10), 2 ** rng.choice([6, 7]))]
        sizes = [size for _, count, size in groups for _ in range(count)]
        if sum(sizes) > 2 ** 16:
            continue
        blocks = carve(f"10.{second}.0.0/16", sizes)
        names = [f"{g}{i + 1}" for g, count, _ in groups for i in range(count)]
        at = dict(zip(names, blocks))
        ask = ["A2", "B1", f"B{groups[1][1]}", "C1", f"C{groups[2][1]}"]
        text = ", ".join(f"{g}: {count} networks of {size} IPs each" for g, count, size in groups)
        out.append(problem("ps2carve", len(out), f"Divide 10.{second}.0.0/16 into {text}. The addresses should be continuous, starting with A1 at 10.{second}.0.0. Enter the beginning IP of each subnet with its mask.",
                           [field(n, n, at[n]) for n in ask], [f"{count} blocks of {size} addresses use /{32 - int(math.log2(size))}." for _, count, size in groups] + ["Each block starts right after the previous one, aligned to its own size."]))
    while len(out) < 10:
        third = rng.randrange(0, 254, 2)
        parent = f"192.168.{third}.0/23"
        hosts = sorted(rng.sample(range(20, 240), 4), reverse=True)
        if sum(block_for_hosts(h) for h in hosts) > 512:
            continue
        blocks = departments(parent, hosts)
        names = "ABCD"
        out.append(problem("ps2carve", len(out), f"An organization has been assigned the prefix {parent} and wants subnets for 4 departments: " + ", ".join(f"{n}: {h} hosts" for n, h in zip(names, hosts)) + ". Give an arrangement, largest department first, starting at the beginning of the block.",
                           [field(n, n, b) for n, b in zip(names, blocks)], [f"{n} needs {h} usable addresses, so a block of {block_for_hosts(h)}." for n, h in zip(names, hosts)]))
    return out


def dv_drills(rng):
    out = []
    while len(out) < 10:
        xy, yz = rng.randint(2, 6), rng.randint(1, 3)
        xz = rng.randrange(xy + yz + 8, 60)
        new = xz + rng.randint(10, 60)
        rounds = cost_jump(xy, yz, xz, new)
        if len(rounds) < 3:
            continue
        one, two = rounds[0], rounds[1]
        start = xy + yz
        prompt = (f"Routers X, Y and Z: X-Y costs {xy}, Y-Z costs {yz}, X-Z costs {xz}. Y's distance to X is {xy} via X and {yz + start} via Z. Z's is {xz} via X and {start} via Y. "
                  f"The cost of X-Y suddenly changes to {new}. Give Y's and Z's tables after Y updates Z and Z updates back, then after the second exchange, then the number of updates Y gets until its distance to X converges.")
        count = updates_until_settled(xy, yz, xz, new)
        out.append(problem("ps2dv", len(out), prompt,
                           [field("y1", "Y via Z, first", one["y_via_z"]), field("z1", "Z via Y, first", one["z_via_y"]), field("y2", "Y via Z, second", two["y_via_z"]),
                            field("z2", "Z via Y, second", two["z_via_y"]), field("n", "Updates until converged", count)],
                           [f"Y's best is {yz + start} via Z, so Z's via-Y becomes {one['z_via_y']}, and Y's via-Z becomes {one['y_via_z']}.",
                            "Each exchange adds the same amount until going through X directly is cheaper.", f"That takes {count} updates to Y."]))
    return out


def grid_drills(rng):
    out = []
    names = list("ABCDEF")
    while len(out) < 10:
        edges = {k: rng.randint(1, 9) for k in GRID}
        node = names[len(out) % 6]
        text = ", ".join(f"{a}-{b} {c}" for (a, b), c in edges.items())
        if len(out) % 2 == 0:
            table = dv_round(edges)[node]
            prompt = f"Links: {text}. Each node knows only its immediate neighbors, then each reports that to its neighbors once. Give node {node}'s distance-vector table: cost and hop for each destination (∞ and - if unknown)."
            steps = ["Take the lowest of the direct cost and each neighbor's reported cost plus the link to that neighbor."]
        else:
            result = link_state(edges, node)
            table = {d: (result[d][0], result[d][1]) for d in names}
            prompt = f"Links: {text}. Use the link-state algorithm to build node {node}'s routing table: next hop and distance for each destination."
            steps = ["Run Dijkstra from the node, settling the closest unsettled node each round, and keep each route's first hop."]
        fields = []
        for d in names:
            if d != node:
                fields += [field(f"{d}c", f"{d} cost", show(table[d][0])), field(f"{d}h", f"{d} hop", table[d][1])]
        out.append(problem("ps2grid", len(out), prompt, fields, steps))
    return out


def path_drills(rng):
    out = []
    while len(out) < 10:
        name = rng.choice(sorted(SOURCES))
        address, own, gateway = SOURCES[name]
        net = ipaddress.ip_network(rng.choice(SUBNETS)[0])
        dest = str(net.network_address + rng.randint(2, net.num_addresses - 2))
        if dest == address:
            continue
        local = ipaddress.ip_address(dest) in ipaddress.ip_network(own)
        target = dest if local else gateway
        out.append(problem("ps2path", len(out), f"Host {name} sends a packet to the destination {dest}. Is it in {name}'s network, and which address does {name}'s first ARP ask for?",
                           [dict(field("local", "In the same network?", "Yes" if local else "No"), options=["Yes", "No"]), field("arp", "ARP asks for", target)],
                           [f"{name} applies its own mask, {own}.", f"So it ARPs for {target}: everyone on the LAN receives the broadcast, only the owner replies, and {name} caches the result."], figure="q06-network.png"))
    return out


def hop_drills():
    out = []
    pairs = [p for p in itertools.permutations("ABCD", 2) if p not in (("B", "C"), ("C", "D"), ("D", "C"))][:10]
    for src, dst in pairs:
        rows = hop_headers(src, dst)
        fields = []
        for i, (name, smac, dmac, sip, dip) in enumerate(rows):
            fields += [field(f"s{i}", f"{name}: src MAC", smac), field(f"d{i}", f"{name}: dst MAC", dmac)]
        fields += [field("sip", "src IP on every hop", rows[0][3]), field("dip", "dst IP on every hop", rows[0][4])]
        out.append(problem("ps2hop", len(out), f"Suppose that {src} send an IP packet to {dst}. Write down the IP packet's content along the path, using the Figure.", fields,
                           ["The source and destination IP addresses never change.", "The MAC addresses are the two interfaces on each hop's link."], figure="q13-network.png"))
    return out


def mpls_drills(rng):
    out = []
    while len(out) < 10:
        labels = rng.sample(range(10, 99), 5)
        t = mpls_tables(*labels)
        lines = [f"R1: -, {t['R1'][1]}, A, 0", f"R2: -, {t['R2'][1]}, C, 0", f"R4: {t['R4'][0]}, -, C, 0", f"R5: {t['R5'][0]}, {t['R5'][1]}, A, 0"]
        a, c = t["R3"]
        out.append(problem("ps2mpls", len(out), "Traffic from R1 to R6 is routed R1->R3->R5->R6->A and traffic from R2 to R4 is routed R2->R3->R4->C. Columns are In label, Out label, Dst, Out Interface. " + "; ".join(lines) + ". Fill in R3's two rows and R6's row.",
                           [field("a1", "R3, flow to A: in", a[0]), field("a2", "out", a[1]), field("a4", "interface", a[3]), field("c1", "R3, flow to C: in", c[0]), field("c2", "out", c[1]), field("c4", "interface", c[3]), field("r1", "R6: in", t["R6"][0]), field("r2", "out", "-"), field("r4", "interface", 0)],
                           ["A router's in label is the out label of the router before it.", "Its out label is the in label of the router after it.", "The last router has no out label."], figure="q16-mpls.png"))
    return out


def valley_drills(rng):
    near = {}
    for a, b in UP + PEER:
        near.setdefault(a, set()).add(b)
        near.setdefault(b, set()).add(a)
    paths = []

    def walk(path):
        if path[-1] == "d":
            paths.append(path)
            return
        if len(path) < 4:
            for other in sorted(near[path[-1]] - set(path)):
                walk(path + [other])
    for start in "12345678":
        walk([start])
    shown = {("1", "3", "d"), ("1", "4", "d"), ("8", "d"), ("6", "d"), ("4", "d"), ("7", "5", "d"), ("7", "5", "3", "d")}
    fresh = [p for p in paths if tuple(p) not in shown]
    rng.shuffle(fresh)
    out = []
    for i in range(10):
        chosen = fresh[i * 3:i * 3 + 3]
        if len(chosen) < 3:
            break
        out.append(problem("ps2valley", i, "Identify which of the following paths are valid and which are invalid, based on the network topology of the Figure.",
                           [dict(field(f"p{j}", " ".join(p), "valid" if valley(p) else "invalid"), options=["valid", "invalid"]) for j, p in enumerate(chosen)],
                           ["Follow each path from its start: climb customer to provider, cross at most one peer link, then only descend."], figure="q18-graph.png"))
    return out


TYPES = [("ps2host", "Valid host and same subnet", "8.1"), ("ps2carve", "Divide a block into subnets", "8.1"), ("ps2path", "Packet path and ARP", "9.1"),
         ("ps2hop", "Packet headers at each hop", "9.1"), ("ps2grid", "Distance-vector and link-state tables", "10.2"), ("ps2dv", "Link cost jumps", "11.2"),
         ("ps2mpls", "MPLS tables", "10.4"), ("ps2valley", "Valid and invalid paths", "12.4")]


def drills():
    rng = random.Random("csci5273-ps2")
    return (host_drills(rng) + carve_drills(rng) + path_drills(rng) + hop_drills() + grid_drills(rng) + dv_drills(rng) + mpls_drills(rng) + valley_drills(rng))
