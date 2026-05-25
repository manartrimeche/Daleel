"""
Contract Analysis Service — Analyse multi-passes de contrats via LLM.

Pipeline en 4 passes :
  1. Détection type de contrat + résumé
  2. Analyse clause par clause (risques, failles, ambiguïtés)
  3. Détection clauses manquantes (grounded via RAG juridique)
  4. Calcul du score + recommandations

Collection gérée : contract_analyses
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
import time
import uuid
from datetime import datetime, timezone
from typing import Optional

from app.config import get_settings
from app.database import get_collection

logger = logging.getLogger(__name__)
_collection = get_collection


# ─────────────────────────────────────────────────────────────
# Constantes — types de contrats et clauses attendues
# ─────────────────────────────────────────────────────────────

CONTRACT_TYPES = {
    "travail": {
        "label_fr": "Contrat de travail",
        "label_ar": "عقد شغل",
        "mandatory_clauses": [
            "identite_parties",
            "objet",
            "duree",
            "remuneration",
            "horaires_travail",
            "periode_essai",
            "lieu_travail",
        ],
        "recommended_clauses": [
            "confidentialite",
            "non_concurrence",
            "preavis",
            "conges",
            "securite_sociale",
            "formation",
            "rupture_anticipee",
            "juridiction_competente",
        ],
        "search_queries": [
            "clauses obligatoires contrat de travail",
            "obligations employeur salarié code du travail",
            "rupture contrat de travail préavis",
            "période d'essai durée maximale",
        ],
    },
    "commercial": {
        "label_fr": "Contrat commercial",
        "label_ar": "عقد تجاري",
        "mandatory_clauses": [
            "identite_parties",
            "objet",
            "prix_paiement",
            "duree",
            "livraison",
        ],
        "recommended_clauses": [
            "force_majeure",
            "responsabilite",
            "garantie",
            "resiliation",
            "confidentialite",
            "propriete_intellectuelle",
            "penalites_retard",
            "juridiction_competente",
            "loi_applicable",
        ],
        "search_queries": [
            "obligations contrat commercial société",
            "clauses abusives contrat commercial",
            "responsabilité contractuelle code sociétés",
        ],
    },
    "bail": {
        "label_fr": "Contrat de bail",
        "label_ar": "عقد كراء",
        "mandatory_clauses": [
            "identite_parties",
            "description_bien",
            "duree",
            "loyer",
            "depot_garantie",
        ],
        "recommended_clauses": [
            "charges",
            "entretien_reparations",
            "sous_location",
            "resiliation",
            "etat_des_lieux",
            "assurance",
            "renouvellement",
            "juridiction_competente",
        ],
        "search_queries": [
            "obligations bailleur locataire",
            "résiliation bail préavis",
            "dépôt de garantie location",
        ],
    },
    "prestation_service": {
        "label_fr": "Contrat de prestation de service",
        "label_ar": "عقد تقديم خدمات",
        "mandatory_clauses": [
            "identite_parties",
            "objet_prestation",
            "duree",
            "prix_modalites_paiement",
        ],
        "recommended_clauses": [
            "obligations_prestataire",
            "obligations_client",
            "delais_execution",
            "confidentialite",
            "propriete_intellectuelle",
            "responsabilite",
            "force_majeure",
            "resiliation",
            "penalites",
            "juridiction_competente",
        ],
        "search_queries": [
            "obligations prestataire de service",
            "responsabilité contractuelle prestation",
        ],
    },
    "societe": {
        "label_fr": "Pacte d'associés / Statuts de société",
        "label_ar": "عقد تأسيس شركة",
        "mandatory_clauses": [
            "identite_associes",
            "forme_juridique",
            "denomination_sociale",
            "siege_social",
            "objet_social",
            "capital_social",
            "apports",
            "duree_societe",
        ],
        "recommended_clauses": [
            "repartition_parts",
            "gerance",
            "assemblees_generales",
            "cession_parts",
            "clause_agrement",
            "dissolution",
            "non_concurrence",
            "juridiction_competente",
        ],
        "search_queries": [
            "statuts société commerciale code sociétés",
            "obligations gérant société à responsabilité limitée",
            "capital social apports associés",
        ],
    },
    "autre": {
        "label_fr": "Autre type de contrat",
        "label_ar": "عقد آخر",
        "mandatory_clauses": [
            "identite_parties",
            "objet",
        ],
        "recommended_clauses": [
            "duree",
            "prix",
            "responsabilite",
            "resiliation",
            "force_majeure",
            "confidentialite",
            "juridiction_competente",
        ],
        "search_queries": [
            "obligations contractuelles droit tunisien",
            "clauses essentielles contrat",
        ],
    },
}

CLAUSE_LABELS = {
    "identite_parties": "Identité des parties",
    "objet": "Objet du contrat",
    "duree": "Durée du contrat",
    "remuneration": "Rémunération / Salaire",
    "prix_paiement": "Prix et modalités de paiement",
    "prix_modalites_paiement": "Prix et modalités de paiement",
    "prix": "Prix",
    "horaires_travail": "Horaires de travail",
    "periode_essai": "Période d'essai",
    "lieu_travail": "Lieu de travail",
    "confidentialite": "Clause de confidentialité",
    "non_concurrence": "Clause de non-concurrence",
    "preavis": "Préavis de rupture",
    "conges": "Congés et absences",
    "securite_sociale": "Sécurité sociale et couverture",
    "formation": "Formation professionnelle",
    "force_majeure": "Force majeure",
    "responsabilite": "Responsabilité et limitation",
    "garantie": "Garantie",
    "resiliation": "Résiliation / Rupture anticipée",
    "rupture_anticipee": "Rupture anticipée",
    "livraison": "Livraison et réception",
    "penalites_retard": "Pénalités de retard",
    "penalites": "Pénalités",
    "propriete_intellectuelle": "Propriété intellectuelle",
    "juridiction_competente": "Juridiction compétente",
    "loi_applicable": "Loi applicable",
    "loyer": "Loyer",
    "depot_garantie": "Dépôt de garantie",
    "description_bien": "Description du bien",
    "charges": "Charges et frais",
    "entretien_reparations": "Entretien et réparations",
    "sous_location": "Sous-location",
    "etat_des_lieux": "État des lieux",
    "assurance": "Assurance",
    "renouvellement": "Renouvellement",
    "objet_prestation": "Objet de la prestation",
    "obligations_prestataire": "Obligations du prestataire",
    "obligations_client": "Obligations du client",
    "delais_execution": "Délais d'exécution",
    "identite_associes": "Identité des associés",
    "forme_juridique": "Forme juridique",
    "denomination_sociale": "Dénomination sociale",
    "siege_social": "Siège social",
    "objet_social": "Objet social",
    "capital_social": "Capital social",
    "apports": "Apports des associés",
    "duree_societe": "Durée de la société",
    "repartition_parts": "Répartition des parts",
    "gerance": "Gérance et direction",
    "assemblees_generales": "Assemblées générales",
    "cession_parts": "Cession de parts",
    "clause_agrement": "Clause d'agrément",
    "dissolution": "Dissolution et liquidation",
}


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return str(uuid.uuid4())


def _scoped_query(
    base: dict,
    organization_id: str | None = None,
) -> dict:
    if organization_id:
        base["organization_id"] = organization_id
    return base


def _strip_code_fences(text: str) -> str:
    """Supprime les clôtures ``` markdown autour du JSON."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```", 1)[1]
        if text.startswith("json"):
            text = text[4:]
        # Supprimer la clôture finale
        if "```" in text:
            text = text.rsplit("```", 1)[0]
        text = text.strip()
    return text


