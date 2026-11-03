"""Variable-length subnet allocation, largest request first."""
from .ipv4 import decode, mask, to_dotted, to_int


def host_bits(hosts):
    h = 1
    while 2 ** h - 2 < hosts:
        h += 1
    return h


def normalize(dotted, prefix):
    return to_dotted(to_int(dotted) & mask(prefix))


def vlsm(parent, prefix, requests):
    base = to_int(normalize(parent, prefix))
    cursor, out = base, []
    for name, hosts in sorted(requests.items(), key=lambda kv: -kv[1]):
        h = host_bits(hosts)
        size = 2 ** h
        if cursor % size:
            cursor += size - cursor % size
        info = decode(to_dotted(cursor), 32 - h)
        out.append({"name": name, "hosts": hosts, "block": f"{to_dotted(cursor)}/{32 - h}", "total": size,
                    "usable": size - 2, "broadcast": info["broadcast"]})
        cursor += size
    if cursor > base + 2 ** (32 - prefix):
        raise ValueError("requests do not fit in the parent block")
    return out


DEPARTMENTS = {"A": 130, "B": 120, "C": 60, "D": 31}


def trace():
    plan = vlsm("128.101.5.0", 23, DEPARTMENTS)
    return {
        "printed_parent": "128.101.5.0/23",
        "normalized_parent": normalize("128.101.5.0", 23) + "/23",
        "plan": plan,
        "plan_table": {"cols": ["Dept", "Hosts", "Block", "Usable"],
                       "rows": [[p["name"], p["hosts"], p["block"], p["usable"]] for p in plan]},
        "plan_total": sum(p["total"] for p in plan),
        "slash27_usable": 2 ** 5 - 2,
    }
