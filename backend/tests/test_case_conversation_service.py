"""
Tests for the Case Conversation Workflow.

Covers:
  - Case creation from a user situation description
  - Fact extraction via LLM (mocked)
  - Generation of clarification questions
  - Message history updates across turns
  - Conversation summary retrieval
  - Context merging across turns
  - JSON parsing robustness
  - Schema validation
"""

import unittest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import json


def _make_client():
    """Create a TestClient with DB init/close and FAISS mocked out."""
    with patch("app.database.init_db", new_callable=AsyncMock), \
         patch("app.database.close_db", new_callable=AsyncMock), \
         patch("app.services.faiss_index.faiss_manager") as mock_faiss:
        mock_faiss.rebuild = AsyncMock()
        mock_faiss.size = 0
        from app.main import app
        from app.config import get_settings
        from fastapi.testclient import TestClient
        get_settings().api_key = "test-key"
        return TestClient(
            app,
            raise_server_exceptions=False,
            headers={"X-API-Key": "test-key"},
        )


# ─────────────────────────────────────────────────────────────
# Helpers — fake Mongo collections and LLM responses
# ─────────────────────────────────────────────────────────────

_NOW = datetime.now(timezone.utc)


def _fake_case(case_id="case-conv-001", **overrides):
    base = {
        "id": case_id,
        "title": "Test Conversation Case",
        "description": "A SARL needs employment contracts.",
        "company_profile_id": None,
        "status": "open",
        "priority": "medium",
        "assigned_to": None,
        "tags": ["conversation", "labour_compliance"],
        "created_by": "user",
        "created_at": _NOW,
        "updated_at": _NOW,
        "closed_at": None,
        "message_count": 0,
        "document_count": 0,
        "finding_count": 0,
        "action_count": 0,
        "conversation_context": {},
    }
    base.update(overrides)
    return base


def _fake_message(msg_id="msg-001", case_id="case-conv-001", role="user",
                  content="Test message", **overrides):
    base = {
        "id": msg_id,
        "case_id": case_id,
        "role": role,
        "content": content,
        "metadata": None,
        "created_at": _NOW,
    }
    base.update(overrides)
    return base


def _fake_llm_context_response():
    """Return the JSON that the LLM would produce for context extraction."""
    return json.dumps({
        "title": "SARL Employment Contract Compliance",
        "facts_known": [
            "The company is a SARL",
            "3 employees lack signed employment contracts",
            "The company is based in Tunisia",
        ],
        "facts_missing": [
            "Number of total employees in the company",
            "Duration of employment for the 3 employees without contracts",
            "Industry sector of the company",
            "Whether the company has an internal employment policy",
        ],
        "matter_type": "labour_compliance",
        "urgency": "high",
        "article_references": ["Art. 14", "Art. 16"],
        "next_question": "Depuis combien de temps ces 3 employés travaillent-ils sans contrat signé ?",
    })


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


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Case creation from conversation
# ═══════════════════════════════════════════════════════════════════════════════

