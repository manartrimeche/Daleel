"""
Integration tests for the FastAPI endpoints (app.api.router).

These tests use the FastAPI TestClient and mock MongoDB + external services
to validate request/response contracts without needing live infrastructure.
"""

import os
import unittest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from bson import ObjectId
from fastapi.testclient import TestClient


def _make_client():
    """Create a TestClient with DB init/close mocked out."""
    with patch("app.database.init_db", new_callable=AsyncMock), \
         patch("app.database.close_db", new_callable=AsyncMock), \
         patch("app.services.faiss_index.faiss_manager") as mock_faiss:
        mock_faiss.rebuild = AsyncMock()
        mock_faiss.size = 0
        from app.main import app
        from app.api.auth import get_current_user, get_optional_current_user, require_admin, require_api_key

        async def fake_current_user():
            return {
                "_id": ObjectId("507f1f77bcf86cd799439011"),
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
        app.dependency_overrides[require_admin] = fake_key
        return TestClient(app, raise_server_exceptions=False)


class TestMetaEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = _make_client()

    def test_api_root(self):
        r = self.client.get("/api/v1")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn("name", data)
        self.assertIn("version", data)

    def test_api_root_trailing_slash(self):
        r = self.client.get("/api/v1/")
        self.assertEqual(r.status_code, 200)

    def test_docs_accessible(self):
        r = self.client.get("/docs")
        self.assertEqual(r.status_code, 200)

    def test_openapi_schema(self):
        r = self.client.get("/openapi.json")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn("paths", data)


class TestFrontendServing(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = _make_client()

    def test_root_serves_chatbot(self):
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)
        self.assertIn("text/html", r.headers.get("content-type", ""))

    def test_admin_serves_admin_panel(self):
        r = self.client.get("/admin")
        self.assertEqual(r.status_code, 200)
        self.assertIn("text/html", r.headers.get("content-type", ""))

    def test_legacy_auth_url_serves_auth_page(self):
        r = self.client.get("/auth")
        self.assertEqual(r.status_code, 200)
        self.assertIn("text/html", r.headers.get("content-type", ""))


class TestDocumentEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = _make_client()

    @patch("app.services.document_service.list_documents", new_callable=AsyncMock)
    def test_list_documents(self, mock_list):
        mock_list.return_value = ([], 0)
        r = self.client.get("/api/v1/documents")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn("documents", data)
        self.assertIn("total", data)

    def test_upload_no_file_returns_422(self):
        r = self.client.post("/api/v1/documents/upload")
        self.assertIn(r.status_code, (400, 422))

    @patch("app.services.search_service.semantic_search", new_callable=AsyncMock)
    def test_search_endpoint(self, mock_search):
        mock_search.return_value = []
        r = self.client.post("/api/v1/search", json={"query": "test", "top_k": 5})
        self.assertEqual(r.status_code, 200)

    @patch("app.services.document_service.reindex_all_documents", new_callable=AsyncMock)
    def test_reindex_reports_ready_index(self, mock_reindex):
        mock_reindex.return_value = {
            "documents_total": 6, "documents_reindexed": 6, "chunks_rebuilt": 2157,
        }
        from app.services import faiss_index as faiss_mod
        with patch.object(faiss_mod.faiss_manager, "mark_unavailable"), \
             patch.object(type(faiss_mod.faiss_manager), "is_ready", new_callable=lambda: property(lambda self: True)), \
             patch.object(type(faiss_mod.faiss_manager), "size", new_callable=lambda: property(lambda self: 2157)), \
             patch.object(type(faiss_mod.faiss_manager), "blocked_reason", new_callable=lambda: property(lambda self: None)):
            r = self.client.post("/api/v1/admin/reindex")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(data["index_ready"])
        self.assertEqual(data["index_size"], 2157)
        self.assertIn("rebuilt", data["message"])

    @patch("app.services.document_service.reindex_all_documents", new_callable=AsyncMock)
    def test_reindex_surfaces_silent_failure(self, mock_reindex):
        mock_reindex.return_value = {
            "documents_total": 6, "documents_reindexed": 6, "chunks_rebuilt": 2157,
        }
        from app.services import faiss_index as faiss_mod
        with patch.object(faiss_mod.faiss_manager, "mark_unavailable"), \
             patch.object(type(faiss_mod.faiss_manager), "is_ready", new_callable=lambda: property(lambda self: False)), \
             patch.object(type(faiss_mod.faiss_manager), "size", new_callable=lambda: property(lambda self: 0)), \
             patch.object(type(faiss_mod.faiss_manager), "blocked_reason", new_callable=lambda: property(lambda self: "build_failed")):
            r = self.client.post("/api/v1/admin/reindex")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertFalse(data["index_ready"])
        self.assertEqual(data["index_size"], 0)
        self.assertEqual(data["blocked_reason"], "build_failed")
        self.assertIn("failed to load", data["message"])

    @patch("app.api.router.search_service.get_vector_stats", new_callable=AsyncMock)
    def test_vector_stats(self, mock_stats):
        mock_stats.return_value = {
            "pgvector_available": False,
            "faiss_available": True,
            "active_backend": "faiss",
            "total_vectors": 100,
            "total_chunks": 100,
        }
        r = self.client.get("/api/v1/admin/vector-stats")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn("total_vectors", data)


class TestAskEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = _make_client()

    @patch("app.services.llm_service.ask", new_callable=AsyncMock)
    def test_ask_classic(self, mock_ask):
        mock_ask.return_value = {
            "answer": "Voici la reponse.",
            "sources": [],
            "model": "qwen2.5:7b",
            "chunks_used": 3,
        }
        r = self.client.post("/api/v1/ask", json={"question": "Qu'est-ce qu'une SARL ?", "top_k": 5})
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn("answer", data)

    @patch("app.services.llm_service.ask_agentic", new_callable=AsyncMock)
    def test_ask_agentic(self, mock_ask):
        mock_ask.return_value = {
            "answer": "reponse agentique.",
            "sources": [],
            "model": "qwen2.5:7b",
            "chunks_used": 5,
            "reasoning_steps": ["step1"],
            "retrieval_attempts": 1,
            "rewritten_query": None,
            "intent": "advice",
            "route_decision": None,
            "timings_ms": {"search": 10, "generation": 50, "total": 60},
        }
        r = self.client.post("/api/v1/ask-agentic", json={"question": "Conseils conformité", "top_k": 5})
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn("answer", data)

    @patch("app.services.llm_service.ask_agentic", new_callable=AsyncMock)
    def test_ask_agentic_saves_history_with_mongo_user_id(self, mock_ask):
        from app.api.auth import get_current_user
        from app.database import get_db
        from app.main import app

        class FakeCollection:
            def __init__(self):
                self.rows = []

            async def insert_one(self, doc):
                self.rows.append(doc)

        class FakeDb(dict):
            def __getitem__(self, name):
                if name not in self:
                    self[name] = FakeCollection()
                return dict.__getitem__(self, name)

        fake_db = FakeDb()

        async def override_get_db():
            yield fake_db

        user_id = "507f1f77bcf86cd799439011"

        async def override_current_user():
            return {
                "_id": ObjectId(user_id),
                "role": "member",
                "organization_id": "org-1",
                "is_active": True,
            }

        mock_ask.return_value = {
            "answer": "reponse agentique.",
            "sources": [],
            "model": "qwen2.5:7b",
            "chunks_used": 5,
            "reasoning_steps": ["step1"],
            "retrieval_attempts": 1,
            "rewritten_query": None,
            "intent": "advice",
            "route_decision": None,
            "timings_ms": {"search": 10, "generation": 50, "total": 60},
        }

        original_user_override = app.dependency_overrides.get(get_current_user)
        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = override_current_user
        try:
            r = self.client.post(
                "/api/v1/ask-agentic",
                json={"question": "Conseils conformité", "top_k": 5},
                headers={"Authorization": "Bearer fake"},
            )
        finally:
            app.dependency_overrides.pop(get_db, None)
            if original_user_override is not None:
                app.dependency_overrides[get_current_user] = original_user_override
            else:
                app.dependency_overrides.pop(get_current_user, None)

        self.assertEqual(r.status_code, 200)
        history = fake_db["chat_history"].rows
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["user_id"], user_id)
        self.assertEqual(history[0]["organization_id"], "org-1")


class TestCompanyProfileEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = _make_client()

    @patch("app.services.applicability_service.list_company_profiles", new_callable=AsyncMock)
    def test_list_profiles(self, mock_list):
        mock_list.return_value = ([], 0)
        r = self.client.get("/api/v1/company-profiles")
        self.assertEqual(r.status_code, 200)

    @patch("app.services.applicability_service.create_company_profile", new_callable=AsyncMock)
    def test_create_profile(self, mock_create):
        now = datetime.now(timezone.utc)
        mock_create.return_value = {
            "id": "test-uuid",
            "name": "Test Corp",
            "sector": "tech",
            "size": "medium",
            "employees": 50,
            "activities": "IT services",
            "jurisdiction": "tunisia",
            "notes": None,
            "created_at": now,
            "updated_at": now,
        }
        r = self.client.post("/api/v1/company-profiles", json={
            "name": "Test Corp",
            "sector": "tech",
            "size": "medium",
            "employees": 50,
        })
        self.assertEqual(r.status_code, 201)
        data = r.json()
        self.assertEqual(data["name"], "Test Corp")

    def test_create_profile_invalid_size_rejected(self):
        r = self.client.post("/api/v1/company-profiles", json={
            "name": "Bad Corp",
            "size": "PME",
        })
        self.assertEqual(r.status_code, 422)


