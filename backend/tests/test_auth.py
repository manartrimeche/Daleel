"""
Unit tests for authentication: API keys, JWT, password validation,
token blacklist, and password reset.
"""

import asyncio
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock, AsyncMock

from bson import ObjectId
from fastapi import HTTPException

from app.api.auth import (
    _constant_time_compare,
    require_admin,
    require_api_key,
    require_api_key_or_roles,
)
from app.api.auth_router import _as_utc
from app.schemas_auth import (
    RegisterRequest,
    ChangePasswordRequest,
    ResetPasswordRequest,
    AcceptInvitationRequest,
)
from app.services.auth_service import (
    calculate_subscription_end_date,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    is_subscription_expired,
    normalize_subscription_type,
    serialize_organization,
    verify_password,
)


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

    def test_auth_disabled_raises_401(self):
        with patch("app.api.auth.get_settings", return_value=_mock_settings()):
            with self.assertRaises(HTTPException) as ctx:
                _run(require_api_key(api_key=None))
            self.assertEqual(ctx.exception.status_code, 401)

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

    def test_auth_disabled_raises_401(self):
        with patch("app.api.auth.get_settings", return_value=_mock_settings()):
            with self.assertRaises(HTTPException) as ctx:
                _run(require_admin(api_key=None))
            self.assertEqual(ctx.exception.status_code, 401)

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


class TestRequireApiKeyOrRoles(unittest.TestCase):
    def test_allowed_jwt_role_passes(self):
        checker = require_api_key_or_roles("owner", "admin", "member")
        fake_user = {"role": "member", "_id": "u1", "is_active": True}

        with patch("app.api.auth.get_optional_current_user", AsyncMock(return_value=fake_user)):
            result = _run(checker(api_key=None, credentials=MagicMock()))

        self.assertEqual(result, "jwt")

    def test_disallowed_jwt_role_raises_403(self):
        checker = require_api_key_or_roles("owner", "admin", "member")
        fake_user = {"role": "viewer", "_id": "u1", "is_active": True}

        with patch("app.api.auth.get_optional_current_user", AsyncMock(return_value=fake_user)):
            with self.assertRaises(HTTPException) as ctx:
                _run(checker(api_key=None, credentials=MagicMock()))

        self.assertEqual(ctx.exception.status_code, 403)

    def test_api_key_fallback_still_passes(self):
        checker = require_api_key_or_roles("owner", "admin", "member")
        with patch("app.api.auth.get_optional_current_user", AsyncMock(return_value=None)), \
             patch("app.api.auth.get_settings", return_value=_mock_settings(api_key="secret")):
            result = _run(checker(api_key="secret", credentials=None))

        self.assertEqual(result, "secret")


class TestSubscriptionHelpers(unittest.TestCase):
    def test_monthly_subscription_adds_one_month(self):
        start = datetime(2026, 5, 16, 10, 30, tzinfo=timezone.utc)
        end = calculate_subscription_end_date(start, "monthly")
        self.assertEqual(end, datetime(2026, 6, 16, 10, 30, tzinfo=timezone.utc))

    def test_annual_subscription_adds_one_year(self):
        start = datetime(2026, 5, 16, 10, 30, tzinfo=timezone.utc)
        end = calculate_subscription_end_date(start, "annual")
        self.assertEqual(end, datetime(2027, 5, 16, 10, 30, tzinfo=timezone.utc))

    def test_month_end_is_clamped(self):
        start = datetime(2025, 1, 31, 10, 30, tzinfo=timezone.utc)
        end = calculate_subscription_end_date(start, "monthly")
        self.assertEqual(end, datetime(2025, 2, 28, 10, 30, tzinfo=timezone.utc))

    def test_unknown_subscription_defaults_to_monthly(self):
        self.assertEqual(normalize_subscription_type("bad"), "monthly")

    def test_existing_organization_without_subscription_gets_default(self):
        created_at = datetime(2026, 5, 16, 10, 30, tzinfo=timezone.utc)
        org = {
            "_id": "org-id",
            "name": "Ancienne SARL",
            "sector": "services",
            "jurisdiction": "tunisia",
            "status": "active",
            "created_at": created_at,
            "updated_at": created_at,
        }
        data = serialize_organization(org)
        self.assertEqual(data["subscription_type"], "monthly")
        self.assertEqual(
            data["subscription_started_at"],
            created_at,
        )
        self.assertEqual(
            data["subscription_ends_at"],
            datetime(2026, 6, 16, 10, 30, tzinfo=timezone.utc),
        )

    def test_subscription_expired_when_end_date_is_past(self):
        now = datetime(2026, 5, 21, 12, 0, tzinfo=timezone.utc)
        org = {"subscription_ends_at": datetime(2026, 5, 21, 11, 59, tzinfo=timezone.utc)}
        self.assertTrue(is_subscription_expired(org, now))

    def test_subscription_not_expired_when_end_date_is_future(self):
        now = datetime(2026, 5, 21, 12, 0, tzinfo=timezone.utc)
        org = {"subscription_ends_at": datetime(2026, 5, 21, 12, 1, tzinfo=timezone.utc)}
        self.assertFalse(is_subscription_expired(org, now))