def _safe_json_parse(text: str, fallback=None):
    """Parse JSON depuis une réponse LLM, avec nettoyage."""
    cleaned = _strip_code_fences(text)
    try:
        return json.loads(cleaned)
    except (json.JSONDecodeError, ValueError):
        pass

    # Essayer chaque candidat JSON (dernier array/objet le plus probable)
    for pattern in (r'\[[\s\S]*\]', r'\{[\s\S]*\}'):
        # Chercher toutes les occurrences, tester chacune
        for m in reversed(list(re.finditer(pattern, cleaned))):
            try:
                return json.loads(m.group())
            except (json.JSONDecodeError, ValueError):
                continue

    logger.warning("Impossible de parser JSON LLM: %.200s", cleaned)
    return fallback


def _analysis_to_dict(doc: dict) -> dict:
    """Sérialise un document MongoDB en dict API-friendly."""
    return {
        "id": doc.get("id"),
        "document_id": doc.get("document_id"),
        "organization_id": doc.get("organization_id"),
        "status": doc.get("status"),
        "contract_type": doc.get("contract_type"),
        "contract_type_label": doc.get("contract_type_label"),
        "language": doc.get("language"),
        "parties": doc.get("parties") or [],
        "summary": doc.get("summary"),
        "score": doc.get("score"),
        "score_category": doc.get("score_category"),
        "score_breakdown": doc.get("score_breakdown"),
        "findings": doc.get("findings") or [],
        "findings_summary": doc.get("findings_summary"),
        "missing_clauses": doc.get("missing_clauses") or [],
        "recommendations": doc.get("recommendations") or [],
        "legal_sources": doc.get("legal_sources") or [],
        "total_chunks_analyzed": doc.get("total_chunks_analyzed", 0),
        "analysis_duration_ms": doc.get("analysis_duration_ms"),
        "llm_model": doc.get("llm_model"),
        "created_at": doc.get("created_at"),
        "updated_at": doc.get("updated_at"),
        "error_message": doc.get("error_message"),
    }


