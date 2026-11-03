"""SNR, code-division arithmetic, contention counters, and who-hears-whom."""
import math


def snr_db(ratio):
    return 10 * math.log10(ratio)


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def cdma_sum(pairs):
    n = len(pairs[0][1])
    return [sum(bit * code[i] for bit, code in pairs) for i in range(n)]


def cdma_decode(z, code):
    return dot(z, code) / dot(code, code)


C1, C2 = (1, 1, -1, -1), (1, -1, 1, -1)


def cdma_table(d1, d2):
    z = cdma_sum([(d1, C1), (d2, C2)])
    return {"cols": ["Chip", "c1", "c2", "d1·c1", "d2·c2", "z"],
            "rows": [[i + 1, C1[i], C2[i], d1 * C1[i], d2 * C2[i], z[i]] for i in range(4)]}


def backoff_counter(start, events):
    n, out = start, []
    for e in events:
        if e == "idle" and n > 0:
            n -= 1
        out.append({"event": e, "counter": n})
    return out


HEARS = {("A", "B"), ("B", "C")}


def hears(a, b, links=HEARS):
    return (a, b) in links or (b, a) in links


def hidden_pair(a, c, receiver, links=HEARS):
    return not hears(a, c, links) and hears(a, receiver, links) and hears(c, receiver, links)


def nav_defer(heard_frame, duration):
    return {"heard": heard_frame, "defer_for": duration}


def spread(bit, code):
    return [bit * c for c in code]


def products(z, code):
    return [a * b for a, b in zip(z, code)]


def trace():
    z1, z2 = cdma_sum([(1, C1), (-1, C2)]), cdma_sum([(-1, C1), (-1, C2)])
    return {
        "c1": list(C1), "c2": list(C2),
        "first_rows": {"a": spread(1, C1), "b": spread(-1, C2), "corr1": products(z1, C1), "corr2": products(z1, C2)},
        "second_rows": {"a": spread(-1, C1), "b": spread(-1, C2), "corr1": products(z2, C1), "corr2": products(z2, C2)},
        "snr_100": snr_db(100),
        "c1c2_dot": dot(C1, C2), "c1c1_dot": dot(C1, C1),
        "first": {"z": cdma_sum([(1, C1), (-1, C2)]), "d1": cdma_decode(cdma_sum([(1, C1), (-1, C2)]), C1),
                  "d2": cdma_decode(cdma_sum([(1, C1), (-1, C2)]), C2)},
        "first_table": cdma_table(1, -1),
        "second": {"z": cdma_sum([(-1, C1), (-1, C2)]), "d1": cdma_decode(cdma_sum([(-1, C1), (-1, C2)]), C1),
                   "d2": cdma_decode(cdma_sum([(-1, C1), (-1, C2)]), C2)},
        "second_table": cdma_table(-1, -1),
        "backoff": backoff_counter(4, ["idle", "idle", "busy", "idle", "idle"]),
        "backoff_exam": backoff_counter(3, ["idle", "idle", "busy"]),
        "hidden_AC": hidden_pair("A", "C", "B"),
        "rtscts": ["RTS", "CTS", "DATA", "ACK"],
    }
