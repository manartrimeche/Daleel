"""
Unit tests for app.api.auth — API key and admin authentication.
"""

import asyncio
import unittest
from unittest.mock import patch, MagicMock

from fastapi import HTTPException

from app.api.auth import _constant_time_compare, require_api_key, require_admin


def _run(coro):
    return asyncio.run(coro)


def _mock_settings(api_key="", admin_key=""):
    s = MagicMock()
    s.api_key = api_key
    s.admin_api_key = admin_key
    return s


class TestConstantTimeCompare(unittest.TestCase):
    def test_equal(self):
        self.assertTrue(_constant_time_compare("abc123", "abc123"))

    def test_not_equal(self):
        self.assertFalse(_constant_time_compare("abc123", "xyz789"))

    def test_empty(self):
        self.assertTrue(_constant_time_compare("", ""))

    def test_one_empty(self):
        self.assertFalse(_constant_time_compare("abc", ""))
        self.assertFalse(_constant_time_compare("", "abc"))


class TestRequireApiKey(unittest.TestCase):
    """Unit tests for the require_api_key dependency."""

    def test_auth_disabled_returns_none(self):
        with patch("app.api.auth.get_settings", return_value=_mock_settings()):
            result = _run(require_api_key(api_key=None))
            self.assertIsNone(result)

    def test_missing_key_raises_401(self):
        with patch("app.api.auth.get_settings", return_value=_mock_settings(api_key="secret")):
            with self.assertRaises(HTTPException) as ctx:
                _run(require_api_key(api_key=None))
            self.assertEqual(ctx.exception.status_code, 401)

    def test_wrong_key_raises_403(self):
        with patch("app.api.auth.get_settings", return_value=_mock_settings(api_key="secret")):
            with self.assertRaises(HTTPException) as ctx:
                _run(require_api_key(api_key="wrong"))
            self.assertEqual(ctx.exception.status_code, 403)

    def test_correct_key_returns_key(self):
        with patch("app.api.auth.get_settings", return_value=_mock_settings(api_key="secret")):
            result = _run(require_api_key(api_key="secret"))
            self.assertEqual(result, "secret")


class TestRequireAdmin(unittest.TestCase):
    """Unit tests for the require_admin dependency."""

    def test_auth_disabled_returns_none(self):
        with patch("app.api.auth.get_settings", return_value=_mock_settings()):
            result = _run(require_admin(api_key=None))
            self.assertIsNone(result)

    def test_falls_back_to_api_key_when_admin_empty(self):
        with patch("app.api.auth.get_settings", return_value=_mock_settings(api_key="shared")):
            result = _run(require_admin(api_key="shared"))
            self.assertEqual(result, "shared")

    def test_admin_key_used_when_set(self):
        with patch("app.api.auth.get_settings", return_value=_mock_settings(api_key="user", admin_key="admin")):
            # user key should fail for admin
            with self.assertRaises(HTTPException) as ctx:
                _run(require_admin(api_key="user"))
            self.assertEqual(ctx.exception.status_code, 403)

    def test_correct_admin_key_passes(self):
        with patch("app.api.auth.get_settings", return_value=_mock_settings(api_key="user", admin_key="admin")):
            result = _run(require_admin(api_key="admin"))
            self.assertEqual(result, "admin")

    def test_missing_key_raises_401(self):
        with patch("app.api.auth.get_settings", return_value=_mock_settings(api_key="user", admin_key="admin")):
            with self.assertRaises(HTTPException) as ctx:
                _run(require_admin(api_key=None))
            self.assertEqual(ctx.exception.status_code, 401)


if __name__ == "__main__":
    unittest.main()
