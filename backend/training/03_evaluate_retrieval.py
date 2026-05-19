"""
Étape 3 — Évaluation du retrieval (Recall@k, MRR@k, nDCG@k).

Utilisable :
  - en ligne de commande pour benchmark baseline ou fine-tuné,
  - comme module importable depuis 04_finetune_embeddings.py (fonction `evaluate`).

Protocole :
  1. Charger le corpus d'articles (output de 01_build_eval_set.py).
  2. Charger le modèle SentenceTransformer (HF name OU chemin local).
  3. Encoder tous les articles → matrice de vecteurs normalisés.
  4. Pour chaque query de l'eval set : encoder, cosine similarity sur la matrice,
     tri descendant, comparer aux `positive_article_keys` gold.
  5. Calculer Recall@k, MRR@k, nDCG@k, produire un rapport JSON.

Pourquoi pas FAISS ici ?
  - FAISS a un overhead pour N petit (~quelques milliers d'articles) et l'eval
    n'a pas de contraintes de perf. NumPy cosine direct = plus simple,
    exactement reproductible, et sans dépendance FAISS.
  - En prod, Daleel utilise bien FAISS via `app/services/faiss_index.py`.

Usage :
    python training/03_evaluate_retrieval.py \\
        --articles training/data/articles.jsonl \\
        --eval training/data/eval_set.jsonl \\
        --model sentence-transformers/paraphrase-multilingual-mpnet-base-v2 \\
        --output training/data/baseline_metrics.json
"""

from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path
from typing import Any, Optional

import numpy as np


# ── Métriques ──────────────────────────────────────────────────────────────


def recall_at_k(ranked_keys: list[str], gold_keys: set[str], k: int) -> float:
    if not gold_keys:
        return 0.0
    hits = sum(1 for key in ranked_keys[:k] if key in gold_keys)
    # On mesure "au moins 1 positive retrouvée" (hit-rate) ET ratio-based :
    # ici on renvoie hit/|gold| plafonné à 1 (≈ recall standard).
    return min(1.0, hits / len(gold_keys))


def hit_at_k(ranked_keys: list[str], gold_keys: set[str], k: int) -> float:
    return 1.0 if any(key in gold_keys for key in ranked_keys[:k]) else 0.0


def mrr_at_k(ranked_keys: list[str], gold_keys: set[str], k: int) -> float:
    for rank, key in enumerate(ranked_keys[:k], 1):
        if key in gold_keys:
            return 1.0 / rank
    return 0.0


def ndcg_at_k(ranked_keys: list[str], gold_keys: set[str], k: int) -> float:
    dcg = 0.0
    for rank, key in enumerate(ranked_keys[:k], 1):
        if key in gold_keys:
            dcg += 1.0 / math.log2(rank + 1)
    ideal_hits = min(len(gold_keys), k)
    idcg = sum(1.0 / math.log2(rank + 1) for rank in range(1, ideal_hits + 1))
    return dcg / idcg if idcg > 0 else 0.0


# ── Évaluation ─────────────────────────────────────────────────────────────


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _detect_device() -> str:
    try:
        import torch  # type: ignore

        return "cuda" if torch.cuda.is_available() else "cpu"
    except ImportError:
        return "cpu"


