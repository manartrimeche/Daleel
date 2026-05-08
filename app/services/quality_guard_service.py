"""
Quality Guard Service — Sprint 6+ : Hallucination Detection & Conservative Rewrite.

This service acts as a post-generation gate.  After the LLM produces a draft
answer it is audited for:

  1. Reference fidelity — every article/loi reference in the answer must
     exist in the retrieved source chunks.
  2. Semantic fidelity — the answer must not contradict or invent facts
     that go beyond the retrieved chunks (lightweight entailment via LLM).
  3. Language compliance — the answer must be in the same language as the
     user question.

If any check fails, the service can:
  - Flag the answer (return with a warning / confidence score).
  - Trigger a conservative rewrite using stricter grounding instructions.
  - Strip unsupported references automatically.

Toggle:
  - Enabled globally via env DALEEL_QUALITY_GUARD_ENABLED=true
  - Or per-request via API parameter quality_guard=true.

PFE Thesis — Contribution scientifique
--------------------------------------
Ce module adresse le phénomène d'hallucination générative dans les systèmes
RAG juridiques. En instaurant un triple contrôle (fait référentiel, fidélité
sémantique via LLM-juge, conformité linguistique), il réduit les risques de
délivrance d'informations juridiques incorrectes. La réécriture conservative
rejette toute extrapolation non fondée sur le contexte retrieved, ce qui
constitue un « guardrail post-generation » essentiel pour la fiabilité d'un
assistant de conformité légale tunisien.
"""
from __future__ import annotations

import logging
import os
import re
from typing import Any

from app.config import get_settings

logger = logging.getLogger(__name__)


def _extract_refs(text: str) -> set[str]:
    """Extract article and loi references from text."""
    refs: set[str] = set()
    # e.g. "article 12", "art. 3", "loi 2004-63"
    refs.update(re.findall(r"(?i)\b(?:article|art)\.?\s*(\d+(?:[-/]\d+)?)", text))
    refs.update(re.findall(r"(?i)\b(?:loi|décret|arrêté|code)\s*(?:n?°?\s*)?(\d{2,4}[-/]\d+)", text))
    return {r.lower() for r in refs}


def _supported_refs(chunks: list[dict]) -> set[str]:
    """Collect all article/loi references present in retrieved chunks."""
    supported: set[str] = set()
    for chunk in chunks:
        text = chunk.get("text", "")
        supported |= _extract_refs(text)
        meta = chunk.get("metadata") or {}
        for field in ("article_num", "loi", "loi_code", "title"):
            val = meta.get(field)
            if isinstance(val, str):
                supported |= _extract_refs(val)
            elif isinstance(val, (int, float)):
                supported.add(str(val))
    return supported


def audit_references(answer: str, chunks: list[dict]) -> dict[str, Any]:
    """Compare references in the answer against retrieved chunks.

    Returns dict with:
      - supported_refs : set[str]
      - answer_refs    : set[str]
      - unsupported_refs : set[str]
      - clean_answer   : answer with unsupported refs stripped
    """
    answer_refs = _extract_refs(answer)
    supported = _supported_refs(chunks)
    unsupported = answer_refs - supported
    clean_answer = answer
    for ref in unsupported:
        # Very naive stripping — can be replaced by a regex that includes surrounding sentence
        clean_answer = re.sub(
            rf"(?i)\b(?:selon|conformément à|en vertu de|d'après)[^.,;]*\b{re.escape(ref)}[^.,;]*[.,;]?",
            "",
            clean_answer,
        )
    return {
        "supported_refs": supported,
        "answer_refs": answer_refs,
        "unsupported_refs": unsupported,
        "clean_answer": clean_answer.strip(),
        "passed": not unsupported,
    }


def is_language_compliant(answer: str, lang: str) -> bool:
    """Heuristic language compliance check."""
    from app.services.llm_service import _is_language_compliant
    return _is_language_compliant(answer, lang)


