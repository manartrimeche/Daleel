"""
Reasoning Dataset Builder — Track 2 (Classification + Extraction).

Génère un JSONL multi-tâches pour fine-tuner un classifieur (XLM-R) ou un petit
LLM en mode JSON-only.

TÂCHES COUVERTES
----------------
1. classify   → {domain, case_type, risk}
2. extract    → {parties, dates, amounts, processing_type, legal_basis_keywords}

SOURCES DE DONNÉES
------------------
A. Cas existants (collection `cases`) :
   - `domain` ← `case.matter_type`
   - `case_type` ← `case.category` ou heuristique
   - `risk` ← `case.priority` mappé (low/medium/high)
   - `parties`/`dates`/... ← extraits depuis `conversation_context`
B. Annotations manuelles dans `training/data/reasoning_curated/*.jsonl`.
C. Augmentation synthétique : paraphrases LLM (FR/AR) avec garde-fous.

SORTIE
------
- training/reasoning_train.jsonl
- training/reasoning_eval.jsonl

SCHÉMAS
-------
Classif :
  {"task": "classify", "text": "...", "language": "fr",
   "labels": {"domain": "labor", "case_type": "complaint", "risk": "medium"}}

Extraction :
  {"task": "extract", "text": "...", "language": "fr",
   "labels": {"parties": [...], "dates": [...], "amounts": [...],
              "processing_type": "...", "legal_basis_keywords": [...]}}
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import random
from collections import Counter
from pathlib import Path
from typing import Iterable

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# Référentiels de labels
# ─────────────────────────────────────────────────────────────

DOMAINS = ["labor", "data_protection", "corporate", "credit_info", "investment", "other"]
CASE_TYPES = ["question", "complaint", "incident", "data_subject_request", "audit", "other"]
RISK_LEVELS = ["low", "medium", "high"]


PRIORITY_TO_RISK = {
    "low": "low",
    "normal": "low",
    "medium": "medium",
    "high": "high",
    "critical": "high",
    "urgent": "high",
}


# ─────────────────────────────────────────────────────────────
# Source A : cas existants
# ─────────────────────────────────────────────────────────────

async def _harvest_classification_from_cases(max_cases: int) -> list[dict]:
    """Itère sur les cases en base et produit des exemples `classify`."""
    examples: list[dict] = []
    # Extension production : décommenter pour connecter la base MongoDB réelle.
    # from app.database import get_db
    # from app.services import case_service
    # db = get_db()
    # cases, _ = await case_service.list_cases(db, limit=max_cases)
    # for case in cases:
    #     text = (case.get("description") or "").strip()
    #     if not text or len(text) < 30:
    #         continue
    #     domain = case.get("matter_type", "other")
    #     if domain not in DOMAINS:
    #         domain = "other"
    #     case_type = case.get("category", "question")
    #     if case_type not in CASE_TYPES:
    #         case_type = "other"
    #     risk = PRIORITY_TO_RISK.get(case.get("priority", "low"), "low")
    #     examples.append({
    #         "task": "classify",
    #         "text": text,
    #         "language": case.get("language", "fr"),
    #         "labels": {"domain": domain, "case_type": case_type, "risk": risk},
    #     })
    logger.info("classify-from-cases : %d examples (stub)", len(examples))
    return examples


async def _harvest_extraction_from_cases(max_cases: int) -> list[dict]:
    """Génère des exemples `extract` à partir de `conversation_context`."""
    examples: list[dict] = []
    # Extension : itérer les cases, lire conversation_context (parties, dates, amounts)
    # et produire l'objet structuré d'extraction.
    logger.info("extract-from-cases : %d examples (stub)", len(examples))
    return examples


# ─────────────────────────────────────────────────────────────
# Source B : exemples curés
# ─────────────────────────────────────────────────────────────

def _load_curated(curated_dir: Path) -> list[dict]:
    if not curated_dir.exists():
        logger.info("Curated dir absent : %s", curated_dir)
        return []
    rows: list[dict] = []
    for f in curated_dir.glob("*.jsonl"):
        with f.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    try:
                        rows.append(json.loads(line))
                    except json.JSONDecodeError:
                        logger.warning("Bad JSON in %s", f)
    logger.info("Loaded %d curated reasoning examples", len(rows))
    return rows


# ─────────────────────────────────────────────────────────────
# Validation
# ─────────────────────────────────────────────────────────────

def _validate_classify(ex: dict) -> bool:
    if ex.get("task") != "classify":
        return False
    labels = ex.get("labels") or {}
    return (
        labels.get("domain") in DOMAINS
        and labels.get("case_type") in CASE_TYPES
        and labels.get("risk") in RISK_LEVELS
        and isinstance(ex.get("text"), str)
        and len(ex["text"]) >= 20
    )


def _validate_extract(ex: dict) -> bool:
    if ex.get("task") != "extract":
        return False
    labels = ex.get("labels") or {}
    expected = {"parties", "dates", "amounts", "processing_type", "legal_basis_keywords"}
    return expected.issubset(labels.keys()) and isinstance(ex.get("text"), str)


def _validate(ex: dict) -> bool:
    task = ex.get("task")
    if task == "classify":
        return _validate_classify(ex)
    if task == "extract":
        return _validate_extract(ex)
    return False


# ─────────────────────────────────────────────────────────────
# Audit de distribution (anti-biais)
# ─────────────────────────────────────────────────────────────

def _audit_distribution(examples: list[dict]) -> None:
    domains = Counter()
    case_types = Counter()
    risks = Counter()
    langs = Counter()
    for ex in examples:
        if ex.get("task") == "classify":
            lbl = ex["labels"]
            domains[lbl["domain"]] += 1
            case_types[lbl["case_type"]] += 1
            risks[lbl["risk"]] += 1
        langs[ex.get("language", "?")] += 1
    logger.info("Domains    : %s", dict(domains))
    logger.info("Case types : %s", dict(case_types))
    logger.info("Risks      : %s", dict(risks))
    logger.info("Languages  : %s", dict(langs))


# ─────────────────────────────────────────────────────────────
# Split + write
# ─────────────────────────────────────────────────────────────

def _split(examples: list[dict], eval_ratio: float, seed: int = 42) -> tuple[list[dict], list[dict]]:
    rnd = random.Random(seed)
    shuffled = list(examples)
    rnd.shuffle(shuffled)
    cut = int(len(shuffled) * (1 - eval_ratio))
    return shuffled[:cut], shuffled[cut:]


def _write_jsonl(path: Path, rows: Iterable[dict]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            n += 1
    return n


async def build_dataset(out_dir: Path, max_cases: int, eval_ratio: float) -> None:
    curated_dir = out_dir / "data" / "reasoning_curated"

    src_a1 = await _harvest_classification_from_cases(max_cases)
    src_a2 = await _harvest_extraction_from_cases(max_cases)
    src_b = _load_curated(curated_dir)

    raw = src_a1 + src_a2 + src_b
    valid = [ex for ex in raw if _validate(ex)]
    logger.info("Valid examples : %d / %d", len(valid), len(raw))

    _audit_distribution(valid)

    train, eval_ = _split(valid, eval_ratio)
    n_train = _write_jsonl(out_dir / "reasoning_train.jsonl", train)
    n_eval = _write_jsonl(out_dir / "reasoning_eval.jsonl", eval_)
    logger.info("Wrote %d train / %d eval to %s", n_train, n_eval, out_dir)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--out-dir", type=Path, default=Path("training"))
    p.add_argument("--max-cases", type=int, default=2000)
    p.add_argument("--eval-ratio", type=float, default=0.15)
    p.add_argument("--log-level", default="INFO")
    args = p.parse_args()

    logging.basicConfig(level=args.log_level, format="%(asctime)s [%(levelname)s] %(message)s")
    asyncio.run(build_dataset(args.out_dir, args.max_cases, args.eval_ratio))


if __name__ == "__main__":
    main()
