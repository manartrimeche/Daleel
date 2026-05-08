"""Tests for the CONTEXT_REWRITE_PROMPT template and _build_rewrite_messages helper.

Covers:
- Message chain structure (4 messages, correct roles)
- Draft section inclusion / exclusion
- All 3 languages (fr, ar, en)
- Key safety phrases present in the prompt
- Correct vs incorrect model behavior examples (as test docstrings)
"""
from __future__ import annotations

import pytest

from app.services.llm_service import (
    CONTEXT_REWRITE_PROMPT,
    GROUNDING_REMINDER,
    _DRAFT_SECTION_TEMPLATE,
    _build_rewrite_messages,
    _get_ack_message,
)

# ── Fixtures ──────────────────────────────────────────────────

SAMPLE_QUESTION_FR = (
    "Notre startup e-commerce à Tunis collecte des données personnelles. "
    "Quelles sont nos obligations envers l'INPDP ?"
)

SAMPLE_QUESTION_AR = (
    "شركتنا شركة ذات مسؤولية محدودة في تونس. "
    "5 عمال يعملون دون عقود عمل مكتوبة. هل نحن في وضع مخالف؟"
)

SAMPLE_CONTEXT = (
    "[Source 1] Article 7 de la Loi 2004-63 : Tout traitement de données "
    "personnelles doit faire l'objet d'une déclaration préalable auprès de "
    "l'INPDP.\n"
    "[Source 2] Article 27 : L'INPDP peut prononcer des sanctions."
)

SAMPLE_DRAFT_BAD = (
    "Selon l'Article 999 du Code de la propriété intellectuelle (CPI), "
    "les données personnelles sont protégées par la loi n°96-59. "
    "L'INPDP exige une déclaration préalable (Article 7 de la Loi 2004-63)."
)


# ── Message chain structure ──────────────────────────────────


class TestBuildRewriteMessages:
    """Verify the message chain produced by _build_rewrite_messages."""

    def test_returns_four_messages(self):
        msgs = _build_rewrite_messages("fr", "question?", "context chunk")
        assert len(msgs) == 4

    def test_message_roles(self):
        msgs = _build_rewrite_messages("fr", "question?", "context chunk")
        roles = [m["role"] for m in msgs]
        assert roles == ["system", "user", "assistant", "user"]

    def test_system_message_contains_system_prompt(self):
        msgs = _build_rewrite_messages("fr", "q", "ctx")
        system = msgs[0]["content"]
        assert "Daleel" in system
        assert GROUNDING_REMINDER["fr"] in system

    def test_context_in_second_message(self):
        msgs = _build_rewrite_messages("fr", "q", "MY_CONTEXT_CHUNKS")
        assert msgs[1]["content"] == "MY_CONTEXT_CHUNKS"

    def test_ack_in_third_message(self):
        msgs = _build_rewrite_messages("fr", "q", "ctx")
        assert msgs[2]["content"] == _get_ack_message("fr")

    def test_rewrite_prompt_contains_question(self):
        msgs = _build_rewrite_messages("fr", SAMPLE_QUESTION_FR, "ctx")
        rewrite = msgs[3]["content"]
        assert SAMPLE_QUESTION_FR in rewrite


# ── Draft section inclusion / exclusion ──────────────────────


class TestDraftSection:
    """When initial_draft is provided, the draft is embedded in the prompt.
    When omitted (prompt-leak recovery), the draft section is absent.
    """

    def test_draft_included_when_provided(self):
        msgs = _build_rewrite_messages(
            "fr", "q", "ctx", initial_draft=SAMPLE_DRAFT_BAD
        )
        rewrite = msgs[3]["content"]
        assert "<<<BROUILLON>>>" in rewrite
        assert SAMPLE_DRAFT_BAD in rewrite
        assert "<<<FIN BROUILLON>>>" in rewrite

    def test_draft_excluded_when_empty(self):
        msgs = _build_rewrite_messages("fr", "q", "ctx", initial_draft="")
        rewrite = msgs[3]["content"]
        assert "<<<BROUILLON>>>" not in rewrite
        assert "BROUILLON INITIAL" not in rewrite

    def test_draft_excluded_when_whitespace_only(self):
        msgs = _build_rewrite_messages("fr", "q", "ctx", initial_draft="   \n  ")
        rewrite = msgs[3]["content"]
        assert "<<<BROUILLON>>>" not in rewrite

    def test_draft_section_arabic(self):
        msgs = _build_rewrite_messages(
            "ar", "سؤال", "سياق", initial_draft="مسودة اختبارية"
        )
        rewrite = msgs[3]["content"]
        assert "<<<مسودة>>>" in rewrite
        assert "مسودة اختبارية" in rewrite

    def test_draft_section_english(self):
        msgs = _build_rewrite_messages(
            "en", "question", "context", initial_draft="test draft"
        )
        rewrite = msgs[3]["content"]
        assert "<<<DRAFT>>>" in rewrite
        assert "test draft" in rewrite


