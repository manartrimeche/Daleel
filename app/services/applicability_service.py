"""
Applicability Service — Evaluate which exigences apply to a company profile.

Uses the LLM to assess whether regulatory requirements apply based on
company characteristics (sector, size, activities, jurisdiction).
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone

from app.config import get_settings
from app.database import mongo_db
from app.services import llm_service

logger = logging.getLogger(__name__)
settings = get_settings()

APPLICABILITY_PROMPT = """You are a Tunisian legal expert evaluating whether a specific regulatory requirement applies to a company.

**Company Profile:**
- Name: NAME
- Sector: SECTOR
- Size: SIZE
- Employees: EMPLOYEES
- Activities: ACTIVITIES
- Jurisdiction: JURISDICTION

**Regulatory Requirement (Exigence):**
- Type: TYPE
- Text: TEXT
- Article: ARTICLE

**Your Task:**
Determine if this exigence applies to the company based on:
1. Company sector and main activities
2. Company size and employee count
3. Jurisdiction (e.g., Tunisian law applies to companies in Tunisia)
4. Scope of the regulation (who it targets: all companies, micro-enterprises, service providers, etc.)
5. Exemptions or special conditions mentioned in the rule

**Response (JSON only, no markdown):**
```json
{{
  "is_applicable": true/false,
  "confidence": 0.0-1.0,
  "explanation": "Clear explanation of the decision",
  "factors": [
    "Factor 1: how it supports the decision",
    "Factor 2: how it supports the decision"
  ],
  "conditions": [
    "Any additional conditions that must be met for applicability"
  ]
}}
```

