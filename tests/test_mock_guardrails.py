"""Adversarial offline tests for IMPERIUM mock only; no wallet or real payments.

Project author and founding architect: Alexander Nikolaevich Romaskevich (RomaskevicH).
"""
import unittest
from imperium_mock.settlement import Intent, MockSettlementLedger, PolicyError

RECIPIENT = "0x0000000000000000000000000000000000000001"
NOW = 1000


def intent(**changes):
    data = dict(intent_id="mock-001", payer_agent_id="AGENT-001",
                recipient=RECIPIENT, amount_base_units=100,
                nonce="nonce-001", expires_at=2000)
    data.update(changes)
    return Intent(**data)


class MockGuardrailTests(unittest.TestCase):
    def setUp(self):
        self.ledger = MockSettlementLedger([RECIPIENT], 200, "OWNER-APPROVER")

    def test_invalid_caps_and_allowlist_fail_before_any_payment_intent(self):
        for limit in [0, -1, True, "200", 1.5]:
            with self.subTest(limit=limit), self.assertRaises(PolicyError):
                MockSettlementLedger([RECIPIENT], limit, "OWNER-APPROVER")
        for recipients in [[], [None], ["0x" + "0" * 40], ["invalid"]]:
            with self.subTest(recipients=recipients), self.assertRaises(PolicyError):
                MockSettlementLedger(recipients, 200, "OWNER-APPROVER")
        for approver in [None, "", "a"]:
            with self.subTest(approver=approver), self.assertRaises(PolicyError):
                MockSettlementLedger([RECIPIENT], 200, approver)

    def test_injected_qa_approval_or_receipt_is_rejected_at_registration(self):
        for changes in [
            {"qa_proof_sha256": "a" * 64},
            {"accepted_by": "CLIENT"},
            {"approved_by": "OWNER-APPROVER"},
            {"mock_receipt": "MOCK-FAKE"},
            {"status": "QA_PASSED"}
        ]:
            with self.subTest(changes=changes), self.assertRaises(PolicyError):
                self.ledger.register(intent(**changes), NOW)
        self.assertEqual(dict(self.ledger.intents), {})
        self.assertEqual(len(self.ledger.audit_events), 0)

    def test_malformed_identity_or_contract_is_denied_with_policy_error(self):
        for changes in [
            {"intent_id": ""},
            {"payer_agent_id": None},
            {"nonce": " "},
            {"chain_id": True},
            {"token_contract": None},
            {"recipient": None},
            {"amount_base_units": True},
        ]:
            with self.subTest(changes=changes), self.assertRaises(PolicyError):
                self.ledger.register(intent(**changes), NOW)

    def test_approver_cannot_impersonate_independent_customer_acceptance(self):
        self.ledger.register(intent(), NOW)
        self.ledger.attest_qa("mock-001", "a" * 64)
        with self.assertRaisesRegex(PolicyError, "Separate customer"):
            self.ledger.accept("mock-001", "OWNER-APPROVER")
        self.assertEqual(self.ledger.intents["mock-001"].status, "QA_PASSED")

    def test_audit_chain_detects_modified_event_before_further_progress(self):
        self.ledger.register(intent(), NOW)
        self.assertTrue(self.ledger.verify_audit_chain())
        action, item, digest = self.ledger.audit_events[0]
        self.ledger.audit_events[0] = (action, item, "f" * 64)
        with self.assertRaisesRegex(PolicyError, "audit chain integrity"):
            self.ledger.verify_audit_chain()
        with self.assertRaisesRegex(PolicyError, "audit chain integrity"):
            self.ledger.attest_qa("mock-001", "a" * 64)
        self.assertEqual(self.ledger.intents["mock-001"].status, "DRAFT")

    def test_audit_chain_detects_missing_event_and_invalid_head(self):
        self.ledger.register(intent(), NOW)
        self.ledger.audit_events.clear()
        with self.assertRaisesRegex(PolicyError, "head mismatch"):
            self.ledger.verify_audit_chain()

    def test_normal_mock_lifecycle_preserves_audit_integrity_and_never_signs(self):
        self.ledger.register(intent(), NOW)
        self.ledger.attest_qa("mock-001", "b" * 64)
        self.ledger.accept("mock-001", "CLIENT")
        self.ledger.approve("mock-001", "OWNER-APPROVER", NOW)
        receipt = self.ledger.simulate_submission("mock-001", NOW)
        self.assertTrue(receipt.startswith("MOCK-NO-ONCHAIN-TX-"))
        self.ledger.simulate_confirmation("mock-001")
        self.ledger.reconcile("mock-001")
        self.assertTrue(self.ledger.verify_audit_chain())
        self.assertEqual(self.ledger.intents["mock-001"].status, "MOCK_RECONCILED")


if __name__ == "__main__":
    unittest.main()
