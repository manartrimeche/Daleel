# Daleel — Embedding Fine-Tuning Pipeline

Pipeline complet pour fine-tuner le modèle d'embedding de Daleel
(`paraphrase-multilingual-mpnet-base-v2`) sur le corpus juridique tunisien,
avec benchmark avant/après.

## Plan global

| # | Script | Rôle |
|---|--------|------|
| 1 | `01_build_eval_set.py` | Exporter les `article_versions` actives + annoter un eval set (question → article_keys gold) |
| 2 | `02_build_train_set.py` | Construire des paires `(query, positive_passage)` depuis `qa_feedback` + génération synthétique via Ollama/Qwen |
| 3 | `03_evaluate_retrieval.py` | Mesurer Recall@k, MRR@k, nDCG@k d'un modèle (base ou fine-tuné) |
| 4 | `04_finetune_embeddings.py` | Fine-tuning `MultipleNegativesRankingLoss` + éval avant/après |

## Prérequis

```powershell
pip install -r training/requirements-training.txt
```

MongoDB de Daleel doit être accessible (`DALEEL_MONGODB_URL`) pour les étapes 1 et 2.
Ollama doit tourner (`http://localhost:11434`) pour la génération synthétique (étape 2, option `--synthetic`).

## Workflow recommandé

```powershell
# 1. Exporter articles + démarrer l'annotation manuelle (~30-50 Q)
python training/01_build_eval_set.py --output training/data/eval_set.jsonl

# 2. Construire le training set (feedback + synthétique)
python training/02_build_train_set.py --output training/data/train_set.jsonl --synthetic --synthetic-per-article 2

# 3. Benchmark baseline (avant fine-tuning)
python training/03_evaluate_retrieval.py --eval training/data/eval_set.jsonl --articles training/data/articles.jsonl --model sentence-transformers/paraphrase-multilingual-mpnet-base-v2 --output training/data/baseline_metrics.json

# 4. Fine-tuning + éval avant/après (automatique)
python training/04_finetune_embeddings.py --train training/data/train_set.jsonl --eval training/data/eval_set.jsonl --articles training/data/articles.jsonl --output-dir training/models/daleel-embedding-finetuned
```

## Intégration dans Daleel

Voir `INTEGRATION.md` pour :
- comment basculer l'API vers le modèle fine-tuné
- reconstruction de l'index FAISS
- stratégie de rollback
