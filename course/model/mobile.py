"""Tunnels, indirect versus direct delivery, and handover state."""

HOME, HA, COA, COA2, CORR = "192.0.2.20", "192.0.2.1", "198.51.100.44", "203.0.113.44", "203.0.113.10"


def tunnel_headers(coa=COA):
    return [{"position": "Correspondent sends", "outer": None, "inner": f"{CORR} → {HOME}"},
            {"position": "Home agent encapsulates", "outer": f"{HA} → {coa}", "inner": f"{CORR} → {HOME}"},
            {"position": "Inside the tunnel", "outer": f"{HA} → {coa}", "inner": f"{CORR} → {HOME}"},
            {"position": "Endpoint decapsulates", "outer": None, "inner": f"{CORR} → {HOME}"}]


def encapsulated(inner, overhead=20):
    return inner + overhead


def triangle(to_anchor, to_mobile, direct):
    return {"indirect": to_anchor + to_mobile, "direct": direct, "saving": to_anchor + to_mobile - direct}


def handover_states():
    return [{"phase": "before", "path": ["S-GW", "A", "UE"], "outer_dst": "A"},
            {"phase": "during", "path": ["S-GW", "A", "B", "UE"], "outer_dst": "A"},
            {"phase": "after", "path": ["S-GW", "B", "UE"], "outer_dst": "B"}]


def handover_steps():
    return ["A selects target B and requests resources", "B reserves resources and acknowledges",
            "A tells the UE to switch; the UE starts using B", "Packets reaching A are forwarded to B",
            "B reports completion; MME tells S-GW to change the endpoint", "S-GW sends directly to B; old resources released"]


def trace():
    return {
        "home": HOME, "coa": COA, "coa2": COA2, "corr": CORR,
        "headers": tunnel_headers(), "headers2": tunnel_headers(COA2),
        "headers_table": {"cols": ["Position", "Outer header", "Inner header"],
                          "rows": [[h["position"], h["outer"] or "none", h["inner"]] for h in tunnel_headers()]},
        "size_1480": encapsulated(1480), "size_1500": encapsulated(1500),
        "example": triangle(40, 50, 10), "guide": triangle(60, 70, 5),
        "handover": handover_states(), "steps": handover_steps(),
        "gtp_stack": ["Outer IP", "UDP", "GTP-U", "Inner IP", "Payload"],
    }