# ─────────────────────────────────────────────────────────────
# CRUD
# ─────────────────────────────────────────────────────────────

async def create_analysis(
    db,
    document_id: str,
    organization_id: str | None = None,
    language_override: str | None = None,
    contract_type_override: str | None = None,
) -> dict:
    """Crée un enregistrement d'analyse et lance le pipeline en arrière-plan."""
    coll = _collection("contract_analyses")

    # Vérifier si une analyse est déjà en cours
    existing = await coll.find_one(
        _scoped_query({"document_id": document_id}, organization_id)
    )
    if existing and existing.get("status") == "analyzing":
        return _analysis_to_dict(existing)

    now = _now()
    settings = get_settings()
    analysis_id = _new_id()
    analysis = {
        "id": analysis_id,
        "document_id": document_id,
        "organization_id": organization_id,
        "status": "analyzing",
        "contract_type": contract_type_override,
        "contract_type_label": None,
        "language": language_override,
        "parties": [],
        "summary": None,
        "score": None,
        "score_category": None,
        "score_breakdown": None,
        "findings": [],
        "findings_summary": None,
        "missing_clauses": [],
        "recommendations": [],
        "legal_sources": [],
        "total_chunks_analyzed": 0,
        "analysis_duration_ms": None,
        "llm_model": settings.llm_model,
        "created_at": now,
        "updated_at": now,
        "error_message": None,
    }

    # Remplacement atomique pour éviter la race condition sur le unique index document_id
    await coll.replace_one(
        {"document_id": document_id},
        analysis,
        upsert=True,
    )
    logger.info("Analyse contrat créée: %s pour doc %s", analysis["id"], document_id)

    # Lancer le pipeline en arrière-plan
    task = asyncio.create_task(
        _run_analysis(
            analysis_id=analysis["id"],
            document_id=document_id,
            organization_id=organization_id,
            language_override=language_override,
            contract_type_override=contract_type_override,
        ),
        name=f"contract-analysis-{analysis['id']}",
    )
    # Log les erreurs non gérées pour éviter les "Task exception was never retrieved"
    task.add_done_callback(lambda t: t.exception() if not t.cancelled() and t.exception() else None)

    return _analysis_to_dict(analysis)


async def get_analysis(
    analysis_id: str,
    organization_id: str | None = None,
) -> dict | None:
    doc = await _collection("contract_analyses").find_one(
        _scoped_query({"id": analysis_id}, organization_id)
    )
    return _analysis_to_dict(doc) if doc else None


async def get_analysis_by_document(
    document_id: str,
    organization_id: str | None = None,
) -> dict | None:
    doc = await _collection("contract_analyses").find_one(
        _scoped_query({"document_id": document_id}, organization_id)
    )
    return _analysis_to_dict(doc) if doc else None


async def list_analyses(
    organization_id: str | None = None,
    skip: int = 0,
    limit: int = 20,
) -> tuple[list[dict], int]:
    query = _scoped_query({}, organization_id)
    coll = _collection("contract_analyses")
    total = await coll.count_documents(query)
    cursor = coll.find(query).sort("created_at", -1).skip(skip).limit(limit)
    analyses = [_analysis_to_dict(doc) async for doc in cursor]
    return analyses, total