class TestCreateCaseFromConversation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = _make_client()

    @patch("app.services.case_conversation_service.call_ollama", new_callable=AsyncMock)
    @patch("app.services.case_conversation_service._collection")
    @patch("app.services.case_service._collection")
    @patch("app.services.audit_service._collection")
    def test_create_case_from_conversation(
        self, mock_audit_col, mock_case_col, mock_conv_col, mock_llm
    ):
        """Creating a case from a situation description extracts facts and returns clarification."""
        mock_llm.return_value = _fake_llm_context_response()

        # Set up case_service mocks
        stored_case = {}
        cases_col = AsyncMock()
        cases_col.insert_one = AsyncMock(side_effect=lambda doc: stored_case.update(doc))

        async def find_one_side_effect(query):
            # After insert_one, stored_case will have an "id" key
            return stored_case if stored_case.get("id") else None

        cases_col.find_one = AsyncMock(side_effect=find_one_side_effect)
        cases_col.update_one = AsyncMock()

        messages_col = MagicMock()
        messages_col.insert_one = AsyncMock()
        messages_col.count_documents = AsyncMock(return_value=0)
        messages_col.find = MagicMock(return_value=MockCursor([]))

        sub_col = AsyncMock()
        sub_col.count_documents = AsyncMock(return_value=0)

        audit_col = AsyncMock()
        audit_col.insert_one = AsyncMock()
        mock_audit_col.return_value = audit_col

        def case_col_router(name):
            if name == "compliance_cases":
                return cases_col
            if name == "case_messages":
                return messages_col
            return sub_col

        mock_case_col.side_effect = case_col_router

        # Conversation service collection mock
        conv_cases_col = AsyncMock()
        conv_cases_col.update_one = AsyncMock()
        conv_cases_col.find_one = AsyncMock(return_value=stored_case)

        def conv_col_router(name):
            if name == "compliance_cases":
                return conv_cases_col
            return sub_col

        mock_conv_col.side_effect = conv_col_router

        r = self.client.post("/api/v1/cases/from-conversation", json={
            "situation": "Notre SARL a 3 employés sans contrats de travail signés. L'entreprise est basée en Tunisie.",
            "created_by": "user",
        })

        self.assertEqual(r.status_code, 201)
        data = r.json()
        self.assertIn("case_id", data)
        self.assertIn("user_message", data)
        self.assertIn("assistant_message", data)
        self.assertIn("context", data)

        ctx = data["context"]
        self.assertIsInstance(ctx["facts_known"], list)
        self.assertIsInstance(ctx["facts_missing"], list)
        self.assertIn(ctx["matter_type"], [
            "labour_compliance", "corporate_formation", "corporate_governance",
            "contract_dispute", "regulatory_compliance", "tax_compliance",
            "intellectual_property", "data_protection", "other",
        ])
        self.assertIn(ctx["urgency"], ["critical", "high", "medium", "low", "unknown"])


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Fact extraction
# ═══════════════════════════════════════════════════════════════════════════════

class TestFactExtraction(unittest.TestCase):

    def test_parse_llm_json_clean(self):
        """Clean JSON is parsed correctly."""
        from app.services.case_conversation_service import _parse_llm_json
        raw = '{"title": "Test", "facts_known": ["fact1"], "matter_type": "other"}'
        result = _parse_llm_json(raw)
        self.assertEqual(result["title"], "Test")
        self.assertEqual(result["facts_known"], ["fact1"])

    def test_parse_llm_json_with_markdown_fences(self):
        """JSON wrapped in markdown code fences is parsed correctly."""
        from app.services.case_conversation_service import _parse_llm_json
        raw = '```json\n{"title": "Test", "facts_known": ["fact1"]}\n```'
        result = _parse_llm_json(raw)
        self.assertEqual(result["title"], "Test")

    def test_parse_llm_json_with_preamble(self):
        """JSON preceded by text explanation is still extracted."""
        from app.services.case_conversation_service import _parse_llm_json
        raw = 'Here is my analysis:\n{"title": "Test", "urgency": "high"}'
        result = _parse_llm_json(raw)
        self.assertEqual(result["urgency"], "high")

    def test_parse_llm_json_invalid(self):
        """Completely invalid output returns empty dict."""
        from app.services.case_conversation_service import _parse_llm_json
        result = _parse_llm_json("This is not JSON at all.")
        self.assertEqual(result, {})

    def test_sanitize_context_valid(self):
        """Valid context passes through sanitization."""
        from app.services.case_conversation_service import _sanitize_context
        parsed = {
            "title": "Employment Case",
            "facts_known": ["fact1", "fact2"],
            "facts_missing": ["missing1"],
            "matter_type": "labour_compliance",
            "urgency": "high",
            "article_references": ["Art. 14"],
            "next_question": "How many employees?",
        }
        result = _sanitize_context(parsed)
        self.assertEqual(result["matter_type"], "labour_compliance")
        self.assertEqual(result["urgency"], "high")
        self.assertEqual(len(result["facts_known"]), 2)

    def test_sanitize_context_invalid_enums(self):
        """Invalid enum values fall back to defaults."""
        from app.services.case_conversation_service import _sanitize_context
        parsed = {
            "matter_type": "quantum_physics",
            "urgency": "super_urgent",
        }
        result = _sanitize_context(parsed)
        self.assertEqual(result["matter_type"], "other")
        self.assertEqual(result["urgency"], "unknown")


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Clarification question generation
# ═══════════════════════════════════════════════════════════════════════════════

