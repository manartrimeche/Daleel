"""
Action Service — Extract structured compliance actions from exigences using LLM.
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from datetime import datetime, timezone

from app.config import get_settings
from app.database import get_collection
from app.services import llm_service

logger = logging.getLogger(__name__)
settings = get_settings()

_ACTION_PROMPT = """Tu es un expert juridique tunisien spécialisé dans la transformation d'exigences réglementaires en actions concrètes de conformité.

**Exigence réglementaire à analyser :**
- Type      : {exigence_type}
- Article   : {article_reference}
- Texte     : {exigence_text}

**Ta mission :**
Extraire une ou plusieurs actions concrètes qu'une entreprise doit mettre en place pour satisfaire cette exigence. Chaque action doit être directement dérivée du texte juridique fourni.

Pour chaque action, fournis :
1. **modalite** : "obligation" | "interdiction" | "sanction" | "condition"
2. **action_precise** : l'action concrète à réaliser (commence par un verbe d'action)
3. **conditions** : liste des conditions d'applicabilité
4. **preuve** : le document ou la preuve de conformité
5. **confidence** : 0.0 à 1.0

**Règles :**
- Sois concret et actionnable — pas de paraphrase abstraite
- Dérive les actions UNIQUEMENT du texte juridique fourni
- Si l'exigence implique plusieurs actions distinctes, liste-les séparément
- Le domaine peut être varié : droit du travail, protection des données, fiscal, sociétés, etc.
- Si le texte est trop vague pour en extraire une action concrète, retourne []

**Exemples de format attendu :**
[
  {{
    "modalite": "obligation",
    "action_precise": "Effectuer la démarche administrative requise dans les délais prescrits",
    "conditions": ["s'applique à tout responsable concerné"],
    "preuve": "Récépissé ou accusé de réception de la démarche",
    "confidence": 0.90
  }}
]

