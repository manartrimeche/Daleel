"""
Reasoning Fine-Tuning — Track 2.

Classifieur multi-tâches XLM-RoBERTa-base :
  - 3 têtes softmax indépendantes : domain, case_type, risk
  - léger (~270M params), rapide (<50ms/inférence CPU), Apache-2.0

USAGE
-----
    python training/reasoning_finetune.py \
        --base-model xlm-roberta-base \
        --train-file training/reasoning_train.jsonl \
        --eval-file training/reasoning_eval.jsonl \
        --output-dir training/models/daleel-reasoning-v1 \
        --epochs 4 --batch-size 16 --lr 2e-5
"""
from __future__ import annotations

import argparse
import json
import logging
import math
import os
from pathlib import Path

import torch
from torch import nn
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModel, get_linear_schedule_with_warmup
from tqdm import tqdm

logger = logging.getLogger(__name__)


DOMAINS = ["labor", "data_protection", "corporate", "credit_info", "investment", "other"]
CASE_TYPES = ["question", "complaint", "incident", "data_subject_request", "audit", "other"]
RISK_LEVELS = ["low", "medium", "high"]

DOMAIN2ID = {d: i for i, d in enumerate(DOMAINS)}
CASETYPE2ID = {c: i for i, c in enumerate(CASE_TYPES)}
RISK2ID = {r: i for i, r in enumerate(RISK_LEVELS)}


def _load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


# ─────────────────────────────────────────────────────────────
# Multi-Head Classifier Model
# ─────────────────────────────────────────────────────────────

class MultiHeadClassifier(nn.Module):
    """Trois têtes softmax au-dessus d'un encoder XLM-R partagé."""

    def __init__(self, base_model_name: str):
        super().__init__()
        self.encoder = AutoModel.from_pretrained(base_model_name)
        hid = self.encoder.config.hidden_size
        self.head_domain = nn.Linear(hid, len(DOMAINS))
        self.head_case = nn.Linear(hid, len(CASE_TYPES))
        self.head_risk = nn.Linear(hid, len(RISK_LEVELS))

    def forward(self, input_ids, attention_mask):
        out = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
        pooled = out.last_hidden_state[:, 0]  # [CLS]
        return self.head_domain(pooled), self.head_case(pooled), self.head_risk(pooled)


class ClassifyDataset(Dataset):
    def __init__(self, rows: list[dict], tokenizer, max_length: int = 256):
        self.rows = rows
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, i: int) -> dict:
        r = self.rows[i]
        enc = self.tokenizer(
            r["text"],
            truncation=True,
            max_length=self.max_length,
            padding="max_length",
            return_tensors="pt",
        )
        return {
            "input_ids": enc["input_ids"][0],
            "attention_mask": enc["attention_mask"][0],
            "y_dom": DOMAIN2ID.get(r["labels"]["domain"], DOMAIN2ID["other"]),
            "y_case": CASETYPE2ID.get(r["labels"]["case_type"], CASETYPE2ID["other"]),
            "y_risk": RISK2ID.get(r["labels"]["risk"], RISK2ID["low"]),
        }


# ─────────────────────────────────────────────────────────────
# Evaluation
# ─────────────────────────────────────────────────────────────

@torch.no_grad()
def evaluate_model(
    model: MultiHeadClassifier,
    loader: DataLoader,
    device: str,
) -> dict[str, float]:
    """Compute per-head accuracy on eval set."""
    model.eval()
    correct = {"domain": 0, "case_type": 0, "risk": 0}
    total = 0

    for batch in loader:
        ids = batch["input_ids"].to(device)
        mask = batch["attention_mask"].to(device)
        logits_dom, logits_case, logits_risk = model(ids, mask)

        correct["domain"] += (logits_dom.argmax(dim=-1) == batch["y_dom"].clone().detach().to(device)).sum().item()
        correct["case_type"] += (logits_case.argmax(dim=-1) == batch["y_case"].clone().detach().to(device)).sum().item()
        correct["risk"] += (logits_risk.argmax(dim=-1) == batch["y_risk"].clone().detach().to(device)).sum().item()
        total += len(batch["input_ids"])

    return {k: round(v / max(total, 1), 4) for k, v in correct.items()}


# ─────────────────────────────────────────────────────────────
# Training
# ─────────────────────────────────────────────────────────────

