from bson import ObjectId
import pytest

from app.api import auth_router


@pytest.mark.asyncio
async def test_auth_activity_notification_targets_organization_owner(monkeypatch):
    owner_id = ObjectId("507f1f77bcf86cd799439099")
    captured = {}

    async def fake_get_owner(org_id):
        return {"_id": owner_id, "organization_id": org_id, "role": "owner"}

    async def fake_create_notification(db, **kwargs):
        captured.update(kwargs)
        return kwargs

    monkeypatch.setattr(auth_router.auth_service, "get_organization_owner", fake_get_owner)
    monkeypatch.setattr(auth_router, "_create_notification", fake_create_notification)

    await auth_router.create_notification(
        object(),
        alert_type="account_login",
        title="Connexion utilisateur",
        message="Member connected",
        details={
            "organization_id": "org-1",
            "user_id": "member-1",
            "activity": "login",
        },
    )

    assert captured["details"]["recipient_user_id"] == str(owner_id)
    assert captured["details"]["recipient_role"] == "owner"


@pytest.mark.asyncio
async def test_owner_login_does_not_create_self_activity_notification(monkeypatch):
    owner_id = ObjectId("507f1f77bcf86cd799439099")
    create_called = False

    async def fake_get_owner(org_id):
        return {"_id": owner_id, "organization_id": org_id, "role": "owner"}

    async def fake_create_notification(db, **kwargs):
        nonlocal create_called
        create_called = True
        return kwargs

    monkeypatch.setattr(auth_router.auth_service, "get_organization_owner", fake_get_owner)
    monkeypatch.setattr(auth_router, "_create_notification", fake_create_notification)

    result = await auth_router.create_notification(
        object(),
        alert_type="account_login",
        title="Connexion utilisateur",
        message="Owner connected",
        details={
            "organization_id": "org-1",
            "user_id": str(owner_id),
            "activity": "login",
        },
    )

    assert result == {}
    assert create_called is False


@pytest.mark.asyncio
async def test_login_without_owner_recipient_does_not_create_in_app_notification(monkeypatch):
    create_called = False

    async def fake_create_notification(db, **kwargs):
        nonlocal create_called
        create_called = True
        return kwargs

    monkeypatch.setattr(auth_router, "_create_notification", fake_create_notification)

    result = await auth_router.create_notification(
        object(),
        alert_type="account_login",
        title="Connexion utilisateur",
        message="Super admin connected",
        details={
            "user_id": "super-admin-1",
            "activity": "login",
        },
    )

    assert result == {}
    assert create_called is False


@pytest.mark.asyncio
async def test_owner_scoped_organization_notification_targets_owner(monkeypatch):
    owner_id = ObjectId("507f1f77bcf86cd799439099")
    captured = {}

    async def fake_get_owner(org_id):
        return {"_id": owner_id, "organization_id": org_id, "role": "owner"}

    async def fake_create_notification(db, **kwargs):
        captured.update(kwargs)
        return kwargs

    monkeypatch.setattr(auth_router.auth_service, "get_organization_owner", fake_get_owner)
    monkeypatch.setattr(auth_router, "_create_notification", fake_create_notification)

    await auth_router.create_notification(
        object(),
        alert_type="subscription_expiring",
        title="Abonnement bientôt expiré",
        message="Subscription expires soon",
        details={
            "organization_id": "org-1",
            "target_type": "subscription",
        },
    )

    assert captured["details"]["recipient_user_id"] == str(owner_id)
    assert captured["details"]["recipient_role"] == "owner"