class TestClarificationGeneration(unittest.TestCase):

    def test_build_assistant_response_fr(self):
        """French response includes facts and next question."""
        from app.services.case_conversation_service import _build_assistant_response
        context = {
            "facts_known": ["L'entreprise est une SARL"],
            "facts_missing": ["Nombre total d'employés"],
            "next_question": "Combien d'employés avez-vous au total ?",
            "matter_type": "labour_compliance",
        }
        response = _build_assistant_response(context, "fr")
        self.assertIn("Éléments établis", response)
        self.assertIn("SARL", response)
        self.assertIn("Combien", response)
        self.assertIn("Conformité du droit du travail", response)

    def test_build_assistant_response_ar(self):
        """Arabic response includes facts and next question."""
        from app.services.case_conversation_service import _build_assistant_response
        context = {
            "facts_known": ["الشركة هي شركة ذات مسؤولية محدودة"],
            "facts_missing": ["عدد الموظفين"],
            "next_question": "كم عدد الموظفين لديكم؟",
            "matter_type": "labour_compliance",
        }
        response = _build_assistant_response(context, "ar")
        self.assertIn("العناصر المثبتة", response)
        self.assertIn("شركة ذات مسؤولية محدودة", response)
        self.assertIn("كم عدد", response)
        self.assertIn("الامتثال لقانون الشغل", response)

    def test_build_assistant_response_en(self):
        """English response includes facts and next question."""
        from app.services.case_conversation_service import _build_assistant_response
        context = {
            "facts_known": ["The company is a SARL"],
            "facts_missing": ["Total employee count"],
            "next_question": "How many employees do you have in total?",
            "matter_type": "labour_compliance",
        }
        response = _build_assistant_response(context, "en")
        self.assertIn("Established facts", response)
        self.assertIn("SARL", response)
        self.assertIn("How many employees", response)
        self.assertIn("Labour compliance", response)

    def test_build_assistant_response_no_question(self):
        """When no missing facts remain, response indicates readiness."""
        from app.services.case_conversation_service import _build_assistant_response
        context = {
            "facts_known": ["Complete facts"],
            "facts_missing": [],
            "next_question": None,
            "matter_type": "labour_compliance",
        }
        response = _build_assistant_response(context, "fr")
        self.assertIn("éléments essentiels", response)
        self.assertIn("Conformité du droit du travail", response)


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Message history updates (process_user_message flow)
# ═══════════════════════════════════════════════════════════════════════════════

