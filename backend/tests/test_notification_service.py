import unittest
from unittest.mock import AsyncMock, MagicMock


class MockCursor:
    def __init__(self, docs):
        self._docs = list(docs)
        self._index = 0

    def sort(self, *args, **kwargs):
        return self

    def skip(self, *args, **kwargs):
        return self

    def limit(self, *args, **kwargs):
        return self

    def __aiter__(self):
        self._index = 0
        return self

    async def __anext__(self):
        if self._index >= len(self._docs):
            raise StopAsyncIteration
        item = self._docs[self._index]
        self._index += 1
        return item


class TestNotificationScope(unittest.IsolatedAsyncioTestCase):
    async def test_list_notifications_filters_by_organization(self):
        from app.services.notification_service import list_notifications

        notifications = MagicMock()
        notifications.count_documents = AsyncMock(return_value=1)
        notifications.find = MagicMock(
            return_value=MockCursor([
                {"id": "n1", "details": {"organization_id": "org-a"}},
            ])
        )
        db = {"notifications": notifications}

        items, total = await list_notifications(
            db,
            organization_id="org-a",
        )

        expected = {"details.organization_id": "org-a"}
        notifications.count_documents.assert_awaited_once_with(expected)
        notifications.find.assert_called_once_with(expected, {"_id": 0})
        self.assertEqual(total, 1)
        self.assertEqual(items[0]["id"], "n1")

    async def test_mark_read_for_org_user_uses_read_by(self):
        from app.services.notification_service import mark_read

        notifications = MagicMock()
        notifications.update_one = AsyncMock()
        notifications.update_one.return_value.matched_count = 1
        notifications.update_one.return_value.modified_count = 1
        db = {"notifications": notifications}

        status = await mark_read(
            db,
            "n1",
            organization_id="org-a",
            user_id="user-1",
        )

        self.assertEqual(status, "ok")
        notifications.update_one.assert_awaited_once_with(
            {"id": "n1", "details.organization_id": "org-a"},
            {"$addToSet": {"read_by": "user-1"}},
        )

    async def test_mark_read_global_sets_read_flag(self):
        from app.services.notification_service import mark_read

        notifications = MagicMock()
        notifications.update_one = AsyncMock()
        notifications.update_one.return_value.matched_count = 1
        notifications.update_one.return_value.modified_count = 1
        db = {"notifications": notifications}

        status = await mark_read(db, "n1", allow_global=True, user_id="super-admin")

        self.assertEqual(status, "ok")
        notifications.update_one.assert_awaited_once_with(
            {"id": "n1"},
            {"$set": {"read": True}},
        )

    async def test_mark_read_idempotent_returns_noop(self):
        from app.services.notification_service import mark_read

        notifications = MagicMock()
        notifications.update_one = AsyncMock()
        notifications.update_one.return_value.matched_count = 1
        notifications.update_one.return_value.modified_count = 0
        db = {"notifications": notifications}

        status = await mark_read(
            db,
            "n1",
            organization_id="org-a",
            user_id="user-1",
        )

        self.assertEqual(status, "noop")

    async def test_mark_read_returns_not_found_when_no_match(self):
        from app.services.notification_service import mark_read

        notifications = MagicMock()
        notifications.update_one = AsyncMock()
        notifications.update_one.return_value.matched_count = 0
        notifications.update_one.return_value.modified_count = 0
        db = {"notifications": notifications}

        status = await mark_read(db, "nope", allow_global=True)

        self.assertEqual(status, "not_found")

    async def test_mark_read_denied_without_required_scope(self):
        from app.services.notification_service import mark_read

        notifications = MagicMock()
        notifications.update_one = AsyncMock()
        db = {"notifications": notifications}

        status = await mark_read(db, "n1", organization_id=None, user_id=None)

        self.assertEqual(status, "denied")
        notifications.update_one.assert_not_called()


if __name__ == "__main__":
    unittest.main()