def train(args: argparse.Namespace) -> None:
    """Entraîne le classifieur multi-tâches XLM-R."""

    train_data = [ex for ex in _load_jsonl(args.train_file) if ex.get("task") == "classify"]
    eval_data = (
        [ex for ex in _load_jsonl(args.eval_file) if ex.get("task") == "classify"]
        if args.eval_file and args.eval_file.exists()
        else []
    )
    logger.info("Train : %d / Eval : %d", len(train_data), len(eval_data))

    if not train_data:
        logger.error("Aucune donnée `classify`. Lance reasoning_dataset_builder.py d'abord.")
        return

    # Device
    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cpu":
        n_threads = os.cpu_count() or 1
        torch.set_num_threads(n_threads)
        logger.info("CPU mode — %d threads", n_threads)
    logger.info("Device : %s", device)

    # Tokenizer + Model
    logger.info("Chargement du modèle : %s", args.base_model)
    tok = AutoTokenizer.from_pretrained(args.base_model)
    model = MultiHeadClassifier(args.base_model).to(device)
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    logger.info("Paramètres entraînables : %s", f"{trainable:,}")

    # Datasets
    train_ds = ClassifyDataset(train_data, tok)
    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True, drop_last=False)
    eval_loader = None
    if eval_data:
        eval_ds = ClassifyDataset(eval_data, tok)
        eval_loader = DataLoader(eval_ds, batch_size=args.batch_size * 2)

    # Optimizer + scheduler
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)
    steps_per_epoch = math.ceil(len(train_data) / args.batch_size)
    total_steps = steps_per_epoch * args.epochs
    warmup_steps = max(1, int(total_steps * 0.1))
    scheduler = get_linear_schedule_with_warmup(
        optimizer, num_warmup_steps=warmup_steps, num_training_steps=total_steps
    )
    ce = nn.CrossEntropyLoss()

    logger.info(
        "Epochs=%d | steps/epoch=%d | total=%d | warmup=%d",
        args.epochs, steps_per_epoch, total_steps, warmup_steps,
    )

    # Training loop
    best_avg_acc = 0.0
    for epoch in range(args.epochs):
        model.train()
        epoch_loss = 0.0
        num_batches = 0

        pbar = tqdm(train_loader, desc=f"Epoch {epoch + 1}/{args.epochs}", unit="batch")
        for batch in pbar:
            ids = batch["input_ids"].to(device)
            mask = batch["attention_mask"].to(device)
            y_dom = batch["y_dom"].clone().detach().to(device)
            y_case = batch["y_case"].clone().detach().to(device)
            y_risk = batch["y_risk"].clone().detach().to(device)

            optimizer.zero_grad()
            logits_dom, logits_case, logits_risk = model(ids, mask)

            loss = (
                ce(logits_dom, y_dom)
                + ce(logits_case, y_case)
                + ce(logits_risk, y_risk)
            )
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            scheduler.step()

            epoch_loss += loss.item()
            num_batches += 1
            pbar.set_postfix({"loss": f"{loss.item():.4f}"})

        avg_loss = epoch_loss / max(num_batches, 1)
        logger.info("Epoch %d/%d — loss moyenne = %.4f", epoch + 1, args.epochs, avg_loss)

        # Eval
        if eval_loader:
            acc = evaluate_model(model, eval_loader, device)
            avg_acc = sum(acc.values()) / len(acc)
            logger.info(
                "  Eval → domain=%.2f%% case_type=%.2f%% risk=%.2f%% (avg=%.2f%%)",
                acc["domain"] * 100, acc["case_type"] * 100, acc["risk"] * 100, avg_acc * 100,
            )
            if avg_acc > best_avg_acc:
                best_avg_acc = avg_acc

    # Save
    args.output_dir.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), args.output_dir / "model.pt")
    tok.save_pretrained(args.output_dir)

    # Save labels + config
    meta = {
        "domains": DOMAINS,
        "case_types": CASE_TYPES,
        "risks": RISK_LEVELS,
        "base_model": args.base_model,
        "epochs": args.epochs,
        "train_size": len(train_data),
        "eval_size": len(eval_data),
    }
    (args.output_dir / "labels.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    logger.info("Modèle sauvegardé dans %s", args.output_dir)
    if eval_data:
        logger.info("Meilleure accuracy moyenne : %.2f%%", best_avg_acc * 100)


def main() -> None:
    p = argparse.ArgumentParser(description="Track 2 — Classifieur multi-tâches XLM-R")
    p.add_argument("--base-model", default="xlm-roberta-base")
    p.add_argument("--train-file", type=Path, default=Path("training/reasoning_train.jsonl"))
    p.add_argument("--eval-file", type=Path, default=Path("training/reasoning_eval.jsonl"))
    p.add_argument("--output-dir", type=Path, default=Path("training/models/daleel-reasoning-v1"))
    p.add_argument("--epochs", type=int, default=4)
    p.add_argument("--batch-size", type=int, default=16)
    p.add_argument("--lr", type=float, default=2e-5)
    p.add_argument("--log-level", default="INFO")
    args = p.parse_args()

    logging.basicConfig(level=args.log_level, format="%(asctime)s [%(levelname)s] %(message)s")
    train(args)


if __name__ == "__main__":
    main()