def _make_client_with_auth(api_key="test-secret"):
    """Create a TestClient with auth enabled."""
    env_patcher = patch.dict(
        os.environ,
        {"DALEEL_API_KEY": api_key, "DALEEL_ADMIN_API_KEY": api_key},
    )
    env_patcher.start()
    with patch("app.database.init_db", new_callable=AsyncMock), \
         patch("app.database.close_db", new_callable=AsyncMock), \
         patch("app.services.faiss_index.faiss_manager") as mock_faiss:
        try:
            mock_faiss.rebuild = AsyncMock()
            mock_faiss.size = 0
            import app.config as app_config
            app_config.get_settings.cache_clear()
            from app.main import app
            app.dependency_overrides.clear()
            client = TestClient(app, raise_server_exceptions=False)
            app_config.get_settings.cache_clear()
            return client, api_key, env_patcher
        except Exception:
            env_patcher.stop()
            raise


class TestAuthEnforcement(unittest.TestCase):
    """Verify that protected endpoints reject unauthenticated requests."""

    @classmethod
    def setUpClass(cls):
        cls.client, cls.api_key, cls._env_patcher = _make_client_with_auth()

    @classmethod
    def tearDownClass(cls):
        import app.config
        cls._env_patcher.stop()
        app.config.get_settings.cache_clear()

    def _headers(self):
        return {"X-API-Key": self.api_key}

    def test_upload_requires_auth(self):
        r = self.client.post("/api/v1/documents/upload")
        self.assertIn(r.status_code, (401, 422))

    @patch("app.services.applicability_service.create_company_profile", new_callable=AsyncMock)
    def test_create_profile_rejected_without_key(self, mock_create):
        r = self.client.post("/api/v1/company-profiles", json={
            "name": "Test", "sector": "tech", "size": "medium",
        })
        self.assertEqual(r.status_code, 401)

    @patch("app.services.applicability_service.create_company_profile", new_callable=AsyncMock)
    def test_create_profile_accepted_with_key(self, mock_create):
        now = datetime.now(timezone.utc)
        mock_create.return_value = {
            "id": "id", "name": "T", "sector": "tech", "size": "medium",
            "employees": 1, "activities": "", "jurisdiction": "", "notes": None,
            "created_at": now, "updated_at": now,
        }
        r = self.client.post(
            "/api/v1/company-profiles",
            json={"name": "T", "sector": "tech", "size": "medium"},
            headers=self._headers(),
        )
        self.assertEqual(r.status_code, 201)

    def test_admin_stats_rejected_without_key(self):
        r = self.client.get("/api/v1/admin/stats")
        self.assertEqual(r.status_code, 401)

    def test_wrong_key_returns_403(self):
        r = self.client.post(
            "/api/v1/company-profiles",
            json={"name": "T", "sector": "tech", "size": "medium"},
            headers={"X-API-Key": "wrong-key"},
        )
        self.assertEqual(r.status_code, 403)


