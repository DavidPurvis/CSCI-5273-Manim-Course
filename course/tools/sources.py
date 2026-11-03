"""Turn the midterm vault and instructor decks into checked, structured data."""
import hashlib
import json
import re
from pathlib import Path

import logging

import yaml
import os

from pypdf import PdfReader

logging.getLogger("pypdf").setLevel(logging.ERROR)

ROOT = Path(__file__).resolve().parents[2]
VAULT = ROOT / "sources/snapshot/vault"
DECKS = VAULT / "Assets/Slides"
OLD_VAULT = None


def main():
    out = ROOT / "sources"
    decks = {}
    recorded = {x["file"]: x["sha256"] for x in json.loads((VAULT.parent / "vault-source-manifest.json").read_text())}
    for pdf in sorted(DECKS.glob("lec*.pdf")):
        digest = hashlib.sha256(pdf.read_bytes()).hexdigest()
        if pdf.name in recorded and recorded[pdf.name] != digest:
            raise SystemExit(f"{pdf.name} no longer matches the vault's recorded hash")
        decks[pdf.name] = {"pages": len(PdfReader(pdf).pages), "sha256": digest, "vault_verified": pdf.name in recorded}
    (out / "decks.json").write_text(json.dumps(decks, indent=1))
    start = (VAULT / "00 - Start Here.md").read_text()
    concepts = {}
    lecture = None
    for line in start.splitlines():
        m = re.match(r"### \[\[(L\d\d)", line)
        if m:
            lecture = m.group(1)
        elif lecture and line.startswith("[["):
            for name in re.findall(r"\[\[([^\]|]+)", line):
                front = (VAULT / "Concepts" / f"{name}.md").read_text().split("---")[1]
                meta = yaml.safe_load(front)
                definition = re.search(r"\[!definition\] Definition\n> (.+)", (VAULT / "Concepts" / f"{name}.md").read_text())
                concepts[name] = {"lecture": lecture, "pages": meta["source-pages"], "definition": definition.group(1) if definition else ""}
        elif line.startswith("## Worked"):
            lecture = None
    if len(concepts) != 176:
        raise SystemExit(f"expected 176 concepts, found {len(concepts)}")
    (out / "concepts.json").write_text(json.dumps(concepts, indent=1, ensure_ascii=False))
    print(f"{len(decks)} decks, {len(concepts)} concepts")


if __name__ == "__main__":
    main()