class TestInvitationDatetimeHelpers(unittest.TestCase):
    def test_as_utc_adds_utc_timezone_to_mongodb_naive_datetime(self):
        value = datetime(2026, 5, 20, 21, 39, 27)
        converted = _as_utc(value)
        self.assertEqual(converted, datetime(2026, 5, 20, 21, 39, 27, tzinfo=timezone.utc))

    def test_as_utc_preserves_aware_utc_datetime(self):
        value = datetime(2026, 5, 20, 21, 39, 27, tzinfo=timezone.utc)
        self.assertEqual(_as_utc(value), value)


class TestPasswordValidation(unittest.TestCase):
    """Pydantic password strength validator."""

    def _validate(self, password: str):
        from app.schemas_auth import _validate_password_strength
        return _validate_password_strength(password)

    def test_valid_password(self):
        result = self._validate("Str0ng!Pass")
        self.assertEqual(result, "Str0ng!Pass")

    def test_missing_uppercase(self):
        with self.assertRaises(ValueError) as ctx:
            self._validate("nouppercase1!")
        self.assertIn("majuscule", str(ctx.exception))

    def test_missing_lowercase(self):
        with self.assertRaises(ValueError) as ctx:
            self._validate("NOLOWERCASE1!")
        self.assertIn("minuscule", str(ctx.exception))

    def test_missing_digit(self):
        with self.assertRaises(ValueError) as ctx:
            self._validate("NoDigits!Here")
        self.assertIn("chiffre", str(ctx.exception))

    def test_missing_special_char(self):
        with self.assertRaises(ValueError) as ctx:
            self._validate("NoSpecial1Here")
        self.assertIn("spécial", str(ctx.exception))

    def test_all_rules_together(self):
        self.assertEqual(self._validate("aB3$xxxx"), "aB3$xxxx")


class TestPasswordSchemaIntegration(unittest.TestCase):
    """Ensure password validators fire on all relevant schemas."""

    def test_register_request_rejects_weak_password(self):
        from pydantic import ValidationError
        with self.assertRaises(ValidationError):
            RegisterRequest(
                email="a@b.com",
                phone="+21698123456",
                password="weakpass",
                full_name="Test User",
                organization_name="Org",
                sector="finance",
                country="tunisia",
            )

    def test_change_password_rejects_weak_password(self):
        from pydantic import ValidationError
        with self.assertRaises(ValidationError):
            ChangePasswordRequest(
                current_password="old",
                new_password="weakpass",
            )

    def test_reset_password_rejects_weak_password(self):
        from pydantic import ValidationError
        with self.assertRaises(ValidationError):
            ResetPasswordRequest(
                token="tok",
                new_password="weakpass",
            )

    def test_accept_invitation_rejects_weak_password(self):
        from pydantic import ValidationError
        with self.assertRaises(ValidationError):
            AcceptInvitationRequest(
                token="tok",
                full_name="Test User",
                password="weakpass",
            )


class TestPasswordHashing(unittest.TestCase):
    def test_hash_and_verify(self):
        pw = "Str0ng!Pass"
        h = hash_password(pw)
        self.assertTrue(verify_password(pw, h))

    def test_wrong_password_fails(self):
        h = hash_password("Str0ng!Pass")
        self.assertFalse(verify_password("Wrong!Pass1", h))

    def test_hash_is_not_plaintext(self):
        h = hash_password("Str0ng!Pass")
        self.assertNotEqual(h, "Str0ng!Pass")
        self.assertTrue(h.startswith("$2"))