class TestMessageHistoryUpdates(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = _make_client()

    @patch("app.services.case_conversation_service.call_ollama", new_callable=AsyncMock)
    @patch("app.services.case_conversation_service._collection")
    @patch("app.services.case_service._collection")
    @patch("app.services.audit_service._collection")
    def test_follow_up_message(
        self, mock_audit_col, mock_case_col, mock_conv_col, mock_llm
    ):
        """Sending a follow-up message updates context and returns new clarification."""
        # LLM returns updated context with more known facts
        mock_llm.return_value = json.dumps({
            "title": "SARL Employment Contracts",
            "facts_known": [
                "The company is a SARL",
                "3 employees lack contracts",
                "Total employees: 15",
            ],
            "facts_missing": [
                "Industry sector",
                "Whether company has HR department",
            ],
            "matter_type": "labour_compliance",
            "urgency": "high",
            "article_references": ["Art. 14", "Art. 16"],
            "next_question": "Dans quel secteur d'activité opère votre entreprise ?",
        })

        # Set up existing case
        existing_case = _fake_case(
            status="in_progress",
            message_count=2,
            conversation_context={
                "facts_known": ["The company is a SARL", "3 employees lack contracts"],
                "facts_missing": ["Total employee count", "Industry sector"],
                "matter_type": "labour_compliance",
                "urgency": "high",
            },
        )

        existing_messages = [
            _fake_message("msg-001", role="user", content="Notre SARL a 3 employés sans contrats."),
            _fake_message("msg-002", role="assistant", content="J'ai bien pris note..."),
        ]

        cases_col = AsyncMock()
        cases_col.find_one = AsyncMock(return_value=existing_case)
        cases_col.update_one = AsyncMock()

        messages_col = MagicMock()
        messages_col.insert_one = AsyncMock()
        messages_col.count_documents = AsyncMock(return_value=2)
        messages_col.find = MagicMock(return_value=MockCursor(existing_messages))

        sub_col = AsyncMock()
        sub_col.count_documents = AsyncMock(return_value=0)

        audit_col = AsyncMock()
        audit_col.insert_one = AsyncMock()
        mock_audit_col.return_value = audit_col

        def case_col_router(name):
            if name == "compliance_cases":
                return cases_col
            if name == "case_messages":
                return messages_col
            return sub_col

        mock_case_col.side_effect = case_col_router

        # Conversation service collection mock
        conv_cases_col = AsyncMock()
        conv_cases_col.update_one = AsyncMock()
        conv_cases_col.find_one = AsyncMock(return_value=existing_case)

        def conv_col_router(name):
            if name == "compliance_cases":
                return conv_cases_col
            return sub_col

        mock_conv_col.side_effect = conv_col_router

        r = self.client.post("/api/v1/cases/case-conv-001/converse", json={
            "content": "Nous avons 15 employés au total.",
        })

        self.assertEqual(r.status_code, 201)
        data = r.json()
        self.assertEqual(data["case_id"], "case-conv-001")

        ctx = data["context"]
        # Should include merged facts
        self.assertIn("Total employees: 15", ctx["facts_known"])
        self.assertIsInstance(ctx["facts_missing"], list)
        self.assertIsNotNone(ctx["next_question"])


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Context merging
# ═══════════════════════════════════════════════════════════════════════════════

class TestContextMerging(unittest.TestCase):

    def test_merge_preserves_existing_facts(self):
        """Merging contexts preserves previously known facts."""
        from app.services.case_conversation_service import _merge_contexts
        existing = {
            "facts_known": ["Fact A", "Fact B"],
            "facts_missing": ["Missing X"],
            "matter_type": "labour_compliance",
            "urgency": "medium",
            "article_references": ["Art. 14"],
        }
        new = {
            "facts_known": ["Fact B", "Fact C"],
            "facts_missing": ["Missing Y"],
            "matter_type": "labour_compliance",
            "urgency": "high",
            "article_references": ["Art. 14", "Art. 16"],
            "next_question": "New question?",
        }
        merged = _merge_contexts(existing, new)

        # Fact A and C preserved, Fact B not duplicated
        self.assertIn("Fact A", merged["facts_known"])
        self.assertIn("Fact B", merged["facts_known"])
        self.assertIn("Fact C", merged["facts_known"])
        self.assertEqual(len([f for f in merged["facts_known"] if f == "Fact B"]), 1)

        # Missing facts come from new extraction
        self.assertEqual(merged["facts_missing"], ["Missing Y"])

        # Urgency updated
        self.assertEqual(merged["urgency"], "high")

        # Article refs merged
        self.assertIn("Art. 14", merged["article_references"])
        self.assertIn("Art. 16", merged["article_references"])

    def test_merge_handles_empty_existing(self):
        """Merging with empty existing context works."""
        from app.services.case_conversation_service import _merge_contexts
        result = _merge_contexts({}, {
            "facts_known": ["New fact"],
            "matter_type": "other",
            "urgency": "low",
        })
        self.assertEqual(result["facts_known"], ["New fact"])
        self.assertEqual(result["matter_type"], "other")


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Conversation summary endpoint
# ═══════════════════════════════════════════════════════════════════════════════

class TestConversationSummary(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = _make_client()

    @patch("app.services.case_conversation_service._collection")
    @patch("app.services.case_service._collection")
    def test_get_summary(self, mock_case_col, mock_conv_col):
        """GET /cases/{id}/summary returns structured context."""
        case = _fake_case(
            conversation_context={
                "facts_known": ["Fact A"],
                "facts_missing": ["Missing X"],
                "matter_type": "labour_compliance",
                "urgency": "high",
                "next_question": "What sector?",
                "article_references": ["Art. 14"],
                "updated_at": _NOW.isoformat(),
            },
        )

        cases_col = AsyncMock()
        cases_col.find_one = AsyncMock(return_value=case)

        sub_col = AsyncMock()
        sub_col.count_documents = AsyncMock(return_value=0)

        def case_col_router(name):
            if name == "compliance_cases":
                return cases_col
            return sub_col

        mock_case_col.side_effect = case_col_router

        conv_cases_col = AsyncMock()
        conv_cases_col.find_one = AsyncMock(return_value=case)

        def conv_col_router(name):
            if name == "compliance_cases":
                return conv_cases_col
            return sub_col

        mock_conv_col.side_effect = conv_col_router

        r = self.client.get("/api/v1/cases/case-conv-001/summary")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data["case_id"], "case-conv-001")
        self.assertIn("context", data)
        self.assertEqual(data["context"]["matter_type"], "labour_compliance")
        self.assertIn("Fact A", data["context"]["facts_known"])

    @patch("app.services.case_conversation_service._collection")
    @patch("app.services.case_service._collection")
    def test_get_summary_not_found(self, mock_case_col, mock_conv_col):
        """GET /cases/{id}/summary returns 404 for nonexistent case."""
        cases_col = AsyncMock()
        cases_col.find_one = AsyncMock(return_value=None)
        mock_case_col.return_value = cases_col
        mock_conv_col.return_value = cases_col

        r = self.client.get("/api/v1/cases/nonexistent/summary")
        self.assertEqual(r.status_code, 404)


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Schema validation
# ═══════════════════════════════════════════════════════════════════════════════

class TestConversationSchemaValidation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = _make_client()

    def test_from_conversation_missing_situation(self):
        """POST /from-conversation requires a situation field."""
        r = self.client.post("/api/v1/cases/from-conversation", json={})
        self.assertEqual(r.status_code, 422)

    def test_from_conversation_situation_too_short(self):
        """Situation must be at least 10 characters."""
        r = self.client.post("/api/v1/cases/from-conversation", json={
            "situation": "short",
        })
        self.assertEqual(r.status_code, 422)

    def test_message_empty_content(self):
        """POST /cases/{id}/messages rejects empty content."""
        r = self.client.post("/api/v1/cases/c1/messages", json={
            "content": "",
        })
        self.assertEqual(r.status_code, 422)


# ═══════════════════════════════════════════════════════════════════════════════
# Test: RAG context builder
# ═══════════════════════════════════════════════════════════════════════════════

class TestBuildCaseContextForRAG(unittest.TestCase):

    @patch("app.services.case_conversation_service._load_conversation_context", new_callable=AsyncMock)
    @patch("app.services.case_conversation_service.case_service.get_case", new_callable=AsyncMock)
    def test_build_rag_context(self, mock_get_case, mock_load_context):
        """build_case_context_for_rag produces a structured prompt injection string."""
        import asyncio
        from app.services.case_conversation_service import build_case_context_for_rag

        mock_get_case.return_value = {
            "id": "case-001",
        }
        mock_load_context.return_value = {
            "facts_known": ["Company is a SARL", "15 employees"],
            "facts_missing": ["Industry sector"],
            "matter_type": "labour_compliance",
            "urgency": "high",
            "article_references": ["Art. 14"],
        }

        result = asyncio.run(
            build_case_context_for_rag(None, "case-001", detected_lang="fr")
        )

        self.assertIsNotNone(result)
        self.assertIn("Contexte du dossier de conformité", result)
        self.assertIn("labour_compliance", result)
        self.assertIn("Company is a SARL", result)
        self.assertIn("Industry sector", result)
        self.assertIn("Art. 14", result)

    @patch("app.services.case_conversation_service._load_conversation_context", new_callable=AsyncMock)
    @patch("app.services.case_conversation_service.case_service.get_case", new_callable=AsyncMock)
    def test_build_rag_context_no_context(self, mock_get_case, mock_load_context):
        """Returns None when case has no conversation context."""
        import asyncio
        from app.services.case_conversation_service import build_case_context_for_rag

        mock_get_case.return_value = {
            "id": "case-001",
        }
        mock_load_context.return_value = {}

        result = asyncio.run(
            build_case_context_for_rag(None, "case-001", detected_lang="fr")
        )

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
