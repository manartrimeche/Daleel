"""
Tests for the Compliance Steering module.

Covers:
  - Gap calculation (posture computation)
  - Evidence attachment
  - Requirement–control mapping
  - Remediation workflow
  - Schema validation
  - CRUD operations via API endpoints
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
        from fastapi.testclient import TestClient
        return TestClient(app, raise_server_exceptions=False)


# ─────────────────────────────────────────────────────────────
# Helpers — fake documents
# ─────────────────────────────────────────────────────────────

_NOW = datetime.now(timezone.utc)


def _fake_profile(pid="profile-001"):
    return {
        "id": pid,
        "name": "SARL Test",
        "created_at": _NOW,
        "updated_at": _NOW,
    }


def _fake_assessment(aid="assess-001", profile_id="profile-001", **overrides):
    base = {
        "id": aid,
        "company_profile_id": profile_id,
        "title": "Annual Gap Analysis",
        "description": "Full annual review",
        "assessment_type": "initial",
        "status": "draft",
        "owner": "compliance-team",
        "risk_level": "medium",
        "overall_coverage_score": 0.0,
        "review_frequency": "annual",
        "due_date": None,
        "completed_at": None,
        "created_by": "system",
        "created_at": _NOW,
        "updated_at": _NOW,
    }
    base.update(overrides)
    return base


def _fake_control(cid="ctrl-001", profile_id="profile-001", **overrides):
    base = {
        "id": cid,
        "company_profile_id": profile_id,
        "title": "Employment contract check",
        "description": "Verify all employees have signed contracts.",
        "control_type": "preventive",
        "implementation_status": "planned",
        "owner": "hr-team",
        "risk_level": "medium",
        "effectiveness_score": 0.0,
        "review_frequency": "quarterly",
        "last_reviewed_at": None,
        "next_review_date": None,
        "created_at": _NOW,
        "updated_at": _NOW,
    }
    base.update(overrides)
    return base


def _fake_evidence(eid="ev-001", control_id="ctrl-001"):
    return {
        "id": eid,
        "control_id": control_id,
        "title": "Signed contracts scan",
        "description": "Scanned copies of all signed contracts.",
        "evidence_type": "document",
        "file_reference": "/uploads/contracts.pdf",
        "document_id": None,
        "collected_by": "hr-team",
        "collected_at": _NOW,
        "valid_from": None,
        "valid_until": None,
        "status": "pending",
        "review_notes": None,
        "created_at": _NOW,
        "updated_at": _NOW,
    }


def _fake_link(lid="link-001", exigence_id="exig-001", control_id="ctrl-001", **overrides):
    base = {
        "id": lid,
        "exigence_id": exigence_id,
        "control_id": control_id,
        "assessment_id": None,
        "coverage_status": "fully_covered",
        "coverage_score": 1.0,
        "gap_description": None,
        "justification": "Contract check procedure covers this requirement.",
        "linked_by": "system",
        "created_at": _NOW,
        "updated_at": _NOW,
    }
    base.update(overrides)
    return base


def _fake_exigence(eid="exig-001"):
    return {
        "id": eid,
        "title": "Employment contract obligation",
        "document_id": "doc-001",
        "page_number": 1,
        "exigence_type": "obligation",
        "created_at": _NOW,
    }


def _fake_exception(exc_id="exc-001", exigence_id="exig-002", profile_id="profile-001"):
    return {
        "id": exc_id,
        "exigence_id": exigence_id,
        "company_profile_id": profile_id,
        "control_id": None,
        "title": "Deferred: safety training",
        "description": "Safety training deferred until Q3.",
        "exception_type": "deferred",
        "status": "requested",
        "risk_level": "high",
        "justification": "Training provider unavailable until Q3.",
        "approved_by": None,
        "approval_date": None,
        "expiry_date": None,
        "remediation_action_id": None,
        "review_frequency": "quarterly",
        "created_at": _NOW,
        "updated_at": _NOW,
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


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Assessment CRUD
# ═══════════════════════════════════════════════════════════════════════════════

class TestAssessmentEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = _make_client()

    @patch("app.services.compliance_service._collection")
    @patch("app.services.audit_service._collection")
    def test_create_assessment(self, mock_audit_col, mock_svc_col):
        profile = _fake_profile()
        stored = {}

        async def insert_one(doc):
            stored.update(doc)

        profiles_col = AsyncMock()
        profiles_col.find_one = AsyncMock(return_value=profile)

        assessments_col = AsyncMock()
        assessments_col.insert_one = AsyncMock(side_effect=insert_one)

        links_col = AsyncMock()
        links_col.count_documents = AsyncMock(return_value=0)

        audit_col = AsyncMock()
        audit_col.insert_one = AsyncMock()
        mock_audit_col.return_value = audit_col

        def col_router(name):
            if name == "company_profiles":
                return profiles_col
            if name == "compliance_assessments":
                return assessments_col
            if name == "requirement_control_links":
                return links_col
            return AsyncMock()

        mock_svc_col.side_effect = col_router

        r = self.client.post("/api/v1/compliance/assessments", json={
            "company_profile_id": "profile-001",
            "title": "Initial Gap Analysis",
            "assessment_type": "initial",
            "risk_level": "high",
        })
        self.assertEqual(r.status_code, 201)
        data = r.json()
        self.assertEqual(data["title"], "Initial Gap Analysis")
        self.assertEqual(data["status"], "draft")
        self.assertEqual(data["risk_level"], "high")

    @patch("app.services.compliance_service._collection")
    def test_list_assessments(self, mock_col):
        a1 = _fake_assessment("a1")
        a2 = _fake_assessment("a2", title="Periodic review")

        assessments_col = MagicMock()
        assessments_col.count_documents = AsyncMock(return_value=2)
        assessments_col.find = MagicMock(return_value=MockCursor([a1, a2]))

        links_col = AsyncMock()
        links_col.count_documents = AsyncMock(return_value=0)

        def col_router(name):
            if name == "compliance_assessments":
                return assessments_col
            if name == "requirement_control_links":
                return links_col
            return AsyncMock()

        mock_col.side_effect = col_router

        r = self.client.get("/api/v1/compliance/assessments")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data["total"], 2)
        self.assertEqual(len(data["assessments"]), 2)


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Control CRUD
# ═══════════════════════════════════════════════════════════════════════════════

class TestControlEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = _make_client()

    @patch("app.services.compliance_service._collection")
    @patch("app.services.audit_service._collection")
    def test_create_control(self, mock_audit_col, mock_svc_col):
        profile = _fake_profile()

        profiles_col = AsyncMock()
        profiles_col.find_one = AsyncMock(return_value=profile)

        controls_col = AsyncMock()
        controls_col.insert_one = AsyncMock()

        evidences_col = AsyncMock()
        evidences_col.count_documents = AsyncMock(return_value=0)

        links_col = AsyncMock()
        links_col.count_documents = AsyncMock(return_value=0)

        audit_col = AsyncMock()
        audit_col.insert_one = AsyncMock()
        mock_audit_col.return_value = audit_col

        def col_router(name):
            if name == "company_profiles":
                return profiles_col
            if name == "controls":
                return controls_col
            if name == "control_evidences":
                return evidences_col
            if name == "requirement_control_links":
                return links_col
            return AsyncMock()

        mock_svc_col.side_effect = col_router

        r = self.client.post("/api/v1/compliance/controls", json={
            "company_profile_id": "profile-001",
            "title": "Contract verification",
            "description": "Check all employees have signed contracts.",
            "control_type": "preventive",
        })
        self.assertEqual(r.status_code, 201)
        data = r.json()
        self.assertEqual(data["control_type"], "preventive")
        self.assertEqual(data["implementation_status"], "planned")

    @patch("app.services.compliance_service._collection")
    @patch("app.services.audit_service._collection")
    def test_update_control_status(self, mock_audit_col, mock_svc_col):
        original = _fake_control()
        updated = _fake_control(implementation_status="implemented")

        controls_col = AsyncMock()
        controls_col.find_one = AsyncMock(side_effect=[original, updated])
        controls_col.update_one = AsyncMock()

        evidences_col = AsyncMock()
        evidences_col.count_documents = AsyncMock(return_value=0)

        links_col = AsyncMock()
        links_col.count_documents = AsyncMock(return_value=0)

        def col_router(name):
            if name == "controls":
                return controls_col
            if name == "control_evidences":
                return evidences_col
            if name == "requirement_control_links":
                return links_col
            return AsyncMock()

        mock_svc_col.side_effect = col_router

        r = self.client.patch("/api/v1/compliance/controls/ctrl-001", json={
            "implementation_status": "implemented",
            "effectiveness_score": 0.85,
        })
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["implementation_status"], "implemented")


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Evidence Attachment
# ═══════════════════════════════════════════════════════════════════════════════

class TestEvidenceEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = _make_client()

    @patch("app.services.compliance_service._collection")
    def test_create_evidence(self, mock_col):
        control = _fake_control()

        controls_col = AsyncMock()
        controls_col.find_one = AsyncMock(return_value=control)

        evidences_col = AsyncMock()
        evidences_col.insert_one = AsyncMock()

        def col_router(name):
            if name == "controls":
                return controls_col
            if name == "control_evidences":
                return evidences_col
            return AsyncMock()

        mock_col.side_effect = col_router

        r = self.client.post("/api/v1/compliance/controls/ctrl-001/evidences", json={
            "title": "Signed contracts",
            "evidence_type": "document",
            "file_reference": "/uploads/contracts.pdf",
            "collected_by": "hr-team",
        })
        self.assertEqual(r.status_code, 201)
        data = r.json()
        self.assertEqual(data["evidence_type"], "document")
        self.assertEqual(data["status"], "pending")

    @patch("app.services.compliance_service._collection")
    def test_list_evidences(self, mock_col):
        ev1 = _fake_evidence("ev-001")
        ev2 = _fake_evidence("ev-002")

        evidences_col = MagicMock()
        evidences_col.count_documents = AsyncMock(return_value=2)
        evidences_col.find = MagicMock(return_value=MockCursor([ev1, ev2]))

        def col_router(name):
            if name == "control_evidences":
                return evidences_col
            return AsyncMock()

        mock_col.side_effect = col_router

        r = self.client.get("/api/v1/compliance/controls/ctrl-001/evidences")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data["total"], 2)
        self.assertEqual(data["control_id"], "ctrl-001")

    @patch("app.services.compliance_service._collection")
    def test_update_evidence_accept(self, mock_col):
        original = _fake_evidence()
        accepted = _fake_evidence()
        accepted["status"] = "accepted"
        accepted["review_notes"] = "Verified by auditor."

        evidences_col = AsyncMock()
        evidences_col.find_one = AsyncMock(side_effect=[original, accepted])
        evidences_col.update_one = AsyncMock()

        def col_router(name):
            if name == "control_evidences":
                return evidences_col
            return AsyncMock()

        mock_col.side_effect = col_router

        r = self.client.patch("/api/v1/compliance/evidences/ev-001", json={
            "status": "accepted",
            "review_notes": "Verified by auditor.",
        })
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["status"], "accepted")


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Requirement–Control Links
# ═══════════════════════════════════════════════════════════════════════════════

class TestLinkEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = _make_client()

    @patch("app.services.compliance_service._collection")
    def test_create_link(self, mock_col):
        exigence = _fake_exigence()
        control = _fake_control()

        exigences_col = AsyncMock()
        exigences_col.find_one = AsyncMock(return_value=exigence)

        controls_col = AsyncMock()
        controls_col.find_one = AsyncMock(return_value=control)

        links_col = AsyncMock()
        links_col.find_one = AsyncMock(return_value=None)  # no duplicate
        links_col.insert_one = AsyncMock()

        def col_router(name):
            if name == "exigences":
                return exigences_col
            if name == "controls":
                return controls_col
            if name == "requirement_control_links":
                return links_col
            return AsyncMock()

        mock_col.side_effect = col_router

        r = self.client.post("/api/v1/compliance/links", json={
            "exigence_id": "exig-001",
            "control_id": "ctrl-001",
            "coverage_status": "fully_covered",
            "coverage_score": 1.0,
            "justification": "Full coverage via contract check.",
        })
        self.assertEqual(r.status_code, 201)
        data = r.json()
        self.assertEqual(data["coverage_status"], "fully_covered")
        self.assertEqual(data["coverage_score"], 1.0)

    @patch("app.services.compliance_service._collection")
    def test_duplicate_link_rejected(self, mock_col):
        exigence = _fake_exigence()
        control = _fake_control()
        existing_link = _fake_link()

        exigences_col = AsyncMock()
        exigences_col.find_one = AsyncMock(return_value=exigence)

        controls_col = AsyncMock()
        controls_col.find_one = AsyncMock(return_value=control)

        links_col = AsyncMock()
        links_col.find_one = AsyncMock(return_value=existing_link)

        def col_router(name):
            if name == "exigences":
                return exigences_col
            if name == "controls":
                return controls_col
            if name == "requirement_control_links":
                return links_col
            return AsyncMock()

        mock_col.side_effect = col_router

        r = self.client.post("/api/v1/compliance/links", json={
            "exigence_id": "exig-001",
            "control_id": "ctrl-001",
        })
        self.assertEqual(r.status_code, 422)

    @patch("app.services.compliance_service._collection")
    def test_delete_link(self, mock_col):
        links_col = AsyncMock()
        delete_result = MagicMock()
        delete_result.deleted_count = 1
        links_col.delete_one = AsyncMock(return_value=delete_result)

        def col_router(name):
            if name == "requirement_control_links":
                return links_col
            return AsyncMock()

        mock_col.side_effect = col_router

        r = self.client.delete("/api/v1/compliance/links/link-001")
        self.assertEqual(r.status_code, 204)


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Gap Calculation (Compliance Posture)
# ═══════════════════════════════════════════════════════════════════════════════

class TestGapCalculation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = _make_client()

    @patch("app.services.compliance_service._collection")
    def test_posture_all_covered(self, mock_col):
        """All applicable exigences have fully_covered links → score = 1.0."""
        profile = _fake_profile()
        applicabilities = [
            {"profile_id": "profile-001", "exigence_id": "exig-001", "is_applicable": True},
            {"profile_id": "profile-001", "exigence_id": "exig-002", "is_applicable": True},
        ]
        links = [
            _fake_link("l1", "exig-001", "ctrl-001", coverage_status="fully_covered", coverage_score=1.0),
            _fake_link("l2", "exig-002", "ctrl-002", coverage_status="fully_covered", coverage_score=1.0),
        ]

        profiles_col = AsyncMock()
        profiles_col.find_one = AsyncMock(return_value=profile)

        app_col = MagicMock()
        app_col.find = MagicMock(return_value=MockCursor(applicabilities))

        exc_col = MagicMock()
        exc_col.find = MagicMock(return_value=MockCursor([]))

        links_col = MagicMock()
        links_col.find = MagicMock(return_value=MockCursor(links))

        def col_router(name):
            if name == "company_profiles":
                return profiles_col
            if name == "exigence_applicabilities":
                return app_col
            if name == "exception_register":
                return exc_col
            if name == "requirement_control_links":
                return links_col
            return AsyncMock()

        mock_col.side_effect = col_router

        r = self.client.get("/api/v1/compliance/posture/profile-001")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data["total_applicable"], 2)
        self.assertEqual(data["fully_covered"], 2)
        self.assertEqual(data["not_covered"], 0)
        self.assertEqual(data["overall_coverage_score"], 1.0)
        self.assertEqual(len(data["gaps"]), 0)

    @patch("app.services.compliance_service._collection")
    def test_posture_with_gaps(self, mock_col):
        """One covered, one partially covered, one not covered → gaps returned."""
        profile = _fake_profile()
        applicabilities = [
            {"profile_id": "profile-001", "exigence_id": "exig-001", "is_applicable": True},
            {"profile_id": "profile-001", "exigence_id": "exig-002", "is_applicable": True},
            {"profile_id": "profile-001", "exigence_id": "exig-003", "is_applicable": True},
        ]
        links = [
            _fake_link("l1", "exig-001", "ctrl-001", coverage_status="fully_covered", coverage_score=1.0),
            _fake_link("l2", "exig-002", "ctrl-002", coverage_status="partially_covered", coverage_score=0.5),
            # exig-003 has no link → not_covered
        ]
        exig_002 = {"id": "exig-002", "title": "Safety training obligation"}
        exig_003 = {"id": "exig-003", "title": "Fire safety audit"}

        profiles_col = AsyncMock()
        profiles_col.find_one = AsyncMock(return_value=profile)

        app_col = MagicMock()
        app_col.find = MagicMock(return_value=MockCursor(applicabilities))

        exc_col = MagicMock()
        exc_col.find = MagicMock(return_value=MockCursor([]))

        links_col = MagicMock()
        links_col.find = MagicMock(return_value=MockCursor(links))

        exigences_col = AsyncMock()
        exigences_col.find_one = AsyncMock(
            side_effect=lambda q: exig_002 if q.get("id") == "exig-002" else exig_003
        )

        def col_router(name):
            if name == "company_profiles":
                return profiles_col
            if name == "exigence_applicabilities":
                return app_col
            if name == "exception_register":
                return exc_col
            if name == "requirement_control_links":
                return links_col
            if name == "exigences":
                return exigences_col
            return AsyncMock()

        mock_col.side_effect = col_router

        r = self.client.get("/api/v1/compliance/posture/profile-001")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data["total_applicable"], 3)
        self.assertEqual(data["fully_covered"], 1)
        self.assertEqual(data["partially_covered"], 1)
        self.assertEqual(data["not_covered"], 1)
        self.assertAlmostEqual(data["overall_coverage_score"], 1 / 3, places=3)
        self.assertEqual(len(data["gaps"]), 2)

    @patch("app.services.compliance_service._collection")
    def test_posture_with_exception(self, mock_col):
        """An approved exception counts as covered."""
        profile = _fake_profile()
        applicabilities = [
            {"profile_id": "profile-001", "exigence_id": "exig-001", "is_applicable": True},
            {"profile_id": "profile-001", "exigence_id": "exig-002", "is_applicable": True},
        ]
        exceptions = [
            {"exigence_id": "exig-002", "status": "approved", "company_profile_id": "profile-001"},
        ]
        links = [
            _fake_link("l1", "exig-001", "ctrl-001", coverage_status="fully_covered", coverage_score=1.0),
        ]

        profiles_col = AsyncMock()
        profiles_col.find_one = AsyncMock(return_value=profile)

        app_col = MagicMock()
        app_col.find = MagicMock(return_value=MockCursor(applicabilities))

        exc_col = MagicMock()
        exc_col.find = MagicMock(return_value=MockCursor(exceptions))

        links_col = MagicMock()
        links_col.find = MagicMock(return_value=MockCursor(links))

        def col_router(name):
            if name == "company_profiles":
                return profiles_col
            if name == "exigence_applicabilities":
                return app_col
            if name == "exception_register":
                return exc_col
            if name == "requirement_control_links":
                return links_col
            return AsyncMock()

        mock_col.side_effect = col_router

        r = self.client.get("/api/v1/compliance/posture/profile-001")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data["total_applicable"], 2)
        self.assertEqual(data["fully_covered"], 1)
        self.assertEqual(data["excepted"], 1)
        self.assertEqual(data["overall_coverage_score"], 1.0)

    @patch("app.services.compliance_service._collection")
    def test_posture_no_applicabilities(self, mock_col):
        """No applicable exigences → score = 1.0 (vacuously compliant)."""
        profile = _fake_profile()

        profiles_col = AsyncMock()
        profiles_col.find_one = AsyncMock(return_value=profile)

        app_col = MagicMock()
        app_col.find = MagicMock(return_value=MockCursor([]))

        def col_router(name):
            if name == "company_profiles":
                return profiles_col
            if name == "exigence_applicabilities":
                return app_col
            return AsyncMock()

        mock_col.side_effect = col_router

        r = self.client.get("/api/v1/compliance/posture/profile-001")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data["total_applicable"], 0)
        self.assertEqual(data["overall_coverage_score"], 1.0)

    @patch("app.services.compliance_service._collection")
    def test_gaps_endpoint(self, mock_col):
        """Gaps endpoint returns only uncovered/partially covered items."""
        profile = _fake_profile()
        applicabilities = [
            {"profile_id": "profile-001", "exigence_id": "exig-001", "is_applicable": True},
            {"profile_id": "profile-001", "exigence_id": "exig-002", "is_applicable": True},
        ]
        exig_002 = {"id": "exig-002", "title": "Missing requirement"}

        profiles_col = AsyncMock()
        profiles_col.find_one = AsyncMock(return_value=profile)

        app_col = MagicMock()
        app_col.find = MagicMock(return_value=MockCursor(applicabilities))

        exc_col = MagicMock()
        exc_col.find = MagicMock(return_value=MockCursor([]))

        links_col = MagicMock()
        links = [_fake_link("l1", "exig-001", "ctrl-001", coverage_status="fully_covered", coverage_score=1.0)]
        links_col.find = MagicMock(return_value=MockCursor(links))

        exigences_col = AsyncMock()
        exigences_col.find_one = AsyncMock(return_value=exig_002)

        def col_router(name):
            if name == "company_profiles":
                return profiles_col
            if name == "exigence_applicabilities":
                return app_col
            if name == "exception_register":
                return exc_col
            if name == "requirement_control_links":
                return links_col
            if name == "exigences":
                return exigences_col
            return AsyncMock()

        mock_col.side_effect = col_router

        r = self.client.get("/api/v1/compliance/gaps/profile-001")
        self.assertEqual(r.status_code, 200)
        gaps = r.json()
        self.assertEqual(len(gaps), 1)
        self.assertEqual(gaps[0]["exigence_id"], "exig-002")
        self.assertEqual(gaps[0]["coverage_status"], "not_covered")


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Exception Register & Remediation Workflow
# ═══════════════════════════════════════════════════════════════════════════════

class TestExceptionAndRemediation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = _make_client()

    @patch("app.services.compliance_service._collection")
    @patch("app.services.audit_service._collection")
    def test_create_exception(self, mock_audit_col, mock_svc_col):
        exigence = _fake_exigence("exig-002")
        profile = _fake_profile()

        exigences_col = AsyncMock()
        exigences_col.find_one = AsyncMock(return_value=exigence)

        profiles_col = AsyncMock()
        profiles_col.find_one = AsyncMock(return_value=profile)

        exc_col = AsyncMock()
        exc_col.insert_one = AsyncMock()

        audit_col = AsyncMock()
        audit_col.insert_one = AsyncMock()
        mock_audit_col.return_value = audit_col

        def col_router(name):
            if name == "exigences":
                return exigences_col
            if name == "company_profiles":
                return profiles_col
            if name == "exception_register":
                return exc_col
            return AsyncMock()

        mock_svc_col.side_effect = col_router

        r = self.client.post("/api/v1/compliance/exceptions", json={
            "exigence_id": "exig-002",
            "company_profile_id": "profile-001",
            "title": "Deferred training",
            "description": "Safety training deferred.",
            "exception_type": "deferred",
            "risk_level": "high",
            "justification": "Provider unavailable.",
        })
        self.assertEqual(r.status_code, 201)
        data = r.json()
        self.assertEqual(data["status"], "requested")
        self.assertEqual(data["exception_type"], "deferred")

    @patch("app.services.compliance_service._collection")
    def test_approve_exception(self, mock_col):
        original = _fake_exception()
        approved = _fake_exception()
        approved["status"] = "approved"
        approved["approved_by"] = "legal-director"

        exc_col = AsyncMock()
        exc_col.find_one = AsyncMock(side_effect=[original, approved])
        exc_col.update_one = AsyncMock()

        def col_router(name):
            if name == "exception_register":
                return exc_col
            return AsyncMock()

        mock_col.side_effect = col_router

        r = self.client.patch("/api/v1/compliance/exceptions/exc-001", json={
            "status": "approved",
            "approved_by": "legal-director",
        })
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["status"], "approved")

    @patch("app.services.compliance_service._collection")
    @patch("app.services.audit_service._collection")
    def test_create_remediation_action(self, mock_audit_col, mock_svc_col):
        profile = _fake_profile()

        profiles_col = AsyncMock()
        profiles_col.find_one = AsyncMock(return_value=profile)

        actions_col = AsyncMock()
        actions_col.insert_one = AsyncMock()

        exc_col = AsyncMock()
        exc_col.update_one = AsyncMock()

        audit_col = AsyncMock()
        audit_col.insert_one = AsyncMock()
        mock_audit_col.return_value = audit_col

        def col_router(name):
            if name == "company_profiles":
                return profiles_col
            if name == "actions":
                return actions_col
            if name == "exception_register":
                return exc_col
            return AsyncMock()

        mock_svc_col.side_effect = col_router

        r = self.client.post("/api/v1/compliance/remediation-actions", json={
            "title": "Schedule safety training",
            "description": "Book safety training for Q3.",
            "company_profile_id": "profile-001",
            "exigence_id": "exig-002",
            "exception_id": "exc-001",
            "priority": "high",
        })
        self.assertEqual(r.status_code, 201)
        data = r.json()
        self.assertEqual(data["status"], "pending")
        self.assertEqual(data["priority"], "high")
        self.assertEqual(data["modalite"], "remediation")


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Schema Validation
# ═══════════════════════════════════════════════════════════════════════════════

class TestComplianceSchemaValidation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = _make_client()

    def test_assessment_missing_title(self):
        r = self.client.post("/api/v1/compliance/assessments", json={
            "company_profile_id": "p1",
        })
        self.assertEqual(r.status_code, 422)

    def test_assessment_invalid_type(self):
        r = self.client.post("/api/v1/compliance/assessments", json={
            "company_profile_id": "p1",
            "title": "Test",
            "assessment_type": "invalid_type",
        })
        self.assertEqual(r.status_code, 422)

    def test_control_invalid_type(self):
        r = self.client.post("/api/v1/compliance/controls", json={
            "company_profile_id": "p1",
            "title": "X",
            "description": "Y",
            "control_type": "magical",
        })
        self.assertEqual(r.status_code, 422)

    def test_evidence_invalid_type(self):
        r = self.client.post("/api/v1/compliance/controls/c1/evidences", json={
            "title": "X",
            "evidence_type": "telepathy",
        })
        self.assertEqual(r.status_code, 422)

    def test_link_invalid_coverage(self):
        r = self.client.post("/api/v1/compliance/links", json={
            "exigence_id": "e1",
            "control_id": "c1",
            "coverage_status": "super_covered",
        })
        self.assertEqual(r.status_code, 422)

    def test_exception_invalid_type(self):
        r = self.client.post("/api/v1/compliance/exceptions", json={
            "exigence_id": "e1",
            "company_profile_id": "p1",
            "title": "X",
            "description": "Y",
            "justification": "Z",
            "exception_type": "magic",
        })
        self.assertEqual(r.status_code, 422)


if __name__ == "__main__":
    unittest.main()
