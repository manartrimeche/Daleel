"""
Criticality Service — Sprint 4 (Step 8 of the workflow).

Assigns a criticality level to each compliance Action using a deterministic
rule-based scoring engine.

Levels:
  critique   — score >= 0.75  (sanctions, fines, criminal liability)
  importante — score >= 0.50  (obligations, prohibitions, domain-specific rules)
  secondaire — score <  0.50  (conditions, informational duties)

Scoring model:
  1. Base score from modalite
  2. Boost for sanction keywords in action text
  3. Boost for monetary penalty amounts
  4. Domain boosts (données perso, santé/sécurité, fiscal)
  5. Penalty for purely conditional language
"""

import logging
import re
import uuid
from datetime import datetime, timezone
from app.database import get_collection

logger = logging.getLogger(__name__)


def get_collection(name: str):
    return mongo_db[name]

# ─────────────────────────────────────────────────────────────
# Scoring constants
# ─────────────────────────────────────────────────────────────

_BASE_SCORES: dict[str, float] = {
    "sanction":    0.85,
    "interdiction": 0.70,
    "obligation":  0.65,
    "condition":   0.35,
}

_SANCTION_KW = re.compile(
    r"\b(?:"
    r"amende|peine|emprisonnement|prison|poursuite|poursuites p[eé]nales|"
    r"infraction|contravention|saisie|fermeture|r[eé]vocation|suspension|"
    r"dissolution|liquidation judiciaire|"
    r"خطية|غرامة|عقوبة|سجن|حبس|توقيف|حل"
    r")\b",
    re.IGNORECASE,
)

_AMOUNT_RE = re.compile(
    r"\b\d[\d\s]*(?:dinar|DT|TND|millime|euro|EUR|USD)\b|"
    r"\b(?:\d+(?:\s*000)*)\s*(?:dinar|DT|TND)\b",
    re.IGNORECASE,
)

_DOMAIN_BOOSTS: list[tuple[re.Pattern, float, str]] = [
    (
        re.compile(
            r"\b(?:donn[eé]es personnelles|donn[eé]es [àa] caract[eè]re|INPDP|"
            r"vie priv[eé]e|protection des donn[eé]es|RGPD|"
            r"البيانات الشخصية|حماية البيانات)\b",
            re.IGNORECASE,
        ),
        0.15,
        "Domaine données personnelles (criticité renforcée)",
    ),
    (
        re.compile(
            r"\b(?:sant[eé] au travail|s[eé]curit[eé] au travail|accident du travail|"
            r"maladie professionnelle|hygi[eè]ne|EPI|equipement de protection|"
            r"السلامة المهنية|الصحة المهنية)\b",
            re.IGNORECASE,
        ),
        0.12,
        "Domaine santé/sécurité au travail",
    ),
    (
        re.compile(
            r"\b(?:fiscal|TVA|impôt|taxe|douane|fraude fiscale|"
            r"comptabilit[eé]|bilan|audit|commissaire aux comptes|"
            r"الجباية|الضريبة|المحاسبة)\b",
            re.IGNORECASE,
        ),
        0.08,
        "Domaine fiscal / comptable",
    ),
    (
        re.compile(
            r"\b(?:travail non d[eé]clar[eé]|travail au noir|clandestin|"
            r"emploi ill[eé]gal|travail forc[eé]|"
            r"العمل غير المصرح|العمل القسري)\b",
            re.IGNORECASE,
        ),
        0.15,
        "Domaine travail clandestin / forcé",
    ),
]

_CONDITIONAL_RE = re.compile(
    r"\b(?:le cas [eé]ch[eé]ant|[eé]ventuellement|si applicable|"
    r"dans la mesure où|sous r[eé]serve|[àa] titre facultatif|"
    r"إن اقتضى الأمر|إذا كان ذلك مناسبًا)\b",
    re.IGNORECASE,
)


# ─────────────────────────────────────────────────────────────
# Rule engine
# ─────────────────────────────────────────────────────────────

