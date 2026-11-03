"""Freeze every model's results as JSON. The chef only ever reads these files."""
import importlib
import json
from pathlib import Path

MODULES = ["ethernet", "ipv4", "subnet", "lpm", "router", "discovery", "routing",
           "convergence", "bgp", "multicast", "wireless", "mobile", "practice"]
ROOT = Path(__file__).resolve().parents[2]


def main():
    for name in MODULES:
        mod = importlib.import_module(f"course.model.{name}")
        path = ROOT / "traces" / f"{name}.json"
        path.write_text(json.dumps(mod.trace(), indent=1, ensure_ascii=False, default=str, sort_keys=True) + "\n")
    print(f"froze {len(MODULES)} trace files")


if __name__ == "__main__":
    main()
