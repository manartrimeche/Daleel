"""
merge_lora_to_ollama.py

Script pour fusionner l'adapter LoRA (Track 1) dans le modèle de base,
sauvegarder le modèle complet, et préparer la conversion GGUF pour Ollama.

PRÉREQUIS
-----------
    pip install peft transformers
    # Optionnel pour GGUF : llama.cpp (pip install llama-cpp-python ou git clone)

USAGE
------
    # 1. Merge LoRA + base
    python training/merge_lora_to_ollama.py \
        --adapter-dir training/models/daleel-style-v1 \
        --output-merged training/models/daleel-style-merged \
        --save-format safetensors

    # 2. Convertir en GGUF (nécessite llama.cpp dans le PATH ou via docker)
    # docker run --rm -v "training/models/daleel-style-merged:/model" \
    #     ghcr.io/ggerganov/llama.cpp:full \
    #     convert_hf_to_gguf /model --outfile /model/daleel-style-v1.gguf

    # 3. Créer le modèle Ollama
    # ollama create daleel-style:v1 -f training/models/daleel-style-v1/Modelfile
"""
from __future__ import annotations

import argparse
import logging
import os
from pathlib import Path

from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

logger = logging.getLogger(__name__)


OLLAMA_MODELFILE = (
    "FROM {{gguf_path}}\n\n"
    "# Paramètres du modèle fine-tuné Daleel-Style\n"
    "PARAMETER temperature 0.1\n"
    "PARAMETER num_ctx 4096\n"
    "PARAMETER top_p 0.85\n"
    "PARAMETER top_k 40\n\n"
    "# System prompt obligatoire — définit le format 7 sections\n"
    'SYSTEM """Tu es Daleel, conseiller juridique tunisien. À partir des faits, '
    "du contexte légal et du brouillon, produis une reponse structurée en 7 sections fixes :\\n\\n"
    "1. Ce que j'ai compris\\n"
    "2. Informations manquantes\\n"
    "3. Contexte légal / articles pertinents\\n"
    "4. Analyse / risques de non-conformité\\n"
    "5. Actions recommandées\\n"
    "6. Preuves / documents à rassembler\\n"
    "7. Nécessité d'une revue humaine\\n\\n"
    "N'invente AUCUN article. Si un article n'est pas dans le contexte fourni, ne le cite pas.\"\"\"\n"
)


def merge_and_save(adapter_dir: Path, output_merged: Path, base_model_name: str | None = None) -> None:
    """Merge LoRA adapter into base model and save."""

    adapter_dir = Path(adapter_dir).resolve()
    output_merged = Path(output_merged).resolve()
    output_merged.mkdir(parents=True, exist_ok=True)

    # 1. Load base model
    logger.info("Chargement de l'adapter depuis %s", adapter_dir)

    # Auto-detect base model from adapter config
    if base_model_name is None:
        from peft.utils import infer_device
        import json as _json
        config_path = adapter_dir / "adapter_config.json"
        if config_path.exists():
            with open(config_path) as f:
                cfg = _json.load(f)
            base_model_name = cfg.get("base_model_name_or_path", "Qwen/Qwen2.5-1.5B-Instruct")
            logger.info("Base model auto-detecté: %s", base_model_name)
        else:
            raise ValueError("--base-model requis ou adapter_config.json manquant")

    logger.info("Chargement du modèle de base: %s", base_model_name)

    model = AutoModelForCausalLM.from_pretrained(
        base_model_name,
        torch_dtype="auto",
        device_map="auto" if _has_cuda() else None,
        low_cpu_mem_usage=True,
    )
    tokenizer = AutoTokenizer.from_pretrained(base_model_name)

    # 2. Merge
    logger.info("Merge de l'adapter LoRA...")
    model = PeftModel.from_pretrained(model, str(adapter_dir))
    model = model.merge_and_unload()

    # 3. Save merged
    logger.info("Sauvegarde du modèle fusionné dans %s", output_merged)
    model.save_pretrained(str(output_merged))
    tokenizer.save_pretrained(str(output_merged))

    # 4. Write Modelfile template
    modelfile_path = output_merged / "Modelfile"
    modelfile_content = OLLAMA_MODELFILE.replace("{{gguf_path}}", "./daleel-style-v1.gguf")
    modelfile_path.write_text(modelfile_content, encoding="utf-8")

    logger.info("Modèle fusionné sauvegardé.")
    logger.info("  → Modelfile template: %s", modelfile_path)
    logger.info("  Prochaines étapes:")
    logger.info("    1. Convertir en GGUF (voir README_GGUF.md)")
    logger.info("    2. ollama create daleel-style:v1 -f %s", modelfile_path)


def _has_cuda() -> bool:
    try:
        import torch
        return torch.cuda.is_available()
    except Exception:
        return False


def main() -> None:
    p = argparse.ArgumentParser(description="Merge LoRA adapter into base model for Ollama")
    p.add_argument("--adapter-dir", type=Path, default=Path("training/models/daleel-style-v1"))
    p.add_argument("--output-merged", type=Path, default=Path("training/models/daleel-style-merged"))
    p.add_argument("--base-model", type=str, default=None, help="Override base model name")
    p.add_argument("--log-level", default="INFO")
    args = p.parse_args()

    logging.basicConfig(level=args.log_level, format="%(asctime)s [%(levelname)s] %(message)s")
    merge_and_save(args.adapter_dir, args.output_merged, args.base_model)


if __name__ == "__main__":
    main()
