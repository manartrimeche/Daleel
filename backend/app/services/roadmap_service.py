"""
Roadmap Service — Sprint 4 (Step 9 of the workflow).

Generates a dynamic, prioritised compliance action plan for a company profile.

The roadmap is dynamic:
  - applicable actions come from MongoDB collections
  - criticalities are loaded or computed on demand
  - dependencies are stored in MongoDB
  - the final ordering is computed in Python with a dependency-aware sort
"""

import logging
import uuid
from collections import defaultdict
from datetime import datetime, timezone

from app.database import get_collection
from app.services import criticality_service

logger = logging.getLogger(__name__)

_LEVEL_ORDER = {"critique": 0, "importante": 1, "secondaire": 2, "unknown": 3}



def _action_to_dict(action: dict) -> dict:
    return action


async def _get_applicable_actions(profile_id: str, organization_id: str | None = None) -> list[dict]:
    """Retrieve all actions for exigences that are applicable to the profile."""
    applicable_exigence_ids = []
    query: dict = {"profile_id": profile_id, "is_applicable": True}
    if organization_id:
        query["organization_id"] = organization_id

    cursor = get_collection("exigence_applicabilities").find(
        query,
        {"exigence_id": 1},
    )
    async for row in cursor:
        exigence_id = row.get("exigence_id")
        if exigence_id:
            applicable_exigence_ids.append(exigence_id)

    if not applicable_exigence_ids:
        return []

    actions = await get_collection("actions").find({"exigence_id": {"$in": applicable_exigence_ids}}).to_list(length=5000)
    return [_action_to_dict(action) for action in actions]


async def _ensure_criticalities(actions: list[dict]) -> dict[str, dict]:
    """Load existing criticalities; auto-compute missing ones."""
    action_ids = [action["id"] for action in actions if action.get("id")]
    if not action_ids:
        return {}

    existing = await get_collection("action_criticalities").find({"action_id": {"$in": action_ids}}).to_list(length=5000)
    crit_map: dict[str, dict] = {criticality["action_id"]: criticality for criticality in existing if criticality.get("action_id")}

    missing = [action for action in actions if action["id"] not in crit_map]
    if missing:
        logger.info("Roadmap: auto-computing criticality for %s actions", len(missing))
        for action in missing:
            result = await criticality_service.compute_and_store(None, action, recompute=False)
            if result:
                stored = await get_collection("action_criticalities").find_one({"action_id": action["id"]})
                if stored:
                    crit_map[action["id"]] = stored

    return crit_map


async def _get_article_context(action: dict) -> dict:
    """Resolve article_key and loi_code for an action via its ArticleVersion."""
    version_id = action.get("article_version_id")
    if not version_id:
        return {"article_key": None, "loi_code": None}

    version = await get_collection("article_versions").find_one({"id": version_id})
    if not version:
        return {"article_key": None, "loi_code": None}

    article = await get_collection("articles").find_one({"id": version.get("article_id")})
    if not article:
        return {"article_key": None, "loi_code": None}

    loi = await get_collection("lois").find_one({"id": article.get("loi_id")})
    return {
        "article_key": article.get("article_key"),
        "loi_code": loi.get("code") if loi else None,
    }


def _topological_sort(action_ids: list[str], dependencies: list[dict], crit_map: dict[str, dict]) -> list[str]:
    """Dependency-aware Kahn sort with criticality priority."""
    dependents: dict[str, set[str]] = defaultdict(set)
    in_degree: dict[str, int] = {action_id: 0 for action_id in action_ids}
    id_set = set(action_ids)

    for dependency in dependencies:
        action_id = dependency.get("action_id")
        depends_on_id = dependency.get("depends_on_id")
        if action_id in id_set and depends_on_id in id_set:
            dependents[depends_on_id].add(action_id)
            in_degree[action_id] = in_degree.get(action_id, 0) + 1

    def _priority(action_id: str) -> tuple:
        criticality = crit_map.get(action_id) or {}
        level = criticality.get("level") or "unknown"
        score = criticality.get("score") or 0.0
        return (_LEVEL_ORDER.get(level, 3), -float(score))

    ready = sorted([action_id for action_id, degree in in_degree.items() if degree == 0], key=_priority)
    ordered: list[str] = []

    while ready:
        current = ready.pop(0)
        ordered.append(current)

        newly_ready = []
        for dependent_id in dependents.get(current, set()):
            in_degree[dependent_id] -= 1
            if in_degree[dependent_id] == 0:
                newly_ready.append(dependent_id)

        newly_ready.sort(key=_priority)
        ready = sorted(ready + newly_ready, key=_priority)

    remaining = [action_id for action_id in action_ids if action_id not in set(ordered)]
    if remaining:
        logger.warning(
            "Roadmap: %s actions have unresolved dependency cycles - appended at end of plan",
            len(remaining),
        )
        remaining.sort(key=_priority)
        ordered.extend(remaining)

    return ordered


