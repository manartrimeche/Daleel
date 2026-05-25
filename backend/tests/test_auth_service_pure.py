"""Tests for auth_service — pure helpers, serializers, subscription logic."""

from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

import pytest
from bson import ObjectId

from app.services.auth_service import (
    _object_id,
    normalize_subscription_type,
    _add_months,
    calculate_subscription_end_date,
    _as_utc,
    is_subscription_expired,
    hash_password,
    verify_password,
    generate_invitation_token,
    serialize_user,
    serialize_organization,
    serialize_invitation,
    create_access_token,
    create_refresh_token,
    decode_token,
)


class TestObjectId:
    def test_valid_hex(self):
        oid = _object_id("507f1f77bcf86cd799439011")
        assert isinstance(oid, ObjectId)

    def test_invalid_string(self):
        assert _object_id("not-a-valid-id") is None

    def test_empty_string(self):
        assert _object_id("") is None

    def test_none_returns_objectid(self):
        result = _object_id(None)
        assert isinstance(result, ObjectId)


class TestNormalizeSubscriptionType:
    def test_monthly(self):
        assert normalize_subscription_type("monthly") == "monthly"

    def test_annual(self):
        assert normalize_subscription_type("annual") == "annual"

    def test_none_defaults_monthly(self):
        assert normalize_subscription_type(None) == "monthly"

    def test_empty_defaults_monthly(self):
        assert normalize_subscription_type("") == "monthly"

    def test_unknown_defaults_monthly(self):
        assert normalize_subscription_type("weekly") == "monthly"

    def test_case_insensitive(self):
        assert normalize_subscription_type("ANNUAL") == "annual"

    def test_whitespace_trimmed(self):
        assert normalize_subscription_type("  monthly  ") == "monthly"


class TestAddMonths:
    def test_simple_add(self):
        dt = datetime(2026, 1, 15, tzinfo=timezone.utc)
        result = _add_months(dt, 1)
        assert result.month == 2
        assert result.day == 15

    def test_year_rollover(self):
        dt = datetime(2026, 12, 15, tzinfo=timezone.utc)
        result = _add_months(dt, 1)
        assert result.year == 2027
        assert result.month == 1

    def test_twelve_months(self):
        dt = datetime(2026, 5, 25, tzinfo=timezone.utc)
        result = _add_months(dt, 12)
        assert result.year == 2027
        assert result.month == 5

    def test_day_clamped_to_month_end(self):
        dt = datetime(2026, 1, 31, tzinfo=timezone.utc)
        result = _add_months(dt, 1)
        assert result.month == 2
        assert result.day == 28


class TestCalculateSubscriptionEndDate:
    def test_monthly(self):
        start = datetime(2026, 5, 1, tzinfo=timezone.utc)
        end = calculate_subscription_end_date(start, "monthly")
        assert end.month == 6

    def test_annual(self):
        start = datetime(2026, 5, 1, tzinfo=timezone.utc)
        end = calculate_subscription_end_date(start, "annual")
        assert end.year == 2027
        assert end.month == 5


class TestAsUtc:
    def test_none(self):
        assert _as_utc(None) is None

    def test_empty_string(self):
        assert _as_utc("") is None

    def test_naive_datetime(self):
        dt = datetime(2026, 5, 25, 12, 0, 0)
        result = _as_utc(dt)
        assert result.tzinfo == timezone.utc

    def test_aware_datetime(self):
        dt = datetime(2026, 5, 25, 12, 0, 0, tzinfo=timezone.utc)
        result = _as_utc(dt)
        assert result.tzinfo is not None

    def test_isoformat_string(self):
        result = _as_utc("2026-05-25T12:00:00")
        assert result.year == 2026
        assert result.tzinfo == timezone.utc


class TestIsSubscriptionExpired:
    def test_no_end_date(self):
        assert is_subscription_expired({}) is False

    def test_not_expired(self):
        future = datetime.now(timezone.utc) + timedelta(days=30)
        assert is_subscription_expired({"subscription_ends_at": future}) is False

    def test_expired(self):
        past = datetime.now(timezone.utc) - timedelta(days=1)
        assert is_subscription_expired({"subscription_ends_at": past}) is True

    def test_with_explicit_now(self):
        end = datetime(2026, 6, 1, tzinfo=timezone.utc)
        now = datetime(2026, 7, 1, tzinfo=timezone.utc)
        assert is_subscription_expired({"subscription_ends_at": end}, now=now) is True

    def test_naive_now(self):
        end = datetime(2020, 1, 1, tzinfo=timezone.utc)
        now = datetime(2026, 5, 25)
        assert is_subscription_expired({"subscription_ends_at": end}, now=now) is True


class TestPasswordHelpers:
    def test_hash_and_verify(self):
        hashed = hash_password("secret123")
        assert hashed != "secret123"
        assert verify_password("secret123", hashed) is True

    def test_wrong_password(self):
        hashed = hash_password("secret123")
        assert verify_password("wrong", hashed) is False


