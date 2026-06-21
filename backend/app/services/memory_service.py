"""
Service de mémoire conversationnelle (court terme + long terme).

Deux niveaux de persistance par-delà la fenêtre glissante des 20 derniers
messages déjà gérée dans ``llm_service`` :

* ``conversation_summaries`` — résumé roulant condensé des messages anciens
  d'une conversation donnée. Recalculé dès que la conversation dépasse un
  seuil (configurable) de messages depuis la dernière condensation.
* ``user_memory`` — faits persistants par utilisateur (nom de la société,
  juridiction par défaut, préférences linguistiques, dossiers en cours,
  etc.). Injectés dans le prompt système pour toutes les questions.

La condensation utilise le même backend LLM qu'``ask`` afin de rester
isolée derrière un seul point d'intégration et auditable. En cas d'erreur,
toutes les fonctions échouent silencieusement (log ``debug``) : la
mémoire est un *enrichissement* et ne doit jamais bloquer la réponse.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from app.config import get_settings

logger = logging.getLogger(__name__)


SUMMARY_TRIGGER_MESSAGES = 20
SUMMARY_KEEP_RECENT = 10
MAX_USER_FACTS = 30
MAX_FACT_LENGTH = 280


_SUMMARY_PROMPTS = {
    "fr": (
        "Tu es un assistant juridique. Résume la conversation suivante "
        "en 6 à 10 puces factuelles, en français, sans interprétation. "
        "Conserve les noms propres, montants, dates, articles de loi cités "
        "et toute décision prise. Ignore les politesses."
    ),
    "en": (
        "You are a legal assistant. Summarize the conversation below in "
        "6–10 factual bullet points in English. Preserve proper names, "
        "amounts, dates, statute references, and any decisions taken. "
        "Skip pleasantries."
    ),
    "ar": (
        "أنت مساعد قانوني. لخّص المحادثة أدناه في 6 إلى 10 نقاط واقعية "
        "بالعربية، مع الحفاظ على الأسماء والمبالغ والتواريخ والمواد القانونية "
        "وأي قرارات. تجاهل عبارات المجاملة."
    ),
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ─────────────────────────── User facts (long-term) ───────────────────────────


async def get_user_memory(db: Any, user_id: str | None) -> dict | None:
    """Retourne le document de mémoire utilisateur, ou ``None``."""
    if not user_id:
        return None
    try:
        return await db["user_memory"].find_one({"user_id": user_id}, {"_id": 0})
    except Exception:
        logger.debug("get_user_memory failed", exc_info=True)
        return None


async def upsert_user_facts(
    db: Any,
    user_id: str,
    facts: list[str],
    organization_id: str | None = None,
    replace: bool = False,
) -> dict:
    """Ajoute (ou remplace) des faits persistants pour un utilisateur.

    ``replace=True`` écrase la liste existante. Sinon les nouveaux faits sont
    ajoutés en tête, dédoublonnés, et la liste est tronquée à
    :data:`MAX_USER_FACTS`.
    """
    cleaned: list[str] = []
    seen: set[str] = set()
    for fact in facts or []:
        if not isinstance(fact, str):
            continue
        f = fact.strip()
        if not f or len(f) > MAX_FACT_LENGTH:
            continue
        key = f.lower()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(f)

    now = _now()
    if replace:
        new_list = cleaned[:MAX_USER_FACTS]
    else:
        existing = await get_user_memory(db, user_id) or {}
        prior = existing.get("facts") or []
        merged: list[str] = []
        seen.clear()
        for f in cleaned + prior:
            k = f.lower()
            if k in seen:
                continue
            seen.add(k)
            merged.append(f)
        new_list = merged[:MAX_USER_FACTS]

    doc = {
        "user_id": user_id,
        "organization_id": organization_id,
        "facts": new_list,
        "updated_at": now,
    }
    try:
        await db["user_memory"].update_one(
            {"user_id": user_id},
            {"$set": doc, "$setOnInsert": {"created_at": now}},
            upsert=True,
        )
    except Exception:
        logger.debug("upsert_user_facts failed", exc_info=True)
    return doc


async def delete_user_memory(db: Any, user_id: str) -> bool:
    try:
        result = await db["user_memory"].delete_one({"user_id": user_id})
        return bool(getattr(result, "deleted_count", 0))
    except Exception:
        logger.debug("delete_user_memory failed", exc_info=True)
        return False


# ───────────────────────── Conversation summary (rolling) ─────────────────────


async def get_conversation_summary(
    db: Any, conversation_id: str | None
) -> dict | None:
    if not conversation_id:
        return None
    try:
        return await db["conversation_summaries"].find_one(
            {"conversation_id": conversation_id}, {"_id": 0}
        )
    except Exception:
        logger.debug("get_conversation_summary failed", exc_info=True)
        return None


def _format_history_for_summary(history: list[dict]) -> str:
    lines: list[str] = []
    for msg in history:
        role = msg.get("role")
        content = (msg.get("content") or "").strip()
        if not content or role not in ("user", "assistant"):
            continue
        label = "User" if role == "user" else "Assistant"
        lines.append(f"{label}: {content}")
    return "\n\n".join(lines)


async def _generate_summary(
    older_messages: list[dict],
    prior_summary: str | None,
    detected_lang: str,
) -> str:
    """Appelle le LLM pour condenser ``older_messages`` (+ résumé antérieur)."""
    # Import tardif : évite un cycle avec llm_service qui importe parfois
    # memory_service via le router.
    from app.services.llm_service import _call_ollama  # type: ignore

    settings = get_settings()
    system = _SUMMARY_PROMPTS.get(detected_lang, _SUMMARY_PROMPTS["en"])
    body = _format_history_for_summary(older_messages)
    if prior_summary:
        body = f"Résumé antérieur:\n{prior_summary}\n\n---\n\nNouveaux échanges:\n{body}"

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": body},
    ]
    return await _call_ollama(
        model=settings.llm_model,
        messages=messages,
        temperature=0.1,
        base_url=settings.llm_base_url,
    )


async def maybe_update_summary(
    db: Any,
    conversation_id: str | None,
    history: list[dict] | None,
    detected_lang: str = "fr",
    user_id: str | None = None,
) -> dict | None:
    """Recalcule le résumé roulant si l'historique dépasse le seuil.

    Retourne le document de résumé courant (ou ``None`` si rien à faire / si
    une erreur survient). Ne lève jamais.
    """
    if not conversation_id or not history:
        return None
    if len(history) < SUMMARY_TRIGGER_MESSAGES:
        return None

    try:
        existing = await get_conversation_summary(db, conversation_id) or {}
        last_indexed = int(existing.get("messages_indexed") or 0)
        # On ne re-condense que si suffisamment de nouveaux messages.
        if len(history) - last_indexed < SUMMARY_TRIGGER_MESSAGES // 2:
            return existing or None

        cutoff = max(0, len(history) - SUMMARY_KEEP_RECENT)
        older = history[:cutoff]
        if not older:
            return existing or None

        summary_text = await _generate_summary(
            older_messages=older,
            prior_summary=existing.get("summary") if existing else None,
            detected_lang=detected_lang,
        )
        if not summary_text or not summary_text.strip():
            return existing or None

        now = _now()
        doc = {
            "conversation_id": conversation_id,
            "user_id": user_id,
            "summary": summary_text.strip(),
            "messages_indexed": cutoff,
            "lang": detected_lang,
            "updated_at": now,
        }
        await db["conversation_summaries"].update_one(
            {"conversation_id": conversation_id},
            {"$set": doc, "$setOnInsert": {"created_at": now}},
            upsert=True,
        )
        return doc
    except Exception:
        logger.debug("maybe_update_summary failed", exc_info=True)
        return None


# ───────────────────────── Prompt injection helper ────────────────────────────


_BLOCK_LABELS = {
    "fr": ("Faits utilisateur persistants", "Résumé de la conversation antérieure"),
    "en": ("Persistent user facts", "Prior conversation summary"),
    "ar": ("معلومات دائمة عن المستخدم", "ملخص المحادثة السابقة"),
}


def build_memory_block(
    user_memory: dict | None,
    summary: dict | None,
    detected_lang: str = "fr",
) -> str:
    """Construit le bloc Markdown injecté dans le system prompt."""
    facts_label, summary_label = _BLOCK_LABELS.get(detected_lang, _BLOCK_LABELS["en"])
    parts: list[str] = []

    facts = (user_memory or {}).get("facts") or []
    if facts:
        bullets = "\n".join(f"- {f}" for f in facts)
        parts.append(f"### {facts_label}\n{bullets}")

    summary_text = (summary or {}).get("summary")
    if summary_text:
        parts.append(f"### {summary_label}\n{summary_text}")

    return "\n\n".join(parts)


def trim_history_after_summary(
    history: list[dict] | None, summary: dict | None
) -> list[dict] | None:
    """Si un résumé couvre les N premiers messages, ne garde que les récents."""
    if not history or not summary:
        return history
    indexed = int(summary.get("messages_indexed") or 0)
    if indexed <= 0 or indexed >= len(history):
        return history
    return history[indexed:]
