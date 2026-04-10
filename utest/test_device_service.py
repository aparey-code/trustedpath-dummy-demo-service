"""Unit tests for the device trust verification service."""
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from services.device_service import DeviceService


class TestDeviceRegistration(unittest.TestCase):
    """Tests for device registration flow."""

    def setUp(self):
        self.db = AsyncMock()
        self.service = DeviceService(self.db)

    def test_register_device_creates_record(self):
        device_info = {
            "platform": "macOS",
            "os_version": "14.3",
            "serial_number": "C02XL0FGJGH5",
            "hostname": "eng-laptop-042",
        }
        self.db.execute.return_value = MagicMock(scalar_one_or_none=MagicMock(return_value=None))

        result = self.service.validate_device_info(device_info)
        self.assertTrue(result)

    def test_register_device_rejects_missing_serial(self):
        device_info = {
            "platform": "macOS",
            "os_version": "14.3",
            "hostname": "eng-laptop-042",
        }
        result = self.service.validate_device_info(device_info)
        self.assertFalse(result)

    def test_register_device_rejects_empty_platform(self):
        device_info = {
            "platform": "",
            "os_version": "14.3",
            "serial_number": "C02XL0FGJGH5",
            "hostname": "eng-laptop-042",
        }
        result = self.service.validate_device_info(device_info)
        self.assertFalse(result)


class TestDeviceTrustVerification(unittest.TestCase):
    """Tests for device posture and trust evaluation."""

    def setUp(self):
        self.db = AsyncMock()
        self.service = DeviceService(self.db)

    def test_trusted_device_passes_posture_check(self):
        posture = {
            "firewall_enabled": True,
            "disk_encrypted": True,
            "os_up_to_date": True,
            "screen_lock_enabled": True,
        }
        score = self.service.compute_trust_score(posture)
        self.assertGreaterEqual(score, 80)

    def test_untrusted_device_fails_posture_check(self):
        posture = {
            "firewall_enabled": False,
            "disk_encrypted": False,
            "os_up_to_date": False,
            "screen_lock_enabled": False,
        }
        score = self.service.compute_trust_score(posture)
        self.assertLess(score, 50)

    def test_partial_posture_gives_medium_score(self):
        posture = {
            "firewall_enabled": True,
            "disk_encrypted": True,
            "os_up_to_date": False,
            "screen_lock_enabled": False,
        }
        score = self.service.compute_trust_score(posture)
        self.assertGreaterEqual(score, 40)
        self.assertLess(score, 80)

    def test_trust_score_range_is_valid(self):
        for combo in [
            {"firewall_enabled": True, "disk_encrypted": True, "os_up_to_date": True, "screen_lock_enabled": True},
            {"firewall_enabled": False, "disk_encrypted": False, "os_up_to_date": False, "screen_lock_enabled": False},
        ]:
            score = self.service.compute_trust_score(combo)
            self.assertGreaterEqual(score, 0)
            self.assertLessEqual(score, 100)


class TestDeviceExpiry(unittest.TestCase):
    """Tests for device registration expiry logic."""

    def test_recently_registered_device_is_not_expired(self):
        registered_at = datetime.now(timezone.utc) - timedelta(hours=12)
        self.assertFalse(DeviceService.is_registration_expired(registered_at, max_age_hours=24))

    def test_old_registration_is_expired(self):
        registered_at = datetime.now(timezone.utc) - timedelta(days=30)
        self.assertTrue(DeviceService.is_registration_expired(registered_at, max_age_hours=24))

    def test_edge_case_exactly_at_expiry(self):
        registered_at = datetime.now(timezone.utc) - timedelta(hours=24)
        self.assertTrue(DeviceService.is_registration_expired(registered_at, max_age_hours=24))


if __name__ == "__main__":
    unittest.main()
