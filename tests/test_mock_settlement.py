"""Tests prove offline behavior only, not production readiness."""
import unittest
from imperium_mock.settlement import Intent, MockSettlementLedger, PolicyError, CONTRACT

RECIPIENT = "0x0000000000000000000000000000000000000001"
NOW = 1000

def sample(**updates):
    data = dict(intent_id="example-1", payer_agent_id="AGENT-1",
                recipient=RECIPIENT, amount_base_units=100, nonce="nonce-1", expires_at=2000)
    data.update(updates)
    return Intent(**data)

class MockSettlementTests(unittest.TestCase):
    def setUp(self):
        self.ledger = MockSettlementLedger({RECIPIENT}, 200, "ARCHITECT-APPROVER")

    def test_happy_path_is_labeled_mock(self):
        self.ledger.register(sample(), NOW)
        self.ledger.attest_qa("example-1", "a" * 64)
        self.ledger.accept("example-1", "CLIENT")
        self.ledger.approve("example-1", "ARCHITECT-APPROVER", NOW)
        receipt = self.ledger.simulate_submission("example-1", NOW)
        self.assertTrue(receipt.startswith("MOCK-NO-ONCHAIN-TX-"))
        self.ledger.simulate_confirmation("example-1")
        self.ledger.reconcile("example-1")
        self.assertEqual(self.ledger.intents["example-1"].status, "MOCK_RECONCILED")
        self.assertEqual(len(self.ledger.audit_events), 7)

    def test_wrong_contract(self):
        with self.assertRaises(PolicyError):
            self.ledger.register(sample(token_contract="0x" + "0" * 40), NOW)

    def test_wrong_chain(self):
        with self.assertRaises(PolicyError):
            self.ledger.register(sample(chain_id=1), NOW)

    def test_unallowlisted_recipient(self):
        with self.assertRaises(PolicyError):
            self.ledger.register(sample(recipient="0x" + "2" * 40), NOW)

    def test_cap(self):
        with self.assertRaises(PolicyError):
            self.ledger.register(sample(amount_base_units=201), NOW)

    def test_duplicate_nonce(self):
        self.ledger.register(sample(), NOW)
        with self.assertRaises(PolicyError):
            self.ledger.register(sample(intent_id="example-2"), NOW)

    def test_expired(self):
        with self.assertRaises(PolicyError):
            self.ledger.register(sample(expires_at=1000), NOW)

    def test_no_submission_before_approval(self):
        self.ledger.register(sample(), NOW)
        with self.assertRaises(PolicyError):
            self.ledger.simulate_submission("example-1", NOW)

    def test_no_payer_self_acceptance(self):
        self.ledger.register(sample(), NOW)
        self.ledger.attest_qa("example-1", "b" * 64)
        with self.assertRaises(PolicyError):
            self.ledger.accept("example-1", "AGENT-1")

    def test_wrong_approver(self):
        self.ledger.register(sample(), NOW)
        self.ledger.attest_qa("example-1", "c" * 64)
        self.ledger.accept("example-1", "CLIENT")
        with self.assertRaises(PolicyError):
            self.ledger.approve("example-1", "AGENT-1", NOW)

    def test_replay_submission_denied(self):
        self.ledger.register(sample(), NOW)
        self.ledger.attest_qa("example-1", "d" * 64)
        self.ledger.accept("example-1", "CLIENT")
        self.ledger.approve("example-1", "ARCHITECT-APPROVER", NOW)
        self.ledger.simulate_submission("example-1", NOW)
        with self.assertRaises(PolicyError):
            self.ledger.simulate_submission("example-1", NOW)

    def test_wrong_qa_hash(self):
        self.ledger.register(sample(), NOW)
        with self.assertRaises(PolicyError):
            self.ledger.attest_qa("example-1", "not-a-hash")

if __name__ == "__main__":
    unittest.main()