class TestChatHistoryConversation(unittest.TestCase):
    """Cover PATCH /chat-history/conversation/{id}/archive and /rename."""

    @classmethod
    def setUpClass(cls):
        cls.client = _make_client()

    def _override_db(self, matched: int):
        from app.database import get_db
        from app.main import app

        class FakeUpdateResult:
            def __init__(self, n):
                self.matched_count = n

        last_call = {}

        class FakeCollection:
            async def update_many(self, query, update):
                last_call["query"] = query
                last_call["update"] = update
                return FakeUpdateResult(matched)

        class FakeDb(dict):
            def __getitem__(self, name):
                if name not in self:
                    self[name] = FakeCollection()
                return dict.__getitem__(self, name)

        fake_db = FakeDb()

        async def override_get_db():
            yield fake_db

        app.dependency_overrides[get_db] = override_get_db
        return last_call, lambda: app.dependency_overrides.pop(get_db, None)

    def test_archive_conversation_ok(self):
        last_call, cleanup = self._override_db(matched=3)
        try:
            r = self.client.patch(
                "/api/v1/chat-history/conversation/conv-1/archive",
                json={"archived": True},
            )
        finally:
            cleanup()
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["conversation_id"], "conv-1")
        self.assertTrue(body["archived"])
        # Scopes to the current user so a foreign conversation cannot be touched.
        self.assertIn("user_id", last_call["query"])
        self.assertEqual(last_call["query"]["conversation_id"], "conv-1")
        self.assertTrue(last_call["update"]["$set"]["archived"])

    def test_restore_conversation_ok(self):
        last_call, cleanup = self._override_db(matched=2)
        try:
            r = self.client.patch(
                "/api/v1/chat-history/conversation/conv-1/archive",
                json={"archived": False},
            )
        finally:
            cleanup()
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.json()["archived"])
        self.assertFalse(last_call["update"]["$set"]["archived"])
        self.assertIn("archived_at", last_call["update"]["$unset"])

    def test_archive_unknown_conversation_returns_404(self):
        _, cleanup = self._override_db(matched=0)
        try:
            r = self.client.patch(
                "/api/v1/chat-history/conversation/missing/archive",
                json={"archived": True},
            )
        finally:
            cleanup()
        self.assertEqual(r.status_code, 404)

    def test_rename_conversation_ok(self):
        last_call, cleanup = self._override_db(matched=4)
        try:
            r = self.client.patch(
                "/api/v1/chat-history/conversation/conv-1/rename",
                json={"title": "  Nouveau titre  "},
            )
        finally:
            cleanup()
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["title"], "Nouveau titre")
        self.assertEqual(last_call["update"]["$set"]["conversation_title"], "Nouveau titre")

    def test_rename_truncates_to_120_chars(self):
        last_call, cleanup = self._override_db(matched=1)
        long_title = "a" * 300
        try:
            r = self.client.patch(
                "/api/v1/chat-history/conversation/conv-1/rename",
                json={"title": long_title},
            )
        finally:
            cleanup()
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(last_call["update"]["$set"]["conversation_title"]), 120)

    def test_rename_empty_title_returns_422(self):
        _, cleanup = self._override_db(matched=0)
        try:
            r = self.client.patch(
                "/api/v1/chat-history/conversation/conv-1/rename",
                json={"title": "   "},
            )
        finally:
            cleanup()
        self.assertEqual(r.status_code, 422)

    def test_rename_unknown_conversation_returns_404(self):
        _, cleanup = self._override_db(matched=0)
        try:
            r = self.client.patch(
                "/api/v1/chat-history/conversation/missing/rename",
                json={"title": "X"},
            )
        finally:
            cleanup()
        self.assertEqual(r.status_code, 404)


if __name__ == "__main__":
    unittest.main()
