"""Extended tests for notification_service — cover list, mark_read, alert generators."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services import notification_service


class _FakeAsyncCursor:
    def __init__(self, items):
        self._items = list(items)
        self._idx = 0

    def sort(self, *args, **kwargs):
        return self

    def skip(self, n):
        self._items = self._items[n:]
        return self

    def limit(self, n):
        self._items = self._items[:n]
        return self

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self._idx >= len(self._items):
            raise StopAsyncIteration
        item = self._items[self._idx]
        self._idx += 1
        return item


def _make_db():
    db = MagicMock()
    notif_col = MagicMock()
    notif_col.insert_one = AsyncMock()
    notif_col.count_documents = AsyncMock(return_value=0)
    notif_col.find = MagicMock(return_value=_FakeAsyncCursor([]))
    notif_col.update_one = AsyncMock(return_value=MagicMock(modified_count=0))
    db.__getitem__ = lambda self, key: notif_col if key == "notifications" else MagicMock()
    db._notif = notif_col
    return db


@pytest.mark.asyncio
async def test_create_notification():
    db = _make_db()
    result = await notification_service.create_notification(
        db,
        alert_type="amendment_impact",
        title="Test",
        message="Test message",
    )
    assert result["alert_type"] == "amendment_impact"
    assert result["title"] == "Test"
    assert result["read"] is False
    assert "id" in result
    db._notif.insert_one.assert_called_once()


@pytest.mark.asyncio
async def test_create_notification_with_details():
    db = _make_db()
    result = await notification_service.create_notification(
        db,
        alert_type="amendment_impact",
        title="Impact",
        message="Changed",
        details={"org": "abc"},
    )
    assert result["details"]["org"] == "abc"


@pytest.mark.asyncio
async def test_list_notifications():
    db = _make_db()
    db._notif.count_documents = AsyncMock(return_value=2)
    items = [
        {"id": "n1", "title": "A", "read": False},
        {"id": "n2", "title": "B", "read": True},
    ]
    db._notif.find = MagicMock(return_value=_FakeAsyncCursor(items))
    result, total = await notification_service.list_notifications(db, skip=0, limit=10)
    assert total == 2
    assert len(result) == 2
    expected = {"alert_type": {"$in": ["amendment_summary", "approval_amendment", "approval_document", "approval_invitation", "approval_organization"]}}
    db._notif.count_documents.assert_awaited_once_with(expected)
    db._notif.find.assert_called_once_with(expected, {"_id": 0})


@pytest.mark.asyncio
async def test_admin_notification_list_keeps_only_platform_alerts():
    db = _make_db()
    db._notif.count_documents = AsyncMock(return_value=0)
    db._notif.find = MagicMock(return_value=_FakeAsyncCursor([]))

    await notification_service.list_notifications(db)

    expected = {"alert_type": {"$in": ["amendment_summary", "approval_amendment", "approval_document", "approval_invitation", "approval_organization"]}}
    db._notif.count_documents.assert_awaited_once_with(expected)
    db._notif.find.assert_called_once_with(expected, {"_id": 0})


@pytest.mark.asyncio
async def test_list_notifications_with_org_filter():
    db = _make_db()
    db._notif.count_documents = AsyncMock(return_value=0)
    db._notif.find = MagicMock(return_value=_FakeAsyncCursor([]))
    result, total = await notification_service.list_notifications(
        db, organization_id="org-1"
    )
    assert total == 0
    assert result == []


@pytest.mark.asyncio
async def test_mark_read_global():
    db = _make_db()
    db._notif.update_one = AsyncMock(
        return_value=MagicMock(matched_count=1, modified_count=1)
    )
    result = await notification_service.mark_read(db, "n1", allow_global=True)
    assert result == "ok"


@pytest.mark.asyncio
async def test_mark_read_no_org_returns_denied():
    db = _make_db()
    result = await notification_service.mark_read(db, "n1")
    assert result == "denied"


@pytest.mark.asyncio
async def test_mark_read_with_org_no_user_returns_denied():
    db = _make_db()
    result = await notification_service.mark_read(
        db, "n1", organization_id="org-1", user_id=None
    )
    assert result == "denied"


@pytest.mark.asyncio
async def test_mark_read_with_org_and_user():
    db = _make_db()
    db._notif.update_one = AsyncMock(
        return_value=MagicMock(matched_count=1, modified_count=1)
    )
    result = await notification_service.mark_read(
        db, "n1", organization_id="org-1", user_id="u1"
    )
    assert result == "ok"


@pytest.mark.asyncio
async def test_create_notification_account_login_has_expiry():
    db = _make_db()
    result = await notification_service.create_notification(
        db,
        alert_type="account_login",
        title="Connexion",
        message="...",
    )
    assert "expires_at" in result, "ephemeral types must set a TTL field"


@pytest.mark.asyncio
async def test_create_notification_amendment_impact_has_no_expiry():
    db = _make_db()
    result = await notification_service.create_notification(
        db,
        alert_type="amendment_impact",
        title="Impact",
        message="...",
    )
    assert "expires_at" not in result, "business notifications must not expire automatically"


@pytest.mark.asyncio
async def test_notify_amendment_summary_creates_single_record():
    """notify_amendment_summary must not iterate over company profiles anymore."""
    db = _make_db()
    profiles_col = MagicMock()
    # If the function still queried profiles, this would be invoked.
    profiles_col.find = MagicMock(side_effect=AssertionError("must not query profiles"))

    def getitem(self, name):
        if name == "notifications":
            return db._notif
        if name == "company_profiles":
            return profiles_col
        return MagicMock()

    db.__getitem__ = getitem

    count = await notification_service.notify_amendment_summary(
        db,
        loi_id="l1",
        loi_code="CT",
        loi_name="Code du travail",
        diff={"added": 1, "modified": 2, "removed": 0},
        operations=[{"type": "ADD", "article_key": "Art. 14"}],
    )
    assert count == 1
    db._notif.insert_one.assert_called_once()
    inserted = db._notif.insert_one.call_args[0][0]
    assert inserted["alert_type"] == "amendment_summary"


@pytest.mark.asyncio
async def test_mark_processed_sets_decision_and_metadata():
    db = _make_db()
    await notification_service.mark_processed(
        db,
        "n1",
        decision="approved",
        result_payload={"organization_id": "org-1"},
    )
    db._notif.update_one.assert_awaited_once()
    args, _ = db._notif.update_one.call_args
    filt, update = args
    assert filt == {"id": "n1"}
    set_payload = update["$set"]
    assert set_payload["read"] is True
    assert set_payload["details.approval_status"] == "approved"
    assert set_payload["details.approved_result"] == {"organization_id": "org-1"}
    assert "processed_at" in set_payload


@pytest.mark.asyncio
async def test_mark_all_read_global_sets_read_flag_on_unread():
    db = _make_db()
    db._notif.update_many = AsyncMock(return_value=MagicMock(modified_count=7))
    updated = await notification_service.mark_all_read(db, allow_global=True)
    assert updated == 7
    db._notif.update_many.assert_awaited_once_with(
        {
            "alert_type": {"$in": ["amendment_summary", "approval_amendment", "approval_document", "approval_invitation", "approval_organization"]},
            "read": {"$ne": True},
        },
        {"$set": {"read": True}},
    )


@pytest.mark.asyncio
async def test_mark_all_read_org_user_uses_read_by():
    db = _make_db()
    db._notif.update_many = AsyncMock(return_value=MagicMock(modified_count=3))
    updated = await notification_service.mark_all_read(
        db, organization_id="org-1", user_id="u1"
    )
    assert updated == 3
    db._notif.update_many.assert_awaited_once_with(
        {
            "details.organization_id": "org-1",
            "details.audience": {"$ne": "super_admin"},
            "alert_type": {"$in": ["account_deactivated", "account_login", "account_updated", "amendment_impact", "invitation_revoked", "member_joined", "organization_approved", "organization_rejected", "subscription_expiring"]},
            "$or": [
                {"details.recipient_user_id": {"$exists": False}},
                {"details.recipient_user_id": None},
                {"details.recipient_user_id": "u1"},
            ],
            "read": {"$ne": True},
            "read_by": {"$ne": "u1"},
        },
        {"$addToSet": {"read_by": "u1"}},
    )


@pytest.mark.asyncio
async def test_mark_all_read_returns_zero_without_scope():
    db = _make_db()
    db._notif.update_many = AsyncMock()
    updated = await notification_service.mark_all_read(db)
    assert updated == 0
    db._notif.update_many.assert_not_called()


@pytest.mark.asyncio
async def test_mark_processed_rejected_uses_rejected_result_key():
    db = _make_db()
    await notification_service.mark_processed(
        db,
        "n1",
        decision="rejected",
        result_payload={"organization_id": "org-1"},
    )
    args, _ = db._notif.update_one.call_args
    _, update = args
    assert "details.rejected_result" in update["$set"]
    assert update["$set"]["details.approval_status"] == "rejected"


@pytest.mark.asyncio
async def test_notify_amendment_impact_no_profiles():
    db = _make_db()
    count = await notification_service.notify_amendment_impact(
        db,
        loi_id="l1",
        loi_code="CT",
        operation_type="REPLACE",
        target_article_key="Art. 14",
        affected_profile_ids=[],
    )
    assert count == 0


@pytest.mark.asyncio
async def test_notify_amendment_impact_with_profiles():
    db = _make_db()
    profiles_col = MagicMock()
    profiles_col.find_one = AsyncMock(return_value={"name": "ACME", "organization_id": "org-1"})

    def getitem(self, name):
        if name == "notifications":
            return db._notif
        if name == "company_profiles":
            return profiles_col
        return MagicMock()

    db.__getitem__ = getitem

    count = await notification_service.notify_amendment_impact(
        db,
        loi_id="l1",
        loi_code="CT",
        operation_type="REPLACE",
        target_article_key="Art. 14",
        affected_profile_ids=["p1", "p2"],
    )
    assert count == 2
