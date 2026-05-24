"""
Arabic Fine-Tuning — Track 3.

LoRA / PEFT fine-tuning de Qwen 2.5 pour comprendre la derja tunisienne
et répondre en arabe standard (MSA) avec le format Daleel en 7 sections.

OBJECTIF
--------
Apprendre au modèle à :
  1. Comprendre les questions en dialecte tunisien (derja)
  2. Répondre en arabe standard (fus'ha) clair et structuré
  3. Suivre le format de réponse Daleel (4 sections avec emojis)
  4. Citer correctement les articles de loi

PRÉREQUIS
---------
    pip install -r training/requirements-training.txt

USAGE
-----
    # Étape 1 : Construire le dataset
    python training/arabic_dataset_builder.py

    # Étape 2 : Fine-tuner
    python training/arabic_finetune.py \\
        --base-model Qwen/Qwen2.5-7B-Instruct \\
        --train-file training/data/arabic_train.jsonl \\
        --eval-file training/data/arabic_eval.jsonl \\
        --output-dir training/models/daleel-arabic-v1 \\
        --epochs 5 --batch-size 2 --lr 2e-4

EXPORT POUR OLLAMA
------------------
Après entraînement :
    1. Merge LoRA → base : python training/merge_lora_to_ollama.py
    2. Mettre à jour .env : DALEEL_LLM_MODEL=daleel-arabic:v1
"""
from __future__ import annotations

import argparse
import json
import logging
import os
from pathlib import Path
from typing import Any

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import LoraConfig, get_peft_model, TaskType
from datasets import Dataset
from trl import SFTTrainer, SFTConfig

import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent))
from arabic_dataset_builder import format_example_as_chat, SYSTEM_PROMPT_AR

logger = logging.getLogger(__name__)


def _load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def train(args: argparse.Namespace) -> None:
    """LoRA fine-tuning for Arabic/Derja → MSA responses."""
    train_data = _load_jsonl(args.train_file)
    eval_data = _load_jsonl(args.eval_file) if args.eval_file and args.eval_file.exists() else []

    logger.info("Train: %d examples — Eval: %d examples", len(train_data), len(eval_data))

    if not train_data:
        logger.error("No training data. Run arabic_dataset_builder.py first.")
        return

    use_cuda = torch.cuda.is_available()
    device = "cuda" if use_cuda else "cpu"
    logger.info("Device: %s", device)

    if device == "cpu":
        n_threads = os.cpu_count() or 1
        torch.set_num_threads(n_threads)
        logger.info("CPU mode — %d threads. Training will be slow.", n_threads)

    # ─── 1. Tokenizer + base model ───────────────────────────────
    logger.info("Loading model: %s", args.base_model)
    tokenizer = AutoTokenizer.from_pretrained(args.base_model, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model_kwargs: dict[str, Any] = {"trust_remote_code": True}
    if use_cuda:
        try:
            from transformers import BitsAndBytesConfig
            bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.float16)
            model_kwargs["quantization_config"] = bnb
            model_kwargs["device_map"] = "auto"
            logger.info("CUDA + 4-bit quantization enabled")
        except ImportError:
            model_kwargs["device_map"] = "auto"
            model_kwargs["torch_dtype"] = torch.float16
            logger.info("CUDA without bitsandbytes — float16")
    else:
        model_kwargs["torch_dtype"] = torch.float32
        logger.info("CPU — float32 (no quantization)")

    model = AutoModelForCausalLM.from_pretrained(args.base_model, **model_kwargs)

    # ─── 2. LoRA config ──────────────────────────────────────────
    # Target more modules for Arabic: q_proj, v_proj, k_proj, o_proj
    # to better adapt attention patterns for RTL Arabic text
    lora = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=args.lora_r,
        lora_alpha=args.lora_r * 2,
        lora_dropout=0.05,
        target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
        bias="none",
    )
    model = get_peft_model(model, lora)
    model.print_trainable_parameters()

    # ─── 3. Dataset ──────────────────────────────────────────────
    def to_text(row):
        chat = format_example_as_chat(row)
        try:
            text = tokenizer.apply_chat_template(chat["messages"], tokenize=False)
        except Exception:
            parts = []
            for m in chat["messages"]:
                parts.append(f"<|{m['role']}|>\n{m['content']}")
            text = "\n".join(parts)
        return {"text": text}

    ds_train = Dataset.from_list(train_data).map(to_text)
    ds_eval = Dataset.from_list(eval_data).map(to_text) if eval_data else None

    # ─── 4. Trainer ──────────────────────────────────────────────
    max_seq = args.max_seq_length
    use_fp16 = use_cuda

    cfg = SFTConfig(
        output_dir=str(args.output_dir),
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        learning_rate=args.lr,
        fp16=use_fp16,
        bf16=False,
        logging_steps=1,
        save_strategy="epoch",
        eval_strategy="epoch" if ds_eval else "no",
        max_length=max_seq,
        report_to="none",
        dataloader_pin_memory=False,
        remove_unused_columns=False,
        warmup_ratio=0.1,
    )
    trainer = SFTTrainer(
        model=model,
        processing_class=tokenizer,
        train_dataset=ds_train,
        eval_dataset=ds_eval,
        args=cfg,
    )

    logger.info("Starting Arabic LoRA training...")
    trainer.train()

    # Save
    trainer.save_model(str(args.output_dir))
    tokenizer.save_pretrained(str(args.output_dir))
    logger.info("Arabic LoRA model saved to %s", args.output_dir)

    meta = {
        "base_model": args.base_model,
        "track": "arabic-derja",
        "lora_r": args.lora_r,
        "target_modules": ["q_proj", "v_proj", "k_proj", "o_proj"],
        "epochs": args.epochs,
        "train_size": len(train_data),
        "eval_size": len(eval_data),
        "max_seq_length": max_seq,
        "objective": "Understand Tunisian derja, respond in MSA with Daleel format",
    }
    (args.output_dir / "training_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def main() -> None:
    p = argparse.ArgumentParser(description="Track 3 — Arabic/Derja LoRA fine-tuning")
    p.add_argument("--base-model", default="Qwen/Qwen2.5-7B-Instruct")
    p.add_argument("--train-file", type=Path, default=Path("training/data/arabic_train.jsonl"))
    p.add_argument("--eval-file", type=Path, default=Path("training/data/arabic_eval.jsonl"))
    p.add_argument("--output-dir", type=Path, default=Path("training/models/daleel-arabic-v1"))
    p.add_argument("--epochs", type=int, default=5)
    p.add_argument("--batch-size", type=int, default=2)
    p.add_argument("--grad-accum", type=int, default=4)
    p.add_argument("--lr", type=float, default=2e-4)
    p.add_argument("--lora-r", type=int, default=16)
    p.add_argument("--max-seq-length", type=int, default=2048)
    p.add_argument("--log-level", default="INFO")
    args = p.parse_args()

    logging.basicConfig(level=args.log_level, format="%(asctime)s [%(levelname)s] %(message)s")
    train(args)


if __name__ == "__main__":
    main()