class TestJWT(unittest.TestCase):
    """JWT create / decode with PyJWT."""

    def test_access_token_roundtrip(self):
        token = create_access_token("user123", "admin", "org456")
        payload = decode_token(token)
        self.assertEqual(payload["sub"], "user123")
        self.assertEqual(payload["role"], "admin")
        self.assertEqual(payload["org_id"], "org456")
        self.assertEqual(payload["type"], "access")

    def test_refresh_token_roundtrip(self):
        token = create_refresh_token("user123")
        payload = decode_token(token)
        self.assertEqual(payload["sub"], "user123")
        self.assertEqual(payload["type"], "refresh")
        self.assertIn("jti", payload)
        self.assertIn("iat", payload)

    def test_refresh_token_has_iat(self):
        token = create_refresh_token("user123")
        payload = decode_token(token)
        self.assertIsInstance(payload["iat"], int)
        now_ts = datetime.now(timezone.utc).timestamp()
        self.assertAlmostEqual(payload["iat"], now_ts, delta=5)

    def test_expired_token_raises(self):
        import jwt as pyjwt
        settings = MagicMock()
        settings.jwt_secret_key = "test-secret-key-for-unit-tests-1234"
        settings.jwt_algorithm = "HS256"
        expired_payload = {
            "sub": "user123",
            "type": "access",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
        }
        with patch("app.services.auth_service.get_settings", return_value=settings):
            token = pyjwt.encode(expired_payload, settings.jwt_secret_key, algorithm="HS256")
            with self.assertRaises(Exception):
                decode_token(token)

    def test_access_token_without_org(self):
        token = create_access_token("user123", "viewer", None)
        payload = decode_token(token)
        self.assertIsNone(payload["org_id"])

    def test_tampered_token_raises(self):
        token = create_access_token("user123", "admin", None)
        tampered = token[:-4] + "XXXX"
        with self.assertRaises(Exception):
            decode_token(tampered)


class TestTokenBlacklist(unittest.TestCase):
    """Token blacklist with revoke_all_before logic."""

    def test_blacklist_single_token(self):
        mock_collection = MagicMock()
        mock_collection.insert_one = AsyncMock()
        mock_collection.find_one = AsyncMock(return_value={"jti": "abc"})

        with patch("app.services.auth_service._token_blacklist", mock_collection):
            from app.services.auth_service import blacklist_token, is_token_blacklisted

            _run(blacklist_token("abc", "user1", datetime.now(timezone.utc)))
            mock_collection.insert_one.assert_called_once()

            result = _run(is_token_blacklisted("abc"))
            self.assertTrue(result)

    def test_non_blacklisted_token(self):
        mock_collection = MagicMock()
        mock_collection.find_one = AsyncMock(return_value=None)

        with patch("app.services.auth_service._token_blacklist", mock_collection):
            from app.services.auth_service import is_token_blacklisted
            result = _run(is_token_blacklisted("nonexistent"))
            self.assertFalse(result)

    def test_revoke_all_before_blocks_old_token(self):
        now = datetime.now(timezone.utc)
        old_iat = now - timedelta(hours=1)

        call_count = [0]
        async def mock_find_one(query):
            call_count[0] += 1
            if "jti" in query and "$exists" not in str(query):
                return None
            if "revoke_all_before" in query:
                return {"user_id": "user1", "revoke_all_before": now}
            return None

        mock_collection = MagicMock()
        mock_collection.find_one = mock_find_one

        with patch("app.services.auth_service._token_blacklist", mock_collection):
            from app.services.auth_service import is_token_blacklisted
            result = _run(is_token_blacklisted("some-jti", "user1", old_iat))
            self.assertTrue(result)

    def test_revoke_all_before_allows_new_token(self):
        now = datetime.now(timezone.utc)
        new_iat = now + timedelta(seconds=10)

        async def mock_find_one(query):
            if "jti" in query and "revoke_all_before" not in query:
                return None
            if "revoke_all_before" in query:
                return None
            return None

        mock_collection = MagicMock()
        mock_collection.find_one = mock_find_one

        with patch("app.services.auth_service._token_blacklist", mock_collection):
            from app.services.auth_service import is_token_blacklisted
            result = _run(is_token_blacklisted("some-jti", "user1", new_iat))
            self.assertFalse(result)

    def test_blacklist_all_user_tokens(self):
        mock_collection = MagicMock()
        mock_result = MagicMock()
        mock_result.inserted_id = "fake_id"
        mock_collection.insert_one = AsyncMock(return_value=mock_result)

        with patch("app.services.auth_service._token_blacklist", mock_collection):
            from app.services.auth_service import blacklist_all_user_tokens
            count = _run(blacklist_all_user_tokens("user1"))
            self.assertEqual(count, 1)
            call_args = mock_collection.insert_one.call_args[0][0]
            self.assertIn("revoke_all_before", call_args)
            self.assertTrue(call_args["jti"].startswith("all-user1-"))


