"""
Lightweight contract analysis for the chat interface.

Unlike the full pipeline (contract_analysis_service) that requires
pre-processed documents (chunks, cleaned_pages), this module works
directly on extracted text for instant chat-based analysis.
"""

from __future__ import annotations

import logging
import uuid

from app.config import get_settings
from app.services.contract_analysis_service import (
    CONTRACT_TYPES,
    CLAUSE_LABELS,
    _safe_json_parse,
    _pass4_compute_score,
)

logger = logging.getLogger(__name__)

ACTIONS = ("summary", "risks", "missing_clauses", "recommendations", "full")


async def analyze_for_chat(text: str, action: str, language: str = "fr") -> dict:
    if action == "summary":
        return await _chat_summary(text, language)
    if action == "risks":
        return await _chat_risks(text, language)
    if action == "missing_clauses":
        return await _chat_missing_clauses(text, language)
    if action == "recommendations":
        return await _chat_recommendations(text, language)
    if action == "full":
        return await _chat_full_analysis(text, language)
    raise ValueError(f"Unknown action: {action}")


# ─── LLM helper ───

async def _call_llm(system_prompt: str, user_prompt: str, temperature: float = 0.1) -> str:
    settings = get_settings()
    from app.services.llm_service import call_ollama

    return await call_ollama(
        model=settings.llm_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
        base_url=settings.llm_base_url,
    )


# ─── Shared analysis steps ───

async def _detect_type_and_summary(text: str, language: str) -> dict:
    preview = text[:4000]
    types_list = ", ".join(CONTRACT_TYPES.keys())

    response = await _call_llm(
        system_prompt=(
            "Vous êtes un expert juridique tunisien. "
            "Analysez le début de ce contrat et retournez UNIQUEMENT du JSON valide."
        ),
        user_prompt=(
            f"Identifiez le type de contrat parmi : {types_list}.\n\n"
            f"Texte du contrat :\n---\n{preview}\n---\n\n"
            "Retournez un objet JSON :\n"
            "{\n"
            '  "contract_type": "type parmi la liste",\n'
            '  "language": "fr ou ar ou en",\n'
            '  "parties": ["Partie A", "Partie B"],\n'
            '  "summary": "Résumé en 2-3 phrases"\n'
            "}"
        ),
    )

    result = _safe_json_parse(response, fallback={})
    if not isinstance(result, dict):
        result = {}

    contract_type = result.get("contract_type", "autre")
    if contract_type not in CONTRACT_TYPES:
        contract_type = "autre"

    type_config = CONTRACT_TYPES[contract_type]
    return {
        "contract_type": contract_type,
        "contract_type_label": type_config.get("label_fr", contract_type),
        "language": result.get("language", language),
        "parties": result.get("parties", []),
        "summary": result.get("summary", ""),
    }


async def _detect_risks(text: str, contract_type: str, language: str) -> dict:
    type_config = CONTRACT_TYPES.get(contract_type, CONTRACT_TYPES["autre"])
    type_label = type_config["label_fr"]
    analysis_text = text[:8000]

    response = await _call_llm(
        system_prompt=(
            f"Vous êtes un expert juridique tunisien. "
            f"Analysez ce {type_label} et identifiez TOUS les problèmes juridiques. "
            "Retournez UNIQUEMENT du JSON valide."
        ),
        user_prompt=(
            f"Texte du contrat :\n---\n{analysis_text}\n---\n\n"
            "Retournez un objet JSON :\n"
            "{\n"
            '  "findings": [\n'
            "    {\n"
            '      "category": "risk|legal_flaw|ambiguity",\n'
            '      "severity": "critical|major|minor",\n'
            '      "title": "Titre court",\n'
            '      "description": "Description détaillée",\n'
            '      "clause_reference": "Clause concernée",\n'
            '      "recommendation": "Modification suggérée"\n'
            "    }\n"
            "  ]\n"
            "}\n\n"
            "Catégories :\n"
            "- risk : clause abusive, déséquilibre, engagement excessif\n"
            "- legal_flaw : non-conformité au droit tunisien\n"
            "- ambiguity : formulation vague, source de litige\n\n"
            'Si aucun problème : {"findings": []}'
        ),
    )

    parsed = _safe_json_parse(response, fallback={})
    if not isinstance(parsed, dict):
        parsed = {}

    findings = []
    for f in parsed.get("findings", []):
        if not isinstance(f, dict):
            continue
        category = f.get("category", "risk")
        if category not in ("risk", "legal_flaw", "ambiguity"):
            category = "risk"
        severity = f.get("severity", "minor")
        if severity not in ("critical", "major", "minor"):
            severity = "minor"
        findings.append({
            "id": str(uuid.uuid4()),
            "category": category,
            "severity": severity,
            "title": str(f.get("title", "")).strip()[:200],
            "description": str(f.get("description", "")).strip()[:500],
            "clause_reference": str(f.get("clause_reference", "")).strip()[:200] or None,
            "recommendation": str(f.get("recommendation", "")).strip()[:500],
        })

    findings_summary = {
        "critical": sum(1 for f in findings if f["severity"] == "critical"),
        "major": sum(1 for f in findings if f["severity"] == "major"),
        "minor": sum(1 for f in findings if f["severity"] == "minor"),
        "total": len(findings),
    }
    return {"findings": findings, "findings_summary": findings_summary}