Réponds UNIQUEMENT avec le tableau JSON, sans markdown ni texte supplémentaire."""



def _action_to_dict(action: dict) -> dict:
    return {
        "id": action.get("id"),
        "exigence_id": action.get("exigence_id"),
        "article_version_id": action.get("article_version_id"),
        "modalite": action.get("modalite"),
        "action_precise": action.get("action_precise"),
        "conditions": action.get("conditions") or [],
        "preuve": action.get("preuve"),
        "confidence": action.get("confidence"),
        "extracted_at": action.get("extracted_at"),
    }


async def _extract_actions_from_exigence(exigence: dict) -> list[dict]:
    prompt = _ACTION_PROMPT.format(
        exigence_type=exigence.get("exigence_type"),
        article_reference=exigence.get("article_reference") or "N/A",
        exigence_text=exigence.get("text"),
    )

    try:
        response = await llm_service.call_ollama(
            model=settings.llm_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Tu es un expert juridique tunisien en conformité réglementaire. "
                        "Extrais les actions concrètes de conformité sous forme de tableau JSON uniquement. "
                        "Pas de markdown, pas de texte supplémentaire."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            base_url=settings.llm_base_url,
        )

        response = response.strip()
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0]
        elif "```" in response:
            response = response.split("```")[1].split("```")[0]

        if not response.strip().startswith("["):
            match = re.search(r"\[.*\]", response, re.DOTALL)
            if match:
                response = match.group(0)
            else:
                logger.warning("No JSON array in LLM response for exigence %s", exigence.get("id"))
                return []

        raw_list = json.loads(response.strip())
        if not isinstance(raw_list, list):
            return []

        validated = []
        valid_modalites = {"obligation", "interdiction", "sanction", "condition"}
        for raw in raw_list:
            if not isinstance(raw, dict):
                continue
            action_precise = str(raw.get("action_precise", "")).strip()
            if len(action_precise) < 10:
                continue
            modalite = str(raw.get("modalite", exigence.get("exigence_type"))).strip().lower()
            if modalite not in valid_modalites:
                modalite = "obligation"
            validated.append(
                {
                    "modalite": modalite,
                    "action_precise": action_precise,
                    "conditions": raw.get("conditions", []) if isinstance(raw.get("conditions"), list) else [],
                    "preuve": str(raw.get("preuve", "")).strip() or None,
                    "confidence": max(0.0, min(1.0, float(raw.get("confidence", 0.7)))),
                }
            )
        return validated
    except json.JSONDecodeError as e:
        logger.error("JSON parse error for exigence %s: %s", exigence.get("id"), e)
        return []
    except Exception as e:
        logger.error("LLM error for exigence %s: %s", exigence.get("id"), e)
        return []


async def extract_and_store_actions(
    db,
    article_version_id: str,
    exigence_ids: list[str] | None = None,
) -> dict:
    version = await get_collection("article_versions").find_one({"id": article_version_id})
    if not version:
        raise ValueError(f"ArticleVersion '{article_version_id}' not found")

    query: dict = {"article_version_id": article_version_id}
    if exigence_ids:
        query["id"] = {"$in": exigence_ids}

    exigences = await get_collection("exigences").find(query).to_list(length=5000)
    if not exigences:
        logger.info(
            "No exigences directly linked to version %s, nothing to extract.",
            article_version_id,
        )
        return {
            "article_version_id": article_version_id,
            "exigences_processed": 0,
            "actions_created": 0,
            "message": "No exigences found for this ArticleVersion.",
        }

    now = datetime.now(timezone.utc)
    actions_created = 0
    exigences_processed = 0

    for exigence in exigences:
        raw_actions = await _extract_actions_from_exigence(exigence)
        if not raw_actions:
            continue

        action_docs = [
            {
                "id": str(uuid.uuid4()),
                "exigence_id": exigence.get("id"),
                "article_version_id": article_version_id,
                "modalite": action["modalite"],
                "action_precise": action["action_precise"],
                "conditions": action["conditions"],
                "preuve": action["preuve"],
                "confidence": action["confidence"],
                "extracted_at": now,
            }
            for action in raw_actions
        ]
        await get_collection("actions").insert_many(action_docs)
        actions_created += len(action_docs)
        exigences_processed += 1

    logger.info(
        "Actions extracted: version=%s, exigences=%s, actions=%s",
        article_version_id,
        exigences_processed,
        actions_created,
    )
    return {
        "article_version_id": article_version_id,
        "exigences_processed": exigences_processed,
        "actions_created": actions_created,
        "message": f"Extracted {actions_created} actions from {exigences_processed} exigences.",
    }


async def get_actions_by_version(
    db,
    article_version_id: str,
    modalite: str | None = None,
    skip: int = 0,
    limit: int = 200,
) -> tuple[list[dict], int, dict]:
    query: dict = {"article_version_id": article_version_id}
    if modalite:
        query["modalite"] = modalite

    total = await get_collection("actions").count_documents(query)
    cursor = (
        get_collection("actions")
        .find(query)
        .sort([("modalite", 1), ("confidence", -1)])
        .skip(skip)
        .limit(limit)
    )
    actions = [_action_to_dict(action) async for action in cursor]

    modalite_counts: dict[str, int] = {}
    async for row in get_collection("actions").aggregate([
        {"$match": {"article_version_id": article_version_id}},
        {"$group": {"_id": "$modalite", "count": {"$sum": 1}}},
    ]):
        modalite_counts[row["_id"]] = row["count"]

    return actions, int(total), modalite_counts


async def get_actions_by_exigence(
    db,
    exigence_id: str,
) -> list[dict]:
    cursor = get_collection("actions").find({"exigence_id": exigence_id}).sort("confidence", -1)
    return [_action_to_dict(action) async for action in cursor]


async def get_action(db, action_id: str) -> dict | None:
    action = await get_collection("actions").find_one({"id": action_id})
    return _action_to_dict(action) if action else None


async def delete_actions_by_version(
    db,
    article_version_id: str,
) -> int:
    result = await get_collection("actions").delete_many({"article_version_id": article_version_id})
    count = result.deleted_count
    logger.info("Deleted %s actions for version %s", count, article_version_id)
    return count
