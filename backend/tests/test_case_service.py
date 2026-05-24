"""
Tests for the Compliance Case Management module.

Uses FastAPI TestClient with mocked MongoDB collections (AsyncMock)
to validate the full create → read → update → delete flow through
the /api/v1/cases endpoints.
"""

import unittest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch


def _make_client():
    """Create a TestClient with DB init/close and FAISS mocked out."""
    with patch("app.database.init_db", new_callable=AsyncMock), \
         patch("app.database.close_db", new_callable=AsyncMock), \
         patch("app.services.faiss_index.faiss_manager") as mock_faiss:
        mock_faiss.rebuild = AsyncMock()
        mock_faiss.size = 0
        from app.main import app
        from app.api.auth import get_current_user, get_optional_current_user, require_api_key
        from app.api.case_router import require_case_user
        from app.api.case_conversation_router import require_case_user as require_case_conversation_user
        from app.api.case_orchestrator_router import require_case_user as require_case_orchestrator_user
        from fastapi.testclient import TestClient

        async def fake_current_user():
            return {
                "_id": "507f1f77bcf86cd799439011",
                "role": "super_admin",
                "is_active": True,
                "organization_id": None,
            }

        async def fake_optional_user():
            return await fake_current_user()

        async def fake_key():
            return "test"

        app.dependency_overrides[get_current_user] = fake_current_user
        app.dependency_overrides[get_optional_current_user] = fake_optional_user
        app.dependency_overrides[require_api_key] = fake_key
        app.dependency_overrides[require_case_user] = fake_key
        app.dependency_overrides[require_case_conversation_user] = fake_key
        app.dependency_overrides[require_case_orchestrator_user] = fake_key
        return TestClient(app, raise_server_exceptions=False)


# ─────────────────────────────────────────────────────────────
# Helpers — fake Mongo collections
# ─────────────────────────────────────────────────────────────

_NOW = datetime.now(timezone.utc)


def _fake_case(case_id="case-001", **overrides):
    base = {
        "id": case_id,
        "title": "SARL Compliance Review",
        "description": "Annual compliance review for SARL Xyz.",
        "company_profile_id": None,
        "status": "open",
        "priority": "medium",
        "assigned_to": None,
        "tags": ["annual"],
        "created_by": "system",
        "created_at": _NOW,
        "updated_at": _NOW,
        "closed_at": None,
    }
    base.update(overrides)
    return base


def _fake_message(msg_id="msg-001", case_id="case-001"):
    return {
        "id": msg_id,
        "case_id": case_id,
        "role": "user",
        "content": "What labour-code obligations apply?",
        "metadata": None,
        "created_at": _NOW,
    }


def _fake_finding(finding_id="find-001", case_id="case-001"):
    return {
        "id": finding_id,
        "case_id": case_id,
        "exigence_id": None,
        "title": "Missing employment contracts",
        "description": "No signed contracts found for 3 employees.",
        "severity": "major",
        "status": "identified",
        "evidence_refs": [],
        "article_references": ["Art. 14"],
        "created_at": _NOW,
        "updated_at": _NOW,
    }


def _fake_case_action(action_id="act-001", case_id="case-001"):
    return {
        "id": action_id,
        "case_id": case_id,
        "finding_id": "find-001",
        "action_id": None,
        "title": "Draft employment contracts",
        "description": "Prepare contracts for the 3 employees.",
        "assigned_to": "legal-team",
        "due_date": None,
        "status": "pending",
        "priority": "high",
        "completion_notes": None,
        "created_at": _NOW,
        "updated_at": _NOW,
        "completed_at": None,
    }


class MockCursor:
    """Async-iterable cursor mock that supports chained .sort/.skip/.limit."""

    def __init__(self, docs):
        self._docs = list(docs)
        self._index = 0

    def sort(self, *a, **kw):
        return self

    def skip(self, *a, **kw):
        return self

    def limit(self, *a, **kw):
        return self

    def __aiter__(self):
        self._index = 0
        return self

    async def __anext__(self):
        if self._index >= len(self._docs):
            raise StopAsyncIteration
        doc = self._docs[self._index]
        self._index += 1
        return doc