async def delete_analysis(
    analysis_id: str,
    organization_id: str | None = None,
) -> bool:
    result = await _collection("contract_analyses").delete_one(
        _scoped_query({"id": analysis_id}, organization_id)
    )
    return result.deleted_count > 0


async def delete_analysis_by_document(
    document_id: str,
    organization_id: str | None = None,
) -> bool:
    result = await _collection("contract_analyses").delete_one(
        _scoped_query({"document_id": document_id}, organization_id)
    )
    return result.deleted_count > 0


# ─────────────────────────────────────────────────────────────
# Pipeline principal (arrière-plan)
# ─────────────────────────────────────────────────────────────

async def _run_analysis(
    analysis_id: str,
    document_id: str,
    organization_id: str | None = None,
    language_override: str | None = None,
    contract_type_override: str | None = None,
) -> None:
    """Exécute le pipeline complet d'analyse en 4 passes."""
    coll = _collection("contract_analyses")
    start_time = time.monotonic()

    try:
        # ── Charger les pages nettoyées ──
        cleaned_cursor = (
            _collection("document_cleaned_texts")
            .find({"document_id": document_id})
            .sort("page_number", 1)
        )
        cleaned_pages = await cleaned_cursor.to_list(length=5000)

        if not cleaned_pages:
            raise ValueError(f"Aucune page nettoyée trouvée pour le document {document_id}")

        # ── Charger les chunks ──
        chunk_cursor = (
            _collection("chunks")
            .find({"document_id": document_id})
            .sort("metadata.chunk_index", 1)
        )
        chunks = await chunk_cursor.to_list(length=5000)

        # ── Passe 1 : Détection du type de contrat ──
        logger.info("Analyse %s — Passe 1 : détection type contrat", analysis_id)
        pass1_result = await _pass1_detect_contract_type(
            cleaned_pages,
            language_override=language_override,
            contract_type_override=contract_type_override,
        )

        contract_type = pass1_result.get("contract_type", "autre")
        language = pass1_result.get("language", "fr")
        type_config = CONTRACT_TYPES.get(contract_type, CONTRACT_TYPES["autre"])

        await coll.update_one(
            {"id": analysis_id},
            {"$set": {
                "contract_type": contract_type,
                "contract_type_label": type_config.get("label_fr"),
                "language": language,
                "parties": pass1_result.get("parties", []),
                "summary": pass1_result.get("summary"),
                "updated_at": _now(),
            }},
        )

        # ── Passe 2 : Analyse des chunks (risques, failles) ──
        logger.info("Analyse %s — Passe 2 : analyse %d chunks", analysis_id, len(chunks))
        all_findings, detected_clauses = await _pass2_analyze_chunks(
            chunks, contract_type, language,
        )

        # ── Passe 3 : Clauses manquantes (RAG-grounded) ──
        logger.info("Analyse %s — Passe 3 : clauses manquantes", analysis_id)
        missing_clauses, legal_sources = await _pass3_detect_missing_clauses(
            detected_clauses, contract_type, language, organization_id,
        )

        # ── Passe 4 : Score + Recommandations ──
        logger.info("Analyse %s — Passe 4 : score et recommandations", analysis_id)
        score_result = _pass4_compute_score(all_findings, missing_clauses)

        recommendations = await _generate_recommendations(
            all_findings, missing_clauses, contract_type, language,
        )

        # ── Résumé des findings ──
        findings_summary = {
            "critical": sum(1 for f in all_findings if f.get("severity") == "critical"),
            "major": sum(1 for f in all_findings if f.get("severity") == "major"),
            "minor": sum(1 for f in all_findings if f.get("severity") == "minor"),
            "total": len(all_findings),
        }

        # Avertissement si l'analyse n'a rien trouvé du tout (possible erreur LLM)
        if not all_findings and not missing_clauses and len(chunks) > 2:
            logger.warning(
                "Analyse %s : aucun finding ni clause manquante détectés sur %d chunks — "
                "vérifier la qualité du LLM",
                analysis_id, len(chunks),
            )

        elapsed_ms = int((time.monotonic() - start_time) * 1000)

        # ── Sauvegarder le résultat final ──
        await coll.update_one(
            {"id": analysis_id},
            {"$set": {
                "status": "completed",
                "findings": all_findings,
                "findings_summary": findings_summary,
                "missing_clauses": missing_clauses,
                "score": score_result["score"],
                "score_category": score_result["category"],
                "score_breakdown": score_result["breakdown"],
                "recommendations": recommendations,
                "legal_sources": legal_sources,
                "total_chunks_analyzed": len(chunks),
                "analysis_duration_ms": elapsed_ms,
                "updated_at": _now(),
            }},
        )

        logger.info(
            "Analyse %s terminée : score=%d (%s), %d findings, %d clauses manquantes, %dms",
            analysis_id,
            score_result["score"],
            score_result["category"],
            len(all_findings),
            len(missing_clauses),
            elapsed_ms,
        )

    except asyncio.CancelledError:
        logger.warning("Analyse %s annulée (shutdown ou cancel)", analysis_id)
        await coll.update_one(
            {"id": analysis_id},
            {"$set": {
                "status": "failed",
                "error_message": "Analyse annulée",
                "analysis_duration_ms": int((time.monotonic() - start_time) * 1000),
                "updated_at": _now(),
            }},
        )
        raise  # Re-raise CancelledError per asyncio convention
    except Exception as exc:
        logger.error("Analyse %s échouée: %s", analysis_id, exc, exc_info=True)
        elapsed_ms = int((time.monotonic() - start_time) * 1000)
        await coll.update_one(
            {"id": analysis_id},
            {"$set": {
                "status": "failed",
                "error_message": "Erreur interne lors de l'analyse",
                "analysis_duration_ms": elapsed_ms,
                "updated_at": _now(),
            }},
        )


