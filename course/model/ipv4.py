"""IPv4 arithmetic done on raw integers so it can be checked against the stdlib."""


def to_int(dotted):
    a, b, c, d = (int(x) for x in dotted.split("."))
    return a << 24 | b << 16 | c << 8 | d


def to_dotted(value):
    return ".".join(str(value >> s & 255) for s in (24, 16, 8, 0))


def mask(prefix):
    return (0xFFFFFFFF << (32 - prefix)) & 0xFFFFFFFF if prefix else 0


def to_bits(dotted):
    return ".".join(f"{int(o):08b}" for o in dotted.split("."))


def decode(dotted, prefix):
    m = mask(prefix)
    net = to_int(dotted) & m
    bcast = net | (~m & 0xFFFFFFFF)
    total = 2 ** (32 - prefix)
    return {"address": dotted, "prefix": prefix, "mask": to_dotted(m), "network": to_dotted(net),
            "broadcast": to_dotted(bcast), "total": total, "usable": total - 2,
            "first": to_dotted(net + 1), "last": to_dotted(bcast - 1),
            "address_bits": to_bits(dotted), "mask_bits": to_bits(to_dotted(m)),
            "network_bits": to_bits(to_dotted(net))}


def fragment(total, header, mtu):
    """Constant-header arithmetic with DF clear; an already fitting datagram stays whole."""
    if not (20 <= header <= 60 and header % 4 == 0 and header <= total <= 65535 and mtu >= header):
        raise ValueError("invalid IPv4 fragmentation inputs")
    payload = total - header
    if total <= mtu:
        return [{"payload": payload,"total": total,"offset_units":0,"offset_bytes":0,"mf":0}]
    if mtu < header + 8:
        raise ValueError("invalid IPv4 fragmentation inputs: no room for an aligned nonfinal payload")
    step = (mtu - header) // 8 * 8
    out, offset = [], 0
    while payload > 0:
        size = min(step, payload)
        payload -= size
        out.append({"payload": size, "total": size + header, "offset_units": offset // 8,
                    "offset_bytes": offset, "mf": 1 if payload else 0})
        offset += size
    return out


def frag_table(frags):
    return {"cols": ["Fragment", "Payload", "Total", "Offset", "MF"],
            "rows": [[i + 1, f["payload"], f["total"], f["offset_units"], f["mf"]] for i, f in enumerate(frags)]}


def checksum(words):
    """One's-complement sum of 16-bit words, complemented."""
    s = 0
    for w in words:
        s += w
        s = (s & 0xFFFF) + (s >> 16)
    return ~s & 0xFFFF


def header_words(version=4, ihl=5, tos=0, total=1500, ident=0x1C46, flags_frag=0x4000,
                 ttl=64, proto=6, csum=0, src="192.0.2.10", dst="203.0.113.80"):
    s, d = to_int(src), to_int(dst)
    return [version << 12 | ihl << 8 | tos, total, ident, flags_frag, ttl << 8 | proto, csum,
            s >> 16, s & 0xFFFF, d >> 16, d & 0xFFFF]


def checksum_example(ttl=64):
    words = header_words(ttl=ttl)
    c = checksum(words)
    return {"ttl": ttl, "checksum": f"0x{c:04X}"}


def traceroute(hops, start_ttl_max=None):
    """Probes with growing TTL: each one dies at the router where TTL reaches zero."""
    out = []
    for probe in range(1, len(hops) + 1):
        ttl, at = probe, 0
        while ttl > 1:
            ttl -= 1
            at += 1
        out.append({"probe_ttl": probe, "reply_from": hops[at],
                    "reply": "time exceeded" if at < len(hops) - 1 else "reached destination"})
    return out


def trace():
    a = decode("10.10.1.97", 23)
    frags = fragment(4000, 20, 1500)
    frags2 = fragment(3200, 20, 1000)
    return {
        "decode_97": a,
        "slash24_total": 2 ** 8, "slash23_total": 2 ** 9,
        "max_total_length": 2 ** 16 - 1,
        "ihl5_bytes": 5 * 4, "ihl6_payload": 1024 - 6 * 4,
        "frag_4000": frags, "frag_4000_table": frag_table(frags),
        "frag_4000_sent": sum(f["total"] for f in frags),
        "frag_4000_payload": sum(f["payload"] for f in frags),
        "frag_3200": frags2, "frag_3200_table": frag_table(frags2),
        "checksum_ttl64": checksum_example(64), "checksum_ttl63": checksum_example(63),
        "traceroute": traceroute(["R1", "R2", "Server"]),
        "aging_contrast": {"ip_ttl": "router hops", "dns_ttl": "seconds", "switch_timer": "seconds"},
    }
