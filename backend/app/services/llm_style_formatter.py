"""
LLM Style Formatter — Track 1 service.

Appelle le modèle de style fine-tuné (Daleel-Style v1) qui transforme un
brouillon RAG + des findings en reponse advisor structurée (7 sections fixes).

Fail-safe : si le modèle n'est pas disponible (env var absente, Ollama down,
échec de réseau), on **retombe sur le markdown déjà produit par
`advisor_response_composer.render_response_as_markdown`**. La pipeline reste
fonctionnelle, le fine-tuning est purement additif.

Intégration appelée depuis :
    app/services/advisor_response_composer.py
        async def compose_from_orchestration_result(...):
            structured = await _build_structured_response(...)
            md = render_response_as_markdown(structured)
            md = await llm_style_formatter.format_advisor_answer(
                draft_markdown=md,
                payload={
                    "language": language,
                    "user_question": question,
                    "extracted_facts": extracted_facts,
                    "legal_context": legal_context,
                    "findings": findings_dicts,
                    "actions": actions_dicts,
                },
            )
            return structured, md   # ou stocker md dans structured.formatted_text
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def _style_model_name() -> str:
    return os.getenv("DALEEL_STYLE_MODEL", "").strip()
_OLLAMA_URL: str = getattr(settings, "ollama_url", "http://localhost:11434")
_TIMEOUT_SECONDS: float = float(getattr(settings, "style_model_timeout", 30.0))


_SYSTEM_PROMPT_FR = (
    "Tu es Daleel, conseiller juridique tunisien. À partir des faits, du "
    "contexte légal et du brouillon, produis une reponse structurée en 7 "
    "sections fixes : "
    "1) Ce que j'ai compris, "
    "2) Informations manquantes, "
    "3) Contexte légal / articles pertinents, "
    "4) Analyse / risques de non-conformité, "
    "5) Actions recommandées, "
    "6) Preuves / documents à rassembler, "
    "7) Nécessité d'une revue humaine. "
    "Règles strictes : (a) N'INVENTE AUCUN article ; (b) ne cite que les "
    "articles présents dans `legal_context` ; (c) si une info manque, dis-le "
    "explicitement plutôt que de l'inventer."
)

_SYSTEM_PROMPT_AR = (
    "أنت دليل، مستشار قانوني تونسي. اعتمادًا على الوقائع، السياق القانوني "
    "والمسودة، أنتج إجابة منظمة في 7 أقسام ثابتة: "
    "1) ما فهمته، 2) المعلومات الناقصة، 3) السياق القانوني / الفصول ذات الصلة، "
    "4) التحليل / مخاطر عدم الامتثال، 5) الإجراءات الموصى بها، "
    "6) الأدلة / الوثائق اللازم جمعها، 7) ضرورة المراجعة البشرية. "
    "قواعد صارمة: (أ) لا تخترع أي فصل؛ (ب) لا تستشهد إلا بالفصول الموجودة في "
    "legal_context؛ (ج) إذا كانت معلومة ناقصة، صرّح بذلك صراحةً."
)

_SYSTEM_PROMPT_EN = (
    "You are Daleel, a Tunisian legal advisor. Given the facts, the legal "
    "context and the draft, produce a structured response with 7 fixed "
    "sections: "
    "1) What I understood, 2) Missing information, 3) Legal context / "
    "relevant articles, 4) Analysis / non-compliance risks, "
    "5) Recommended actions, 6) Evidence / documents to gather, "
    "7) Need for human review. "
    "Strict rules: (a) NEVER invent any article; (b) only cite articles that "
    "appear in `legal_context`; (c) if information is missing, say so "
    "explicitly rather than fabricating."
)


def _system_prompt(language: str) -> str:
    return {"ar": _SYSTEM_PROMPT_AR, "en": _SYSTEM_PROMPT_EN}.get(language, _SYSTEM_PROMPT_FR)


def is_enabled() -> bool:
    """Vrai si une variable d'env DALEEL_STYLE_MODEL est définie."""
    path = os.getenv("DALEEL_STYLE_MODEL", "").strip()
    return bool(path) and os.path.exists(path)


async def format_advisor_answer(
    draft_markdown: str,
    payload: dict[str, Any],
    language: str = "fr",
) -> str:
    """Reformate un brouillon en reponse advisor 7-sections.

    Args:
        draft_markdown: la sortie déjà composée par `advisor_response_composer`
            (sera utilisée comme fallback si le modèle de style est absent).
        payload: contexte structuré attendu par le modèle fine-tuné, contenant :
            - user_question, extracted_facts, legal_context, findings,
              actions, draft_answer
        language: "fr" | "ar" | "en"

    Returns:
        markdown final, prêt à passer dans `quality_guard_service.audit_and_guard`.
    """
    if not is_enabled():
        # Fail-safe : pas de modèle déployé → on garde le markdown du composer.
        logger.debug("style_formatter disabled, returning draft_markdown unchanged")
        return draft_markdown

    payload = {**payload, "draft_answer": payload.get("draft_answer") or draft_markdown}
    user_message = json.dumps(payload, ensure_ascii=False, indent=2)

    model_name = _style_model_name()
    body = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": _system_prompt(language)},
            {"role": "user", "content": user_message},
        ],
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_ctx": 4096,
        },
    }

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT_SECONDS) as client:
            resp = await client.post(f"{_OLLAMA_URL}/api/chat", json=body)
            resp.raise_for_status()
            data = resp.json()
        formatted = (data.get("message") or {}).get("content") or ""
        if not formatted.strip():
            logger.warning("style model returned empty content, using draft fallback")
            return draft_markdown
        return formatted
    except Exception as exc:  # noqa: BLE001
        logger.warning("style model call failed (%s) — returning draft", exc)
        return draft_markdown


# ──────────────────────────────────────────────────────────────────────────
# Helper : construire `payload` depuis une OrchestrationResult + contexte
# ──────────────────────────────────────────────────────────────────────────

def build_payload_from_orchestration(
    *,
    user_question: str,
    language: str,
    extracted_facts: dict[str, Any] | None,
    legal_context: list[dict[str, Any]] | None,
    findings: list[Any] | None,
    actions: list[Any] | None,
    draft_answer: str = "",
) -> dict[str, Any]:
    """Construit le payload attendu par le modèle de style en sérialisant les
    objets dataclass de `compliance_case_orchestrator` / `advisor_response_composer`.
    """

    def _serialize(obj: Any) -> Any:
        if hasattr(obj, "to_dict") and callable(obj.to_dict):
            return obj.to_dict()
        if hasattr(obj, "__dict__"):
            return {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}
        return obj

    return {
        "language": language,
        "user_question": user_question or "",
        "extracted_facts": extracted_facts or {},
        "legal_context": legal_context or [],
        "findings": [_serialize(f) for f in (findings or [])],
        "actions": [_serialize(a) for a in (actions or [])],
        "draft_answer": draft_answer,
    }