class TestPasswordResetTokens(unittest.TestCase):
    """Password reset token lifecycle."""

    def test_create_reset_token_for_existing_user(self):
        mock_resets = MagicMock()
        mock_resets.delete_many = AsyncMock()
        mock_resets.insert_one = AsyncMock()

        fake_user = {"_id": "user1", "email": "a@b.com"}

        with patch("app.services.auth_service._password_resets", mock_resets), \
             patch("app.services.auth_service.get_user_by_email", AsyncMock(return_value=fake_user)):
            from app.services.auth_service import create_password_reset_token
            token = _run(create_password_reset_token("a@b.com"))
            self.assertIsNotNone(token)
            self.assertGreater(len(token), 20)
            mock_resets.delete_many.assert_called_once()
            mock_resets.insert_one.assert_called_once()

    def test_create_reset_token_for_missing_user_returns_none(self):
        with patch("app.services.auth_service.get_user_by_email", AsyncMock(return_value=None)):
            from app.services.auth_service import create_password_reset_token
            token = _run(create_password_reset_token("missing@b.com"))
            self.assertIsNone(token)

    def test_validate_reset_token_valid(self):
        future = datetime.now(timezone.utc) + timedelta(hours=1)
        doc = {"token": "tok", "used": False, "expires_at": future, "user_id": "u1"}

        mock_resets = MagicMock()
        mock_resets.find_one = AsyncMock(return_value=doc)

        with patch("app.services.auth_service._password_resets", mock_resets):
            from app.services.auth_service import validate_reset_token
            result = _run(validate_reset_token("tok"))
            self.assertIsNotNone(result)
            self.assertEqual(result["user_id"], "u1")

    def test_validate_reset_token_expired(self):
        past = datetime(2020, 1, 1, tzinfo=timezone.utc)
        doc = {"token": "tok", "used": False, "expires_at": past, "user_id": "u1"}

        mock_resets = MagicMock()
        mock_resets.find_one = AsyncMock(return_value=doc)

        with patch("app.services.auth_service._password_resets", mock_resets):
            from app.services.auth_service import validate_reset_token
            result = _run(validate_reset_token("tok"))
            self.assertIsNone(result)

    def test_validate_reset_token_not_found(self):
        mock_resets = MagicMock()
        mock_resets.find_one = AsyncMock(return_value=None)

        with patch("app.services.auth_service._password_resets", mock_resets):
            from app.services.auth_service import validate_reset_token
            result = _run(validate_reset_token("nonexistent"))
            self.assertIsNone(result)


