"""Unit tests for the access policy evaluation service."""
import unittest
from unittest.mock import MagicMock

from services.policy_service import evaluate_access, list_policies


class TestEvaluateAccess(unittest.TestCase):
    """Tests for the evaluate_access function."""

    def setUp(self):
        self.db = MagicMock()

    def _mock_session(self, *, is_valid=True, user_id=1):
        session = MagicMock()
        session.is_valid = is_valid
        session.user_id = user_id
        return session

    def _mock_device(self, *, owner_id=1, trust_level="trusted"):
        device = MagicMock()
        device.owner_id = owner_id
        device.trust_level = trust_level
        return device

    def _setup_db(self, session, device):
        """Configure db.execute to return session on first call and device on second."""
        result_session = MagicMock()
        result_session.scalar_one_or_none.return_value = session

        result_device = MagicMock()
        result_device.scalar_one_or_none.return_value = device

        self.db.execute.side_effect = [result_session, result_device]

    def test_access_granted_for_trusted_device(self):
        session = self._mock_session()
        device = self._mock_device(trust_level="trusted")
        self._setup_db(session, device)

        result = evaluate_access(self.db, "token123", "devkey", "standard")
        self.assertTrue(result["allowed"])

    def test_access_denied_for_invalid_session(self):
        result_session = MagicMock()
        result_session.scalar_one_or_none.return_value = None
        self.db.execute.return_value = result_session

        result = evaluate_access(self.db, "bad-token", "devkey", "standard")
        self.assertFalse(result["allowed"])
        self.assertIn("session", result["reason"].lower())

    def test_access_denied_for_expired_session(self):
        session = self._mock_session(is_valid=False)
        result_session = MagicMock()
        result_session.scalar_one_or_none.return_value = session
        self.db.execute.return_value = result_session

        result = evaluate_access(self.db, "expired", "devkey", "standard")
        self.assertFalse(result["allowed"])

    def test_access_denied_for_unknown_device(self):
        session = self._mock_session()
        self._setup_db(session, None)

        result = evaluate_access(self.db, "token123", "unknown-dev", "standard")
        self.assertFalse(result["allowed"])
        self.assertIn("unregistered", result["reason"].lower())

    def test_access_denied_for_device_not_owned_by_user(self):
        session = self._mock_session(user_id=1)
        device = self._mock_device(owner_id=99, trust_level="trusted")
        self._setup_db(session, device)

        result = evaluate_access(self.db, "token123", "devkey", "standard")
        self.assertFalse(result["allowed"])
        self.assertIn("not owned", result["reason"].lower())

    def test_access_denied_for_untrusted_device_on_strict_policy(self):
        session = self._mock_session()
        device = self._mock_device(trust_level="moderate")
        self._setup_db(session, device)

        result = evaluate_access(self.db, "token123", "devkey", "strict")
        self.assertFalse(result["allowed"])

    def test_access_granted_for_moderate_device_on_standard_policy(self):
        session = self._mock_session()
        device = self._mock_device(trust_level="moderate")
        self._setup_db(session, device)

        result = evaluate_access(self.db, "token123", "devkey", "standard")
        self.assertTrue(result["allowed"])

    def test_unknown_policy_denied(self):
        result = evaluate_access(self.db, "token", "devkey", "nonexistent")
        self.assertFalse(result["allowed"])
        self.assertIn("unknown policy", result["reason"].lower())


class TestListPolicies(unittest.TestCase):
    """Tests for the list_policies function."""

    def test_returns_all_policies(self):
        policies = list_policies()
        names = {p["name"] for p in policies}
        self.assertEqual(names, {"strict", "standard", "permissive"})

    def test_each_policy_has_trust_levels(self):
        for policy in list_policies():
            self.assertIn("accepted_trust_levels", policy)
            self.assertIsInstance(policy["accepted_trust_levels"], list)
            self.assertGreater(len(policy["accepted_trust_levels"]), 0)


if __name__ == "__main__":
    unittest.main()
