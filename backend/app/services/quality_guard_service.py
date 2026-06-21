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


def _extract_quoted_claims(answer: str) -> list[dict]:
    """Extract quoted text from the answer (text between quotation marks)."""
    claims = []
    for m in re.finditer(r'[""«]([^""»]{15,})[""»]', answer):
        claims.append({"quote": m.group(1), "start": m.start(), "end": m.end()})
    return claims


def _verify_quotes_against_chunks(answer: str, chunks: list[dict]) -> dict[str, Any]:
    """Check that quoted text in the answer actually appears in chunks."""
    claims = _extract_quoted_claims(answer)
    if not claims:
        return {"fabricated_quotes": [], "passed": True, "clean_answer": answer}

    chunk_texts = " ".join(c.get("text", "") for c in chunks).lower()
    fabricated = []
    clean_answer = answer

    for claim in claims:
        quote_lower = claim["quote"].lower().strip()
        words = quote_lower.split()
        if len(words) < 4:
            continue
        # Check if a significant portion of the quote appears in chunk texts
        # Use sliding window of 5+ consecutive words
        found = False
        for window_size in range(min(len(words), 8), 3, -1):
            for i in range(len(words) - window_size + 1):
                fragment = " ".join(words[i:i + window_size])
                if fragment in chunk_texts:
                    found = True
                    break
            if found:
                break
        if not found:
            fabricated.append(claim["quote"])
            clean_answer = clean_answer.replace(f'"{claim["quote"]}"', "[citation non vérifiée]")
            clean_answer = clean_answer.replace(f'«{claim["quote"]}»', "[citation non vérifiée]")
            clean_answer = clean_answer.replace(f'“{claim["quote"]}”', "[citation non vérifiée]")

    return {
        "fabricated_quotes": fabricated,
        "passed": len(fabricated) == 0,
        "clean_answer": clean_answer,
    }


def _verify_article_content_match(answer: str, chunks: list[dict]) -> list[str]:
    """Verify that article descriptions in the answer match actual chunk content.

    Catches cases like: "Article 409 states that attendance records must be..."
    when Article 409 actually talks about something else entirely.
    """
    mismatched = []
    article_claims = re.finditer(
        r"(?i)(?:Article|Art\.?|الفصل)\s*(\d+)(?:\s*(?::|—|-|–|stipulates?|states?|provides?|prévoit|dispose|stipule|ينص))\s*[:\-–—]?\s*(.{20,120}?)(?:[.\n]|$)",
        answer,
    )
    chunk_texts_by_article: dict[str, str] = {}
    for chunk in chunks:
        text = chunk.get("text", "")
        for m in re.finditer(r"(?i)(?:Article|Art\.?|الفصل)\s*(\d+)", text):
            art_num = m.group(1)
            if art_num not in chunk_texts_by_article:
                chunk_texts_by_article[art_num] = ""
            chunk_texts_by_article[art_num] += " " + text

    for m in article_claims:
        art_num = m.group(1)
        claim_text = m.group(2).lower().strip()
        claim_words = set(re.findall(r"[a-zA-ZÀ-ÿ؀-ۿ]{4,}", claim_text))
        if not claim_words or len(claim_words) < 3:
            continue

        if art_num in chunk_texts_by_article:
            source_text = chunk_texts_by_article[art_num].lower()
            source_words = set(re.findall(r"[a-zA-ZÀ-ÿ؀-ۿ]{4,}", source_text))
            overlap = claim_words & source_words
            # If less than 30% of claim's key words appear in the source, it's likely fabricated
            if len(overlap) < len(claim_words) * 0.3:
                mismatched.append(f"Article {art_num}")

    return mismatched


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
        clean_answer = re.sub(
            rf"(?i)\b(?:selon|conformément à|en vertu de|d'après|according to|under|pursuant to|بموجب|وفقاً)[^.,;]*\b{re.escape(ref)}[^.,;]*[.,;]?",
            "",
            clean_answer,
        )

    # Check quoted text against actual chunk content
    quote_audit = _verify_quotes_against_chunks(clean_answer, chunks)
    if not quote_audit["passed"]:
        clean_answer = quote_audit["clean_answer"]
        unsupported = unsupported | {f"fabricated_quote:{q[:50]}" for q in quote_audit["fabricated_quotes"]}

    # Check article content descriptions match actual chunk text
    content_mismatches = _verify_article_content_match(clean_answer, chunks)
    if content_mismatches:
        unsupported = unsupported | {f"content_mismatch:{a}" for a in content_mismatches}

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
    # Fail open when the optional LLM checker is unavailable.
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

    # 3. Optional semantic fidelity check. It calls the LLM a second time, so
    # keep it opt-in for low-latency responses while retaining deterministic
    # reference and language checks by default.
    if getattr(settings, "quality_guard_semantic_check_enabled", False):
        fidelity = await _semantic_fidelity_check(answer, chunks, lang)
        if not fidelity["supported"]:
            issues.extend(fidelity["issues"])
    else:
        fidelity = {"supported": True, "confidence": 1.0, "issues": []}

    # Decision logic
    confidence = fidelity["confidence"]
    if not issues:
        return {"status": "accepted", "answer": answer, "confidence": confidence, "issues": []}

    # If confidence is very low, rewrite; otherwise flag with warning
    if confidence < 0.5 or len(issues) >= 2:
        rewritten = await conservative_rewrite(question, chunks, lang, answer, issues)
        return {"status": "rewritten", "answer": rewritten, "confidence": confidence, "issues": issues}

    return {"status": "flagged", "answer": answer, "confidence": confidence, "issues": issues}
