"""
Style Dataset Builder — Track 1 (Response Style & Format Fine-Tuning).

Assemble un dataset JSONL pour fine-tuner un petit LLM sur le **format de
reponse advisor Daleel** (7 sections fixes).

Sources de données combinées :
  1. Cas existants en base : `cases` + `findings` + `actions` + `messages`
     → on reconstruit (input, output) en passant par
       `advisor_response_composer.compose_from_orchestration_result`.
  2. Exemples curés à la main dans `training/data/style_curated/*.json`.
  3. Exemples synthétiques générés par le LLM courant via
     `llm_service.ask_*`, puis nettoyés (filtre quality_guard).

Sortie :
  - training/style_train.jsonl
  - training/style_eval.jsonl  (split 90/10 par défaut)

Schéma JSONL d'une ligne :
{
  "input": {
    "language": "fr|ar|en",
    "user_question": "...",
    "extracted_facts": {...},
    "legal_context": [{"article_ref": "...", "text": "..."}, ...],
    "findings": [...],
    "actions": [...],
    "draft_answer": "..."         # brouillon LLM avant style-format
  },
  "output": "## Ce que j'ai compris\n...\n## Informations manquantes\n..."
}

USAGE
-----
    python training/style_dataset_builder.py \
        --out-dir training \
        --max-cases 500 \
        --eval-ratio 0.1 \
        --pseudonymize

NOTE PFE
--------
Ce script est un SQUELETTE. Les fonctions marquées `# TODO` doivent être
remplies au cas par cas selon les données réellement disponibles.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import random
import re
from pathlib import Path
from typing import Any, Iterable

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# Pseudonymisation (RGPD / INPDP)
# ─────────────────────────────────────────────────────────────

_EMAIL_RE = re.compile(r"[\w\.-]+@[\w\.-]+\.\w+")
_PHONE_RE = re.compile(r"\+?\d[\d\s\-\.]{6,}\d")
_CIN_RE = re.compile(r"\b\d{8}\b")


def pseudonymize(text: str) -> str:
    """Remplace identifiants personnels par des placeholders avant export.

    À étendre : noms propres (NER), raisons sociales, IBANs, adresses.
    """
    if not text:
        return text
    text = _EMAIL_RE.sub("<EMAIL>", text)
    text = _PHONE_RE.sub("<PHONE>", text)
    text = _CIN_RE.sub("<CIN>", text)
    return text


# ─────────────────────────────────────────────────────────────
# Source 1 : cas existants en base
# ─────────────────────────────────────────────────────────────

async def _harvest_from_existing_cases(max_cases: int, pseudonymize_flag: bool) -> list[dict]:
    """Itère sur les cas en base et reconstruit (input, output) pour chaque cas
    qui a déjà été traité par l'orchestrator + advisor_response_composer.

    Stratégie :
      - récupérer les cases avec status in {"analyzed", "completed"}
      - pour chacun : findings, actions, conversation_context
      - rejouer `compose_from_orchestration_result` pour récupérer la version
        markdown (= "output" cible du fine-tuning)
      - extraire `draft_answer` depuis le dernier message assistant brut

    Returns: liste de dicts {"input": {...}, "output": "..."}
    """
    examples: list[dict] = []
    # TODO: connexion DB + extraction réelle. Squelette ici.
    # from app.database import get_db
    # from app.services import case_service, advisor_response_composer
    # db = get_db()
    # cases, _ = await case_service.list_cases(db, status="analyzed", limit=max_cases)
    # for case in cases:
    #     inp = await _build_input_payload(db, case)
    #     resp = await advisor_response_composer.compose_from_orchestration_result(
    #         case_id=case["id"], orchestration_result=..., language=inp["language"]
    #     )
    #     out_md = resp.to_markdown() if hasattr(resp, "to_markdown") else str(resp)
    #     if pseudonymize_flag:
    #         out_md = pseudonymize(out_md)
    #     examples.append({"input": inp, "output": out_md})
    logger.info("harvest_from_existing_cases: %d examples (stub)", len(examples))
    return examples


async def _build_input_payload(db: Any, case: dict) -> dict:
    """Construit le champ `input` à partir d'un case + ses findings/actions."""
    # TODO : récupérer findings, actions, last user message, retrieved chunks
    return {
        "language": case.get("language", "fr"),
        "user_question": case.get("description", ""),
        "extracted_facts": case.get("conversation_context", {}),
        "legal_context": [],
        "findings": [],
        "actions": [],
        "draft_answer": "",
    }


