"""OFFLINE ONLY IMPERIUM settlement state-machine proof of concept.

No wallet, RPC, transaction, exchange or live-custody functionality.
Never use this prototype for real asset transfers.
"""
from dataclasses import dataclass
from hashlib import sha256
import re

CONTRACT = "0xcFd2149B2b1a9c0A55954A937adBee0DdaA3c9b3"
CHAIN_ID = 137


class PolicyError(ValueError):
    """Deny-by-default violation."""


@dataclass
class Intent:
    intent_id: str
    payer_agent_id: str
    recipient: str
    amount_base_units: int
    nonce: str
    expires_at: int
    chain_id: int = CHAIN_ID
    token_contract: str = CONTRACT
    status: str = "DRAFT"
    qa_proof_sha256: str = ""
    accepted_by: str = ""
    approved_by: str = ""
    mock_receipt: str = ""


class MockSettlementLedger:
    """In-memory state machine. All receipt strings are marked MOCK."""

    def __init__(self, recipient_allowlist, max_amount_base_units, approver_id):
        self.recipient_allowlist = {a.lower() for a in recipient_allowlist}
        self.max_amount = max_amount_base_units
        self.approver_id = approver_id
        self.intents = {}
        self.nonces = set()
        self.audit_events = []
        self.previous_hash = "0" * 64

    def _audit(self, action, intent_id):
        record = f"{self.previous_hash}|{action}|{intent_id}|MOCK_ONLY"
        digest = sha256(record.encode("utf-8")).hexdigest()
        self.audit_events.append((action, intent_id, digest))
        self.previous_hash = digest

    @staticmethod
    def _require_state(intent, state):
        if intent.status != state:
            raise PolicyError(f"Expected {state}; got {intent.status}")

    def register(self, intent, now):
        if not intent.intent_id or not intent.payer_agent_id or not intent.nonce:
            raise PolicyError("Intent identity, agent passport and nonce required")
        if intent.chain_id != CHAIN_ID or intent.token_contract.lower() != CONTRACT.lower():
            raise PolicyError("Wrong chain or contract")
        if not re.fullmatch(r"0x[0-9a-fA-F]{40}", intent.recipient):
            raise PolicyError("Invalid recipient address")
        if intent.recipient.lower() not in self.recipient_allowlist:
            raise PolicyError("Recipient not on allowlist")
        if not isinstance(intent.amount_base_units, int) or isinstance(intent.amount_base_units, bool):
            raise PolicyError("Base units must be an integer")
        if not 0 < intent.amount_base_units <= self.max_amount:
            raise PolicyError("Exceeded policy limit")
        if now >= intent.expires_at:
            raise PolicyError("Expired intent")
        if intent.intent_id in self.intents or intent.nonce in self.nonces:
            raise PolicyError("Duplicate intent ID or nonce")
        self._require_state(intent, "DRAFT")
        self.intents[intent.intent_id] = intent
        self.nonces.add(intent.nonce)
        self._audit("REGISTER", intent.intent_id)

    def attest_qa(self, intent_id, proof_sha256):
        intent = self.intents[intent_id]
        self._require_state(intent, "DRAFT")
        if not re.fullmatch(r"[0-9a-fA-F]{64}", proof_sha256):
            raise PolicyError("Independent QA evidence hash required")
        intent.qa_proof_sha256 = proof_sha256.lower()
        intent.status = "QA_PASSED"
        self._audit("QA_PASSED", intent_id)

    def accept(self, intent_id, accepted_by):
        intent = self.intents[intent_id]
        self._require_state(intent, "QA_PASSED")
        if not accepted_by or accepted_by == intent.payer_agent_id:
            raise PolicyError("Independent acceptance required")
        intent.accepted_by = accepted_by
        intent.status = "ACCEPTED"
        self._audit("ACCEPTED", intent_id)

    def approve(self, intent_id, actor_id, now):
        intent = self.intents[intent_id]
        self._require_state(intent, "ACCEPTED")
        if actor_id != self.approver_id or actor_id == intent.payer_agent_id:
            raise PolicyError("Authorized separate approver required")
        if now >= intent.expires_at:
            raise PolicyError("Intent expired")
        intent.approved_by = actor_id
        intent.status = "APPROVED"
        self._audit("APPROVED", intent_id)

    def simulate_submission(self, intent_id, now):
        intent = self.intents[intent_id]
        self._require_state(intent, "APPROVED")
        if now >= intent.expires_at:
            raise PolicyError("Intent expired")
        # This is intentionally NOT a chain transaction hash.
        intent.mock_receipt = "MOCK-NO-ONCHAIN-TX-" + intent.intent_id
        intent.status = "MOCK_SUBMITTED"
        self._audit("MOCK_SUBMITTED", intent_id)
        return intent.mock_receipt

    def simulate_confirmation(self, intent_id):
        intent = self.intents[intent_id]
        self._require_state(intent, "MOCK_SUBMITTED")
        intent.status = "MOCK_CONFIRMED"
        self._audit("MOCK_CONFIRMED", intent_id)

    def reconcile(self, intent_id):
        intent = self.intents[intent_id]
        self._require_state(intent, "MOCK_CONFIRMED")
        intent.status = "MOCK_RECONCILED"
        self._audit("MOCK_RECONCILED", intent_id)
