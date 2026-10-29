#!/usr/bin/env python3
"""Offline integrity checks; no RPC credentials or live token transfers."""
import json
import pathlib
import re
import sys
root = pathlib.Path(__file__).resolve().parents[1]
required = ["README.md","SECURITY.md","CONTRIBUTING.md","docs/ARCHITECTURE.md","docs/AGENT-SETTLEMENT-PROTOCOL.md","docs/TOKEN-FACTS.md","docs/ROADMAP.md","docs/EXCHANGE-READINESS.md","docs/TRANSPARENCY.md","docs/WHITEPAPER-OUTLINE.md","registry/imperium.polygon.json"]
errors = []
for f in required:
    p = root / f
    if not p.is_file() or not p.read_text(encoding="utf-8").strip():
        errors.append("missing/empty: "+f)
try:
    token = json.loads((root/"registry/imperium.polygon.json").read_text(encoding="utf-8"))
    if token["network"]["chain_id"] != 137:
        errors.append("incorrect chain")
    if token["contract"]["address"] != "0xcFd2149B2b1a9c0A55954A937adBee0DdaA3c9b3":
        errors.append("incorrect contract")
    if token["exchange_listing_attested"] or token["verified_live_agent_settlement"]:
        errors.append("unverified status cannot be marked true")
except Exception as e:
    errors.append("invalid registry: "+str(e))
for f in required:
    p = root / f
    if p.is_file() and p.suffix == ".md":
        for dest in re.findall(r"\]\(([^)]+)\)", p.read_text(encoding="utf-8")):
            if dest.startswith(("https://","http://","#","mailto:")):
                continue
            if not (p.parent/dest.split("#")[0]).is_file():
                errors.append("broken link in "+f+": "+dest)
if errors:
    print("FAIL", *errors, sep="\n- ")
    sys.exit(1)
print("PASS: repository docs, links and identity assertions")