async def generate_roadmap(db, profile_id: str, organization_id: str | None = None) -> dict:
    """Generate the dynamic compliance roadmap for a company profile."""
    profile_query: dict = {"id": profile_id}
    if organization_id:
        profile_query["organization_id"] = organization_id

    profile = await get_collection("company_profiles").find_one(profile_query)
    if not profile:
        raise ValueError(f"Company profile '{profile_id}' not found")

    actions = await _get_applicable_actions(profile_id, organization_id=organization_id)
    if not actions:
        return {
            "profile_id": profile_id,
            "profile_name": profile.get("name"),
            "total_actions": 0,
            "by_level": {"critique": 0, "importante": 0, "secondaire": 0},
            "ordered_plan": [],
            "generated_at": datetime.now(timezone.utc),
            "message": (
                "No applicable actions found. Run applicability evaluation first, then extract actions."
            ),
        }

    crit_map = await _ensure_criticalities(actions)
    action_ids = [action["id"] for action in actions]
    dependencies = await get_collection("action_dependencies").find(
        {"action_id": {"$in": action_ids}, "depends_on_id": {"$in": action_ids}}
    ).to_list(length=5000)

    deps_by_action: dict[str, list[str]] = defaultdict(list)
    for dependency in dependencies:
        deps_by_action[dependency.get("action_id")].append(dependency.get("depends_on_id"))

    ordered_ids = _topological_sort(action_ids, list(dependencies), crit_map)
    action_lookup: dict[str, dict] = {action["id"]: action for action in actions}

    ordered_plan = []
    by_level: dict[str, int] = {"critique": 0, "importante": 0, "secondaire": 0}

    for position, action_id in enumerate(ordered_ids, start=1):
        action = action_lookup.get(action_id)
        if not action:
            continue

        criticality = crit_map.get(action_id) or {}
        level = criticality.get("level") or "secondaire"
        score = criticality.get("score") or 0.0
        context = await _get_article_context(action)

        by_level[level] = by_level.get(level, 0) + 1
        ordered_plan.append({
            "position": position,
            "action_id": action_id,
            "article_version_id": action.get("article_version_id"),
            "article_key": context["article_key"],
            "loi_code": context["loi_code"],
            "modalite": action.get("modalite"),
            "action_precise": action.get("action_precise"),
            "conditions": action.get("conditions") or [],
            "preuve": action.get("preuve"),
            "criticality_level": level,
            "criticality_score": score,
            "depends_on_ids": deps_by_action.get(action_id, []),
        })

    logger.info(
        "Roadmap generated for profile=%s: %s actions (critique=%s, importante=%s, secondaire=%s)",
        profile_id,
        len(ordered_plan),
        by_level.get("critique", 0),
        by_level.get("importante", 0),
        by_level.get("secondaire", 0),
    )

    return {
        "profile_id": profile_id,
        "profile_name": profile.get("name"),
        "total_actions": len(ordered_plan),
        "by_level": by_level,
        "ordered_plan": ordered_plan,
        "generated_at": datetime.now(timezone.utc),
        "message": (
            f"Roadmap ready: {len(ordered_plan)} actions - "
            f"critique: {by_level.get('critique', 0)}, "
            f"importante: {by_level.get('importante', 0)}, "
            f"secondaire: {by_level.get('secondaire', 0)}."
        ),
    }


async def add_dependency(db, action_id: str, depends_on_id: str, dependency_type: str, reason: str | None = None) -> dict:
    """Add a dependency: action_id depends on depends_on_id."""
    a1 = await get_collection("actions").find_one({"id": action_id})
    a2 = await get_collection("actions").find_one({"id": depends_on_id})
    if not a1:
        raise ValueError(f"Action '{action_id}' not found")
    if not a2:
        raise ValueError(f"Action '{depends_on_id}' not found")
    if action_id == depends_on_id:
        raise ValueError("An action cannot depend on itself")

    existing = await get_collection("action_dependencies").find_one({
        "action_id": action_id,
        "depends_on_id": depends_on_id,
    })
    if existing:
        raise ValueError("This dependency already exists")

    now = datetime.now(timezone.utc)
    dependency = {
        "id": str(uuid.uuid4()),
        "action_id": action_id,
        "depends_on_id": depends_on_id,
        "dependency_type": dependency_type,
        "reason": reason,
        "created_at": now,
    }
    await get_collection("action_dependencies").insert_one(dependency)
    return dependency


async def list_dependencies(db, action_id: str) -> list[dict]:
    """List all dependencies where action_id is the dependent."""
    dependencies = await get_collection("action_dependencies").find({"action_id": action_id}).to_list(length=5000)
    return dependencies


async def delete_dependency(db, dep_id: str) -> bool:
    """Delete a dependency by ID."""
    result = await get_collection("action_dependencies").delete_one({"id": dep_id})
    return result.deleted_count > 0
