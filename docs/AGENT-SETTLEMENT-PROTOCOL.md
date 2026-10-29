# Agent Settlement Protocol — Draft v0.1
**Status: NOT IMPLEMENTED. Example below is illustrative, not an executable transfer.**

```json
{
  "schema": "imperium.agent-intent.v0.1",
  "intent_id": "EXAMPLE-001",
  "chain_id": 137,
  "token_contract": "0xcFd2149B2b1a9c0A55954A937adBee0DdaA3c9b3",
  "agent_passport": "EXAMPLE-AGENT",
  "recipient": "0x0000000000000000000000000000000000000001",
  "amount_base_units": "1000000000000000000",
  "quote_ref": "EXAMPLE-QUOTE",
  "qa_proof_hash": "EXAMPLE-ONLY",
  "expires_at": "2027-01-01T00:00:00Z",
  "nonce": "EXAMPLE-UNIQUE-NONCE",
  "approval_ref": null,
  "status": "AWAITING_APPROVAL"
}
```

All example values are placeholders. Decimals must be read from the contract; a value in base units does not imply any market price.

## State machine
`DRAFT -> QUOTED -> EXECUTED -> QA_PASSED -> ACCEPTED -> AWAITING_APPROVAL -> APPROVED -> SUBMITTED -> CONFIRMED -> RECONCILED`.

Terminal/exception states: `REJECTED`, `EXPIRED`, `PAUSED`, `FAILED`, `DISPUTED`. Never conflate `SUBMITTED` and `CONFIRMED`.

## Identity and settlement guarantees
- Signed AI Passport references are verified before access.
- Guardian Core validates scope, recipient allowlists, quote, jurisdiction, contract and spending cap.
- Approval Gateway enforces human authority; Owner Kill Switch has priority.
- An isolated signer processes **one** valid intent per nonce; retries are idempotent.
- Evidence-linked receipts include chain, transaction hash, block, confirmation depth and audit identifiers.
- Failed or uncertain execution must be investigated rather than silently retried.

## Threat-model checklist
Prompt injection, identity forgery, transaction replay, cross-chain confusion, RPC compromise, wrong-recipient attacks, duplicate payment, custody compromise, contract upgrade risk, frontrunning, network reorg and stolen approval tokens. Each threat needs a documented control and test before mainnet deployment.
