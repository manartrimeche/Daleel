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

        expected = {
            "details.organization_id": "org-a",
            "details.audience": {"$ne": "super_admin"},
            "alert_type": {"$in": ["account_deactivated", "account_login", "account_updated", "amendment_impact", "invitation_revoked", "member_joined", "organization_approved", "organization_rejected", "subscription_expiring"]},
        }
        notifications.count_documents.assert_awaited_once_with(expected)
        notifications.find.assert_called_once_with(expected, {"_id": 0})
        self.assertEqual(total, 1)
        self.assertEqual(items[0]["id"], "n1")

    async def test_organization_notification_query_excludes_super_admin_only_alerts(self):
        from app.services.notification_service import organization_notification_query

        self.assertEqual(
            organization_notification_query("org-a"),
            {
                "details.organization_id": "org-a",
                "details.audience": {"$ne": "super_admin"},
                "alert_type": {"$in": ["account_deactivated", "account_login", "account_updated", "amendment_impact", "invitation_revoked", "member_joined", "organization_approved", "organization_rejected", "subscription_expiring"]},
            },
        )

    async def test_organization_notification_query_filters_recipient_when_user_given(self):
        from app.services.notification_service import organization_notification_query

        self.assertEqual(
            organization_notification_query("org-a", user_id="owner-1"),
            {
                "details.organization_id": "org-a",
                "details.audience": {"$ne": "super_admin"},
                "alert_type": {"$in": ["account_deactivated", "account_login", "account_updated", "amendment_impact", "invitation_revoked", "member_joined", "organization_approved", "organization_rejected", "subscription_expiring"]},
                "$or": [
                    {"details.recipient_user_id": {"$exists": False}},
                    {"details.recipient_user_id": None},
                    {"details.recipient_user_id": "owner-1"},
                ],
            },
        )

    async def test_organization_notification_query_can_require_recipient(self):
        from app.services.notification_service import organization_notification_query

        self.assertEqual(
            organization_notification_query(
                "org-a",
                user_id="member-1",
                include_org_wide=False,
            ),
            {
                "details.organization_id": "org-a",
                "details.audience": {"$ne": "super_admin"},
                "alert_type": {"$in": ["account_deactivated", "account_login", "account_updated", "amendment_impact", "invitation_revoked", "member_joined", "organization_approved", "organization_rejected", "subscription_expiring"]},
                "details.recipient_user_id": "member-1",
            },
        )

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
            {
                "id": "n1",
                "details.organization_id": "org-a",
                "details.audience": {"$ne": "super_admin"},
                "alert_type": {"$in": ["account_deactivated", "account_login", "account_updated", "amendment_impact", "invitation_revoked", "member_joined", "organization_approved", "organization_rejected", "subscription_expiring"]},
                "$or": [
                    {"details.recipient_user_id": {"$exists": False}},
                    {"details.recipient_user_id": None},
                    {"details.recipient_user_id": "user-1"},
                ],
            },
            {"$addToSet": {"read_by": "user-1"}},
        )

    async def test_mark_read_for_member_requires_targeted_notification(self):
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
            user_id="member-1",
            include_org_wide=False,
        )

        self.assertEqual(status, "ok")
        notifications.update_one.assert_awaited_once_with(
            {
                "id": "n1",
                "details.organization_id": "org-a",
                "details.audience": {"$ne": "super_admin"},
                "alert_type": {"$in": ["account_deactivated", "account_login", "account_updated", "amendment_impact", "invitation_revoked", "member_joined", "organization_approved", "organization_rejected", "subscription_expiring"]},
                "details.recipient_user_id": "member-1",
            },
            {"$addToSet": {"read_by": "member-1"}},
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

    async def test_delete_notification_for_org_user_uses_org_scope(self):
        from app.services.notification_service import delete_notification

        notifications = MagicMock()
        notifications.delete_one = AsyncMock()
        notifications.delete_one.return_value.deleted_count = 1
        db = {"notifications": notifications}

        status = await delete_notification(
            db,
            "n1",
            organization_id="org-a",
            user_id="owner-1",
        )

        self.assertEqual(status, "ok")
        notifications.delete_one.assert_awaited_once_with(
            {
                "id": "n1",
                "details.organization_id": "org-a",
                "details.audience": {"$ne": "super_admin"},
                "alert_type": {"$in": ["account_deactivated", "account_login", "account_updated", "amendment_impact", "invitation_revoked", "member_joined", "organization_approved", "organization_rejected", "subscription_expiring"]},
                "$or": [
                    {"details.recipient_user_id": {"$exists": False}},
                    {"details.recipient_user_id": None},
                    {"details.recipient_user_id": "owner-1"},
                ],
            }
        )

    async def test_delete_notification_global_deletes_by_id(self):
        from app.services.notification_service import delete_notification

        notifications = MagicMock()
        notifications.delete_one = AsyncMock()
        notifications.delete_one.return_value.deleted_count = 1
        db = {"notifications": notifications}

        status = await delete_notification(db, "n1", allow_global=True)

        self.assertEqual(status, "ok")
        notifications.delete_one.assert_awaited_once_with({"id": "n1"})

    async def test_delete_notification_returns_not_found_when_no_match(self):
        from app.services.notification_service import delete_notification

        notifications = MagicMock()
        notifications.delete_one = AsyncMock()
        notifications.delete_one.return_value.deleted_count = 0
        db = {"notifications": notifications}

        status = await delete_notification(db, "nope", allow_global=True)

        self.assertEqual(status, "not_found")

    async def test_delete_notification_denied_without_required_scope(self):
        from app.services.notification_service import delete_notification

        notifications = MagicMock()
        notifications.delete_one = AsyncMock()
        db = {"notifications": notifications}

        status = await delete_notification(db, "n1", organization_id=None, user_id=None)

        self.assertEqual(status, "denied")
        notifications.delete_one.assert_not_called()


if __name__ == "__main__":
    unittest.main()