# ─────────────────────────────────────────────────────────────
# Source 2 : exemples curés à la main
# ─────────────────────────────────────────────────────────────

def _load_curated_examples(curated_dir: Path) -> list[dict]:
    """Charge des fichiers JSON du dossier `training/data/style_curated/`.

    Chaque fichier doit avoir la structure {input, output} attendue.
    """
    if not curated_dir.exists():
        logger.info("Curated dir absent : %s", curated_dir)
        return []
    examples: list[dict] = []
    for f in curated_dir.glob("*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            if isinstance(data, list):
                examples.extend(data)
            elif isinstance(data, dict):
                examples.append(data)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Skip curated %s : %s", f, exc)
    logger.info("Loaded %d curated examples", len(examples))
    return examples


# ─────────────────────────────────────────────────────────────
# Source 3 : synthèse LLM (à utiliser avec parcimonie)
# ─────────────────────────────────────────────────────────────

async def _generate_synthetic_examples(seed_questions: list[str], n: int) -> list[dict]:
    """Génère n exemples synthétiques en faisant tourner le pipeline complet
    (RAG + orchestrator + composer) sur des questions d'amorce.

    À filtrer ensuite par `quality_guard_service` pour éliminer les sorties
    avec articles non supportés.
    """
    # TODO : appeler llm_service.ask_auto + quality_guard_service.audit_and_guard
    # pour chaque seed_question. Garder uniquement les sorties "guard_passed".
    return []


# ─────────────────────────────────────────────────────────────
# Validation et split
# ─────────────────────────────────────────────────────────────

REQUIRED_SECTIONS_FR = [
    "Ce que j'ai compris",
    "Informations manquantes",
    "Contexte légal",
    "Analyse",
    "Actions recommandées",
    "Preuves",
    "revue humaine",
]


def _is_well_formed(example: dict) -> bool:
    """Vérifie que la sortie contient bien les 7 sections (heuristique FR)."""
    out = example.get("output", "")
    if not isinstance(out, str) or len(out) < 200:
        return False
    hits = sum(1 for s in REQUIRED_SECTIONS_FR if s.lower() in out.lower())
    return hits >= 5  # tolérant pour AR/EN


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


# ─────────────────────────────────────────────────────────────
# Orchestration principale
# ─────────────────────────────────────────────────────────────

async def build_dataset(out_dir: Path, max_cases: int, eval_ratio: float, pseudonymize_flag: bool) -> None:
    curated_dir = out_dir / "data" / "style_curated"

    src1 = await _harvest_from_existing_cases(max_cases, pseudonymize_flag)
    src2 = _load_curated_examples(curated_dir)
    src3 = await _generate_synthetic_examples(seed_questions=[], n=0)

    all_examples = [e for e in (src1 + src2 + src3) if _is_well_formed(e)]
    logger.info("Total well-formed examples : %d", len(all_examples))

    if not all_examples:
        logger.warning("Aucun exemple — seuls les fichiers vides seront créés.")

    train, eval_ = _split(all_examples, eval_ratio)
    n_train = _write_jsonl(out_dir / "style_train.jsonl", train)
    n_eval = _write_jsonl(out_dir / "style_eval.jsonl", eval_)
    logger.info("Wrote %d train / %d eval to %s", n_train, n_eval, out_dir)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--out-dir", type=Path, default=Path("training"))
    p.add_argument("--max-cases", type=int, default=500)
    p.add_argument("--eval-ratio", type=float, default=0.1)
    p.add_argument("--pseudonymize", action="store_true")
    p.add_argument("--log-level", default="INFO")
    args = p.parse_args()

    logging.basicConfig(level=args.log_level, format="%(asctime)s [%(levelname)s] %(message)s")
    asyncio.run(build_dataset(args.out_dir, args.max_cases, args.eval_ratio, args.pseudonymize))


if __name__ == "__main__":
    main()