# ── Language coverage ─────────────────────────────────────────


class TestLanguageCoverage:
    """All three languages must have matching template keys."""

    @pytest.mark.parametrize("lang", ["fr", "ar", "en"])
    def test_context_rewrite_prompt_key_exists(self, lang):
        assert lang in CONTEXT_REWRITE_PROMPT

    @pytest.mark.parametrize("lang", ["fr", "ar", "en"])
    def test_draft_section_template_key_exists(self, lang):
        assert lang in _DRAFT_SECTION_TEMPLATE

    @pytest.mark.parametrize("lang", ["fr", "ar", "en"])
    def test_messages_build_for_all_languages(self, lang):
        msgs = _build_rewrite_messages(lang, "q", "ctx", initial_draft="d")
        assert len(msgs) == 4
        # Every rewrite prompt must mention [Source N]
        assert "[Source N]" in msgs[3]["content"]

    def test_unknown_lang_falls_back_to_english(self):
        msgs = _build_rewrite_messages("de", "q", "ctx")
        rewrite = msgs[3]["content"]
        assert "MANDATORY RULES" in rewrite


# ── Safety phrases present ────────────────────────────────────


class TestSafetyPhrases:
    """The rewrite prompt must contain critical guardrail instructions."""

    @pytest.mark.parametrize(
        "lang, phrase",
        [
            ("fr", "INTERDICTION ABSOLUE"),
            ("fr", "Ignorez totalement"),
            ("fr", "[Source N]"),
            ("fr", "Contexte insuffisant"),
            ("fr", "N'inventez JAMAIS"),
            ("ar", "يُمنع منعاً باتاً"),
            ("ar", "تجاهل تماماً"),
            ("ar", "[Source N]"),
            ("ar", "سياق غير كافٍ"),
            ("ar", "لا تخترع أبداً"),
            ("en", "ABSOLUTE PROHIBITION"),
            ("en", "Completely ignore"),
            ("en", "[Source N]"),
            ("en", "Insufficient context"),
            ("en", "NEVER invent"),
        ],
    )
    def test_safety_phrase_present(self, lang, phrase):
        prompt = CONTEXT_REWRITE_PROMPT[lang].format(
            question="q", draft_section=""
        )
        assert phrase in prompt, f"Missing safety phrase '{phrase}' in {lang} template"


# ── Correct vs Incorrect model behavior ──────────────────────


