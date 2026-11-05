"""Project author and founding architect: Alexander Nikolaevich Romaskevich (RomaskevicH).

OFFLINE ONLY IMPERIUM settlement state-machine proof of concept.

No wallet, RPC, transaction, exchange or live-custody functionality.
Never use this prototype for real asset transfers.
"""
from dataclasses import dataclass, replace
from hashlib import sha256
import re
from types import MappingProxyType

CONTRACT = "0xcFd2149B2b1a9c0A55954A937adBee0DdaA3c9b3"
CHAIN_ID = 137


class PolicyError(ValueError):
    """Deny-by-default violation."""


@dataclass(frozen=True)
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
        self._recipient_allowlist = frozenset(a.lower() for a in recipient_allowlist)
        self._max_amount = max_amount_base_units
        self._approver_id = approver_id
        self._intents = {}
        self._nonces = set()
        self.audit_events = []
        self.previous_hash = "0" * 64

    @property
    def recipient_allowlist(self):
        return self._recipient_allowlist

    @property
    def max_amount(self):
        return self._max_amount

    @property
    def approver_id(self):
        return self._approver_id

    @property
    def intents(self):
        return MappingProxyType(self._intents)

    @property
    def nonces(self):
        return frozenset(self._nonces)

    def _audit(self, action, intent_id):
        record = f"{self.previous_hash}|{action}|{intent_id}|MOCK_ONLY"
        digest = sha256(record.encode("utf-8")).hexdigest()
        self.audit_events.append((action, intent_id, digest))
        self.previous_hash = digest

    @staticmethod
    def _require_state(intent, state):
        if intent.status != state:
            raise PolicyError(f"Expected {state}; got {intent.status}")

    @staticmethod
    def _require_fresh(intent, now):
        if (not isinstance(now, int) or isinstance(now, bool) or
                not isinstance(intent.expires_at, int) or isinstance(intent.expires_at, bool) or
                now < 0 or intent.expires_at < 0 or now >= intent.expires_at):
            raise PolicyError("Expired or invalid intent clock")

    def register(self, intent, now):
        if not isinstance(intent, Intent):
            raise PolicyError("Intent object required")
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
        self._require_fresh(intent, now)
        if intent.intent_id in self._intents or intent.nonce in self._nonces:
            raise PolicyError("Duplicate intent ID or nonce")
        self._require_state(intent, "DRAFT")
        self._intents[intent.intent_id] = intent
        self._nonces.add(intent.nonce)
        self._audit("REGISTER", intent.intent_id)

    def attest_qa(self, intent_id, proof_sha256):
        intent = self._intents[intent_id]
        self._require_state(intent, "DRAFT")
        if not re.fullmatch(r"[0-9a-fA-F]{64}", proof_sha256):
            raise PolicyError("Independent QA evidence hash required")
        self._intents[intent_id] = replace(
            intent, qa_proof_sha256=proof_sha256.lower(), status="QA_PASSED")
        self._audit("QA_PASSED", intent_id)

    def accept(self, intent_id, accepted_by):
        intent = self._intents[intent_id]
        self._require_state(intent, "QA_PASSED")
        if not accepted_by or accepted_by == intent.payer_agent_id:
            raise PolicyError("Independent acceptance required")
        self._intents[intent_id] = replace(intent, accepted_by=accepted_by, status="ACCEPTED")
        self._audit("ACCEPTED", intent_id)

    def approve(self, intent_id, actor_id, now):
        intent = self._intents[intent_id]
        self._require_state(intent, "ACCEPTED")
        if actor_id != self.approver_id or actor_id == intent.payer_agent_id:
            raise PolicyError("Authorized separate approver required")
        self._require_fresh(intent, now)
        self._intents[intent_id] = replace(intent, approved_by=actor_id, status="APPROVED")
        self._audit("APPROVED", intent_id)

    def simulate_submission(self, intent_id, now):
        intent = self._intents[intent_id]
        self._require_state(intent, "APPROVED")
        self._require_fresh(intent, now)
        # This is intentionally NOT a chain transaction hash.
        intent = replace(intent, mock_receipt="MOCK-NO-ONCHAIN-TX-" + intent.intent_id,
                         status="MOCK_SUBMITTED")
        self._intents[intent_id] = intent
        self._audit("MOCK_SUBMITTED", intent_id)
        return intent.mock_receipt

    def simulate_confirmation(self, intent_id):
        intent = self._intents[intent_id]
        self._require_state(intent, "MOCK_SUBMITTED")
        self._intents[intent_id] = replace(intent, status="MOCK_CONFIRMED")
        self._audit("MOCK_CONFIRMED", intent_id)

    def reconcile(self, intent_id):
        intent = self._intents[intent_id]
        self._require_state(intent, "MOCK_CONFIRMED")
        self._intents[intent_id] = replace(intent, status="MOCK_RECONCILED")
        self._audit("MOCK_RECONCILED", intent_id)