# ─────────────────────────────────────────────────────────────
# Passe 1 — Détection type de contrat
# ─────────────────────────────────────────────────────────────

async def _pass1_detect_contract_type(
    cleaned_pages: list[dict],
    language_override: str | None = None,
    contract_type_override: str | None = None,
) -> dict:
    """Analyse le début du contrat pour identifier type, parties, résumé."""
    # Prendre les 3 premières pages (~3000 chars)
    page_texts = []
    total_chars = 0
    for page in cleaned_pages[:5]:
        text = page.get("cleaned_text", "")
        page_texts.append(text)
        total_chars += len(text)
        if total_chars > 3000:
            break

    combined_text = "\n\n".join(page_texts)[:4000]

    if contract_type_override:
        # L'utilisateur a précisé le type — on analyse juste parties et résumé
        type_instruction = f'Le type de contrat est déjà identifié : "{contract_type_override}". Retournez ce type tel quel.'
    else:
        types_list = ", ".join(CONTRACT_TYPES.keys())
        type_instruction = f"Identifiez le type de contrat parmi : {types_list}."

    settings = get_settings()
    from app.services.llm_service import call_ollama

    response = await call_ollama(
        model=settings.llm_model,
        messages=[
            {
                "role": "system",
                "content": (
                    "Vous êtes un expert juridique tunisien. "
                    "Analysez le début de ce contrat et retournez UNIQUEMENT du JSON valide, sans texte avant ou après."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"{type_instruction}\n\n"
                    f"Texte du contrat :\n---\n{combined_text}\n---\n\n"
                    "Retournez un objet JSON avec cette structure exacte :\n"
                    "{\n"
                    '  "contract_type": "type parmi la liste ci-dessus",\n'
                    '  "language": "fr ou ar",\n'
                    '  "parties": ["Partie A (nom/description)", "Partie B (nom/description)"],\n'
                    '  "summary": "Résumé du contrat en 2-3 phrases"\n'
                    "}"
                ),
            },
        ],
        temperature=0.1,
        base_url=settings.llm_base_url,
    )

    result = _safe_json_parse(response, fallback={})
    if not isinstance(result, dict):
        result = {}

    contract_type = contract_type_override or result.get("contract_type", "autre")
    if contract_type not in CONTRACT_TYPES:
        contract_type = "autre"

    return {
        "contract_type": contract_type,
        "language": language_override or result.get("language", "fr"),
        "parties": result.get("parties", []),
        "summary": result.get("summary", ""),
    }


# ─────────────────────────────────────────────────────────────
# Passe 2 — Analyse clause par clause
# ─────────────────────────────────────────────────────────────

