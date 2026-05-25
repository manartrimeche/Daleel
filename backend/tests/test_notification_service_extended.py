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
        alert_type="coverage_change",
        title="Coverage",
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
    db._notif.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
    result = await notification_service.mark_read(db, "n1", allow_global=True)
    assert result is True


@pytest.mark.asyncio
async def test_mark_read_no_org_returns_false():
    db = _make_db()
    result = await notification_service.mark_read(db, "n1")
    assert result is False


@pytest.mark.asyncio
async def test_mark_read_with_org_no_user_returns_false():
    db = _make_db()
    result = await notification_service.mark_read(
        db, "n1", organization_id="org-1", user_id=None
    )
    assert result is False


@pytest.mark.asyncio
async def test_mark_read_with_org_and_user():
    db = _make_db()
    db._notif.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
    result = await notification_service.mark_read(
        db, "n1", organization_id="org-1", user_id="u1"
    )
    assert result is True


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