class TestCorrectVsIncorrectBehavior:
    """These tests document expected model behavior for the rewrite mode.

    They do NOT call the LLM — they verify that the prompt template
    structurally sets up the right constraints.  The docstrings serve
    as the behavioral specification.

    ──────────────────────────────────────────────────────────────
    CORRECT BEHAVIOR (what the model SHOULD do):
    ──────────────────────────────────────────────────────────────

    ✅ Example 1 — Stripping invented references:
       Draft says: "Selon l'Article 999 du CPI et la loi n°96-59..."
       Context only has: [Source 1] Article 7 Loi 2004-63 about INPDP.
       Expected: The model removes Article 999/CPI/loi 96-59 and keeps
       only Article 7 of Loi 2004-63, citing [Source 1].

    ✅ Example 2 — Admitting insufficient context:
       Question asks about GDPR applicability and EU data transfers.
       Context only has Tunisian Loi 2004-63 articles.
       Expected: The model answers the Tunisian part citing sources,
       then adds: "⚠️ Contexte insuffisant — Les sources disponibles
       ne contiennent pas d'information sur le RGPD européen.
       Documents nécessaires : Règlement (UE) 2016/679 (RGPD)."

    ✅ Example 3 — Preserving exact source wording:
       Context says: "L'INPDP peut prononcer des sanctions" [Source 2].
       Expected: The model quotes the exact phrase with [Source 2],
       not a paraphrase like "des pénalités peuvent être infligées".

    ──────────────────────────────────────────────────────────────
    INCORRECT BEHAVIOR (what the model must NOT do):
    ──────────────────────────────────────────────────────────────

    ❌ Example 1 — Hallucinating legal references:
       Context has only Loi 2004-63.
       Incorrect: "La Loi n°96-59 du 6 juillet 1996 relative aux
       échanges électroniques stipule que..."
       → This law was never in the context.

    ❌ Example 2 — Inventing rules to fill gaps:
       Question asks about sanctions for late INPDP declaration.
       Context has no sanctions article.
       Incorrect: "Le non-respect entraîne une amende de 50 000 DT."
       → Sanction amount fabricated; correct response is to flag the
       gap and suggest consulting the full text of Loi 2004-63.

    ❌ Example 3 — Citing the wrong code:
       Question is about labor contracts, context has Code du Travail.
       Incorrect: "Selon l'Article 10 du Code des Sociétés..."
       → Wrong legal code, not in context.

    ❌ Example 4 — Omitting source citations:
       Correct: "L'INPDP exige une déclaration préalable [Source 1]."
       Incorrect: "L'INPDP exige une déclaration préalable."
       → Missing [Source N] citation.
    """

    def test_prompt_separates_question_from_draft(self):
        """The model sees question and draft in clearly delimited sections."""
        msgs = _build_rewrite_messages(
            "fr", SAMPLE_QUESTION_FR, SAMPLE_CONTEXT, initial_draft=SAMPLE_DRAFT_BAD
        )
        rewrite = msgs[3]["content"]
        # Question section appears before draft section
        q_pos = rewrite.index("QUESTION D'ORIGINE")
        d_pos = rewrite.index("BROUILLON INITIAL")
        assert q_pos < d_pos

    def test_prompt_separates_draft_from_rules(self):
        """Rules section comes after the draft so the model processes them last."""
        msgs = _build_rewrite_messages(
            "fr", SAMPLE_QUESTION_FR, SAMPLE_CONTEXT, initial_draft=SAMPLE_DRAFT_BAD
        )
        rewrite = msgs[3]["content"]
        d_pos = rewrite.index("FIN BROUILLON")
        r_pos = rewrite.index("RÈGLES IMPÉRATIVES")
        assert d_pos < r_pos

    def test_insufficient_context_section_present(self):
        """The prompt must instruct the model on how to handle narrow context."""
        msgs = _build_rewrite_messages("fr", SAMPLE_QUESTION_FR, SAMPLE_CONTEXT)
        rewrite = msgs[3]["content"]
        assert "CONTEXTE EST INSUFFISANT" in rewrite
        assert "documents" in rewrite.lower()
        assert "N'inventez JAMAIS" in rewrite

    def test_no_prior_knowledge_instruction(self):
        """The prompt explicitly tells the model to ignore prior legal knowledge."""
        msgs = _build_rewrite_messages("fr", "q", "ctx")
        rewrite = msgs[3]["content"]
        assert "Ignorez totalement" in rewrite
        assert "connaissances juridiques préalables" in rewrite

    def test_source_citation_requirement(self):
        """The prompt requires [Source N] citations for every assertion."""
        msgs = _build_rewrite_messages("fr", "q", "ctx")
        rewrite = msgs[3]["content"]
        assert "[Source N]" in rewrite

    def test_forbids_new_references(self):
        """The prompt forbids introducing laws/articles not in the extracts."""
        msgs = _build_rewrite_messages("fr", "q", "ctx")
        rewrite = msgs[3]["content"]
        assert "mot pour mot" in rewrite

    def test_arabic_behavioral_parity(self):
        """Arabic template has the same behavioral constraints as French."""
        msgs = _build_rewrite_messages(
            "ar", SAMPLE_QUESTION_AR, "سياق", initial_draft="مسودة"
        )
        rewrite = msgs[3]["content"]
        # Must have: prohibition, ignore prior knowledge, source citation,
        # insufficient context handling, no invention
        assert "يُمنع منعاً باتاً" in rewrite
        assert "تجاهل تماماً" in rewrite
        assert "[Source N]" in rewrite
        assert "سياق غير كافٍ" in rewrite
        assert "لا تخترع أبداً" in rewrite