async def _pass2_analyze_chunks(
    chunks: list[dict],
    contract_type: str,
    language: str,
) -> tuple[list[dict], list[str]]:
    """Analyse chaque chunk pour trouver risques, failles, ambiguïtés.

    Retourne (findings, detected_clauses).
    """
    if not chunks:
        return [], []

    settings = get_settings()
    type_config = CONTRACT_TYPES.get(contract_type, CONTRACT_TYPES["autre"])
    type_label = type_config["label_fr"]

    all_findings: list[dict] = []
    detected_clauses: list[str] = []

    # Traiter par batchs de 3 pour paralléliser
    batch_size = 3
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        tasks = [
            _analyze_single_chunk(chunk, contract_type, type_label, language, settings)
            for chunk in batch
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        failed_in_batch = 0
        for chunk, result in zip(batch, results):
            if isinstance(result, Exception):
                logger.warning("Échec analyse chunk %s: %s", chunk.get("id"), result)
                failed_in_batch += 1
                continue
            findings, clauses = result
            all_findings.extend(findings)
            detected_clauses.extend(clauses)

        # Circuit breaker : si tout un batch échoue, le LLM est probablement down
        if failed_in_batch == len(batch) and len(batch) > 0:
            logger.error("Batch entier échoué — arrêt anticipé de l'analyse des chunks")
            break

    # Dédupliquer les clauses détectées en préservant l'ordre
    detected_clauses = list(dict.fromkeys(detected_clauses))

    return all_findings, detected_clauses


async def _analyze_single_chunk(
    chunk: dict,
    contract_type: str,
    type_label: str,
    language: str,
    settings,
) -> tuple[list[dict], list[str]]:
    """Analyse un seul chunk via LLM."""
    from app.services.llm_service import call_ollama

    chunk_text = chunk.get("text", "")
    if len(chunk_text) < 30:
        return [], []

    # Tronquer à 2500 chars pour laisser de la place au prompt
    chunk_text = chunk_text[:2500]

    chunk_id = chunk.get("id", "")
    page = chunk.get("metadata", {}).get("page", 0)

    response = await call_ollama(
        model=settings.llm_model,
        messages=[
            {
                "role": "system",
                "content": (
                    f"Vous êtes un expert juridique tunisien. "
                    f"Analysez cet extrait d'un {type_label}. "
                    "Identifiez les problèmes juridiques et retournez UNIQUEMENT du JSON valide."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Extrait du contrat :\n---\n{chunk_text}\n---\n\n"
                    "Analysez cet extrait et retournez un objet JSON :\n"
                    "{\n"
                    '  "findings": [\n'
                    "    {\n"
                    '      "category": "risk|legal_flaw|ambiguity",\n'
                    '      "severity": "critical|major|minor",\n'
                    '      "title": "Titre court du problème",\n'
                    '      "description": "Description détaillée du risque ou de la faille",\n'
                    '      "clause_reference": "Référence à la clause concernée dans le contrat",\n'
                    '      "recommendation": "Modification suggérée"\n'
                    "    }\n"
                    "  ],\n"
                    '  "detected_clauses": ["liste des thèmes de clauses présents dans cet extrait"]\n'
                    "}\n\n"
                    "Catégories de problèmes :\n"
                    "- risk : clause abusive, déséquilibre, engagement excessif, risque financier\n"
                    "- legal_flaw : non-conformité au droit tunisien, formulation juridiquement invalide\n"
                    "- ambiguity : formulation vague, imprécise, source de litige potentiel\n\n"
                    "Si aucun problème, retournez {\"findings\": [], \"detected_clauses\": [...]}"
                ),
            },
        ],
        temperature=0.1,
        base_url=settings.llm_base_url,
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
            "id": _new_id(),
            "category": category,
            "severity": severity,
            "title": str(f.get("title", "")).strip()[:200],
            "description": str(f.get("description", "")).strip()[:500],
            "clause_reference": str(f.get("clause_reference", "")).strip()[:200] or None,
            "legal_reference": str(f.get("legal_reference", "")).strip()[:200] or None,
            "recommendation": str(f.get("recommendation", "")).strip()[:500],
            "page_numbers": [page] if page else [],
            "chunk_ids": [chunk_id] if chunk_id else [],
        })

    detected = [str(c).strip().lower() for c in parsed.get("detected_clauses", []) if c and str(c).strip()]

    return findings, detected


