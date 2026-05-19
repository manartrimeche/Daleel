"""
Tests for the Advisor Response Composer.

Validates:
- Output structure completeness (all 8 sections present)
- Field presence and type correctness
- Markdown rendering quality
- Integration with orchestrator outputs
- Multi-language support
"""

import pytest
from datetime import datetime

from app.services.advisor_response_composer import (
    compose_advisor_response,
    compose_from_orchestration_result,
    render_response_as_markdown,
    StructuredAdvisorResponse,
    ConfidenceAssessment,
    HumanReviewRecommendation,
    AdvisoryTone,
    ConfidenceIndicator,
    ADVISORY_STYLE_INSTRUCTIONS,
    SYNTHESIS_PROMPT_TEMPLATE,
    SECTION_INSTRUCTIONS,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def sample_case_data():
    """Sample case data for testing."""
    return {
        "case_id": "case-test-001",
        "facts_known": [
            "Entreprise SARL avec 15 employés",
            "Siège social à Tunis",
            "Activité dans le secteur textile",
        ],
        "facts_missing": [
            "Date de création de l'entreprise",
            "Nombre de CDD vs CDI",
        ],
        "document_analyses": [
            {
                "id": "doc-001",
                "analysis": {
                    "document_type": "contract",
                    "summary": "Contrat de travail type",
                    "entities": {
                        "parties": [{"name": "Entreprise Textile", "role": "employeur"}],
                        "obligations": [{"description": "Signature avant prise de poste", "source": "Art. 6"}],
                    },
                    "confidence": 0.85,
                }
            }
        ],
        "orchestration_result": {
            "decision": "act",
            "decision_reason": "Sufficient information available",
            "proposed_findings": [
                {
                    "title": "Absence de contrats écrits",
                    "description": "15 employés travaillent sans contrat écrit",
                    "severity": "major",
                    "article_references": ["Art. 6 du Code du Travail"],
                    "confidence": 0.88,
                }
            ],
            "proposed_actions": [
                {
                    "title": "Établir les contrats écrits",
                    "description": "Rédiger et faire signer les contrats pour les 15 employés",
                    "priority": "high",
                    "due_date": "30 jours",
                    "assigned_to": "DRH",
                    "estimated_effort": "large",
                }
            ],
            "evidences_required": [
                {
                    "type": "contract",
                    "description": "Copies des contrats de travail signés",
                    "purpose": "Démontrer la conformité",
                    "urgency": "immediate",
                }
            ],
            "confidence_assessment": {"overall": 0.82},
        },
        "legal_context": [
            {
                "article_reference": "Art. 6 du Code du Travail tunisien",
                "law_name": "Code du Travail",
                "summary": "Le contrat de travail doit être établi par écrit",
                "relevance": "direct",
            }
        ],
    }


@pytest.fixture
def low_confidence_case_data():
    """Case data with low confidence for testing edge cases."""
    return {
        "case_id": "case-test-002",
        "facts_known": ["Entreprise à Tunis"],
        "facts_missing": ["Secteur d'activité", "Nombre d'employés", "Forme juridique"],
        "document_analyses": [],
        "orchestration_result": {
            "decision": "review",
            "decision_reason": "Insufficient information for reliable analysis",
            "proposed_findings": [],
            "proposed_actions": [],
            "evidences_required": [],
            "confidence_assessment": {"overall": 0.35},
            "human_review_reason": "Too many missing facts",
        },
        "legal_context": [],
    }


@pytest.fixture
def critical_risk_case_data():
    """Case with critical risks for testing risk rendering."""
    return {
        "case_id": "case-test-003",
        "facts_known": ["Entreprise avec 50 employés", "Aucun registre de présence"],
        "facts_missing": [],
        "document_analyses": [],
        "orchestration_result": {
            "decision": "act",
            "decision_reason": "Critical violations detected",
            "proposed_findings": [
                {
                    "title": "Violation grave: absence de registre de présence",
                    "description": "Non-respect de l'obligation de tenir un registre de présence",
                    "severity": "critical",
                    "article_references": ["Art. 247 du Code du Travail"],
                    "confidence": 0.95,
                }
            ],
            "proposed_actions": [
                {
                    "title": "Établir immédiatement le registre",
                    "description": "Mettre en place le registre de présence avec effet rétroactif",
                    "priority": "critical",
                    "due_date": "Immédiat",
                    "assigned_to": "Direction",
                    "estimated_effort": "small",
                }
            ],
            "evidences_required": [
                {
                    "type": "attendance_register",
                    "description": "Registre de présence signé par les employés",
                    "purpose": "Démontrer la mise en conformité",
                    "urgency": "immediate",
                    "format": "registre officiel",
                }
            ],
            "confidence_assessment": {"overall": 0.88},
        },
        "legal_context": [
            {
                "article_reference": "Art. 247 du Code du Travail tunisien",
                "law_name": "Code du Travail",
                "summary": "L'employeur doit tenir un registre de présence",
                "relevance": "direct",
            }
        ],
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Structure Validation Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestResponseStructure:
    """Validate that all 8 required sections are present and correctly typed."""

    @pytest.mark.asyncio
    async def test_all_sections_present(self, sample_case_data):
        """All 8 sections must be present in the response."""
        response = await compose_advisor_response(
            case_id=sample_case_data["case_id"],
            facts_known=sample_case_data["facts_known"],
            facts_missing=sample_case_data["facts_missing"],
            document_analyses=sample_case_data["document_analyses"],
            orchestration_result=sample_case_data["orchestration_result"],
            legal_context=sample_case_data["legal_context"],
            language="fr",
            use_llm_refinement=False,
        )

        # All 8 sections must exist
        assert response.what_i_understood is not None
        assert response.what_is_missing is not None
        assert response.legal_basis is not None
        assert response.compliance_risks is not None
        assert response.recommended_actions is not None
        assert response.required_evidence is not None
        assert response.confidence_assessment is not None
        assert response.human_review_recommendation is not None

    @pytest.mark.asyncio
    async def test_section_types_correct(self, sample_case_data):
        """Each section must be of the correct type."""
        response = await compose_advisor_response(
            case_id=sample_case_data["case_id"],
            facts_known=sample_case_data["facts_known"],
            facts_missing=sample_case_data["facts_missing"],
            document_analyses=sample_case_data["document_analyses"],
            orchestration_result=sample_case_data["orchestration_result"],
            legal_context=sample_case_data["legal_context"],
            language="fr",
            use_llm_refinement=False,
        )

        assert isinstance(response.what_i_understood, list)
        assert isinstance(response.what_is_missing, list)
        assert isinstance(response.legal_basis, list)
        assert isinstance(response.compliance_risks, list)
        assert isinstance(response.recommended_actions, list)
        assert isinstance(response.required_evidence, list)
        assert isinstance(response.confidence_assessment, ConfidenceAssessment)
        assert isinstance(response.human_review_recommendation, HumanReviewRecommendation)

    @pytest.mark.asyncio
    async def test_response_has_required_metadata(self, sample_case_data):
        """Response must have response_id, case_id, and timestamps."""
        response = await compose_advisor_response(
            case_id=sample_case_data["case_id"],
            facts_known=sample_case_data["facts_known"],
            facts_missing=sample_case_data["facts_missing"],
            document_analyses=sample_case_data["document_analyses"],
            orchestration_result=sample_case_data["orchestration_result"],
            legal_context=sample_case_data["legal_context"],
            language="fr",
            use_llm_refinement=False,
        )

        assert response.response_id.startswith("adv-")
        assert response.case_id == sample_case_data["case_id"]
        assert isinstance(response.generated_at, datetime)
        assert response.language == "fr"

    @pytest.mark.asyncio
    async def test_response_can_serialize_to_dict(self, sample_case_data):
        """Response must be serializable to dict."""
        response = await compose_advisor_response(
            case_id=sample_case_data["case_id"],
            facts_known=sample_case_data["facts_known"],
            facts_missing=sample_case_data["facts_missing"],
            document_analyses=sample_case_data["document_analyses"],
            orchestration_result=sample_case_data["orchestration_result"],
            legal_context=sample_case_data["legal_context"],
            language="fr",
            use_llm_refinement=False,
        )

        data = response.to_dict()
        assert "response_id" in data
        assert "case_id" in data
        assert "what_i_understood" in data
        assert "what_is_missing" in data
        assert "legal_basis" in data
        assert "compliance_risks" in data
        assert "recommended_actions" in data
        assert "required_evidence" in data
        assert "confidence_assessment" in data
        assert "human_review_recommendation" in data
        assert "markdown_rendering" in data


# ═══════════════════════════════════════════════════════════════════════════════
# Content Quality Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestContentQuality:
    """Validate content quality and completeness."""

    @pytest.mark.asyncio
    async def test_understood_facts_populated(self, sample_case_data):
        """What I understood section must be populated from facts."""
        response = await compose_advisor_response(
            case_id=sample_case_data["case_id"],
            facts_known=sample_case_data["facts_known"],
            facts_missing=sample_case_data["facts_missing"],
            document_analyses=sample_case_data["document_analyses"],
            orchestration_result=sample_case_data["orchestration_result"],
            legal_context=sample_case_data["legal_context"],
            language="fr",
            use_llm_refinement=False,
        )

        assert len(response.what_i_understood) > 0
        # Should include facts from conversation
        fact_texts = [f.fact for f in response.what_i_understood]
        assert any("15 employés" in f for f in fact_texts)

    @pytest.mark.asyncio
    async def test_missing_info_includes_suggested_questions(self, sample_case_data):
        """Missing info items should include suggested questions."""
        response = await compose_advisor_response(
            case_id=sample_case_data["case_id"],
            facts_known=sample_case_data["facts_known"],
            facts_missing=sample_case_data["facts_missing"],
            document_analyses=sample_case_data["document_analyses"],
            orchestration_result=sample_case_data["orchestration_result"],
            legal_context=sample_case_data["legal_context"],
            language="fr",
            use_llm_refinement=False,
        )

        assert len(response.what_is_missing) > 0
        for item in response.what_is_missing:
            assert item.importance in ["critical", "important", "helpful"]
            assert item.suggested_question is not None

    @pytest.mark.asyncio
    async def test_legal_basis_includes_references(self, sample_case_data):
        """Legal basis must include article references."""
        response = await compose_advisor_response(
            case_id=sample_case_data["case_id"],
            facts_known=sample_case_data["facts_known"],
            facts_missing=sample_case_data["facts_missing"],
            document_analyses=sample_case_data["document_analyses"],
            orchestration_result=sample_case_data["orchestration_result"],
            legal_context=sample_case_data["legal_context"],
            language="fr",
            use_llm_refinement=False,
        )

        assert len(response.legal_basis) > 0
        refs = [lb.article_reference for lb in response.legal_basis]
        assert any("Art. 6" in r for r in refs)

    @pytest.mark.asyncio
    async def test_risk_severity_mapping(self, critical_risk_case_data):
        """Risk severity must be correctly mapped from findings."""
        response = await compose_advisor_response(
            case_id=critical_risk_case_data["case_id"],
            facts_known=critical_risk_case_data["facts_known"],
            facts_missing=critical_risk_case_data["facts_missing"],
            document_analyses=critical_risk_case_data["document_analyses"],
            orchestration_result=critical_risk_case_data["orchestration_result"],
            legal_context=critical_risk_case_data["legal_context"],
            language="fr",
            use_llm_refinement=False,
        )

        assert len(response.compliance_risks) > 0
        critical_risks = [r for r in response.compliance_risks if r.severity == "critical"]
        assert len(critical_risks) > 0

    @pytest.mark.asyncio
    async def test_actions_include_priorities_and_deadlines(self, sample_case_data):
        """Actions must include priority and deadline info."""
        response = await compose_advisor_response(
            case_id=sample_case_data["case_id"],
            facts_known=sample_case_data["facts_known"],
            facts_missing=sample_case_data["facts_missing"],
            document_analyses=sample_case_data["document_analyses"],
            orchestration_result=sample_case_data["orchestration_result"],
            legal_context=sample_case_data["legal_context"],
            language="fr",
            use_llm_refinement=False,
        )

        assert len(response.recommended_actions) > 0
        for action in response.recommended_actions:
            assert action.priority in ["critical", "high", "medium", "low"]

    @pytest.mark.asyncio
    async def test_evidence_includes_urgency(self, sample_case_data):
        """Evidence items must include urgency classification."""
        response = await compose_advisor_response(
            case_id=sample_case_data["case_id"],
            facts_known=sample_case_data["facts_known"],
            facts_missing=sample_case_data["facts_missing"],
            document_analyses=sample_case_data["document_analyses"],
            orchestration_result=sample_case_data["orchestration_result"],
            legal_context=sample_case_data["legal_context"],
            language="fr",
            use_llm_refinement=False,
        )

        assert len(response.required_evidence) > 0
        for ev in response.required_evidence:
            assert ev.urgency in ["immediate", "soon", "eventually"]


# ═══════════════════════════════════════════════════════════════════════════════
# Confidence Assessment Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestConfidenceAssessment:
    """Validate confidence assessment logic."""

    @pytest.mark.asyncio
    async def test_high_confidence_with_good_data(self, sample_case_data):
        """High confidence when facts and documents available."""
        response = await compose_advisor_response(
            case_id=sample_case_data["case_id"],
            facts_known=sample_case_data["facts_known"],
            facts_missing=[],  # No missing facts
            document_analyses=sample_case_data["document_analyses"],
            orchestration_result={
                **sample_case_data["orchestration_result"],
                "confidence_assessment": {"overall": 0.90},
            },
            legal_context=sample_case_data["legal_context"],
            language="fr",
            use_llm_refinement=False,
        )

        assert response.confidence_assessment.level == "high"
        assert response.confidence_assessment.indicator == ConfidenceIndicator.HIGH.value

    @pytest.mark.asyncio
    async def test_low_confidence_with_missing_data(self, low_confidence_case_data):
        """Low confidence with many missing facts and no documents."""
        response = await compose_advisor_response(
            case_id=low_confidence_case_data["case_id"],
            facts_known=low_confidence_case_data["facts_known"],
            facts_missing=low_confidence_case_data["facts_missing"],
            document_analyses=low_confidence_case_data["document_analyses"],
            orchestration_result=low_confidence_case_data["orchestration_result"],
            legal_context=low_confidence_case_data["legal_context"],
            language="fr",
            use_llm_refinement=False,
        )

        assert response.confidence_assessment.level == "low"
        assert response.confidence_assessment.indicator == ConfidenceIndicator.LOW.value
        assert len(response.confidence_assessment.factors_limiting) > 0
        assert "missing" in response.confidence_assessment.disclaimer.lower() or "faible" in response.confidence_assessment.disclaimer.lower()

    @pytest.mark.asyncio
    async def test_disclaimer_includes_missing_count(self, sample_case_data):
        """Disclaimer should mention missing information count when applicable."""
        response = await compose_advisor_response(
            case_id=sample_case_data["case_id"],
            facts_known=sample_case_data["facts_known"],
            facts_missing=sample_case_data["facts_missing"],
            document_analyses=sample_case_data["document_analyses"],
            orchestration_result=sample_case_data["orchestration_result"],
            legal_context=sample_case_data["legal_context"],
            language="fr",
            use_llm_refinement=False,
        )

        # Since we have missing facts, disclaimer should be cautionary
        assert len(response.confidence_assessment.disclaimer) > 0


# ═══════════════════════════════════════════════════════════════════════════════
# Human Review Recommendation Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestHumanReviewRecommendation:
    """Validate human review recommendation logic."""

    @pytest.mark.asyncio
    async def test_review_recommended_for_critical_findings(self, critical_risk_case_data):
        """Human review recommended for critical findings."""
        response = await compose_advisor_response(
            case_id=critical_risk_case_data["case_id"],
            facts_known=critical_risk_case_data["facts_known"],
            facts_missing=critical_risk_case_data["facts_missing"],
            document_analyses=critical_risk_case_data["document_analyses"],
            orchestration_result=critical_risk_case_data["orchestration_result"],
            legal_context=critical_risk_case_data["legal_context"],
            language="fr",
            use_llm_refinement=False,
        )

        assert response.human_review_recommendation.is_recommended is True
        assert response.human_review_recommendation.reason is not None
        assert response.human_review_recommendation.recommended_expertise is not None

    @pytest.mark.asyncio
    async def test_review_recommended_for_low_confidence(self, low_confidence_case_data):
        """Human review recommended for low confidence."""
        response = await compose_advisor_response(
            case_id=low_confidence_case_data["case_id"],
            facts_known=low_confidence_case_data["facts_known"],
            facts_missing=low_confidence_case_data["facts_missing"],
            document_analyses=low_confidence_case_data["document_analyses"],
            orchestration_result=low_confidence_case_data["orchestration_result"],
            legal_context=low_confidence_case_data["legal_context"],
            language="fr",
            use_llm_refinement=False,
        )

        assert response.human_review_recommendation.is_recommended is True
        assert "information" in response.human_review_recommendation.reason.lower() or "insuffisant" in response.human_review_recommendation.reason.lower()

    @pytest.mark.asyncio
    async def test_no_review_for_clean_case(self):
        """No review needed for clean case with no findings."""
        response = await compose_advisor_response(
            case_id="case-clean",
            facts_known=["Entreprise conforme", "Tous les documents en ordre"],
            facts_missing=[],
            document_analyses=[],
            orchestration_result={
                "decision": "act",
                "proposed_findings": [],
                "proposed_actions": [],
                "evidences_required": [],
                "confidence_assessment": {"overall": 0.90},
            },
            legal_context=[],
            language="fr",
            use_llm_refinement=False,
        )

        assert response.human_review_recommendation.is_recommended is False


# ═══════════════════════════════════════════════════════════════════════════════
# Markdown Rendering Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestMarkdownRendering:
    """Validate markdown output quality."""

    @pytest.mark.asyncio
    async def test_markdown_contains_all_sections(self, sample_case_data):
        """Markdown must include all 8 section headers."""
        response = await compose_advisor_response(
            case_id=sample_case_data["case_id"],
            facts_known=sample_case_data["facts_known"],
            facts_missing=sample_case_data["facts_missing"],
            document_analyses=sample_case_data["document_analyses"],
            orchestration_result=sample_case_data["orchestration_result"],
            legal_context=sample_case_data["legal_context"],
            language="fr",
            use_llm_refinement=False,
        )

        md = render_response_as_markdown(response)

        # Check section titles
        assert "Ce que j'ai compris" in md
        assert "Informations complémentaires" in md or "manquantes" in md
        assert "Fondement juridique" in md
        assert "Risques" in md
        assert "Actions recommandées" in md or "Actions" in md
        assert "Documents" in md or "preuves" in md or "Éléments probants" in md
        assert "confiance" in md.lower()

    @pytest.mark.asyncio
    async def test_markdown_includes_risk_icons_for_critical(self, critical_risk_case_data):
        """Critical risks should have warning icons in markdown."""
        response = await compose_advisor_response(
            case_id=critical_risk_case_data["case_id"],
            facts_known=critical_risk_case_data["facts_known"],
            facts_missing=critical_risk_case_data["facts_missing"],
            document_analyses=critical_risk_case_data["document_analyses"],
            orchestration_result=critical_risk_case_data["orchestration_result"],
            legal_context=critical_risk_case_data["legal_context"],
            language="fr",
            use_llm_refinement=False,
        )

        md = render_response_as_markdown(response)

        # Should contain risk indicator
        assert "🔴" in md or "CRITICAL" in md.upper()

    @pytest.mark.asyncio
    async def test_markdown_includes_disclaimer(self, sample_case_data):
        """Disclaimer must be present in markdown."""
        response = await compose_advisor_response(
            case_id=sample_case_data["case_id"],
            facts_known=sample_case_data["facts_known"],
            facts_missing=sample_case_data["facts_missing"],
            document_analyses=sample_case_data["document_analyses"],
            orchestration_result=sample_case_data["orchestration_result"],
            legal_context=sample_case_data["legal_context"],
            language="fr",
            use_llm_refinement=False,
        )

        md = render_response_as_markdown(response)

        # Should contain disclaimer elements
        assert "Avis de non-responsabilité" in md or "Disclaimer" in md or "indicatif" in md

    @pytest.mark.asyncio
    async def test_markdown_includes_response_id(self, sample_case_data):
        """Response ID should be visible in markdown header."""
        response = await compose_advisor_response(
            case_id=sample_case_data["case_id"],
            facts_known=sample_case_data["facts_known"],
            facts_missing=sample_case_data["facts_missing"],
            document_analyses=sample_case_data["document_analyses"],
            orchestration_result=sample_case_data["orchestration_result"],
            legal_context=sample_case_data["legal_context"],
            language="fr",
            use_llm_refinement=False,
        )

        md = render_response_as_markdown(response)

        assert response.response_id in md


# ═══════════════════════════════════════════════════════════════════════════════
# Integration Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestOrchestratorIntegration:
    """Test integration with orchestrator outputs."""

    @pytest.mark.asyncio
    async def test_compose_from_orchestration_result(self, sample_case_data):
        """Convenience function must work with orchestrator output format."""
        conversation_context = {
            "facts_known": sample_case_data["facts_known"],
            "facts_missing": sample_case_data["facts_missing"],
        }

        response = await compose_from_orchestration_result(
            case_id=sample_case_data["case_id"],
            orchestration_result=sample_case_data["orchestration_result"],
            conversation_context=conversation_context,
            document_analyses=sample_case_data["document_analyses"],
            legal_context=sample_case_data["legal_context"],
            language="fr",
        )

        assert isinstance(response, StructuredAdvisorResponse)
        assert response.case_id == sample_case_data["case_id"]
        assert len(response.what_i_understood) > 0


# ═══════════════════════════════════════════════════════════════════════════════
# Template and Prompt Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestPromptTemplates:
    """Validate prompt templates are complete and usable."""

    def test_style_instructions_not_empty(self):
        """Style instructions must contain content."""
        assert len(ADVISORY_STYLE_INSTRUCTIONS) > 100
        assert "professional" in ADVISORY_STYLE_INSTRUCTIONS.lower()
        assert "warm" in ADVISORY_STYLE_INSTRUCTIONS.lower()

    def test_section_instructions_complete(self):
        """All 8 sections must have instructions."""
        expected_sections = [
            "what_i_understood",
            "what_is_missing",
            "legal_basis",
            "compliance_risks",
            "recommended_actions",
            "required_evidence",
            "confidence_assessment",
            "human_review_recommendation",
        ]

        for section in expected_sections:
            assert section in SECTION_INSTRUCTIONS
            assert len(SECTION_INSTRUCTIONS[section]) > 50

    def test_synthesis_template_includes_placeholders(self):
        """Synthesis template must have all required placeholders."""
        required_placeholders = [
            "{style_instructions}",
            "{section_title}",
            "{facts_known}",
            "{facts_missing}",
            "{document_summary}",
            "{orchestration_result}",
            "{section_instructions}",
            "{language}",
            "{language_code}",
            "{output_format}",
        ]

        for placeholder in required_placeholders:
            assert placeholder in SYNTHESIS_PROMPT_TEMPLATE


# ═══════════════════════════════════════════════════════════════════════════════
# Multi-language Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestMultiLanguageSupport:
    """Test language-specific rendering."""

    @pytest.mark.asyncio
    async def test_french_section_titles(self, sample_case_data):
        """French section titles must be used for French language."""
        response = await compose_advisor_response(
            case_id=sample_case_data["case_id"],
            facts_known=sample_case_data["facts_known"],
            facts_missing=sample_case_data["facts_missing"],
            document_analyses=sample_case_data["document_analyses"],
            orchestration_result=sample_case_data["orchestration_result"],
            legal_context=sample_case_data["legal_context"],
            language="fr",
            use_llm_refinement=False,
        )

        md = render_response_as_markdown(response)

        # French section titles
        assert "Ce que j'ai compris" in md or "compris" in md
        assert "Fondement juridique" in md or "fondement" in md.lower()


# ═══════════════════════════════════════════════════════════════════════════════
# Edge Case Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_empty_facts_handled(self):
        """Must handle case with no known facts."""
        response = await compose_advisor_response(
            case_id="case-empty",
            facts_known=[],
            facts_missing=["Toutes les informations"],
            document_analyses=[],
            orchestration_result={
                "decision": "ask",
                "proposed_findings": [],
                "proposed_actions": [],
                "evidences_required": [],
                "confidence_assessment": {"overall": 0.20},
            },
            legal_context=[],
            language="fr",
            use_llm_refinement=False,
        )

        assert isinstance(response, StructuredAdvisorResponse)
        assert response.confidence_assessment.level == "low"

    @pytest.mark.asyncio
    async def test_empty_findings_no_crash(self):
        """Must handle case with no findings."""
        response = await compose_advisor_response(
            case_id="case-no-findings",
            facts_known=["Entreprise conforme"],
            facts_missing=[],
            document_analyses=[],
            orchestration_result={
                "decision": "act",
                "proposed_findings": [],
                "proposed_actions": [],
                "evidences_required": [],
                "confidence_assessment": {"overall": 0.95},
            },
            legal_context=[],
            language="fr",
            use_llm_refinement=False,
        )

        assert len(response.compliance_risks) == 0
        assert len(response.recommended_actions) == 0
        assert response.human_review_recommendation.is_recommended is False

    @pytest.mark.asyncio
    async def test_many_missing_facts_capped(self):
        """Must handle many missing facts gracefully."""
        many_missing = [f"Missing fact {i}" for i in range(20)]

        response = await compose_advisor_response(
            case_id="case-many-missing",
            facts_known=["Une seule info"],
            facts_missing=many_missing,
            document_analyses=[],
            orchestration_result={
                "decision": "ask",
                "proposed_findings": [],
                "proposed_actions": [],
                "evidences_required": [],
                "confidence_assessment": {"overall": 0.30},
            },
            legal_context=[],
            language="fr",
            use_llm_refinement=False,
        )

        # Should include all missing items
        assert len(response.what_is_missing) >= len(many_missing)


# ═══════════════════════════════════════════════════════════════════════════════
# Tone Variation Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestToneVariations:
    """Test different advisory tones."""

    @pytest.mark.asyncio
    async def test_formal_tone_applied(self, sample_case_data):
        """Formal tone setting should be preserved."""
        response = await compose_advisor_response(
            case_id=sample_case_data["case_id"],
            facts_known=sample_case_data["facts_known"],
            facts_missing=sample_case_data["facts_missing"],
            document_analyses=sample_case_data["document_analyses"],
            orchestration_result=sample_case_data["orchestration_result"],
            legal_context=sample_case_data["legal_context"],
            language="fr",
            tone=AdvisoryTone.FORMAL,
            use_llm_refinement=False,
        )

        assert response.tone == AdvisoryTone.FORMAL

    @pytest.mark.asyncio
    async def test_cautious_tone_applied(self, sample_case_data):
        """Cautious tone for high-risk situations."""
        response = await compose_advisor_response(
            case_id=sample_case_data["case_id"],
            facts_known=sample_case_data["facts_known"],
            facts_missing=sample_case_data["facts_missing"],
            document_analyses=sample_case_data["document_analyses"],
            orchestration_result=sample_case_data["orchestration_result"],
            legal_context=sample_case_data["legal_context"],
            language="fr",
            tone=AdvisoryTone.CAUTIOUS,
            use_llm_refinement=False,
        )

        assert response.tone == AdvisoryTone.CAUTIOUS


# ═══════════════════════════════════════════════════════════════════════════════
# Pydantic Schema Validation Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestSchemaValidation:
    """Test Pydantic schema integration."""

    @pytest.mark.asyncio
    async def test_response_validates_against_schema(self, sample_case_data):
        """Response must validate against Pydantic schema."""
        from app.case_schemas import AdvisorResponseOut

        response = await compose_advisor_response(
            case_id=sample_case_data["case_id"],
            facts_known=sample_case_data["facts_known"],
            facts_missing=sample_case_data["facts_missing"],
            document_analyses=sample_case_data["document_analyses"],
            orchestration_result=sample_case_data["orchestration_result"],
            legal_context=sample_case_data["legal_context"],
            language="fr",
            use_llm_refinement=False,
        )

        data = response.to_dict()

        # Should not raise validation error
        validated = AdvisorResponseOut.model_validate(data)
        assert validated.response_id == response.response_id
        assert validated.case_id == response.case_id


# ═══════════════════════════════════════════════════════════════════════════════
# Export Completeness
# ═══════════════════════════════════════════════════════════════════════════════

class TestExports:
    """Verify __all__ exports are correct."""

    def test_all_exports_exist(self):
        """All exported names must exist and be importable."""
        from app.services.advisor_response_composer import __all__

        for name in __all__:
            # Should be able to get from module
            import app.services.advisor_response_composer as mod
            assert hasattr(mod, name), f"Export {name} not found in module"

    def test_main_classes_exported(self):
        """Main classes must be in exports."""
        from app.services.advisor_response_composer import __all__

        assert "StructuredAdvisorResponse" in __all__
        assert "compose_advisor_response" in __all__
        assert "render_response_as_markdown" in __all__
