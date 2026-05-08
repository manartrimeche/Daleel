"""
Étape 4 — Fine-tuning de l'embedding model + éval comparative avant/après.

Modèle : `sentence-transformers/paraphrase-multilingual-mpnet-base-v2` (768d).
Loss   : `MultipleNegativesRankingLoss` (state-of-the-art pour les paires
         (query, positive) sans négatifs explicites — les autres exemples du
         batch servent de négatifs).

Bonnes pratiques appliquées :
  - Learning rate faible (2e-5) pour préserver les capacités multilingues.
  - Warmup 10 % des steps.
  - Batch size élevé si possible (32 ou 64) — MNR exploite tout le batch
    comme pool de négatifs, donc batch_size ↑ = plus de négatifs = meilleur
    apprentissage contrastif.
  - Peu d'epochs (1 à 3) pour éviter le catastrophic forgetting.

Interprétation des résultats :
  - Améliorations typiques sur données domain-specific : +5 à +15 points de
    Recall@5 / MRR@10 après 1–3 epochs.
  - Si les métriques *se dégradent* → soit le dataset est trop bruité (paires
    synthétiques de mauvaise qualité), soit trop peu de données, soit le LR
    est trop élevé.
  - Un signe de trop-apprentissage : Recall@1 explose mais Recall@20 stagne
    → le modèle a mémorisé les queries plutôt que le domaine.

Usage :
    python training/04_finetune_embeddings.py \\
        --train training/data/train_set.jsonl \\
        --eval training/data/eval_set.jsonl \\
        --articles training/data/articles.jsonl \\
        --output-dir training/models/daleel-embedding-finetuned \\
        --epochs 2 --batch-size 32
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# On réutilise l'évaluateur de l'étape 3
sys.path.insert(0, str(Path(__file__).parent))
from importlib import import_module

_eval_module = import_module("03_evaluate_retrieval")
evaluate = _eval_module.evaluate
load_jsonl = _eval_module.load_jsonl


def _detect_device() -> str:
    # NOTE: PyTorch dans ce venv est compilé sans CUDA.
    # On force CPU ; corriger le venv pour CUDA permettrait un speedup 5-10x.
    import torch  # type: ignore
    if torch.cuda.is_available():
        print("[WARN] torch.cuda.is_available()==True mais le venv utilise torch CPU-only ; forçage CPU", flush=True)
    return "cpu"


def finetune(
    base_model: str,
    train_pairs: list[dict],
    output_dir: Path,
    epochs: int,
    batch_size: int,
    learning_rate: float,
    warmup_ratio: float,
) -> str:
    """Fine-tune avec MNR loss (training loop PyTorch manuel).

    Bypass complet de `model.fit()` / `datasets` / `pyarrow` qui provoquent
    un segfault sur cet environnement Windows.
    """
    import math
    import random

    import torch
    import torch.nn.functional as F
    from sentence_transformers import SentenceTransformer
    from torch.optim import AdamW
    from tqdm import tqdm
    from transformers import get_linear_schedule_with_warmup

    device = _detect_device()
    print(f"[train] Modèle de base : {base_model}", flush=True)
    print(f"[train] Device : {device}", flush=True)
    print(f"[train] Paires d'entraînement : {len(train_pairs)}", flush=True)

    # Filtrage
    examples: list[tuple[str, str]] = []
    for p in train_pairs:
        q = (p.get("query") or "").strip()
        pos = (p.get("positive") or "").strip()
        if len(q) < 3 or len(pos) < 20:
            continue
        examples.append((q, pos))

    if not examples:
        raise ValueError("Aucun exemple d'entraînement valide après filtrage.")

    print(f"[train] {len(examples)} exemples valides | batch={batch_size}", flush=True)

    if device == "cpu":
        n_threads = os.cpu_count() or 1
        torch.set_num_threads(n_threads)
        torch.set_num_interop_threads(min(4, n_threads))
        est_s = (len(examples) / batch_size) * epochs * 6.0
        est_m = int(est_s // 60) or 1
        print(
            f"[train] CPU-only — {n_threads} threads | "
            f"estimation ~{est_m} min/epoch (variable)",
            flush=True,
        )

    # Chargement CPU puis déplacement manuel sur CUDA.
    # Le constructeur SentenceTransformer(..., device='cuda') provoque un
    # segfault sur cet environnement Windows ; le charger sur CPU puis
    # .to('cuda') contourne le problème.
    model = SentenceTransformer(base_model, device='cpu')
    if device == 'cuda':
        try:
            model = model.to(device)
            print(f"[train] Modèle déplacé sur {device}", flush=True)
        except Exception as exc:
            print(f"[train] Échec déplacement CUDA ({exc}), entraînement sur CPU", flush=True)
            device = 'cpu'
    model.train()

    optimizer = AdamW(model.parameters(), lr=learning_rate)
    steps_per_epoch = math.ceil(len(examples) / batch_size)
    total_steps = steps_per_epoch * epochs
    warmup_steps = math.ceil(total_steps * warmup_ratio)
    scheduler = get_linear_schedule_with_warmup(
        optimizer, num_warmup_steps=warmup_steps, num_training_steps=total_steps
    )

    print(
        f"[train] Epochs={epochs} | steps/epoch={steps_per_epoch} | "
        f"total_steps={total_steps} | warmup={warmup_steps}",
        flush=True,
    )

    # MNR loss manuelle (CosineSimilarity → CrossEntropy sur batch)
    def _mnr_loss(a: torch.Tensor, b: torch.Tensor, scale: float = 20.0) -> torch.Tensor:
        scores = torch.matmul(a, b.T) * scale  # (batch, batch)
        labels = torch.arange(len(scores), device=scores.device)
        return torch.nn.CrossEntropyLoss()(scores, labels)

    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        for epoch in range(epochs):
            random.shuffle(examples)
            epoch_loss = 0.0
            num_batches = 0

            pbar = tqdm(
                range(0, len(examples), batch_size),
                desc=f"Epoch {epoch + 1}/{epochs}",
                unit="batch",
            )
            for i in pbar:
                batch = examples[i : i + batch_size]
                if len(batch) < 2:
                    continue  # MNR a besoin d'au moins 2 négatifs

                queries = [b[0] for b in batch]
                positives = [b[1] for b in batch]

                # Tokenize + forward (gradient activé)
                q_features = model.tokenize(queries)
                p_features = model.tokenize(positives)

                for k in q_features:
                    q_features[k] = q_features[k].to(device)
                    p_features[k] = p_features[k].to(device)

                q_out = model(q_features)
                p_out = model(p_features)

                q_emb = F.normalize(q_out["sentence_embedding"], p=2, dim=1)
                p_emb = F.normalize(p_out["sentence_embedding"], p=2, dim=1)

                loss = _mnr_loss(q_emb, p_emb)

                optimizer.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                optimizer.step()
                scheduler.step()

                epoch_loss += loss.item()
                num_batches += 1
                pbar.set_postfix({"loss": f"{loss.item():.4f}"})

            avg_loss = epoch_loss / max(num_batches, 1)
            print(
                f"[train] Epoch {epoch + 1}/{epochs} terminée — "
                f"loss moyenne = {avg_loss:.4f}",
                flush=True,
            )
    except KeyboardInterrupt:
        print("\n[INTERRUPT] Sauvegarde du checkpoint intermédiaire...", flush=True)
        ckpt = output_dir / "_interrupted"
        ckpt.mkdir(parents=True, exist_ok=True)
        model.save(str(ckpt))
        print(f"[INTERRUPT] Checkpoint sauvegardé dans {ckpt}", flush=True)
        return str(ckpt)

    # Sauvegarde au format SentenceTransformer natif
    model.save(str(output_dir))
    print(f"[train] Modèle sauvegardé dans {output_dir}", flush=True)
    return str(output_dir)


def _diff_metrics(before: dict, after: dict) -> dict:
    """Calcule delta(after - before) pour chaque métrique agrégée."""
    out = {}
    for key in before.get("summary", {}):
        b = before["summary"].get(key, 0.0)
        a = after["summary"].get(key, 0.0)
        out[key] = round(a - b, 4)
    return out


def print_comparison(before: dict, after: dict) -> None:
    print("\n" + "=" * 72)
    print("  Comparaison baseline vs fine-tune")
    print("=" * 72)
    summary_b = before["summary"]
    summary_a = after["summary"]
    keys_sorted = sorted(summary_b.keys(), key=lambda k: (k.split("@")[0], int(k.split("@")[1])))
    print(f"  {'Metrique':<14} {'Baseline':>10} {'Fine-tune':>10} {'Delta':>10}")
    print(f"  {'-' * 14} {'-' * 10} {'-' * 10} {'-' * 10}")
    for k in keys_sorted:
        b = summary_b.get(k, 0.0)
        a = summary_a.get(k, 0.0)
        delta = a - b
        marker = " +" if delta > 0.001 else (" -" if delta < -0.001 else "  ")
        print(f"  {k:<14} {b:>10.4f} {a:>10.4f} {delta:>+10.4f}{marker}")

    print("\n  Par langue :")
    langs = sorted(set(list(before.get("summary_by_language", {}).keys()) + list(after.get("summary_by_language", {}).keys())))
    for lang in langs:
        b_l = before.get("summary_by_language", {}).get(lang, {})
        a_l = after.get("summary_by_language", {}).get(lang, {})
        print(f"  [{lang}] recall@5: {b_l.get('recall@5', 0):.4f} -> {a_l.get('recall@5', 0):.4f}  "
              f"| mrr@10: {b_l.get('mrr@10', 0):.4f} -> {a_l.get('mrr@10', 0):.4f}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Fine-tune embedding model + évaluation avant/après")
    parser.add_argument("--train", required=True, type=Path, help="train_set.jsonl (output étape 2)")
    parser.add_argument("--eval", required=True, type=Path, help="eval_set.jsonl (output étape 1)")
    parser.add_argument("--articles", required=True, type=Path, help="articles.jsonl (corpus)")
    parser.add_argument("--base-model", default="sentence-transformers/paraphrase-multilingual-mpnet-base-v2")
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--epochs", type=int, default=2)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--learning-rate", type=float, default=2e-5)
    parser.add_argument("--warmup-ratio", type=float, default=0.1)
    parser.add_argument("--eval-batch-size", type=int, default=64)
    parser.add_argument("--ks", nargs="+", type=int, default=[1, 5, 10, 20])
    parser.add_argument("--skip-baseline", action="store_true",
                        help="Sauter l'éval baseline (si déjà mesurée)")
    parser.add_argument("--metrics-dir", type=Path, default=None,
                        help="Dossier où sauvegarder les JSON de métriques (par défaut output-dir)")
    parser.add_argument("--max-train-pairs", type=int, default=0,
                        help="Limiter le train set à N paires (0 = illimité, utile pour test rapide)")
    parser.add_argument("--quick-test", action="store_true",
                        help="Mode rapide : 100 paires, 1 epoch, batch=4 (overwrite les défauts)")
    args = parser.parse_args()

    if args.quick_test:
        args.max_train_pairs = args.max_train_pairs or 100
        args.epochs = 1
        args.batch_size = 4
        print(f"[quick-test] Mode rapide : {args.max_train_pairs} paires, 1 epoch, batch=4", flush=True)

    articles = load_jsonl(args.articles)
    eval_rows = load_jsonl(args.eval)
    train_pairs = load_jsonl(args.train)

    if args.max_train_pairs:
        train_pairs = train_pairs[: args.max_train_pairs]
        print(f"[setup] Train set limité à {len(train_pairs)} paires", flush=True)

    metrics_dir = args.metrics_dir or args.output_dir
    metrics_dir.mkdir(parents=True, exist_ok=True)

    # ── Baseline ────────────────────────────────────────────────────
    baseline_path = metrics_dir / "baseline_metrics.json"
    if args.skip_baseline and baseline_path.exists():
        print(f"[skip] Baseline déjà présent : {baseline_path}")
        before = json.loads(baseline_path.read_text(encoding="utf-8"))
    else:
        print("\n### 1/3 — Évaluation BASELINE ###")
        before = evaluate(
            args.base_model, articles, eval_rows,
            ks=tuple(args.ks), batch_size=args.eval_batch_size,
        )
        baseline_path.write_text(json.dumps(before, ensure_ascii=False, indent=2), encoding="utf-8")

    # ── Fine-tuning ─────────────────────────────────────────────────
    print("\n### 2/3 — Fine-tuning ###", flush=True)
    try:
        model_path = finetune(
            base_model=args.base_model,
            train_pairs=train_pairs,
            output_dir=args.output_dir,
            epochs=args.epochs,
            batch_size=args.batch_size,
            learning_rate=args.learning_rate,
            warmup_ratio=args.warmup_ratio,
        )
    except Exception as exc:
        import traceback
        print(f"\n[FATAL] Fine-tuning échoué : {type(exc).__name__}: {exc}", flush=True)
        traceback.print_exc()
        sys.exit(1)

    # ── Évaluation fine-tuné ────────────────────────────────────────
    print("\n### 3/3 — Évaluation FINE-TUNED ###")
    after = evaluate(
        model_path, articles, eval_rows,
        ks=tuple(args.ks), batch_size=args.eval_batch_size,
    )
    finetuned_path = metrics_dir / "finetuned_metrics.json"
    finetuned_path.write_text(json.dumps(after, ensure_ascii=False, indent=2), encoding="utf-8")

    # ── Comparaison ────────────────────────────────────────────────
    print_comparison(before, after)
    diff = _diff_metrics(before, after)
    (metrics_dir / "comparison.json").write_text(
        json.dumps({"delta": diff, "before": before["summary"], "after": after["summary"]},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\n[OK] Modèle : {model_path}")
    print(f"[OK] Métriques : {baseline_path}, {finetuned_path}, {metrics_dir / 'comparison.json'}")


if __name__ == "__main__":
    main()