# ─────────────────────────────────────────────────────────────
# Passe 3 — Clauses manquantes (RAG-grounded)
# ─────────────────────────────────────────────────────────────

async def _pass3_detect_missing_clauses(
    detected_clauses: list[str],
    contract_type: str,
    language: str,
    organization_id: str | None = None,
) -> tuple[list[dict], list[dict]]:
    """Détecte les clauses manquantes en comparant aux attendues + RAG.

    Retourne (missing_clauses, legal_sources).
    """
    type_config = CONTRACT_TYPES.get(contract_type, CONTRACT_TYPES["autre"])
    all_expected = type_config["mandatory_clauses"] + type_config["recommended_clauses"]
    mandatory_set = set(type_config["mandatory_clauses"])

    # ── RAG : chercher les références juridiques ──
    legal_sources: list[dict] = []
    rag_context = ""

    try:
        from app.services.search_service import semantic_search
        from app.database import mongo_db

        search_queries = type_config.get("search_queries", [])
        for query in search_queries[:3]:
            results = await semantic_search(
                mongo_db,
                query=query,
                top_k=3,
                organization_id=organization_id,
            )
            for r in results:
                source = {
                    "text": r.get("text", "")[:300],
                    "source": r.get("metadata", {}).get("source", ""),
                    "page": r.get("metadata", {}).get("page"),
                    "article": r.get("metadata", {}).get("source_article"),
                }
                legal_sources.append(source)
                rag_context += f"\n- {source['text'][:200]}"

    except Exception as exc:
        logger.warning(
            "RAG search pour clauses manquantes échoué: %s — "
            "l'analyse des clauses manquantes se fera sans contexte juridique",
            exc,
        )

    # ── LLM : identifier les clauses manquantes ──
    settings = get_settings()
    from app.services.llm_service import call_ollama

    detected_str = ", ".join(detected_clauses) if detected_clauses else "aucune clause détectée"
    expected_labels = [CLAUSE_LABELS.get(c, c) for c in all_expected]
    expected_str = ", ".join(expected_labels)

    response = await call_ollama(
        model=settings.llm_model,
        messages=[
            {
                "role": "system",
                "content": (
                    f"Vous êtes un expert juridique tunisien spécialisé dans les {type_config['label_fr']}s. "
                    "Retournez UNIQUEMENT du JSON valide."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Un {type_config['label_fr']} a été analysé.\n\n"
                    f"Clauses détectées dans le contrat : {detected_str}\n\n"
                    f"Clauses normalement attendues pour ce type de contrat : {expected_str}\n\n"
                    f"Références juridiques du droit tunisien :{rag_context}\n\n"
                    "Identifiez les clauses manquantes importantes. "
                    "Retournez un array JSON :\n"
                    "[\n"
                    "  {\n"
                    '    "clause_name": "Nom de la clause manquante",\n'
                    '    "importance": "mandatory ou recommended",\n'
                    '    "legal_basis": "Article X, Code Y (si applicable)",\n'
                    '    "risk_if_missing": "Conséquence de l\'absence de cette clause"\n'
                    "  }\n"
                    "]\n"
                    "Si aucune clause ne manque, retournez []."
                ),
            },
        ],
        temperature=0.1,
        base_url=settings.llm_base_url,
    )

    raw_missing = _safe_json_parse(response, fallback=[])
    if not isinstance(raw_missing, list):
        raw_missing = []

    missing_clauses = []
    for item in raw_missing:
        if not isinstance(item, dict):
            continue
        importance = item.get("importance", "recommended")
        if importance not in ("mandatory", "recommended"):
            importance = "recommended"

        missing_clauses.append({
            "id": _new_id(),
            "clause_name": str(item.get("clause_name", "")).strip()[:200],
            "importance": importance,
            "legal_basis": str(item.get("legal_basis", "")).strip()[:300] or None,
            "risk_if_missing": str(item.get("risk_if_missing", "")).strip()[:500],
        })

    return missing_clauses, legal_sources


# ─────────────────────────────────────────────────────────────
# Passe 4 — Calcul du score (déterministe)
# ─────────────────────────────────────────────────────────────

