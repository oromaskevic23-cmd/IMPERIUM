# Evidence-Gated Engineering Roadmap

| Gate | Completion criterion | Current evidence |
|---|---|---|
| G0 — Contract identity | Exact-match deployed-source verification | **PASS:** Sourcify |
| G1 — Token review | Block-anchored supply, decimals, permissions, concentration | **PENDING** |
| G2 — Disclosure | Verified allocations, treasury and vesting, rights and risks | **PENDING** |
| G3 — Mock settlement | State machine, approval and replay tests (zero value) | **NOT IMPLEMENTED** |
| G4 — Security | Independent audit, threat model, incident plan | **PENDING** |
| G5 — Authorized pilot | Testnet then strictly controlled live payment evidence | **PENDING** |
| G6 — Commercial proof | Reconciled real customer invoices and usage | **PENDING** |
| G7 — Listing dossier | Validated technical, market, legal and applicant documents | **PENDING** |
| G8 — Listing decision | Official exchange confirmation | **NOT CLAIMED** |

## Suggested engineering sprints
**Sprint 1:** establish on-chain read-only attestation, admin privileges, supply facts and disclosure register.  
**Sprint 2:** build mock transaction lifecycle, replay protection, negative tests and CI.  
**Sprint 3:** plan signer and Approval Gateway isolation, threat model and proof collection.  
**Sprint 4:** independent QA, legal review, actual use-case pilot assessment and release decision.

Completion reports must state commit SHA, environment, test evidence, incident limitations, responsible reviewers and explicit PASS / FAIL / BLOCKED. Roadmap tasks never constitute a forecast of market price or exchange acceptance.