def compute_criticality_score(action: dict) -> tuple[float, list[str]]:
    """
    Compute a 0–1 criticality score and human-readable factors for an Action.

    Returns: (score, factors_list)
    """
    score: float = _BASE_SCORES.get(str(action.get("modalite", "")), 0.50)
    factors: list[str] = [
        f"Modalité '{action.get('modalite')}': score de base {score:.2f}"
    ]

    combined_text = " ".join(filter(None, [
        str(action.get("action_precise") or ""),
        str(action.get("preuve") or ""),
        " ".join(action.get("conditions") or []),
    ]))

    # ── Sanction keyword boost ──
    if _SANCTION_KW.search(combined_text):
        boost = 0.18
        score = min(1.0, score + boost)
        factors.append(f"Sanction/pénalité détectée dans le texte (+{boost:.2f})")

    # ── Monetary amount boost ──
    if _AMOUNT_RE.search(combined_text):
        boost = 0.10
        score = min(1.0, score + boost)
        factors.append(f"Montant de pénalité explicite (+{boost:.2f})")

    # ── Domain boosts ──
    for pattern, boost, label in _DOMAIN_BOOSTS:
        if pattern.search(combined_text):
            score = min(1.0, score + boost)
            factors.append(f"{label} (+{boost:.2f})")

    # ── Conditional language penalty ──
    if _CONDITIONAL_RE.search(combined_text):
        penalty = 0.10
        score = max(0.0, score - penalty)
        factors.append(f"Langage conditionnel/facultatif détecté (-{penalty:.2f})")

    return round(score, 4), factors


def score_to_level(score: float) -> str:
    """Map numeric score to level string."""
    if score >= 0.75:
        return "critique"
    if score >= 0.50:
        return "importante"
    return "secondaire"


# ─────────────────────────────────────────────────────────────
# Serialiser
# ─────────────────────────────────────────────────────────────

def _crit_to_dict(c: dict) -> dict:
    return {
        "id": c.get("id"),
        "action_id": c.get("action_id"),
        "level": c.get("level"),
        "score": c.get("score"),
        "factors": c.get("factors") or [],
        "computed_at": c.get("computed_at"),
        "computed_by": c.get("computed_by"),
    }


# ─────────────────────────────────────────────────────────────
# Database operations
# ─────────────────────────────────────────────────────────────

async def compute_and_store(
    db,
    action: dict,
    recompute: bool = False,
) -> dict | None:
    """
    Compute criticality for one Action and persist it.

    Returns the ActionCriticality dict, or None if skipped.
    """
    existing = await get_collection("action_criticalities").find_one({"action_id": action.get("id")})

    if existing and not recompute:
        return None  # Already computed, skip

    score, factors = compute_criticality_score(action)
    level = score_to_level(score)
    now = datetime.now(timezone.utc)

    crit = {
        "id": existing.get("id") if existing else str(uuid.uuid4()),
        "action_id": action.get("id"),
        "level": level,
        "score": score,
        "factors": factors,
        "computed_at": now,
        "computed_by": "rule-engine",
    }

    if existing:
        await get_collection("action_criticalities").update_one(
            {"id": existing["id"]},
            {"$set": crit},
        )
    else:
        await get_collection("action_criticalities").insert_one(crit)

    return _crit_to_dict(crit)


