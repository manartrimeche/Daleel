"""
Shared pytest fixtures for the Daleel backend test suite.
"""

import os
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from bson import ObjectId

os.environ.setdefault("MONGODB_URL", "mongodb://localhost:27017")
os.environ.setdefault("MONGODB_DB_NAME", "daleel_test")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-testing-only")


@pytest.fixture()
def fake_user():
    return {
        "_id": ObjectId("507f1f77bcf86cd799439011"),
        "id": "507f1f77bcf86cd799439011",
        "email": "test@example.com",
        "full_name": "Test User",
        "role": "super_admin",
        "is_active": True,
        "organization_id": None,
        "created_at": datetime.now(timezone.utc),
    }


@pytest.fixture()
def fake_org_user():
    org_id = str(ObjectId())
    return {
        "_id": ObjectId("507f1f77bcf86cd799439012"),
        "id": "507f1f77bcf86cd799439012",
        "email": "member@company.tn",
        "full_name": "Org Member",
        "role": "member",
        "is_active": True,
        "organization_id": org_id,
        "created_at": datetime.now(timezone.utc),
    }


@pytest.fixture()
def test_client(fake_user):
    with patch("app.database.init_db", new_callable=AsyncMock), \
         patch("app.database.close_db", new_callable=AsyncMock), \
         patch("app.services.faiss_index.faiss_manager") as mock_faiss:
        mock_faiss.rebuild = AsyncMock()
        mock_faiss.size = 0
        from app.main import app
        from app.api.auth import get_current_user, get_optional_current_user, require_admin, require_api_key

        async def _current():
            return fake_user

        async def _optional():
            return fake_user

        async def _key():
            return "test"

        app.dependency_overrides[get_current_user] = _current
        app.dependency_overrides[get_optional_current_user] = _optional
        app.dependency_overrides[require_api_key] = _key
        app.dependency_overrides[require_admin] = _key

        from fastapi.testclient import TestClient
        with TestClient(app, raise_server_exceptions=False) as client:
            yield client

        app.dependency_overrides.clear()


@pytest.fixture()
def mock_db():
    db = AsyncMock()
    db.__getitem__ = lambda self, key: AsyncMock()
    return db
