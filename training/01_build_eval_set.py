"""
Étape 1 — Construction du dataset d'évaluation retrieval (gold standard).

Ce script :
  1. Se connecte à MongoDB (base Daleel) et exporte tous les `article_versions`
     actifs enrichis avec leur `article_key` et `loi_code` vers `articles.jsonl`.
  2. Fournit un mode interactif pour aider à annoter manuellement 30–50 questions
     juridiques avec les `article_key` pertinents (champ `positive_article_keys`).
  3. Produit `eval_set.jsonl` au format :
        {"query": str, "language": "fr|ar|en",
         "positive_article_keys": ["CT-Art-95", ...],
         "domain": "labor|corporate|data_protection|..."}

Pourquoi annoter à la main :
  - Évite le leakage entre train et eval (sinon les métriques sont biaisées).
  - Reflète les vrais besoins utilisateurs (pas seulement la distribution des
    feedbacks historiques).

Usage :
    python training/01_build_eval_set.py --export-only
    python training/01_build_eval_set.py --annotate
    python training/01_build_eval_set.py --from-feedback --limit 40

Variables d'env respectées : DALEEL_MONGODB_URL, DALEEL_MONGODB_DB_NAME.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from pymongo import MongoClient


DEFAULT_DATA_DIR = Path(__file__).parent / "data"


def _mongo_client() -> MongoClient:
    url = os.environ.get("DALEEL_MONGODB_URL", "mongodb://localhost:27017")
    return MongoClient(url)


def _mongo_db():
    name = os.environ.get("DALEEL_MONGODB_DB_NAME", "daleel")
    return _mongo_client()[name]


def export_articles(output_path: Path) -> int:
    """Export tous les `article_versions` actifs + join avec articles/lois.

    Produit un JSONL : {article_key, loi_code, text, language, heading}.
    Ce fichier sert de corpus pour indexation lors de l'évaluation.
    """
    db = _mongo_db()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Précharger lois (loi_id -> loi_code) pour éviter N requêtes
    lois = {l["id"]: l.get("code") or l.get("loi_code") for l in db["lois"].find({}, {"id": 1, "code": 1, "loi_code": 1})}
    # Précharger articles (article_id -> {article_key, loi_id})
    articles_map = {
        a["id"]: {"article_key": a.get("article_key"), "loi_id": a.get("loi_id")}
        for a in db["articles"].find({}, {"id": 1, "article_key": 1, "loi_id": 1})
    }

    count = 0
    with output_path.open("w", encoding="utf-8") as f:
        cursor = db["article_versions"].find({"status": "active"})
        for version in cursor:
            art = articles_map.get(version.get("article_id"))
            if not art or not art.get("article_key"):
                continue
            text = version.get("text") or version.get("content") or ""
            if not text.strip():
                continue
            record = {
                "article_key": art["article_key"],
                "loi_code": lois.get(art.get("loi_id")) or "UNKNOWN",
                "language": version.get("language") or "fr",
                "heading": version.get("heading") or "",
                "text": text.strip(),
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            count += 1

    print(f"[OK] {count} article_versions actifs exportés vers {output_path}")
    return count


def export_chunks(output_path: Path, min_chars: int = 80, max_chars: int = 4000) -> int:
    """Export tous les `chunks` (toutes langues, tous documents) comme corpus.

    Produit un JSONL au MÊME schéma que `export_articles` (pour compat avec 02/03/04) :
      {article_key, loi_code, language, heading, text}
    où :
      - `article_key` = chunk_id (clé unique stable)
      - `loi_code`    = filename du document source
      - `heading`     = section extraite par le chunker (si présente)

    Filtre les chunks vides, trop courts (<80 chars) ou trop longs (>4000 chars
    pour rester dans la fenêtre Qwen lors de la génération synthétique).
    """
    db = _mongo_db()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Précharger documents : id -> filename (pour identifier la source)
    docs = {d["id"]: d.get("filename") or "UNKNOWN" for d in db["documents"].find({}, {"id": 1, "filename": 1})}

    count = 0
    skipped_short = 0
    skipped_long = 0
    skipped_empty = 0
    with output_path.open("w", encoding="utf-8") as f:
        cursor = db["chunks"].find({})
        for chunk in cursor:
            text = (chunk.get("text") or "").strip()
            if not text:
                skipped_empty += 1
                continue
            if len(text) < min_chars:
                skipped_short += 1
                continue
            if len(text) > max_chars:
                skipped_long += 1
                continue
            metadata = chunk.get("metadata") or {}
            doc_id = chunk.get("document_id") or metadata.get("document_id")
            source_name = docs.get(doc_id) or metadata.get("source") or "UNKNOWN"
            record = {
                "article_key": chunk["id"],  # On réutilise le champ pour rester compat avec 02/03/04
                "loi_code": source_name,
                "language": chunk.get("language") or metadata.get("language") or "fr",
                "heading": metadata.get("section") or "",
                "text": text,
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            count += 1

    print(f"[OK] {count} chunks exportés vers {output_path}")
    print(f"     (skipped: short={skipped_short}, long={skipped_long}, empty={skipped_empty})")
    return count


def seed_from_feedback(output_path: Path, limit: int) -> int:
    """Initialise un eval set Daleel à partir de `qa_feedback` (à compléter à la main).

    ATTENTION : Cette source peut leaker dans le training set.
    Utiliser uniquement comme point de départ — valider manuellement chaque
    entrée et idéalement exclure ces questions du training set (étape 2).
    """
    db = _mongo_db()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    count = 0
    with output_path.open("w", encoding="utf-8") as f:
        cursor = db["qa_feedback"].find({}).sort("created_at", -1).limit(limit)
        for item in cursor:
            record = {
                "query": item.get("question", ""),
                "language": item.get("language") or "fr",
                "positive_article_keys": [],  # À remplir à la main
                "domain": None,
                "_source": "feedback",
                "_hint_answer": (item.get("corrected_answer") or "")[:400],
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            count += 1

    print(f"[OK] {count} questions (feedback) initialisées dans {output_path}")
    print("    -> Édite ce fichier à la main pour remplir `positive_article_keys`.")
    return count


def annotate_interactive(eval_path: Path, articles_path: Path) -> None:
    """Boucle CLI pour annoter les `positive_article_keys` de chaque query.

    Recherche lexicale simple (fallback sans modèle) pour proposer des candidats.
    """
    if not eval_path.exists():
        print(f"[ERR] {eval_path} introuvable. Lance d'abord --from-feedback ou écris le fichier.")
        sys.exit(1)
    if not articles_path.exists():
        print(f"[ERR] {articles_path} introuvable. Lance d'abord --export-only.")
        sys.exit(1)

    articles = [json.loads(line) for line in articles_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    rows = [json.loads(line) for line in eval_path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def _suggest(query: str, top: int = 10) -> list[dict]:
        q_tokens = {t.lower() for t in query.split() if len(t) > 3}
        scored = []
        for art in articles:
            body = (art.get("text") or "").lower()
            score = sum(1 for t in q_tokens if t in body)
            if score > 0:
                scored.append((score, art))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [a for _, a in scored[:top]]

    for i, row in enumerate(rows):
        if row.get("positive_article_keys"):
            continue  # Déjà annoté
        print("\n" + "=" * 80)
        print(f"[{i + 1}/{len(rows)}] {row['query']}")
        if row.get("_hint_answer"):
            print(f"    Hint: {row['_hint_answer'][:200]}...")
        suggestions = _suggest(row["query"])
        for j, s in enumerate(suggestions):
            print(f"  [{j}] {s['article_key']} ({s['loi_code']}) — {s['heading'][:80]}")
        resp = input("Indices pertinents (séparés par virgules, 's' skip, 'q' quit) : ").strip()
        if resp.lower() == "q":
            break
        if resp.lower() == "s" or not resp:
            continue
        try:
            indices = [int(x.strip()) for x in resp.split(",") if x.strip()]
            row["positive_article_keys"] = [suggestions[k]["article_key"] for k in indices if 0 <= k < len(suggestions)]
        except ValueError:
            print("    Format invalide, skip.")

    with eval_path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"\n[OK] Sauvegardé dans {eval_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Construction de l'eval set retrieval Daleel")
    parser.add_argument("--articles-out", default=str(DEFAULT_DATA_DIR / "articles.jsonl"),
                        help="Fichier de sortie pour l'export des article_versions")
    parser.add_argument("--eval-out", default=str(DEFAULT_DATA_DIR / "eval_set.jsonl"),
                        help="Fichier de sortie pour l'eval set")
    parser.add_argument("--export-only", action="store_true",
                        help="N'exporte que les articles (pas d'annotation)")
    parser.add_argument("--from-feedback", action="store_true",
                        help="Initialise l'eval set depuis qa_feedback")
    parser.add_argument("--limit", type=int, default=40,
                        help="Nombre de questions à extraire depuis feedback")
    parser.add_argument("--annotate", action="store_true",
                        help="Mode annotation interactive CLI")
    parser.add_argument("--source", choices=["articles", "chunks"], default="chunks",
                        help="Source du corpus : 'articles' (article_versions) ou 'chunks' "
                             "(défaut, couvre tous les documents). 'chunks' recommandé si "
                             "tous les documents ne sont pas segmentés en articles.")
    args = parser.parse_args()

    articles_path = Path(args.articles_out)
    eval_path = Path(args.eval_out)

    # Exporter le corpus selon la source choisie
    if args.source == "chunks":
        export_chunks(articles_path)
    else:
        export_articles(articles_path)

    if args.export_only:
        return
    if args.from_feedback and not eval_path.exists():
        seed_from_feedback(eval_path, args.limit)
    if args.annotate:
        annotate_interactive(eval_path, articles_path)


if __name__ == "__main__":
    main()