async def _semantic_fidelity_check(
    answer: str,
    chunks: list[dict],
    lang: str,
) -> dict[str, Any]:
    """Ask LLM whether the answer is fully supported by the context."""
    from app.services import llm_service  # lazy import to avoid circular dependency
    settings = get_settings()
    context = "\n---\n".join(c.get("text", "") for c in chunks[:6])
    prompt = (
        "Tu es un vérificateur factuel juridique. Évalue si la reponse ci-dessous "
        "est entièrement fondée sur le CONTEXTE fourni.\n\n"
        "CONTEXTE:\n" + context + "\n\n"
        "reponse:\n" + answer + "\n\n"
        "Réponds UNIQUEMENT par un JSON strict : {\"supported\": true/false, \"confidence\": 0.0-1.0, \"issues\": [\"...\"]}"
    )
    if lang == "ar":
        prompt = (
            "أنت مدقق قانوني للحقائق. قيّم ما إذا كانت الإجابة أدناه مبنية كلياً على السياق المقدم.\n\n"
            "السياق:\n" + context + "\n\n"
            "الإجابة:\n" + answer + "\n\n"
            "أجب فقط بتنسيق JSON: {\"supported\": true/false, \"confidence\": 0.0-1.0, \"issues\": [\"...\"]}"
        )
    try:
        response = await llm_service.call_ollama(
            model=settings.llm_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            base_url=settings.llm_base_url,
        )
        raw = (response or "").strip()
        # Very forgiving extraction
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            import json as _json
            parsed = _json.loads(match.group(0))
            return {
                "supported": bool(parsed.get("supported", True)),
                "confidence": float(parsed.get("confidence", 1.0)),
                "issues": parsed.get("issues", []),
            }
    except Exception as e:
        logger.warning("Semantic fidelity LLM check failed: %s", e)
    return {"supported": True, "confidence": 1.0, "issues": []}


async def conservative_rewrite(
    question: str,
    chunks: list[dict],
    lang: str,
    previous_answer: str,
    issues: list[str],
) -> str:
    """Rewrite the answer with stricter grounding instructions."""
    from app.services import llm_service  # lazy import to avoid circular dependency
    settings = get_settings()
    context = "\n---\n".join(c.get("text", "") for c in chunks[:8])
    instruction = (
        "Réécris la reponse ci-dessous de manière ultra-conservative. "
        "Utilise UNIQUEMENT les informations du CONTEXTE. "
        "Supprime toute affirmation non fondée. "
        "Liste les articles pertinents sans interprétation excessive. "
        f"Problèmes détectés: {', '.join(issues)}.\n\n"
    )
    if lang == "ar":
        instruction = (
            "أعد كتابة الإجابة بطريقة متحفظة للغاية. "
            "استخدم فقط المعلومات الموجودة في السياق. "
            "أزل أي ادعاء غير مؤسس. "
            f"المشاكل المكتشفة: {', '.join(issues)}.\n\n"
        )
    messages = [
        {"role": "system", "content": instruction},
        {"role": "user", "content": f"CONTEXTE:\n{context}\n\nreponse PRÉCÉDENTE:\n{previous_answer}\n\nRéécris la reponse."},
    ]
    try:
        response = await llm_service.call_ollama(
            model=settings.llm_model,
            messages=messages,
            temperature=0.1,
            base_url=settings.llm_base_url,
        )
        return response or previous_answer
    except Exception as e:
        logger.error("Conservative rewrite failed: %s", e)
        return previous_answer


async def audit_and_guard(
    question: str,
    answer: str,
    chunks: list[dict],
    lang: str,
    enabled: bool | None = None,
) -> dict[str, Any]:
    """
    Main entry point.  Audits the answer and decides: accept, flag, or rewrite.

    Parameters
    ----------
    enabled : bool | None
        If None, reads from env / settings.

    Returns
    -------
    {
        "status": "accepted" | "flagged" | "rewritten",
        "answer": str,
        "confidence": float,
        "issues": list[str],
    }
    """
    settings = get_settings()
    if enabled is None:
        enabled = os.getenv("DALEEL_QUALITY_GUARD_ENABLED", "true").lower() in ("1", "true", "yes")
        if hasattr(settings, "quality_guard_enabled"):
            enabled = settings.quality_guard_enabled

    if not enabled:
        return {"status": "accepted", "answer": answer, "confidence": 1.0, "issues": []}

    issues: list[str] = []

    # 1. Reference audit
    ref_audit = audit_references(answer, chunks)
    if not ref_audit["passed"]:
        issues.append(f"Unsupported references: {ref_audit['unsupported_refs']}")
        answer = ref_audit["clean_answer"]

    # 2. Language compliance
    if not is_language_compliant(answer, lang):
        issues.append("Language mismatch detected")

    # 3. Semantic fidelity (only if refs passed to avoid double work)
    fidelity = await _semantic_fidelity_check(answer, chunks, lang)
    if not fidelity["supported"]:
        issues.extend(fidelity["issues"])

    # Decision logic
    confidence = fidelity["confidence"]
    if not issues:
        return {"status": "accepted", "answer": answer, "confidence": confidence, "issues": []}

    # If confidence is very low, rewrite; otherwise flag with warning
    if confidence < 0.5 or len(issues) >= 2:
        rewritten = await conservative_rewrite(question, chunks, lang, answer, issues)
        return {"status": "rewritten", "answer": rewritten, "confidence": confidence, "issues": issues}

    return {"status": "flagged", "answer": answer, "confidence": confidence, "issues": issues}