class TestGetCurrentUser(unittest.TestCase):
    """JWT-based get_current_user dependency."""

    def test_missing_credentials_raises_401(self):
        from app.api.auth import get_current_user
        with self.assertRaises(HTTPException) as ctx:
            _run(get_current_user(credentials=None))
        self.assertEqual(ctx.exception.status_code, 401)

    def test_valid_token_returns_user(self):
        from app.api.auth import get_current_user
        from bson import ObjectId

        token = create_access_token("507f1f77bcf86cd799439011", "member", "org1")
        creds = MagicMock()
        creds.credentials = token

        fake_user = {
            "_id": ObjectId("507f1f77bcf86cd799439011"),
            "email": "a@b.com",
            "role": "member",
            "is_active": True,
        }

        with patch("app.services.auth_service.get_user_by_id", AsyncMock(return_value=fake_user)), \
             patch("app.services.auth_service.is_token_blacklisted", AsyncMock(return_value=False)):
            result = _run(get_current_user(credentials=creds))
            self.assertEqual(result["email"], "a@b.com")

    def test_inactive_user_raises_403(self):
        from app.api.auth import get_current_user
        from bson import ObjectId

        token = create_access_token("507f1f77bcf86cd799439011", "member", None)
        creds = MagicMock()
        creds.credentials = token

        fake_user = {
            "_id": ObjectId("507f1f77bcf86cd799439011"),
            "email": "a@b.com",
            "role": "member",
            "is_active": False,
        }

        with patch("app.services.auth_service.get_user_by_id", AsyncMock(return_value=fake_user)), \
             patch("app.services.auth_service.is_token_blacklisted", AsyncMock(return_value=False)):
            with self.assertRaises(HTTPException) as ctx:
                _run(get_current_user(credentials=creds))
            self.assertEqual(ctx.exception.status_code, 403)

    def test_invalid_token_raises_401(self):
        from app.api.auth import get_current_user
        creds = MagicMock()
        creds.credentials = "invalid.token.here"
        with self.assertRaises(HTTPException) as ctx:
            _run(get_current_user(credentials=creds))
        self.assertEqual(ctx.exception.status_code, 401)

    def test_refresh_token_type_raises_401(self):
        from app.api.auth import get_current_user
        token = create_refresh_token("507f1f77bcf86cd799439011")
        creds = MagicMock()
        creds.credentials = token
        with self.assertRaises(HTTPException) as ctx:
            _run(get_current_user(credentials=creds))
        self.assertEqual(ctx.exception.status_code, 401)


class TestGetOptionalCurrentUser(unittest.TestCase):
    def test_no_credentials_returns_none(self):
        from app.api.auth import get_optional_current_user
        result = _run(get_optional_current_user(credentials=None))
        self.assertIsNone(result)

    def test_invalid_token_returns_none(self):
        from app.api.auth import get_optional_current_user
        creds = MagicMock()
        creds.credentials = "bad.token"
        result = _run(get_optional_current_user(credentials=creds))
        self.assertIsNone(result)


class TestRequireRole(unittest.TestCase):
    def test_allowed_role_passes(self):
        from app.api.auth import require_role
        checker = require_role("admin", "super_admin")
        user = {"role": "admin", "_id": "u1"}
        result = _run(checker(user=user))
        self.assertEqual(result["role"], "admin")

    def test_disallowed_role_raises_403(self):
        from app.api.auth import require_role
        checker = require_role("admin", "super_admin")
        user = {"role": "viewer", "_id": "u1"}
        with self.assertRaises(HTTPException) as ctx:
            _run(checker(user=user))
        self.assertEqual(ctx.exception.status_code, 403)

    def test_error_message_is_generic(self):
        from app.api.auth import require_role
        checker = require_role("admin")
        user = {"role": "viewer", "_id": "u1"}
        with self.assertRaises(HTTPException) as ctx:
            _run(checker(user=user))
        self.assertNotIn("admin", ctx.exception.detail.lower())
        self.assertIn("insuffisantes", ctx.exception.detail.lower())


class TestInvitationScope(unittest.TestCase):
    def test_revoke_invitation_scopes_by_organization(self):
        from app.services import auth_service

        invitations = MagicMock()
        result = MagicMock()
        result.modified_count = 1
        invitations.update_one = AsyncMock(return_value=result)

        invitation_id = "507f1f77bcf86cd799439011"
        with patch("app.services.auth_service._invitations", invitations):
            revoked = _run(
                auth_service.revoke_invitation(
                    invitation_id,
                    organization_id="org-a",
                )
            )

        self.assertTrue(revoked)
        invitations.update_one.assert_awaited_once_with(
            {
                "_id": auth_service.ObjectId(invitation_id),
                "organization_id": "org-a",
            },
            {"$set": {"status": "revoked"}},
        )