def evaluate(
    model_name_or_path: str,
    articles: list[dict],
    eval_rows: list[dict],
    ks: tuple[int, ...] = (1, 5, 10, 20),
    batch_size: int = 64,
    device: Optional[str] = None,
) -> dict[str, Any]:
    """Évalue un modèle SentenceTransformer sur un eval set.

    Args:
        model_name_or_path : HF id ou chemin local vers un modèle ST.
        articles : liste {article_key, text, ...}.
        eval_rows : liste {query, positive_article_keys: [...]}.

    Returns:
        Dict avec métriques agrégées + métriques par langue + détails par query.
    """
    from sentence_transformers import SentenceTransformer  # import tardif

    if device is None:
        device = _detect_device()
    print(f"[eval] Modèle: {model_name_or_path} | device={device}")

    model = SentenceTransformer(model_name_or_path, device=device)
    dim = model.get_sentence_embedding_dimension()
    print(f"[eval] Dimension des vecteurs : {dim}")

    # Filtrer les eval rows sans gold
    eval_rows = [r for r in eval_rows if r.get("positive_article_keys")]
    if not eval_rows:
        raise ValueError("Eval set vide ou sans `positive_article_keys` annotés.")

    # Encoder le corpus une seule fois
    keys = [a["article_key"] for a in articles]
    texts = [a["text"] for a in articles]
    t0 = time.perf_counter()
    doc_emb = model.encode(
        texts, batch_size=batch_size, normalize_embeddings=True,
        show_progress_bar=True, convert_to_numpy=True,
    )
    t_corpus = time.perf_counter() - t0

    # Encoder les queries
    queries = [r["query"] for r in eval_rows]
    t1 = time.perf_counter()
    q_emb = model.encode(
        queries, batch_size=batch_size, normalize_embeddings=True,
        show_progress_bar=False, convert_to_numpy=True,
    )
    t_queries = time.perf_counter() - t1

    # Similarités cosine (vecteurs normalisés → produit scalaire)
    sims = q_emb @ doc_emb.T  # (N_queries, N_docs)

    per_query: list[dict] = []
    agg: dict[str, list[float]] = {f"recall@{k}": [] for k in ks}
    agg.update({f"hit@{k}": [] for k in ks})
    agg.update({f"mrr@{k}": [] for k in ks})
    agg.update({f"ndcg@{k}": [] for k in ks})

    per_lang: dict[str, dict[str, list[float]]] = {}

    max_k = max(ks)
    for i, row in enumerate(eval_rows):
        scores = sims[i]
        top_idx = np.argsort(-scores)[:max_k]
        ranked_keys = [keys[j] for j in top_idx]
        gold = set(row["positive_article_keys"])
        lang = row.get("language") or "unknown"

        row_metrics = {}
        for k in ks:
            r = recall_at_k(ranked_keys, gold, k)
            h = hit_at_k(ranked_keys, gold, k)
            m = mrr_at_k(ranked_keys, gold, k)
            n = ndcg_at_k(ranked_keys, gold, k)
            row_metrics[f"recall@{k}"] = r
            row_metrics[f"hit@{k}"] = h
            row_metrics[f"mrr@{k}"] = m
            row_metrics[f"ndcg@{k}"] = n
            agg[f"recall@{k}"].append(r)
            agg[f"hit@{k}"].append(h)
            agg[f"mrr@{k}"].append(m)
            agg[f"ndcg@{k}"].append(n)

        lang_bucket = per_lang.setdefault(lang, {})
        for mk, mv in row_metrics.items():
            lang_bucket.setdefault(mk, []).append(mv)

        per_query.append({
            "query": row["query"],
            "language": lang,
            "gold": sorted(gold),
            "top5": ranked_keys[:5],
            "metrics": row_metrics,
        })

    summary = {k: round(float(np.mean(v)), 4) if v else 0.0 for k, v in agg.items()}
    summary_by_lang = {
        lang: {k: round(float(np.mean(v)), 4) for k, v in d.items() if v}
        for lang, d in per_lang.items()
    }

    print("\n=== Résultats globaux ===")
    for k in ks:
        print(
            f"  k={k:<3} | recall={summary[f'recall@{k}']:.4f} "
            f"| hit={summary[f'hit@{k}']:.4f} "
            f"| mrr={summary[f'mrr@{k}']:.4f} "
            f"| ndcg={summary[f'ndcg@{k}']:.4f}"
        )

    # Sanity checks
    if summary[f"recall@{min(ks)}"] >= 0.95:
        print("[WARN] Recall@1 >= 0.95 — l'eval set semble trop facile ou leaké.")
    if summary[f"recall@{max(ks)}"] < 0.10:
        print("[WARN] Recall@max très bas — vérifier l'alignement des `article_key` entre eval et articles.")

    return {
        "model": model_name_or_path,
        "dimension": dim,
        "device": device,
        "n_articles": len(articles),
        "n_queries": len(eval_rows),
        "timings": {
            "encode_corpus_s": round(t_corpus, 2),
            "encode_queries_s": round(t_queries, 2),
        },
        "summary": summary,
        "summary_by_language": summary_by_lang,
        "per_query": per_query,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Évalue un modèle d'embedding sur l'eval set Daleel")
    parser.add_argument("--articles", required=True, type=Path)
    parser.add_argument("--eval", required=True, type=Path)
    parser.add_argument("--model", default="sentence-transformers/paraphrase-multilingual-mpnet-base-v2")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--ks", nargs="+", type=int, default=[1, 5, 10, 20])
    parser.add_argument("--device", default=None, help="cuda | cpu (auto-détecté si vide)")
    args = parser.parse_args()

    articles = load_jsonl(args.articles)
    eval_rows = load_jsonl(args.eval)
    result = evaluate(
        args.model, articles, eval_rows,
        ks=tuple(args.ks), batch_size=args.batch_size, device=args.device,
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[OK] Rapport sauvegardé dans {args.output}")


if __name__ == "__main__":
    main()