class TestGenerateInvitationToken:
    def test_returns_string(self):
        token = generate_invitation_token()
        assert isinstance(token, str)
        assert len(token) > 20

    def test_unique(self):
        t1 = generate_invitation_token()
        t2 = generate_invitation_token()
        assert t1 != t2


class TestSerializeUser:
    def test_full_user(self):
        now = datetime.now(timezone.utc)
        user = {
            "_id": ObjectId(),
            "email": "test@example.com",
            "full_name": "Test User",
            "role": "admin",
            "organization_id": "org-1",
            "is_active": True,
            "last_login": now,
            "created_at": now,
        }
        result = serialize_user(user)
        assert result["email"] == "test@example.com"
        assert result["role"] == "admin"
        assert "password" not in result
        assert "_id" not in result
        assert "id" in result

    def test_minimal_user(self):
        user = {
            "_id": ObjectId(),
            "email": "a@b.com",
            "full_name": "A",
            "role": "user",
            "created_at": datetime.now(timezone.utc),
        }
        result = serialize_user(user)
        assert result["is_active"] is True
        assert result["organization_id"] is None


class TestSerializeOrganization:
    def test_full_org(self):
        now = datetime.now(timezone.utc)
        org = {
            "_id": ObjectId(),
            "name": "ACME",
            "sector": "tech",
            "size": "PME",
            "employees": 50,
            "activities": "Software",
            "jurisdiction": "tunisia",
            "logo_url": None,
            "status": "active",
            "subscription_type": "monthly",
            "subscription_started_at": now,
            "subscription_ends_at": now + timedelta(days=30),
            "created_at": now,
            "updated_at": now,
        }
        result = serialize_organization(org, member_count=5)
        assert result["name"] == "ACME"
        assert result["member_count"] == 5
        assert "id" in result

    def test_missing_subscription_ends_at(self):
        now = datetime.now(timezone.utc)
        org = {
            "_id": ObjectId(),
            "name": "Test",
            "sector": "legal",
            "subscription_type": "annual",
            "subscription_started_at": now,
            "created_at": now,
            "updated_at": now,
        }
        result = serialize_organization(org)
        assert result["subscription_ends_at"] is not None

    def test_no_subscription_started_at(self):
        now = datetime.now(timezone.utc)
        org = {
            "_id": ObjectId(),
            "name": "Test",
            "sector": "legal",
            "created_at": now,
            "updated_at": now,
        }
        result = serialize_organization(org)
        assert result["subscription_ends_at"] is not None


class TestSerializeInvitation:
    def test_full_invitation(self):
        now = datetime.now(timezone.utc)
        inv = {
            "_id": ObjectId(),
            "email": "invite@example.com",
            "role": "member",
            "organization_id": "org-1",
            "invited_by": "user-1",
            "status": "pending",
            "created_at": now,
            "expires_at": now + timedelta(hours=72),
        }
        result = serialize_invitation(inv, org_name="ACME")
        assert result["email"] == "invite@example.com"
        assert result["organization_name"] == "ACME"
        assert "id" in result

    def test_without_org_name(self):
        now = datetime.now(timezone.utc)
        inv = {
            "_id": ObjectId(),
            "email": "a@b.com",
            "role": "admin",
            "organization_id": "org-2",
            "invited_by": "u-1",
            "status": "pending",
            "created_at": now,
            "expires_at": now + timedelta(hours=24),
        }
        result = serialize_invitation(inv)
        assert result["organization_name"] is None


class TestJWTHelpers:
    def _mock_settings(self):
        s = MagicMock()
        s.jwt_secret_key = "test-secret-key-for-jwt-testing-1234567890"
        s.jwt_algorithm = "HS256"
        s.jwt_access_token_expire_minutes = 30
        s.jwt_refresh_token_expire_days = 7
        return s

    def test_create_and_decode_access_token(self):
        settings = self._mock_settings()
        with patch("app.services.auth_service.get_settings", return_value=settings):
            token = create_access_token("user-1", "admin", "org-1")
            payload = decode_token(token)
        assert payload["sub"] == "user-1"
        assert payload["role"] == "admin"
        assert payload["org_id"] == "org-1"
        assert payload["type"] == "access"

    def test_create_and_decode_refresh_token(self):
        settings = self._mock_settings()
        with patch("app.services.auth_service.get_settings", return_value=settings):
            token = create_refresh_token("user-2")
            payload = decode_token(token)
        assert payload["sub"] == "user-2"
        assert payload["type"] == "refresh"

    def test_access_token_without_org(self):
        settings = self._mock_settings()
        with patch("app.services.auth_service.get_settings", return_value=settings):
            token = create_access_token("user-1", "user")
            payload = decode_token(token)
        assert payload["org_id"] is None
