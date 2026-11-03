"""Router fabric capacity and queue timing."""


def output_queue(n, size_bytes, rate_bps):
    service_ms = size_bytes * 8 / rate_bps * 1000
    return [{"packet": i + 1, "wait_ms": i * service_ms, "done_ms": (i + 1) * service_ms} for i in range(n)]


def hol_round(queues):
    """One slot of strict FIFO inputs. Lowest input index wins a contested output."""
    taken, moved, blocked = set(), [], []
    for name in sorted(queues):
        q = queues[name]
        if not q:
            continue
        head = q[0]
        if head in taken:
            blocked.append({"input": name, "wanted": head, "stuck_behind": q[1:]})
        else:
            taken.add(head)
            moved.append({"input": name, "output": head})
    idle = sorted({o for q in queues.values() for o in q} - taken)
    return {"moved": moved, "blocked": blocked, "idle_outputs": idle}


def backlog_bytes(arrive_bps, serve_bps, seconds):
    return max(0, arrive_bps - serve_bps) * seconds / 8


def trace():
    q = output_queue(3, 1500, 12e6)
    return {
        "output_three": q,
        "output_table": {"cols": ["Packet", "Wait (ms)", "Done (ms)"],
                         "rows": [[p["packet"], f"{p['wait_ms']:g}", f"{p['done_ms']:g}"] for p in q]},
        "hol": hol_round({"B": [1], "C": [1, 2]}),
        "fabric_offered_gbps": 4 * 10,
        "backlog_bytes": backlog_bytes(8e6, 4e6, 0.01),
    }
