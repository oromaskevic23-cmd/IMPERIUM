# IMPERIUM — Offline Settlement Guardrail Increment

**2026-11-05 · Alexander Nikolaevich Romaskevich (RomaskevicH)**  
**Scope:** source-level in-memory simulation. Not a blockchain settlement engine, external audit or payment approval.

## Verified source boundaries

The canonical Polygon PoS Mainnet (chain ID 137) contract remains
`0xcFd2149B2b1a9c0A55954A937adBee0DdaA3c9b3`.
IMPERIUM remains a **long-term architectural digital currency intended for AI agents worldwide**. No live worldwide usage, listing, secondary-market liquidity or agent-payment production is inferred.

## Implemented security controls (local simulation)

1. Validate the spending cap as a strictly positive integer, reject empty or invalid recipient allowlists (including the zero address), and require a named approver.
2. Validate agent, intent and nonce identifiers and the exact chain/contract. Reject non-string and malformed contract identities without an uncontrolled Python exception.
3. Require newly registered `DRAFT` intents to have no prefilled QA hash, acceptance, approval or mock receipt. No caller-supplied state may pretend evidence was collected.
4. Keep payer, accepting customer and approving owner role labels separate. These labels are **not authenticated human or AI Passport identities**.
5. Recompute the hash-chained mock audit events before each state transition. Reject modified/missing events and altered chain heads instead of continuing after an observable mutation.
6. Add adversarial offline regression tests and preserve the previously documented test suite.

## Verify

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -v
python3 -m compileall -q src tests
```

Source: `src/imperium_mock/settlement.py`  
New tests: `tests/test_mock_guardrails.py`

## Limitations and next production gates

A chain of ordinary SHA-256 hashes **within one Python process is not tamper-proof**. An attacker with process write access could reconstruct the entire chain. The in-memory ledger has no durable replay store, authenticated QA signer, independently enrolled Owner key, finality verifier, wallet custody service, encryption, multi-tenant isolation, transaction broadcast or independently certified audit log.

Before real funds, implement a protected persistent Audit Ledger, cryptographically signed AI Passport and QA evidence, Guardian Core / Approval Gateway with Owner Kill Switch and per-task bounds, secure non-custodial signing, testnet rehearsals, rollback/incident procedures, external security and jurisdiction-specific legal review. Continue to enforce the Public/Private Boundary and CRYPTO IMPERIAL Ecosystem Boundary. No private key belongs in this repository or any NCA prompt.
