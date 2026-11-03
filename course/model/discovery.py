"""DHCP, ARP, DNS and the complete three-subnet journey from vault example 01."""
from .ipv4 import mask, to_int

CLIENT = {"ip": "192.0.2.10", "prefix": 24, "gateway": "192.0.2.1", "dns": "198.51.100.53"}
SERVER_IP = "203.0.113.80"
# Each hop: (emitting device, source MAC, next-hop IP, destination MAC)
ROUTERS = {
    "R1": {"near": "192.0.2.1", "far": "198.51.100.1", "routes": [("198.51.100.0", 24, None), ("203.0.113.0", 24, "198.51.100.2")]},
    "R2": {"near": "198.51.100.2", "far": "203.0.113.1", "routes": [("203.0.113.0", 24, None)]},
}
NAMES = {"192.0.2.1": "R1-near", "198.51.100.2": "R2-middle", "203.0.113.80": "server", "198.51.100.53": "DNS"}


def same_subnet(a, b, prefix):
    return to_int(a) & mask(prefix) == to_int(b) & mask(prefix)


def next_hop(src, dst, prefix, gateway):
    return dst if same_subnet(src, dst, prefix) else gateway


def journey(dst=SERVER_IP, ttl=64):
    hops = []
    nh = next_hop(CLIENT["ip"], dst, CLIENT["prefix"], CLIENT["gateway"])
    hops.append({"stage": "A emits to R1", "eth_src": "A", "eth_dst": NAMES[nh], "arp_for": nh,
                 "ip_src": CLIENT["ip"], "ip_dst": dst, "ttl": ttl})
    router = "R1"
    while True:
        r = ROUTERS[router]
        ttl -= 1
        best = max((x for x in r["routes"] if to_int(dst) & mask(x[1]) == to_int(x[0]) & mask(x[1])), key=lambda x: x[1])
        nh = best[2] or dst
        src_name = "R1-middle" if router == "R1" else "R2-far"
        hops.append({"stage": f"{router} emits", "eth_src": src_name, "eth_dst": NAMES[nh], "arp_for": nh,
                     "ip_src": CLIENT["ip"], "ip_dst": dst, "ttl": ttl})
        if best[2] is None:
            return hops
        router = "R2"


def dhcp():
    return [{"msg": "Discover", "from": "client", "to": "broadcast", "means": "is any server here?"},
            {"msg": "Offer", "from": "server", "to": "client", "means": "you could use 192.0.2.10"},
            {"msg": "Request", "from": "client", "to": "broadcast", "means": "I choose that offer"},
            {"msg": "ACK", "from": "server", "to": "client", "means": "confirmed, with a lease"}]


def dns_lookup(name="www.example.test", cache=None):
    cache = dict(cache or {})
    if name in cache:
        return {"steps": [{"from": "resolver", "to": "cache", "gets": cache[name]}], "answer": cache[name], "queries_out": 0}
    labels = name.split(".")
    tld, zone = labels[-1], ".".join(labels[-2:])
    steps = [{"from": "resolver", "to": "root", "gets": f"referral to .{tld}"},
             {"from": "resolver", "to": f".{tld}", "gets": f"referral to {zone}"},
             {"from": "resolver", "to": zone, "gets": f"A {SERVER_IP}"}]
    return {"steps": steps, "answer": SERVER_IP, "queries_out": len(steps)}


def cache_valid(stored_at_s, ttl_s, now_s):
    return now_s - stored_at_s < ttl_s


def trace():
    j = journey()
    return {
        "client": CLIENT, "dhcp": dhcp(), "journey": j,
        "journey_table": {"cols": ["Stage", "Ethernet", "IP", "TTL"],
                          "rows": [[h["stage"], f"{h['eth_src']} → {h['eth_dst']}", f"A → server", h["ttl"]] for h in j]},
        "dns_is_remote": not same_subnet(CLIENT["ip"], CLIENT["dns"], 24),
        "dns_next_hop": next_hop(CLIENT["ip"], CLIENT["dns"], 24, CLIENT["gateway"]),
        "local_dns_next_hop": next_hop(CLIENT["ip"], "192.0.2.53", 24, CLIENT["gateway"]),
        "dns_cold": dns_lookup(),
        "dns_cached": dns_lookup(cache={"www.example.test": SERVER_IP}),
        "ttl_300_at_240": cache_valid(0, 300, 240),
        "ttl_300_at_300": cache_valid(0, 300, 300),
    }