**Important:**
- is_applicable: boolean (true if the exigence applies, false if it doesn't)
- confidence: 0.0-1.0 (higher = more certain)
- explanation: Clear, concise reasoning in Tunisian legal context
- factors: List key decision factors
- conditions: List prerequisites or conditions that must be true
- Return ONLY valid JSON, no markdown, no extra text
"""


def _collection(name: str):
    return mongo_db[name]


def _format_applicability_prompt(company_profile: dict, exigence: dict) -> str:
    prompt = APPLICABILITY_PROMPT
    prompt = prompt.replace("NAME", company_profile.get("name", "Unknown"))
    prompt = prompt.replace("SECTOR", company_profile.get("sector") or "Not specified")
    prompt = prompt.replace("SIZE", company_profile.get("size") or "Not specified")
    prompt = prompt.replace("EMPLOYEES", str(company_profile.get("employees") or "Not specified"))
    prompt = prompt.replace("ACTIVITIES", company_profile.get("activities") or "Not specified")
    prompt = prompt.replace("JURISDICTION", company_profile.get("jurisdiction", "tunisia"))
    prompt = prompt.replace("TYPE", exigence.get("exigence_type", "unknown"))
    prompt = prompt.replace("TEXT", exigence.get("text", ""))
    prompt = prompt.replace("ARTICLE", exigence.get("article_reference") or "N/A")
    return prompt


async def evaluate_exigence_applicability(
    company_profile: dict,
    exigence: dict,
) -> dict:
    prompt = _format_applicability_prompt(company_profile, exigence)
    messages = [
        {
            "role": "system",
            "content": "You are a Tunisian legal expert. Evaluate applicability based strictly on the company profile and regulation text. Return ONLY valid JSON with no markdown formatting, no code blocks, no extra text."
        },
        {"role": "user", "content": prompt},
    ]

    try:
        response_text = await llm_service.call_ollama(
            model=settings.llm_model,
            messages=messages,
            temperature=0.1,
            base_url=settings.llm_base_url,
        )

        response_text = response_text.strip()
        json_str = response_text
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0]
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0]
        json_str = json_str.strip()

        if not json_str.startswith("{"):
            start_idx = json_str.find("{")
            end_idx = json_str.rfind("}")
            if start_idx != -1 and end_idx != -1:
                json_str = json_str[start_idx:end_idx + 1]

        logger.debug("Parsing JSON: %s...", json_str[:200])
        result = json.loads(json_str)
        return {
            "is_applicable": bool(result.get("is_applicable", False)),
            "confidence": max(0.0, min(1.0, float(result.get("confidence", 0.5)))),
            "explanation": str(result.get("explanation", "")).strip(),
            "factors": result.get("factors", []) if isinstance(result.get("factors"), list) else [],
            "conditions": result.get("conditions", []) if isinstance(result.get("conditions"), list) else [],
        }
    except json.JSONDecodeError as e:
        logger.error("JSON parse error evaluating applicability: %s", e)
        logger.error("Response text: %s", response_text[:300])
        return {
            "is_applicable": False,
            "confidence": 0.3,
            "explanation": "Unable to determine applicability (parsing error)",
            "factors": [],
            "conditions": [],
        }
    except Exception as e:
        logger.error("Error evaluating applicability: %s", e)
        return {
            "is_applicable": False,
            "confidence": 0.3,
            "explanation": f"Evaluation error: {str(e)[:100]}",
            "factors": [],
            "conditions": [],
        }


async def create_company_profile(
    db,
    name: str,
    sector: str | None = None,
    size: str | None = None,
    employees: int | None = None,
    activities: str | None = None,
    jurisdiction: str = "tunisia",
    notes: str | None = None,
) -> dict:
    profile = {
        "id": str(uuid.uuid4()),
        "name": name,
        "sector": sector,
        "size": size,
        "employees": employees,
        "activities": activities,
        "jurisdiction": jurisdiction,
        "notes": notes,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    await _collection("company_profiles").insert_one(profile)
    logger.info("Created company profile: %s (%s)", profile["id"], name)
    return _profile_to_dict(profile)


async def get_company_profile(db, profile_id: str) -> dict | None:
    profile = await _collection("company_profiles").find_one({"id": profile_id})
    return _profile_to_dict(profile) if profile else None


async def list_company_profiles(db, skip: int = 0, limit: int = 50) -> tuple[list[dict], int]:
    total = await _collection("company_profiles").count_documents({})
    cursor = _collection("company_profiles").find({}).sort("created_at", -1).skip(skip).limit(limit)
    profiles = [_profile_to_dict(profile) async for profile in cursor]
    return profiles, int(total)


async def update_company_profile(db, profile_id: str, **kwargs) -> dict | None:
    allowed_fields = {"name", "sector", "size", "employees", "activities", "jurisdiction", "notes"}
    updates = {key: value for key, value in kwargs.items() if key in allowed_fields}
    if not updates:
        return await get_company_profile(db, profile_id)
    updates["updated_at"] = datetime.now(timezone.utc)
    result = await _collection("company_profiles").find_one_and_update(
        {"id": profile_id},
        {"$set": updates},
        return_document=__import__("pymongo").ReturnDocument.AFTER,
    )
    return _profile_to_dict(result) if result else None


async def delete_company_profile(db, profile_id: str) -> bool:
    profile = await _collection("company_profiles").find_one({"id": profile_id})
    if not profile:
        return False
    await _collection("exigence_applicabilities").delete_many({"profile_id": profile_id})
    await _collection("company_profiles").delete_one({"id": profile_id})
    logger.info("Deleted company profile: %s", profile_id)
    return True


async def evaluate_applicabilities(
    db,
    profile_id: str,
    exigence_ids: list[str] | None = None,
    document_id: str | None = None,
) -> int:
    profile = await _collection("company_profiles").find_one({"id": profile_id})
    if not profile:
        logger.error("Profile %s not found", profile_id)
        return 0

    query: dict = {}
    if exigence_ids:
        query["id"] = {"$in": exigence_ids}
    if document_id:
        query["document_id"] = document_id

    exigences = await _collection("exigences").find(query).to_list(length=None)
    if not exigences:
        logger.info("No exigences found for profile %s", profile_id)
        return 0

    exigence_lookup = {exigence["id"] for exigence in exigences}
    await _collection("exigence_applicabilities").delete_many(
        {"profile_id": profile_id, "exigence_id": {"$in": list(exigence_lookup)}}
    )

    applicabilities: list[dict] = []
    now = datetime.now(timezone.utc)

    profile_dict = _profile_to_dict(profile)
    for exigence in exigences:
        exigence_dict = {
            "text": exigence.get("text"),
            "exigence_type": exigence.get("exigence_type"),
            "article_reference": exigence.get("article_reference"),
        }
        evaluation = await evaluate_exigence_applicability(profile_dict, exigence_dict)
        applicabilities.append(
            {
                "id": str(uuid.uuid4()),
                "profile_id": profile_id,
                "exigence_id": exigence.get("id"),
                "is_applicable": evaluation["is_applicable"],
                "explanation": evaluation["explanation"],
                "confidence": evaluation["confidence"],
                "reasoning": {
                    "factors": evaluation["factors"],
                    "conditions": evaluation["conditions"],
                    "decision": "applicable" if evaluation["is_applicable"] else "not_applicable",
                },
                "calculated_at": now,
                "calculated_by": "llm",
            }
        )

    if applicabilities:
        await _collection("exigence_applicabilities").insert_many(applicabilities)
        logger.info("Evaluated %s applicabilities for profile %s", len(applicabilities), profile_id)

    return len(applicabilities)


async def get_applicabilities(
    db,
    profile_id: str,
    is_applicable: bool | None = None,
    skip: int = 0,
    limit: int = 100,
) -> tuple[list[dict], int]:
    query: dict = {"profile_id": profile_id}
    if is_applicable is not None:
        query["is_applicable"] = is_applicable

    total = await _collection("exigence_applicabilities").count_documents(query)
    cursor = (
        _collection("exigence_applicabilities")
        .find(query)
        .sort([("is_applicable", -1), ("confidence", -1)])
        .skip(skip)
        .limit(limit)
    )
    applicabilities = [_applicability_to_dict(app) async for app in cursor]
    return applicabilities, int(total)


async def get_applicability_summary(
    db,
    profile_id: str,
) -> dict:
    applicabilities = await _collection("exigence_applicabilities").find({"profile_id": profile_id}).to_list(length=None)
    applicable_count = sum(1 for app in applicabilities if app.get("is_applicable"))
    not_applicable_count = len(applicabilities) - applicable_count
    avg_confidence = sum(float(app.get("confidence", 0.0)) for app in applicabilities) / len(applicabilities) if applicabilities else 0.0

    by_type: dict[str, dict[str, int]] = {}
    exigences = {exigence["id"]: exigence for exigence in await _collection("exigences").find({}).to_list(length=None)}
    for app in applicabilities:
        exig = exigences.get(app.get("exigence_id"))
        exig_type = exig.get("exigence_type") if exig else "unknown"
        if exig_type not in by_type:
            by_type[exig_type] = {"applicable": 0, "not_applicable": 0}
        key = "applicable" if app.get("is_applicable") else "not_applicable"
        by_type[exig_type][key] += 1

    return {
        "applicable": applicable_count,
        "not_applicable": not_applicable_count,
        "total": len(applicabilities),
        "avg_confidence": avg_confidence,
        "by_type": by_type,
    }


def _profile_to_dict(profile: dict | None) -> dict | None:
    if not profile:
        return None
    return {
        "id": profile.get("id"),
        "name": profile.get("name"),
        "sector": profile.get("sector"),
        "size": profile.get("size"),
        "employees": profile.get("employees"),
        "activities": profile.get("activities"),
        "jurisdiction": profile.get("jurisdiction", "tunisia"),
        "notes": profile.get("notes"),
        "created_at": profile.get("created_at"),
        "updated_at": profile.get("updated_at"),
    }


def _applicability_to_dict(app: dict) -> dict:
    return {
        "id": app.get("id"),
        "profile_id": app.get("profile_id"),
        "exigence_id": app.get("exigence_id"),
        "is_applicable": app.get("is_applicable"),
        "explanation": app.get("explanation"),
        "confidence": app.get("confidence"),
        "reasoning": app.get("reasoning", {}),
        "calculated_at": app.get("calculated_at"),
        "calculated_by": app.get("calculated_by"),
    }
