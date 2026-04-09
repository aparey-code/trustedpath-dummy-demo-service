"""Unit tests for authentication service."""

import unittest

from services.auth_service import hash_password, verify_password


class TestPasswordHashing(unittest.TestCase):

    def test_hash_and_verify_roundtrip(self):
        password = "correct-horse-battery-staple"
        hashed, salt = hash_password(password)
        self.assertTrue(verify_password(password, hashed, salt))

    def test_wrong_password_fails(self):
        password = "correct-horse-battery-staple"
        hashed, salt = hash_password(password)
        self.assertFalse(verify_password("wrong-password", hashed, salt))

    def test_different_salts_produce_different_hashes(self):
        password = "test-password"
        hash1, salt1 = hash_password(password)
        hash2, salt2 = hash_password(password)
        self.assertNotEqual(salt1, salt2)
        self.assertNotEqual(hash1, hash2)

    def test_same_salt_produces_same_hash(self):
        password = "test-password"
        salt = "fixed-salt-for-test"
        hash1, _ = hash_password(password, salt)
        hash2, _ = hash_password(password, salt)
        self.assertEqual(hash1, hash2)


class TestDeviceTrustLevel(unittest.TestCase):

    def test_compute_trust_level_trusted(self):
        from services.device_service import _compute_trust_level
        self.assertEqual(_compute_trust_level(95.0), "trusted")

    def test_compute_trust_level_moderate(self):
        from services.device_service import _compute_trust_level
        self.assertEqual(_compute_trust_level(65.0), "moderate")

    def test_compute_trust_level_untrusted(self):
        from services.device_service import _compute_trust_level
        self.assertEqual(_compute_trust_level(30.0), "untrusted")


if __name__ == "__main__":
    unittest.main()