def _pass4_compute_score(
    findings: list[dict],
    missing_clauses: list[dict],
) -> dict:
    """Calcul déterministe du score 0-100."""
    score = 100
    breakdown = {
        "critical_risks": 0,
        "major_risks": 0,
        "minor_risks": 0,
        "missing_mandatory": 0,
        "missing_recommended": 0,
    }

    # Risques
    critical_count = sum(1 for f in findings if f.get("severity") == "critical")
    major_count = sum(1 for f in findings if f.get("severity") == "major")
    minor_count = sum(1 for f in findings if f.get("severity") == "minor")

    critical_penalty = min(critical_count * 15, 45)
    major_penalty = min(major_count * 8, 32)
    minor_penalty = min(minor_count * 3, 15)

    breakdown["critical_risks"] = -critical_penalty
    breakdown["major_risks"] = -major_penalty
    breakdown["minor_risks"] = -minor_penalty

    # Clauses manquantes
    mandatory_missing = sum(1 for c in missing_clauses if c.get("importance") == "mandatory")
    recommended_missing = sum(1 for c in missing_clauses if c.get("importance") == "recommended")

    mandatory_penalty = min(mandatory_missing * 10, 40)
    recommended_penalty = min(recommended_missing * 3, 12)

    breakdown["missing_mandatory"] = -mandatory_penalty
    breakdown["missing_recommended"] = -recommended_penalty

    # Score final
    total_penalty = (
        critical_penalty + major_penalty + minor_penalty
        + mandatory_penalty + recommended_penalty
    )
    score = max(0, 100 - total_penalty)

    # Catégorie
    if score >= 90:
        category = "excellent"
    elif score >= 70:
        category = "bon"
    elif score >= 50:
        category = "attention"
    else:
        category = "critique"

    return {
        "score": score,
        "category": category,
        "breakdown": breakdown,
    }


# ─────────────────────────────────────────────────────────────
# Recommandations (LLM)
# ─────────────────────────────────────────────────────────────

async def _generate_recommendations(
    findings: list[dict],
    missing_clauses: list[dict],
    contract_type: str,
    language: str,
) -> list[str]:
    """Génère des recommandations lisibles à partir des findings."""
    if not findings and not missing_clauses:
        return ["Le contrat semble complet et ne présente pas de risques majeurs identifiés."]

    settings = get_settings()
    from app.services.llm_service import call_ollama

    type_config = CONTRACT_TYPES.get(contract_type, CONTRACT_TYPES["autre"])

    # Résumé des problèmes pour le prompt
    problems_summary = []
    for f in findings[:10]:
        problems_summary.append(
            f"- [{f['severity'].upper()}] {f['title']}: {f['description'][:100]}"
        )
    for mc in missing_clauses[:8]:
        problems_summary.append(
            f"- [MANQUANT {'OBLIGATOIRE' if mc['importance'] == 'mandatory' else 'RECOMMANDÉ'}] "
            f"{mc['clause_name']}"
        )

    problems_text = "\n".join(problems_summary)
    lang_instruction = "en arabe" if language == "ar" else "en français"

    response = await call_ollama(
        model=settings.llm_model,
        messages=[
            {
                "role": "system",
                "content": (
                    f"Vous êtes un conseiller juridique tunisien spécialisé dans les {type_config['label_fr']}s. "
                    f"Donnez des recommandations pratiques et concrètes {lang_instruction}."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Voici les problèmes identifiés dans un {type_config['label_fr']} :\n\n"
                    f"{problems_text}\n\n"
                    "Donnez 5 à 8 recommandations concrètes pour améliorer ce contrat. "
                    "Chaque recommandation doit être une phrase complète et actionable. "
                    "Retournez UNIQUEMENT un array JSON de strings :\n"
                    '["Recommandation 1", "Recommandation 2", ...]'
                ),
            },
        ],
        temperature=0.3,
        base_url=settings.llm_base_url,
    )

    recs = _safe_json_parse(response, fallback=[])
    if isinstance(recs, list):
        return [str(r).strip() for r in recs if isinstance(r, str) and r.strip()][:10]

    # Fallback : découper la réponse texte en lignes
    lines = [
        re.sub(r'^[\s\-•*\d.)\]]+', '', l).strip()
        for l in response.split("\n")
        if l.strip()
    ]
    return [l for l in lines if len(l) > 20 and not l.startswith("{") and not l.startswith("[")][:10]