async def _detect_missing(text: str, contract_type: str, language: str) -> dict:
    type_config = CONTRACT_TYPES.get(contract_type, CONTRACT_TYPES["autre"])
    type_label = type_config["label_fr"]
    expected_labels = [
        CLAUSE_LABELS.get(c, c)
        for c in type_config["mandatory_clauses"] + type_config["recommended_clauses"]
    ]
    expected_str = ", ".join(expected_labels)
    preview = text[:6000]

    response = await _call_llm(
        system_prompt=(
            f"Vous êtes un expert juridique tunisien spécialisé dans les {type_label}s. "
            "Retournez UNIQUEMENT du JSON valide."
        ),
        user_prompt=(
            f"Voici le texte d'un {type_label} :\n---\n{preview}\n---\n\n"
            f"Clauses normalement attendues : {expected_str}\n\n"
            "Identifiez les clauses manquantes. Retournez un array JSON :\n"
            "[\n"
            "  {\n"
            '    "clause_name": "Nom de la clause",\n'
            '    "importance": "mandatory|recommended",\n'
            '    "legal_basis": "Article X, Code Y",\n'
            '    "risk_if_missing": "Conséquence"\n'
            "  }\n"
            "]\n"
            "Si aucune clause ne manque, retournez []."
        ),
    )

    raw = _safe_json_parse(response, fallback=[])
    if not isinstance(raw, list):
        raw = []

    missing = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        importance = item.get("importance", "recommended")
        if importance not in ("mandatory", "recommended"):
            importance = "recommended"
        missing.append({
            "id": str(uuid.uuid4()),
            "clause_name": str(item.get("clause_name", "")).strip()[:200],
            "importance": importance,
            "legal_basis": str(item.get("legal_basis", "")).strip()[:300] or None,
            "risk_if_missing": str(item.get("risk_if_missing", "")).strip()[:500],
        })

    return {"missing_clauses": missing}


async def _generate_recs(
    findings: list, missing_clauses: list, contract_type: str, language: str,
) -> list[str]:
    if not findings and not missing_clauses:
        return ["Le contrat semble complet et ne présente pas de risques majeurs identifiés."]

    type_config = CONTRACT_TYPES.get(contract_type, CONTRACT_TYPES["autre"])
    problems = []
    for f in findings[:10]:
        problems.append(f"- [{f['severity'].upper()}] {f['title']}: {f['description'][:100]}")
    for mc in missing_clauses[:8]:
        label = "OBLIGATOIRE" if mc["importance"] == "mandatory" else "RECOMMANDÉ"
        problems.append(f"- [MANQUANT {label}] {mc['clause_name']}")

    response = await _call_llm(
        system_prompt=(
            "Vous êtes un conseiller juridique tunisien. "
            "Donnez des recommandations pratiques et concrètes en français."
        ),
        user_prompt=(
            f"Problèmes identifiés dans un {type_config['label_fr']} :\n\n"
            + "\n".join(problems)
            + "\n\nDonnez 5 à 8 recommandations concrètes. "
            "Retournez UNIQUEMENT un array JSON de strings :\n"
            '["Recommandation 1", "Recommandation 2", ...]'
        ),
        temperature=0.3,
    )

    recs = _safe_json_parse(response, fallback=[])
    if isinstance(recs, list):
        return [str(r).strip() for r in recs if isinstance(r, str) and r.strip()][:10]
    return []


# ─── Public action functions ───

async def _chat_summary(text: str, language: str) -> dict:
    info = await _detect_type_and_summary(text, language)
    return {"action": "summary", "analysis": info}


async def _chat_risks(text: str, language: str) -> dict:
    info = await _detect_type_and_summary(text, language)
    risks = await _detect_risks(text, info["contract_type"], language)
    return {"action": "risks", "analysis": {**info, **risks}}


async def _chat_missing_clauses(text: str, language: str) -> dict:
    info = await _detect_type_and_summary(text, language)
    missing = await _detect_missing(text, info["contract_type"], language)
    return {"action": "missing_clauses", "analysis": {**info, **missing}}


async def _chat_recommendations(text: str, language: str) -> dict:
    info = await _detect_type_and_summary(text, language)
    risks = await _detect_risks(text, info["contract_type"], language)
    missing = await _detect_missing(text, info["contract_type"], language)
    recs = await _generate_recs(
        risks["findings"], missing["missing_clauses"],
        info["contract_type"], language,
    )
    return {"action": "recommendations", "analysis": {**info, "recommendations": recs}}


async def _chat_full_analysis(text: str, language: str) -> dict:
    info = await _detect_type_and_summary(text, language)
    ct = info["contract_type"]
    risks = await _detect_risks(text, ct, language)
    missing = await _detect_missing(text, ct, language)
    score_result = _pass4_compute_score(risks["findings"], missing["missing_clauses"])
    recs = await _generate_recs(
        risks["findings"], missing["missing_clauses"], ct, language,
    )
    return {
        "action": "full",
        "analysis": {
            **info,
            **risks,
            **missing,
            "score": score_result["score"],
            "score_category": score_result["category"],
            "score_breakdown": score_result["breakdown"],
            "recommendations": recs,
        },
    }