class MockAggregation:
    """Async-iterable aggregation result mock."""

    def __init__(self, rows):
        self._rows = list(rows)
        self._index = 0

    def __aiter__(self):
        self._index = 0
        return self

    async def __anext__(self):
        if self._index >= len(self._rows):
            raise StopAsyncIteration
        row = self._rows[self._index]
        self._index += 1
        return row


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Case CRUD via API endpoints
# ═══════════════════════════════════════════════════════════════════════════════

class TestCaseOrganizationScope(unittest.IsolatedAsyncioTestCase):
    @patch("app.services.audit_service.log_event", new_callable=AsyncMock)
    @patch("app.services.case_service._collection")
    async def test_create_case_stores_org_and_scopes_profile(
        self,
        mock_col,
        mock_log_event,
    ):
        from app.services import case_service

        profile_col = AsyncMock()
        profile_col.find_one = AsyncMock(
            return_value={"id": "profile-1", "organization_id": "org-a"}
        )

        cases_col = AsyncMock()
        stored_case = {}

        async def insert_case(doc):
            stored_case.update(doc)

        cases_col.insert_one = AsyncMock(side_effect=insert_case)

        sub_col = AsyncMock()
        sub_col.count_documents = AsyncMock(return_value=0)

        def col_router(name):
            if name == "company_profiles":
                return profile_col
            if name == "compliance_cases":
                return cases_col
            return sub_col

        mock_col.side_effect = col_router

        case = await case_service.create_case(
            None,
            title="Scoped case",
            company_profile_id="profile-1",
            organization_id="org-a",
        )

        profile_col.find_one.assert_awaited_once_with(
            {"id": "profile-1", "organization_id": "org-a"}
        )
        self.assertEqual(stored_case["organization_id"], "org-a")
        self.assertEqual(case["organization_id"], "org-a")
        mock_log_event.assert_awaited_once()

    @patch("app.services.case_service._collection")
    async def test_list_cases_filters_by_organization(self, mock_col):
        from app.services import case_service

        cases_col = MagicMock()
        cases_col.count_documents = AsyncMock(return_value=1)
        cases_col.find = MagicMock(
            return_value=MockCursor([
                _fake_case("c1", organization_id="org-a"),
            ])
        )

        sub_col = AsyncMock()
        sub_col.count_documents = AsyncMock(return_value=0)

        def col_router(name):
            if name == "compliance_cases":
                return cases_col
            return sub_col

        mock_col.side_effect = col_router

        cases, total = await case_service.list_cases(
            None,
            organization_id="org-a",
        )

        cases_col.count_documents.assert_awaited_once_with(
            {"organization_id": "org-a"}
        )
        cases_col.find.assert_called_once_with({"organization_id": "org-a"})
        self.assertEqual(total, 1)
        self.assertEqual(cases[0]["organization_id"], "org-a")


class TestCaseEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = _make_client()

    # ── CREATE ──

    @patch("app.services.case_service._collection")
    @patch("app.services.audit_service._collection")
    def test_create_case(self, mock_audit_col, mock_case_col):
        # Mock compliance_cases.insert_one + audit_logs.insert_one
        cases_col = AsyncMock()
        cases_col.find_one = AsyncMock(return_value=None)
        cases_col.insert_one = AsyncMock()
        # After insert, get_case is called internally (enrichment)
        # We need _collection to route calls for different collection names.
        messages_col = AsyncMock()
        messages_col.count_documents = AsyncMock(return_value=0)
        docs_col = AsyncMock()
        docs_col.count_documents = AsyncMock(return_value=0)
        findings_col = AsyncMock()
        findings_col.count_documents = AsyncMock(return_value=0)
        actions_col = AsyncMock()
        actions_col.count_documents = AsyncMock(return_value=0)
        audit_col = AsyncMock()
        audit_col.insert_one = AsyncMock()

        stored_case = {}

        async def insert_case(doc):
            stored_case.update(doc)

        cases_col.insert_one = AsyncMock(side_effect=insert_case)

        # find_one returns the stored case on second call (get_case)
        call_count = {"n": 0}

        async def find_one_side_effect(query):
            call_count["n"] += 1
            if call_count["n"] <= 1:
                return None  # company_profiles check skipped
            return stored_case if stored_case else None

        cases_col.find_one = AsyncMock(side_effect=find_one_side_effect)

        def col_router(name):
            return {
                "compliance_cases": cases_col,
                "case_messages": messages_col,
                "case_documents": docs_col,
                "case_findings": findings_col,
                "case_actions": actions_col,
            }.get(name, AsyncMock())

        mock_case_col.side_effect = col_router
        mock_audit_col.return_value = audit_col

        r = self.client.post("/api/v1/cases", json={
            "title": "New Compliance Case",
            "priority": "high",
            "tags": ["urgent"],
        })
        self.assertEqual(r.status_code, 201)
        data = r.json()
        self.assertEqual(data["title"], "New Compliance Case")
        self.assertEqual(data["status"], "open")
        self.assertEqual(data["priority"], "high")
        self.assertIn("id", data)

    # ── LIST ──

    @patch("app.services.case_service._collection")
    def test_list_cases(self, mock_col):
        case1 = _fake_case("c1")
        case2 = _fake_case("c2", title="Second case")

        cases_col = MagicMock()
        cases_col.count_documents = AsyncMock(return_value=2)
        cases_col.find = MagicMock(return_value=MockCursor([case1, case2]))

        sub_col = AsyncMock()
        sub_col.count_documents = AsyncMock(return_value=0)

        def col_router(name):
            if name == "compliance_cases":
                return cases_col
            return sub_col

        mock_col.side_effect = col_router

        r = self.client.get("/api/v1/cases")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data["total"], 2)
        self.assertEqual(len(data["cases"]), 2)

    # ── GET by ID ──

    @patch("app.services.case_service._collection")
    def test_get_case(self, mock_col):
        case = _fake_case("c1")

        cases_col = AsyncMock()
        cases_col.find_one = AsyncMock(return_value=case)

        sub_col = AsyncMock()
        sub_col.count_documents = AsyncMock(return_value=0)

        def col_router(name):
            if name == "compliance_cases":
                return cases_col
            return sub_col

        mock_col.side_effect = col_router

        r = self.client.get("/api/v1/cases/c1")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["id"], "c1")

    @patch("app.services.case_service._collection")
    def test_get_case_not_found(self, mock_col):
        cases_col = AsyncMock()
        cases_col.find_one = AsyncMock(return_value=None)
        mock_col.return_value = cases_col

        r = self.client.get("/api/v1/cases/nonexistent")
        self.assertEqual(r.status_code, 404)

    # ── UPDATE (PATCH) ──

    @patch("app.services.case_service._collection")
    @patch("app.services.audit_service._collection")
    def test_update_case_status(self, mock_audit_col, mock_col):
        original = _fake_case("c1")
        updated = _fake_case("c1", status="in_progress")

        cases_col = AsyncMock()
        cases_col.find_one = AsyncMock(side_effect=[original, updated])
        cases_col.update_one = AsyncMock()

        sub_col = AsyncMock()
        sub_col.count_documents = AsyncMock(return_value=0)

        audit_col = AsyncMock()
        audit_col.insert_one = AsyncMock()
        mock_audit_col.return_value = audit_col

        def col_router(name):
            if name == "compliance_cases":
                return cases_col
            return sub_col

        mock_col.side_effect = col_router

        r = self.client.patch("/api/v1/cases/c1", json={"status": "in_progress"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["status"], "in_progress")

    # ── DELETE ──

    @patch("app.services.case_service._collection")
    @patch("app.services.audit_service._collection")
    def test_delete_case(self, mock_audit_col, mock_col):
        case = _fake_case("c1")
        cases_col = AsyncMock()
        cases_col.find_one = AsyncMock(return_value=case)
        cases_col.delete_one = AsyncMock()

        sub_col = AsyncMock()
        sub_col.delete_many = AsyncMock()

        audit_col = AsyncMock()
        audit_col.insert_one = AsyncMock()
        mock_audit_col.return_value = audit_col

        def col_router(name):
            if name == "compliance_cases":
                return cases_col
            return sub_col

        mock_col.side_effect = col_router

        r = self.client.delete("/api/v1/cases/c1")
        self.assertEqual(r.status_code, 204)


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Case Messages via API endpoints
# ═══════════════════════════════════════════════════════════════════════════════

class TestCaseMessageEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = _make_client()

    @patch("app.services.case_service._collection")
    def test_add_and_list_messages(self, mock_col):
        case = _fake_case("c1")
        msg = _fake_message()

        cases_col = AsyncMock()
        cases_col.find_one = AsyncMock(return_value=case)
        cases_col.update_one = AsyncMock()

        messages_col = MagicMock()
        messages_col.insert_one = AsyncMock()
        messages_col.count_documents = AsyncMock(return_value=1)
        messages_col.find = MagicMock(return_value=MockCursor([msg]))

        sub_col = AsyncMock()
        sub_col.count_documents = AsyncMock(return_value=0)

        def col_router(name):
            if name == "compliance_cases":
                return cases_col
            if name == "case_messages":
                return messages_col
            return sub_col

        mock_col.side_effect = col_router

        # Add message
        r = self.client.post("/api/v1/cases/c1/messages", json={
            "role": "user",
            "content": "What are the labour-code requirements?",
        })
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.json()["role"], "user")

        # List messages
        r = self.client.get("/api/v1/cases/c1/messages")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["total"], 1)


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Case Findings
# ═══════════════════════════════════════════════════════════════════════════════

class TestCaseFindingEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = _make_client()

    @patch("app.services.case_service._collection")
    def test_create_finding(self, mock_col):
        case = _fake_case("c1")

        cases_col = AsyncMock()
        cases_col.find_one = AsyncMock(return_value=case)
        cases_col.update_one = AsyncMock()

        findings_col = AsyncMock()
        findings_col.insert_one = AsyncMock()

        sub_col = AsyncMock()
        sub_col.count_documents = AsyncMock(return_value=0)

        def col_router(name):
            if name == "compliance_cases":
                return cases_col
            if name == "case_findings":
                return findings_col
            return sub_col

        mock_col.side_effect = col_router

        r = self.client.post("/api/v1/cases/c1/findings", json={
            "title": "Missing contracts",
            "description": "3 employees lack signed contracts.",
            "severity": "major",
        })
        self.assertEqual(r.status_code, 201)
        data = r.json()
        self.assertEqual(data["severity"], "major")
        self.assertEqual(data["status"], "identified")


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Case Actions
# ═══════════════════════════════════════════════════════════════════════════════

class TestCaseActionEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = _make_client()

    @patch("app.services.case_service._collection")
    def test_create_case_action(self, mock_col):
        case = _fake_case("c1")

        cases_col = AsyncMock()
        cases_col.find_one = AsyncMock(return_value=case)
        cases_col.update_one = AsyncMock()

        actions_col = AsyncMock()
        actions_col.insert_one = AsyncMock()

        sub_col = AsyncMock()
        sub_col.count_documents = AsyncMock(return_value=0)

        def col_router(name):
            if name == "compliance_cases":
                return cases_col
            if name == "case_actions":
                return actions_col
            return sub_col

        mock_col.side_effect = col_router

        r = self.client.post("/api/v1/cases/c1/actions", json={
            "title": "Prepare contracts",
            "description": "Draft employment contracts for 3 employees.",
            "priority": "high",
        })
        self.assertEqual(r.status_code, 201)
        data = r.json()
        self.assertEqual(data["status"], "pending")
        self.assertEqual(data["priority"], "high")


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Schema validation
# ═══════════════════════════════════════════════════════════════════════════════

class TestCaseSchemaValidation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = _make_client()

    def test_create_case_missing_title(self):
        r = self.client.post("/api/v1/cases", json={"priority": "low"})
        self.assertEqual(r.status_code, 422)

    def test_create_case_invalid_priority(self):
        r = self.client.post("/api/v1/cases", json={
            "title": "Test",
            "priority": "ultra-critical",
        })
        self.assertEqual(r.status_code, 422)

    def test_update_case_invalid_status(self):
        r = self.client.patch("/api/v1/cases/c1", json={"status": "invalid"})
        self.assertEqual(r.status_code, 422)

    def test_create_finding_invalid_severity(self):
        r = self.client.post("/api/v1/cases/c1/findings", json={
            "title": "X",
            "description": "Y",
            "severity": "catastrophic",
        })
        self.assertEqual(r.status_code, 422)

    def test_add_message_invalid_role(self):
        r = self.client.post("/api/v1/cases/c1/messages", json={
            "role": "admin",
            "content": "hello",
        })
        self.assertEqual(r.status_code, 422)


if __name__ == "__main__":
    unittest.main()