class TestOwnerUniqueness(unittest.TestCase):
    def test_create_owner_requires_organization(self):
        from app.services import auth_service

        with self.assertRaises(ValueError):
            _run(
                auth_service.create_user(
                    email="owner@example.com",
                    password_hash="hash",
                    full_name="Owner",
                    role="owner",
                    organization_id=None,
                )
            )

    def test_create_owner_rejects_existing_owner(self):
        from app.services import auth_service

        users = MagicMock()
        users.find_one = AsyncMock(return_value={"_id": ObjectId()})
        users.insert_one = AsyncMock()

        with patch("app.services.auth_service._users", users):
            with self.assertRaises(ValueError):
                _run(
                    auth_service.create_user(
                        email="owner2@example.com",
                        password_hash="hash",
                        full_name="Owner Two",
                        role="owner",
                        organization_id="org-a",
                    )
                )

        users.insert_one.assert_not_called()

    def test_update_user_rejects_owner_role_change(self):
        from app.services import auth_service

        user_id = "507f1f77bcf86cd799439011"
        users = MagicMock()
        users.find_one = AsyncMock(
            return_value={
                "_id": ObjectId(user_id),
                "organization_id": "org-a",
                "role": "owner",
            }
        )
        users.update_one = AsyncMock()

        with patch("app.services.auth_service._users", users):
            with self.assertRaises(ValueError):
                _run(auth_service.update_user(user_id, {"role": "admin"}))

        users.update_one.assert_not_called()

    def test_update_user_rejects_second_owner(self):
        from app.services import auth_service

        user_id = "507f1f77bcf86cd799439011"
        users = MagicMock()
        users.find_one = AsyncMock(
            side_effect=[
                {
                    "_id": ObjectId(user_id),
                    "organization_id": "org-a",
                    "role": "member",
                },
                {"_id": ObjectId("507f1f77bcf86cd799439012")},
            ]
        )
        users.update_one = AsyncMock()

        with patch("app.services.auth_service._users", users):
            with self.assertRaises(ValueError):
                _run(auth_service.update_user(user_id, {"role": "owner"}))

        users.update_one.assert_not_called()


class TestIdentityUniqueness(unittest.TestCase):
    def test_create_user_rejects_duplicate_email(self):
        from app.services import auth_service

        users = MagicMock()
        users.find_one = AsyncMock(return_value={"_id": ObjectId()})
        users.insert_one = AsyncMock()

        with patch("app.services.auth_service._users", users):
            with self.assertRaises(ValueError) as ctx:
                _run(
                    auth_service.create_user(
                        email="taken@example.com",
                        password_hash="hash",
                        full_name="Taken",
                        role="member",
                        organization_id="org-a",
                    )
                )

        self.assertIn("email existe déjà", str(ctx.exception))
        users.insert_one.assert_not_called()

    def test_create_user_rejects_duplicate_phone(self):
        from app.services import auth_service

        users = MagicMock()
        users.find_one = AsyncMock(side_effect=[None, {"_id": ObjectId()}])
        users.insert_one = AsyncMock()

        with patch("app.services.auth_service._users", users):
            with self.assertRaises(ValueError) as ctx:
                _run(
                    auth_service.create_user(
                        email="new@example.com",
                        phone="+21698123456",
                        password_hash="hash",
                        full_name="New",
                        role="member",
                        organization_id="org-a",
                    )
                )

        self.assertIn("numéro de téléphone existe déjà", str(ctx.exception))
        users.insert_one.assert_not_called()

    def test_create_organization_rejects_duplicate_name(self):
        from app.services import auth_service

        organizations = MagicMock()
        organizations.find_one = AsyncMock(return_value={"_id": ObjectId()})
        organizations.insert_one = AsyncMock()

        with patch("app.services.auth_service._organizations", organizations):
            with self.assertRaises(ValueError) as ctx:
                _run(
                    auth_service.create_organization(
                        name="ACME",
                        sector="finance",
                    )
                )

        self.assertIn("nom de l'entreprise existe déjà", str(ctx.exception))
        organizations.insert_one.assert_not_called()

    def test_update_organization_rejects_duplicate_name(self):
        from app.services import auth_service

        org_id = "507f1f77bcf86cd799439011"
        organizations = MagicMock()
        organizations.find_one = AsyncMock(return_value={"_id": ObjectId()})
        organizations.update_one = AsyncMock()

        with patch("app.services.auth_service._organizations", organizations):
            with self.assertRaises(ValueError) as ctx:
                _run(auth_service.update_organization(org_id, {"name": "ACME"}))

        self.assertIn("nom de l'entreprise existe déjà", str(ctx.exception))
        organizations.update_one.assert_not_called()


if __name__ == "__main__":
    unittest.main()
