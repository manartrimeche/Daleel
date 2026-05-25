"""Tests for config._validate_production_settings."""

import os
import pytest
from unittest.mock import patch, MagicMock
from app.config import _validate_production_settings


def _make_settings(**overrides):
    s = MagicMock()
    s.api_key = overrides.get("api_key", "test-key")
    s.admin_api_key = overrides.get("admin_api_key", "admin-key")
    s.jwt_secret_key = overrides.get("jwt_secret_key", "a" * 64)
    s.cors_origins = overrides.get("cors_origins", "http://localhost:3000")
    return s


class TestValidateProductionSettings:
    def test_dev_env_passes_without_keys(self):
        s = _make_settings(api_key="", admin_api_key="", jwt_secret_key="")
        with patch.dict(os.environ, {"DALEEL_ENV": "dev"}):
            _validate_production_settings(s)

    def test_production_requires_api_key(self):
        s = _make_settings(api_key="")
        with patch.dict(os.environ, {"DALEEL_ENV": "production"}):
            with pytest.raises(RuntimeError, match="DALEEL_API_KEY"):
                _validate_production_settings(s)

    def test_production_requires_admin_key(self):
        s = _make_settings(admin_api_key="")
        with patch.dict(os.environ, {"DALEEL_ENV": "production"}):
            with pytest.raises(RuntimeError, match="ADMIN_API_KEY"):
                _validate_production_settings(s)

    def test_production_requires_strong_jwt(self):
        s = _make_settings(jwt_secret_key="short")
        with patch.dict(os.environ, {"DALEEL_ENV": "production"}):
            with pytest.raises(RuntimeError, match="JWT_SECRET_KEY"):
                _validate_production_settings(s)

    def test_production_rejects_cors_wildcard(self):
        s = _make_settings(cors_origins="*")
        with patch.dict(os.environ, {"DALEEL_ENV": "production"}):
            with pytest.raises(RuntimeError, match="CORS"):
                _validate_production_settings(s)

    def test_production_valid_config_passes(self):
        s = _make_settings()
        with patch.dict(os.environ, {"DALEEL_ENV": "production"}):
            _validate_production_settings(s)

    def test_staging_same_as_production(self):
        s = _make_settings(api_key="")
        with patch.dict(os.environ, {"DALEEL_ENV": "staging"}):
            with pytest.raises(RuntimeError, match="DALEEL_API_KEY"):
                _validate_production_settings(s)
