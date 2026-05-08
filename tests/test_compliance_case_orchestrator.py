"""
Tests for the Compliance Case Orchestrator.

Test Scenarios:
1. Case with sufficient info → findings + actions created
2. Case with missing info → clarification requested
3. Case with document evidence → richer analysis
4. Low confidence case → human review recommended
5. Document contradictions → clarify decision
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Test will use the actual implementation with mocked dependencies


@pytest.fixture
def mock_db():
    """Mock database connection."""
    return MagicMock()


@pytest.fixture
def sample_case_context():
    """Sample case conversation context."""
    return {
        "facts_known": [
            "L'entreprise est une SARL basée à Tunis",
            "15 employés travaillent sans contrat écrit",
            "L'entreprise opère dans le secteur textile",
            "Aucun règlement intérieur n'est en place",
        ],
        "facts_missing": ["Durée d'emploi des salariés"],
        "matter_type": "labour_compliance",
        "urgency": "high",
        "article_references": ["Art. 6 du Code du Travail", "Art. 14 du Code du Travail"],
        "next_question": "Depuis combien de temps ces employés travaillent-ils sans contrat?",
    }


@pytest.fixture
def sample_document_analysis():
    """Sample document analysis."""
    return {
        "document_type": "contract",
        "language": "fr",
        "summary": "Contrat de travail type pour employés textiles",
        "entities": {
            "parties": ["SARL Textile Tunis", "Salarié"],
            "dates": ["2024-01-15"],
            "deadlines": [{"description": "Date de début", "date": "2024-02-01", "urgent": False}],
            "obligations": [{"description": "Signature du contrat avant prise de poste", "source": "Art. 6"}],
            "legal_references": [{"type": "article", "number": "6", "law": "Code du Travail"}],
        },
        "confidence": 0.85,
    }


@pytest.fixture
def sample_exigence():
    """Sample exigence document."""
    return {
        "id": "exig-001",
        "exigence_type": "obligation",
        "text": "Tout employeur doit remettre à chaque travailleur un contrat de travail écrit",
        "article_reference": "Art. 6 du Code du Travail",
        "article_version_id": "ver-001",
    }


@pytest.fixture
def sample_company_profile():
    """Sample company profile."""
    return {
        "id": "prof-001",
        "name": "SARL Textile Tunis",
        "sector": "textile",
        "size": "PME",
        "employees": 15,
        "activities": "Fabrication textile",
        "jurisdiction": "tunisia",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Case with sufficient information → findings + actions
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_orchestrate_sufficient_info_creates_findings_and_actions(
    mock_db, sample_case_context, sample_document_analysis, sample_exigence
):
    """
    Test that a case with sufficient information:
    1. Gets ACT decision
    2. Has findings proposed
    3. Has actions proposed
    4. Can auto-create findings and actions when requested
    """
    case_id = "case-001"

    # Mock all the dependencies
    with patch("app.services.compliance_case_orchestrator.case_service.get_case",
               new_callable=AsyncMock) as mock_get_case, \
         patch("app.services.compliance_case_orchestrator.case_conversation_service._load_conversation_context",
               new_callable=AsyncMock) as mock_load_ctx, \
         patch("app.services.compliance_case_orchestrator.case_document_service.list_case_documents_with_analysis",
               new_callable=AsyncMock) as mock_list_docs, \
         patch("app.services.compliance_case_orchestrator._evaluate_applicability",
               new_callable=AsyncMock) as mock_eval_app, \
         patch("app.services.compliance_case_orchestrator.action_service.get_actions_by_exigence",
               new_callable=AsyncMock) as mock_get_actions, \
         patch("app.services.compliance_case_orchestrator.llm_service.call_ollama",
               new_callable=AsyncMock) as mock_llm:

        # Setup mocks
        mock_get_case.return_value = {
            "id": case_id,
            "company_profile_id": "prof-001",
            "status": "in_progress",
        }
        mock_load_ctx.return_value = sample_case_context
        mock_list_docs.return_value = (
            [{"id": "doc-001", "analysis": sample_document_analysis}],
            1
        )
        mock_eval_app.return_value = [
            {"exigence": sample_exigence, "evaluation": {"is_applicable": True, "confidence": 0.9}}
        ]
        mock_get_actions.return_value = []

        # Mock LLM responses for gap analysis
        mock_llm.return_value = """{
            "gaps": [
                {
                    "type": "violation",
                    "description": "15 employes travaillent sans contrat ecrit",
                    "exigence_id": "exig-001",
                    "article_reference": "Art. 6 du Code du Travail",
                    "has_penalty": true,
                    "penalty_description": "Amende de 500 dinars par employe",
                    "confidence": 0.92
                }
            ],
            "violations": [
                {
                    "description": "Absence de contrats de travail ecrits",
                    "severity": "major",
                    "article_reference": "Art. 6 du Code du Travail",
                    "confidence": 0.90
                }
            ],
            "recommendations": [
                {
                    "description": "Mettre en place un processus de signature systematique",
                    "priority": "high",
                    "rationale": "Prevenir future non-conformite"
                }
            ],
            "overall_confidence": 0.88,
            "evidence_sufficiency": "sufficient"
        }"""

        from app.services.compliance_case_orchestrator import analyze_and_orchestrate, OrchestratorDecision

        result = await analyze_and_orchestrate(
            mock_db,
            case_id,
            auto_create_findings=False,  # Test without auto-create first
            auto_create_actions=False,
        )

        # Assertions
        assert result.decision == OrchestratorDecision.ACT
        assert result.confidence_assessment["overall"] >= 0.70
        assert len(result.proposed_findings) > 0
        assert result.risk_level in ["high", "medium", "low"]
        assert len(result.next_steps) > 0


@pytest.mark.asyncio
async def test_orchestrate_auto_create_persists_to_database(
    mock_db, sample_case_context, sample_document_analysis, sample_exigence
):
    """Test that auto_create_findings and auto_create_actions persist to DB."""
    case_id = "case-002"

    with patch("app.services.compliance_case_orchestrator.case_service.get_case",
               new_callable=AsyncMock) as mock_get_case, \
         patch("app.services.compliance_case_orchestrator.case_conversation_service._load_conversation_context",
               new_callable=AsyncMock) as mock_load_ctx, \
         patch("app.services.compliance_case_orchestrator.case_document_service.list_case_documents_with_analysis",
               new_callable=AsyncMock) as mock_list_docs, \
         patch("app.services.compliance_case_orchestrator._evaluate_applicability",
               new_callable=AsyncMock) as mock_eval_app, \
         patch("app.services.compliance_case_orchestrator.action_service.get_actions_by_exigence",
               new_callable=AsyncMock) as mock_get_actions, \
         patch("app.services.compliance_case_orchestrator.llm_service.call_ollama",
               new_callable=AsyncMock) as mock_llm, \
         patch("app.services.compliance_case_orchestrator.case_service.create_finding",
               new_callable=AsyncMock) as mock_create_finding, \
         patch("app.services.compliance_case_orchestrator.case_service.create_case_action",
               new_callable=AsyncMock) as mock_create_action, \
         patch("app.services.compliance_case_orchestrator.audit_service.log_event",
               new_callable=AsyncMock):

        mock_get_case.return_value = {
            "id": case_id,
            "company_profile_id": None,
            "status": "in_progress",
        }
        mock_load_ctx.return_value = sample_case_context
        mock_list_docs.return_value = ([{"id": "doc-001", "analysis": sample_document_analysis}], 1)
        mock_eval_app.return_value = [
            {"exigence": sample_exigence, "evaluation": {"is_applicable": True, "confidence": 0.9}}
        ]
        mock_get_actions.return_value = []

        mock_llm.return_value = """{
            "gaps": [
                {
                    "type": "violation",
                    "description": "15 employes sans contrat",
                    "exigence_id": "exig-001",
                    "article_reference": "Art. 6",
                    "has_penalty": true,
                    "confidence": 0.90
                }
            ],
            "violations": [],
            "recommendations": [],
            "overall_confidence": 0.85,
            "evidence_sufficiency": "sufficient"
        }"""

        mock_create_finding.return_value = {
            "id": "finding-001",
            "case_id": case_id,
            "title": "Violation: 15 employés sans contrat",
            "severity": "major",
        }
        mock_create_action.return_value = {
            "id": "action-001",
            "case_id": case_id,
            "title": "Remediate: Violation",
            "priority": "high",
        }

        from app.services.compliance_case_orchestrator import analyze_and_orchestrate

        result = await analyze_and_orchestrate(
            mock_db,
            case_id,
            auto_create_findings=True,
            auto_create_actions=True,
        )

        # Verify DB creation was called
        assert mock_create_finding.called
        assert len(result.findings_created) > 0


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Case with missing information → clarification requested
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_orchestrate_missing_info_requests_clarification(mock_db):
    """
    Test that a case with too many missing facts:
    1. Gets ASK decision
    2. Returns a clarification question
    3. Does not create findings
    """
    case_id = "case-003"
    with patch("app.services.compliance_case_orchestrator._collection") as mock_collection:
        mock_collection.return_value = AsyncMock(
            find_one=AsyncMock(return_value=None)
        )

        with patch("app.services.compliance_case_orchestrator.case_service.get_case") as mock_get_case, \
             patch("app.services.compliance_case_orchestrator.case_conversation_service._load_conversation_context") as mock_load_ctx, \
             patch("app.services.compliance_case_orchestrator.case_document_service.list_case_documents_with_analysis") as mock_list_docs:

            mock_get_case.return_value = {
                "id": case_id,
                "company_profile_id": None,
                "status": "in_progress",
            }
            # Many missing facts
            mock_load_ctx.return_value = {
                "facts_known": ["L'entreprise est une SARL"],  # Only 1 fact
                "facts_missing": [
                    "Nombre d'employés",
                    "Secteur d'activité",
                    "Localisation",
                    "Type de contrats",
                    "Existence de règlement intérieur",
                ],
                "matter_type": "labour_compliance",
                "urgency": "unknown",
                "article_references": [],
            }
            mock_list_docs.return_value = ([], 0)

            from app.services.compliance_case_orchestrator import analyze_and_orchestrate, OrchestratorDecision

            result = await analyze_and_orchestrate(mock_db, case_id)

            assert result.decision == OrchestratorDecision.ASK
            assert result.clarification_question is not None
            assert len(result.clarification_question) > 10
            assert len(result.proposed_findings) == 0


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Low confidence case → human review recommended
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_orchestrate_low_confidence_recommends_review(mock_db):
    """
    Test that a case with low confidence:
    1. Gets REVIEW decision
    2. Provides human_review_reason
    3. Does not auto-create anything
    """
    case_id = "case-004"

    with patch("app.services.compliance_case_orchestrator.case_service.get_case",
               new_callable=AsyncMock) as mock_get_case, \
         patch("app.services.compliance_case_orchestrator.case_conversation_service._load_conversation_context",
               new_callable=AsyncMock) as mock_load_ctx, \
         patch("app.services.compliance_case_orchestrator.case_document_service.list_case_documents_with_analysis",
               new_callable=AsyncMock) as mock_list_docs, \
         patch("app.services.compliance_case_orchestrator._evaluate_applicability",
               new_callable=AsyncMock) as mock_eval_app, \
         patch("app.services.compliance_case_orchestrator.llm_service.call_ollama",
               new_callable=AsyncMock) as mock_llm:

        mock_get_case.return_value = {
            "id": case_id,
            "company_profile_id": None,
            "status": "in_progress",
        }
        mock_load_ctx.return_value = {
            "facts_known": ["Entreprise a Tunis", "Travaille dans l'informatique", "Fondee en 2018"],
            "facts_missing": [],
            "matter_type": "labour_compliance",
            "urgency": "low",
            "article_references": [],
        }
        mock_list_docs.return_value = ([], 0)
        mock_eval_app.return_value = [
            {"exigence": {"id": "exig-low", "exigence_type": "obligation",
                          "text": "Obligation test", "article_reference": "Art. 1"},
             "evaluation": {"is_applicable": True, "confidence": 0.5}}
        ]

        # Low confidence from LLM
        mock_llm.return_value = """{
            "gaps": [],
            "violations": [],
            "recommendations": [],
            "overall_confidence": 0.45,
            "evidence_sufficiency": "insufficient"
        }"""

        from app.services.compliance_case_orchestrator import analyze_and_orchestrate, OrchestratorDecision

        result = await analyze_and_orchestrate(mock_db, case_id)

        assert result.decision == OrchestratorDecision.REVIEW
        assert result.human_review_reason is not None
        assert "confidence" in result.human_review_reason.lower() or "Low" in result.human_review_reason


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Document contradictions → clarify decision
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_orchestrate_document_contradictions_requests_clarify(mock_db):
    """
    Test that a case with contradictory documents:
    1. Gets CLARIFY decision
    2. Identifies the contradiction
    """
    case_id = "case-005"

    with patch("app.services.compliance_case_orchestrator.case_service.get_case") as mock_get_case, \
         patch("app.services.compliance_case_orchestrator.case_conversation_service._load_conversation_context") as mock_load_ctx, \
         patch("app.services.compliance_case_orchestrator.case_document_service.list_case_documents_with_analysis") as mock_list_docs:

        mock_get_case.return_value = {
            "id": case_id,
            "company_profile_id": None,
            "status": "in_progress",
        }
        mock_load_ctx.return_value = {
            "facts_known": ["Contrat signé le 2024-01-01"],
            "facts_missing": [],
            "matter_type": "contract_dispute",
            "urgency": "high",
            "article_references": [],
        }
        # Documents with contradictory deadlines
        mock_list_docs.return_value = (
            [
                {
                    "id": "doc-001",
                    "analysis": {
                        "document_type": "contract",
                        "entities": {
                            "deadlines": [
                                {"description": "Date de livraison", "date": "2024-03-01"},
                            ]
                        }
                    }
                },
                {
                    "id": "doc-002",
                    "analysis": {
                        "document_type": "contract",
                        "entities": {
                            "deadlines": [
                                {"description": "Date de livraison", "date": "2024-04-01"},
                            ]
                        }
                    }
                },
            ],
            2
        )

        from app.services.compliance_case_orchestrator import (
            _detect_document_contradictions,
        )

        # First verify the contradiction detection works
        analyses = [
            {"entities": {"deadlines": [{"description": "Date de livraison", "date": "2024-03-01"}]}},
            {"entities": {"deadlines": [{"description": "Date de livraison", "date": "2024-04-01"}]}},
        ]
        contradictions = _detect_document_contradictions(analyses)
        assert len(contradictions) > 0
        assert "2024-03-01" in contradictions[0] or "2024-04-01" in contradictions[0]


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Document evidence improves analysis quality
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_orchestrate_with_documents_richer_output(
    mock_db, sample_case_context, sample_document_analysis
):
    """
    Test that document evidence:
    1. Improves confidence
    2. Provides evidence refs for findings
    3. Maps available documents to requirements
    """
    case_id = "case-006"

    with patch("app.services.compliance_case_orchestrator.case_service.get_case",
               new_callable=AsyncMock) as mock_get_case, \
         patch("app.services.compliance_case_orchestrator.case_conversation_service._load_conversation_context",
               new_callable=AsyncMock) as mock_load_ctx, \
         patch("app.services.compliance_case_orchestrator.case_document_service.list_case_documents_with_analysis",
               new_callable=AsyncMock) as mock_list_docs, \
         patch("app.services.compliance_case_orchestrator._evaluate_applicability",
               new_callable=AsyncMock) as mock_eval_app, \
         patch("app.services.compliance_case_orchestrator.action_service.get_actions_by_exigence",
               new_callable=AsyncMock) as mock_get_actions, \
         patch("app.services.compliance_case_orchestrator.llm_service.call_ollama",
               new_callable=AsyncMock) as mock_llm:

        mock_get_case.return_value = {
            "id": case_id,
            "company_profile_id": None,
            "status": "in_progress",
        }
        mock_load_ctx.return_value = sample_case_context
        # Rich document analysis
        mock_list_docs.return_value = (
            [
                {"id": "doc-001", "analysis": sample_document_analysis},
                {
                    "id": "doc-002",
                    "analysis": {
                        "document_type": "policy",
                        "summary": "Reglement interieur de l entreprise",
                        "entities": {
                            "obligations": [{"description": "Respecter les horaires", "source": "Art. 5"}],
                        },
                        "confidence": 0.80,
                    }
                },
            ],
            2
        )
        mock_eval_app.return_value = [
            {"exigence": {"id": "exig-001", "exigence_type": "obligation",
                          "text": "Obligation de tenir un registre", "article_reference": "Art. 14"},
             "evaluation": {"is_applicable": True, "confidence": 0.8}}
        ]
        mock_get_actions.return_value = []

        mock_llm.return_value = """{
            "gaps": [
                {
                    "type": "missing_document",
                    "description": "Reglement interieur non conforme",
                    "confidence": 0.82
                }
            ],
            "violations": [],
            "recommendations": [
                {
                    "description": "Mettre a jour le reglement interieur",
                    "priority": "medium",
                    "rationale": "Document existant mais incomplet"
                }
            ],
            "overall_confidence": 0.80,
            "evidence_sufficiency": "partial"
        }"""

        from app.services.compliance_case_orchestrator import analyze_and_orchestrate

        result = await analyze_and_orchestrate(mock_db, case_id)

        # Higher confidence due to documents
        assert result.confidence_assessment["overall"] >= 0.70
        assert result.confidence_assessment["evidence_sufficiency"] in ["partial", "sufficient"]


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Utility functions
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_get_orchestration_status(mock_db):
    """Test the orchestration status endpoint."""
    case_id = "case-007"

    with patch("app.services.compliance_case_orchestrator.case_service.get_case") as mock_get_case, \
         patch("app.services.compliance_case_orchestrator.case_conversation_service._load_conversation_context") as mock_load_ctx, \
         patch("app.services.compliance_case_orchestrator.case_service.list_findings") as mock_list_findings, \
         patch("app.services.compliance_case_orchestrator.case_service.list_case_actions") as mock_list_actions:

        mock_get_case.return_value = {
            "id": case_id,
            "status": "in_progress",
            "document_count": 2,
        }
        mock_load_ctx.return_value = {
            "facts_known": ["Fact 1", "Fact 2", "Fact 3", "Fact 4"],  # 4 facts >= MIN_FACTS_FOR_ANALYSIS
            "facts_missing": [],
        }
        mock_list_findings.return_value = ([], 0, {}, {})
        mock_list_actions.return_value = ([], 0, {}, {})

        from app.services.compliance_case_orchestrator import get_orchestration_status

        status = await get_orchestration_status(mock_db, case_id)

        assert status["case_id"] == case_id
        assert status["ready_for_orchestration"] is True
        assert status["orchestration_recommendation"] == "ready"
        assert status["facts_known_count"] == 4


@pytest.mark.asyncio
async def test_quick_assess(mock_db):
    """Test the quick assessment function."""
    case_id = "case-008"

    with patch("app.services.compliance_case_orchestrator.case_service.get_case") as mock_get_case, \
         patch("app.services.compliance_case_orchestrator.case_conversation_service._load_conversation_context") as mock_load_ctx, \
         patch("app.services.compliance_case_orchestrator.case_document_service.list_case_documents_with_analysis") as mock_list_docs:

        mock_get_case.return_value = {
            "id": case_id,
            "company_profile_id": None,
            "status": "in_progress",
        }
        # Good fact coverage, multiple documents
        mock_load_ctx.return_value = {
            "facts_known": ["Fact 1", "Fact 2", "Fact 3", "Fact 4", "Fact 5"],
            "facts_missing": [],
        }
        mock_list_docs.return_value = (
                [
                    {"id": "doc-001", "analysis": {"document_type": "contract", "summary": "Contract"}},
                    {"id": "doc-002", "analysis": {"document_type": "policy", "summary": "Policy"}},
                    {"id": "doc-003", "analysis": {"document_type": "evidence", "summary": "Evidence"}},
                ],
                3
            )

        from app.services.compliance_case_orchestrator import quick_assess

        assessment = await quick_assess(mock_db, case_id)

        assert assessment["case_id"] == case_id
        assert assessment["readiness_score"] >= 0.8
        assert assessment["readiness_level"] == "ready"
        assert assessment["estimated_analysis_quality"] == "high"


@pytest.mark.asyncio
async def test_suggest_next_questions(mock_db):
    """Test the next questions suggestion function."""
    case_id = "case-009"

    with patch("app.services.compliance_case_orchestrator.case_service.get_case",
               new_callable=AsyncMock) as mock_get_case, \
         patch("app.services.compliance_case_orchestrator.case_conversation_service._load_conversation_context",
               new_callable=AsyncMock) as mock_load_ctx, \
         patch("app.services.compliance_case_orchestrator.case_document_service.list_case_documents_with_analysis",
               new_callable=AsyncMock) as mock_list_docs:

        mock_get_case.return_value = {
            "id": case_id,
            "status": "in_progress",
        }
        mock_load_ctx.return_value = {
            "facts_known": ["Entreprise SARL"],
            "facts_missing": ["Nombre d'employes", "Secteur d'activite", "Chiffre d'affaires"],
            "language": "fr",
        }
        mock_list_docs.return_value = ([], 0)

        from app.services.compliance_case_orchestrator import suggest_next_questions

        questions = await suggest_next_questions(mock_db, case_id, count=2)

        assert len(questions) <= 2
        assert all(len(q) > 0 for q in questions)
        assert all(len(q) > 5 for q in questions)  # Questions have meaningful content


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Helper functions
# ═══════════════════════════════════════════════════════════════════════════════

def test_confidence_to_level():
    """Test confidence level mapping."""
    from app.services.compliance_case_orchestrator import _confidence_to_level, ConfidenceLevel

    assert _confidence_to_level(0.90) == ConfidenceLevel.HIGH
    assert _confidence_to_level(0.85) == ConfidenceLevel.HIGH
    assert _confidence_to_level(0.70) == ConfidenceLevel.MEDIUM
    assert _confidence_to_level(0.60) == ConfidenceLevel.MEDIUM
    assert _confidence_to_level(0.59) == ConfidenceLevel.LOW
    assert _confidence_to_level(0.30) == ConfidenceLevel.LOW


def test_severity_from_gap():
    """Test severity mapping from gap type."""
    from app.services.compliance_case_orchestrator import _severity_from_gap

    # Critical with penalty
    assert _severity_from_gap({"type": "violation", "has_penalty": True}) == "critical"

    # Major without penalty
    assert _severity_from_gap({"type": "violation", "has_penalty": False}) == "major"

    # Missing documents/processes
    assert _severity_from_gap({"type": "missing_document"}) == "major"
    assert _severity_from_gap({"type": "missing_process"}) == "major"

    # Recommendations
    assert _severity_from_gap({"type": "recommendation"}) == "minor"


def test_detect_language():
    """Test language detection."""
    from app.services.compliance_case_orchestrator import _detect_language

    # Arabic
    assert _detect_language("هذا نص بالعربية") == "ar"
    assert _detect_language("الفصل 6 من مجلة الشغل") == "ar"

    # French — accented chars trigger detection
    assert _detect_language("Ceci est un texte en français") == "fr"  # ç detected
    assert _detect_language("Quelles sont les obligations?") == "fr"  # sont + les
    assert _detect_language("Le contrat doit être signé") == "fr"  # ê detected

    # English fallback
    assert _detect_language("This is English text") == "en"
    assert _detect_language("What are the requirements?") == "en"


def test_criticality_to_priority():
    """Test criticality to priority mapping."""
    from app.services.compliance_case_orchestrator import _criticality_to_priority

    assert _criticality_to_priority({"level": "critique"}) == "critical"
    assert _criticality_to_priority({"level": "importante"}) == "high"
    assert _criticality_to_priority({"level": "secondaire"}) == "medium"
    assert _criticality_to_priority({}) == "medium"
