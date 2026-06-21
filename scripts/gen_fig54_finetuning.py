# -*- coding: utf-8 -*-
"""Figure 5.4 — Comparaison des metriques de retrieval avant/apres fine-tuning.
Valeurs reelles (run v2, 30 requetes gold : 20 FR + 10 AR)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

LABELS = ["Recall@1", "Recall@5", "Recall@10", "MRR@10", "nDCG@5", "nDCG@10"]
BASE   = [0.33, 0.53, 0.70, 0.42, 0.43, 0.49]
FINE   = [0.53, 0.67, 0.67, 0.59, 0.61, 0.61]
GAIN   = ["+60%", "+25%", "-5%", "+40%", "+42%", "+26%"]  # gain relatif

GREY = "#7F7F7F"
BLUE = "#1F6FE0"
GREEN = "#2E9E2F"
RED = "#D43A2F"
INK = "#222222"
MUTED = "#555555"

x = np.arange(len(LABELS))
w = 0.38

fig, ax = plt.subplots(figsize=(13.5, 8), dpi=120)

b1 = ax.bar(x - w/2, BASE, w, label="Baseline (mpnet)", color=GREY, zorder=3)
b2 = ax.bar(x + w/2, FINE, w, label="Fine-tuné Daleel v2", color=BLUE, zorder=3)

# valeurs au-dessus des barres
for xi, v in zip(x - w/2, BASE):
    ax.text(xi, v + 0.012, f"{v:.2f}", ha="center", va="bottom", fontsize=13, color=INK)
for xi, v in zip(x + w/2, FINE):
    ax.text(xi, v + 0.012, f"{v:.2f}", ha="center", va="bottom", fontsize=13, color=INK)

# fleche + gain relatif au-dessus de la barre fine-tunee
for xi, v, g in zip(x + w/2, FINE, GAIN):
    up = not g.startswith("-")
    col = GREEN if up else RED
    arrow = "↑" if up else "↓"
    ax.text(xi, v + 0.058, f"{arrow} {g}", ha="center", va="bottom",
            fontsize=13.5, fontweight="bold", color=col)

ax.set_ylim(0, 1.0)
ax.set_yticks(np.arange(0, 1.01, 0.2))
ax.set_ylabel("Score", fontsize=15)
ax.set_xticks(x)
ax.set_xticklabels(LABELS, fontsize=14)
ax.tick_params(axis="y", labelsize=12)

ax.yaxis.grid(True, linestyle="--", linewidth=0.8, color="#CCCCCC", zorder=0)
ax.set_axisbelow(True)
for spine in ["top", "right"]:
    ax.spines[spine].set_visible(False)
ax.spines["left"].set_color("#999999")
ax.spines["bottom"].set_color("#999999")

# titre + sous-titre
fig.suptitle("Comparaison des métriques de retrieval", fontsize=22,
             fontweight="bold", color=INK, y=0.97)
ax.set_title("Baseline (mpnet) vs Fine-tuné Daleel v2 — 30 requêtes gold (20 FR + 10 AR)",
             fontsize=15, color=MUTED, pad=16)

ax.legend(loc="upper right", fontsize=13, framealpha=0.95, edgecolor="#DDDDDD")

plt.tight_layout(rect=[0, 0, 1, 0.96])
OUT = "captures/fig_5_4_finetuning_resultats_v60.png"
plt.savefig(OUT, dpi=120, bbox_inches="tight", facecolor="white")
print("OK ->", OUT)
