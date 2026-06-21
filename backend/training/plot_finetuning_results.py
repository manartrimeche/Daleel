"""Génère la figure de comparaison baseline vs fine-tuné (Recall/MRR/nDCG).

Lit directement backend/training/data/baseline_v2_metrics.json et
finetuned_v2_metrics.json, puis produit fig_5_4_finetuning_resultats.png
avec les valeurs réelles. Aucune valeur n'est codée en dur.

Usage:
    python backend/training/plot_finetuning_results.py
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

DATA_DIR = Path(__file__).parent / "data"
OUT_PATH = Path(__file__).parents[2] / "captures" / "fig_5_4_finetuning_resultats.png"

# Fichiers de métriques: éval propre (50 questions, sans fuite) par défaut
BASELINE_FILE = "baseline_clean_metrics.json"
FINETUNED_FILE = "finetuned_clean_metrics.json"

# Métriques affichées et clés correspondantes dans le JSON "summary"
METRICS = [
    ("Recall@1", "recall@1"),
    ("Recall@5", "recall@5"),
    ("Recall@10", "recall@10"),
    ("MRR@10", "mrr@10"),
    ("nDCG@5", "ndcg@5"),
    ("nDCG@10", "ndcg@10"),
]


def load_summary(name: str) -> dict[str, float]:
    with open(DATA_DIR / name, encoding="utf-8") as f:
        return json.load(f)["summary"]


def main() -> None:
    baseline = load_summary(BASELINE_FILE)
    finetuned = load_summary(FINETUNED_FILE)

    labels = [m[0] for m in METRICS]
    base_vals = [baseline[m[1]] for m in METRICS]
    ft_vals = [finetuned[m[1]] for m in METRICS]

    x = np.arange(len(labels))
    width = 0.38

    fig, ax = plt.subplots(figsize=(9, 5))
    bars_base = ax.bar(x - width / 2, base_vals, width,
                       label="Baseline (MPNet pré-entraîné)", color="#9aa7b8")
    bars_ft = ax.bar(x + width / 2, ft_vals, width,
                     label="Daleel (MPNet fine-tuné)", color="#2563eb")

    ax.set_ylabel("Score")
    ax.set_title("Performance du retrieval avant et après fine-tuning "
                 "(50 requêtes gold)")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 1.0)
    ax.legend(loc="upper right")
    ax.grid(axis="y", linestyle="--", alpha=0.4)

    # Annoter chaque barre avec sa valeur
    for bars in (bars_base, bars_ft):
        for b in bars:
            h = b.get_height()
            ax.annotate(f"{h:.2f}", xy=(b.get_x() + b.get_width() / 2, h),
                        xytext=(0, 3), textcoords="offset points",
                        ha="center", va="bottom", fontsize=8)

    fig.tight_layout()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_PATH, dpi=200, bbox_inches="tight")
    print(f"Figure enregistrée: {OUT_PATH}")
    print("Valeurs utilisées:")
    for lbl, b, f in zip(labels, base_vals, ft_vals):
        rel = (f - b) / b * 100 if b else 0.0
        print(f"  {lbl:10s} baseline={b:.4f}  finetuned={f:.4f}  ({rel:+.0f}%)")


if __name__ == "__main__":
    main()