async def compute_for_article_version(
    db,
    article_version_id: str,
    action_ids: list[str] | None = None,
    recompute: bool = False,
) -> dict:
    """
    Compute criticality for all (or selected) Actions of an ArticleVersion.

    Returns: {computed, skipped, by_level, message}
    """
    query: dict = {"article_version_id": article_version_id}
    if action_ids:
        query["id"] = {"$in": action_ids}
    actions = await get_collection("actions").find(query).to_list(length=None)

    computed = 0
    skipped = 0
    by_level: dict[str, int] = {"critique": 0, "importante": 0, "secondaire": 0}

    for action in actions:
        result = await compute_and_store(db, action, recompute=recompute)
        if result:
            computed += 1
            by_level[result["level"]] = by_level.get(result["level"], 0) + 1
        else:
            skipped += 1

    logger.info(
        f"Criticality computed: version={article_version_id}, "
        f"computed={computed}, skipped={skipped}, by_level={by_level}"
    )
    return {
        "computed": computed,
        "skipped": skipped,
        "by_level": by_level,
        "message": (
            f"Computed {computed} criticalities "
            f"(critique={by_level['critique']}, "
            f"importante={by_level['importante']}, "
            f"secondaire={by_level['secondaire']}). "
            f"Skipped {skipped} already-computed actions."
        ),
    }


async def compute_for_loi(
    db,
    loi_id: str,
    recompute: bool = False,
) -> dict:
    """
    Compute criticality for all Actions linked to any ArticleVersion of a Loi.
    """
    # Get all active article versions for this loi
    articles = await get_collection("articles").find({"loi_id": loi_id}).to_list(length=None)
    article_ids = [article["id"] for article in articles]
    versions = await get_collection("article_versions").find({
        "article_id": {"$in": article_ids},
        "status": "active",
    }).to_list(length=None)

    total_computed = 0
    total_skipped = 0
    total_by_level: dict[str, int] = {"critique": 0, "importante": 0, "secondaire": 0}

    for version in versions:
        result = await compute_for_article_version(db, version["id"], recompute=recompute)
        total_computed += result["computed"]
        total_skipped += result["skipped"]
        for level, count in result["by_level"].items():
            total_by_level[level] = total_by_level.get(level, 0) + count

    logger.info(
        f"Criticality (loi={loi_id}): {total_computed} computed, {total_skipped} skipped"
    )
    return {
        "computed": total_computed,
        "skipped": total_skipped,
        "by_level": total_by_level,
        "message": (
            f"Computed {total_computed} criticalities across {len(versions)} active versions "
            f"(critique={total_by_level['critique']}, "
            f"importante={total_by_level['importante']}, "
            f"secondaire={total_by_level['secondaire']})."
        ),
    }


async def get_criticality(db, action_id: str) -> dict | None:
    """Get the ActionCriticality record for an Action."""
    c = await get_collection("action_criticalities").find_one({"action_id": action_id})
    return _crit_to_dict(c) if c else None


async def get_criticality_summary_for_profile(
    db,
    profile_id: str,
) -> dict:
    """
    Get criticality breakdown for all applicable actions of a company profile.
    """
    applicable = await get_collection("exigence_applicabilities").find({
        "profile_id": profile_id,
        "is_applicable": True,
    }).to_list(length=None)
    applicable_ids = [item["exigence_id"] for item in applicable]

    if not applicable_ids:
        return {"critique": 0, "importante": 0, "secondaire": 0, "uncomputed": 0, "total": 0}

    # Get actions for those exigences
    actions = await get_collection("actions").find({"exigence_id": {"$in": applicable_ids}}).to_list(length=None)
    action_ids = [action["id"] for action in actions]

    if not action_ids:
        return {"critique": 0, "importante": 0, "secondaire": 0, "uncomputed": 0, "total": 0}

    # Count by level
    level_counts: dict[str, int] = {}
    rows = await get_collection("action_criticalities").aggregate([
        {"$match": {"action_id": {"$in": action_ids}}},
        {"$group": {"_id": "$level", "count": {"$sum": 1}}},
    ]).to_list(length=None)
    for row in rows:
        level_counts[row["_id"]] = row["count"]

    computed_total = sum(level_counts.values())
    uncomputed = len(action_ids) - computed_total

    return {
        "critique": level_counts.get("critique", 0),
        "importante": level_counts.get("importante", 0),
        "secondaire": level_counts.get("secondaire", 0),
        "uncomputed": uncomputed,
        "total": len(action_ids),
    }
