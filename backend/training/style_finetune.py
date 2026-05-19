"""
Style Fine-Tuning — Track 1.

LoRA / PEFT fine-tuning d'un petit LLM multilingue sur le format de reponse
advisor Daleel (7 sections fixes).

OBJECTIF PFE
------------
Prouver qu'avec ~200-500 exemples bien formés, un LoRA léger suffit à
stabiliser le format en 7 sections.

PRÉREQUIS
---------
    pip install -r training/requirements-training.txt

USAGE
-----
    python training/style_finetune.py \
        --base-model Qwen/Qwen2.5-1.5B-Instruct \
        --train-file training/style_train.jsonl \
        --eval-file training/style_eval.jsonl \
        --output-dir training/models/daleel-style-v1 \
        --epochs 3 --batch-size 2 --lr 2e-4

EXPORT POUR OLLAMA
------------------
Après entraînement :
    1. Merge LoRA → base : `peft.PeftModel.merge_and_unload()`
    2. Convertir en GGUF avec llama.cpp (`convert-hf-to-gguf.py`)
    3. `ollama create daleel-style:v1 -f Modelfile`
    4. Mettre à jour `.env` : `DALEEL_STYLE_MODEL=daleel-style:v1`
"""
from __future__ import annotations

import argparse
import json
import logging
import os
from pathlib import Path
from typing import Any

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments
from peft import LoraConfig, get_peft_model, TaskType
from datasets import Dataset
from trl import SFTTrainer, SFTConfig

logger = logging.getLogger(__name__)


SYSTEM_PROMPT_FR = (
    "Tu es Daleel, conseiller juridique tunisien. À partir des faits, du "
    "contexte légal et du brouillon, produis une reponse structurée en 7 "
    "sections fixes : 1) Ce que j'ai compris, 2) Informations manquantes, "
    "3) Contexte légal / articles pertinents, 4) Analyse / risques de "
    "non-conformité, 5) Actions recommandées, 6) Preuves / documents à "
    "rassembler, 7) Nécessité d'une revue humaine. N'invente AUCUN article. "
    "Si un article n'est pas dans le contexte fourni, ne le cite pas."
)


def _format_example_as_chat(example: dict, language: str = "fr") -> dict[str, Any]:
    """Convertit un exemple JSONL en messages chat-style pour le tokenizer."""
    inp = example["input"]
    out = example["output"]

    user_payload = {
        "user_question": inp.get("user_question", ""),
        "extracted_facts": inp.get("extracted_facts", {}),
        "legal_context": inp.get("legal_context", []),
        "findings": inp.get("findings", []),
        "actions": inp.get("actions", []),
        "draft_answer": inp.get("draft_answer", ""),
    }
    user_msg = json.dumps(user_payload, ensure_ascii=False, indent=2)

    return {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT_FR},
            {"role": "user", "content": user_msg},
            {"role": "assistant", "content": out},
        ]
    }


def _load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def train(args: argparse.Namespace) -> None:
    """Entraînement LoRA sur petit LLM pour style de reponse advisor."""
    train_data = _load_jsonl(args.train_file)
    eval_data = _load_jsonl(args.eval_file) if args.eval_file and args.eval_file.exists() else []

    logger.info("Train : %d examples — Eval : %d examples", len(train_data), len(eval_data))

    if not train_data:
        logger.error("Pas de données d'entraînement. Lance d'abord style_dataset_builder.py.")
        return

    # Device detection
    use_cuda = torch.cuda.is_available()
    device = "cuda" if use_cuda else "cpu"
    logger.info("Device : %s", device)

    if device == "cpu":
        n_threads = os.cpu_count() or 1
        torch.set_num_threads(n_threads)
        logger.info("CPU mode — %d threads. L'entraînement sera lent.", n_threads)

    # ─── 1. Tokenizer + base model ───────────────────────────────
    logger.info("Chargement du modèle : %s", args.base_model)
    tokenizer = AutoTokenizer.from_pretrained(args.base_model, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # CPU: load in float32 (no bitsandbytes needed)
    # CUDA: try 4-bit quantization if bitsandbytes available
    model_kwargs: dict[str, Any] = {"trust_remote_code": True}
    if use_cuda:
        try:
            from transformers import BitsAndBytesConfig
            bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.float16)
            model_kwargs["quantization_config"] = bnb
            model_kwargs["device_map"] = "auto"
            logger.info("CUDA + 4-bit quantization activé")
        except ImportError:
            model_kwargs["device_map"] = "auto"
            model_kwargs["torch_dtype"] = torch.float16
            logger.info("CUDA sans bitsandbytes — float16")
    else:
        model_kwargs["torch_dtype"] = torch.float32
        logger.info("CPU — float32 (pas de quantization)")

    model = AutoModelForCausalLM.from_pretrained(args.base_model, **model_kwargs)

    # ─── 2. LoRA ─────────────────────────────────────────────────
    lora = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=args.lora_r,
        lora_alpha=args.lora_r * 2,
        lora_dropout=0.05,
        target_modules=["q_proj", "v_proj"],
        bias="none",
    )
    model = get_peft_model(model, lora)
    model.print_trainable_parameters()

    # ─── 3. Dataset ──────────────────────────────────────────────
    def to_text(row):
        chat = _format_example_as_chat(row)
        try:
            text = tokenizer.apply_chat_template(chat["messages"], tokenize=False)
        except Exception:
            # Fallback: concatenate messages manually
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
    )
    trainer = SFTTrainer(
        model=model,
        processing_class=tokenizer,
        train_dataset=ds_train,
        eval_dataset=ds_eval,
        args=cfg,
    )

    logger.info("Lancement de l'entraînement LoRA...")
    trainer.train()

    # Save
    trainer.save_model(str(args.output_dir))
    tokenizer.save_pretrained(str(args.output_dir))
    logger.info("Modèle LoRA sauvegardé dans %s", args.output_dir)

    # Save meta
    meta = {
        "base_model": args.base_model,
        "lora_r": args.lora_r,
        "epochs": args.epochs,
        "train_size": len(train_data),
        "eval_size": len(eval_data),
        "max_seq_length": max_seq,
    }
    (args.output_dir / "training_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def main() -> None:
    p = argparse.ArgumentParser(description="Track 1 — Style LoRA fine-tuning")
    p.add_argument("--base-model", default="Qwen/Qwen2.5-1.5B-Instruct")
    p.add_argument("--train-file", type=Path, default=Path("training/style_train.jsonl"))
    p.add_argument("--eval-file", type=Path, default=Path("training/style_eval.jsonl"))
    p.add_argument("--output-dir", type=Path, default=Path("training/models/daleel-style-v1"))
    p.add_argument("--epochs", type=int, default=3)
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
