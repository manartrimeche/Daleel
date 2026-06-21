"""
Pre-cache les modeles lourds pendant le build Docker.
Cela evite les telechargements au premier demarrage.
"""

import os
import shutil
from pathlib import Path

# Forcer le cache dans un repertoire previsible
os.environ.setdefault("HF_HOME", "/app/.cache/huggingface")
os.environ.setdefault("SENTENCE_TRANSFORMERS_HOME", "/app/.cache/sentence-transformers")
os.environ.setdefault("EASYOCR_MODULE_PATH", "/app/.cache/easyocr")
os.environ.setdefault("PIPER_VOICES_DIR", "/app/.cache/piper")


SENTENCE_MODELS = [
    # Modele principal (768d)
    "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
    # Modele legacy compat (384d)
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
]

EASYOCR_LANG_SETS = [
    ["ar", "en"],
    ["fr", "en"],
]

PIPER_VOICE_FILES = [
    (
        "rhasspy/piper-voices",
        "fr/fr_FR/siwis/medium/fr_FR-siwis-medium.onnx",
        "fr_FR-siwis-medium.onnx",
    ),
    (
        "rhasspy/piper-voices",
        "fr/fr_FR/siwis/medium/fr_FR-siwis-medium.onnx.json",
        "fr_FR-siwis-medium.onnx.json",
    ),
    (
        "rhasspy/piper-voices",
        "en/en_US/lessac/medium/en_US-lessac-medium.onnx",
        "en_US-lessac-medium.onnx",
    ),
    (
        "rhasspy/piper-voices",
        "en/en_US/lessac/medium/en_US-lessac-medium.onnx.json",
        "en_US-lessac-medium.onnx.json",
    ),
]


def cache_sentence_transformers() -> None:
    from sentence_transformers import SentenceTransformer

    for name in SENTENCE_MODELS:
        print(f"[precache] SentenceTransformer: {name} ...", flush=True)
        model = SentenceTransformer(name, device="cpu")
        dim = model.get_sentence_embedding_dimension()
        print(f"[precache] OK: {name} (dim={dim})", flush=True)
        del model


def cache_easyocr() -> None:
    import easyocr

    model_dir = Path(os.environ["EASYOCR_MODULE_PATH"])
    model_dir.mkdir(parents=True, exist_ok=True)

    for lang_list in EASYOCR_LANG_SETS:
        print(f"[precache] EasyOCR: {','.join(lang_list)} ...", flush=True)
        easyocr.Reader(
            lang_list,
            gpu=False,
            verbose=False,
            model_storage_directory=str(model_dir),
        )
        print(f"[precache] OK: EasyOCR {','.join(lang_list)}", flush=True)


def cache_faster_whisper() -> None:
    from faster_whisper import WhisperModel

    model_name = os.environ.get("DALEEL_WHISPER_MODEL", "small")
    print(f"[precache] faster-whisper: {model_name} ...", flush=True)
    model = WhisperModel(model_name, device="cpu", compute_type="int8")
    del model
    print(f"[precache] OK: faster-whisper {model_name}", flush=True)


def cache_piper_voices() -> None:
    from huggingface_hub import hf_hub_download

    voice_dir = Path(os.environ["PIPER_VOICES_DIR"])
    voice_dir.mkdir(parents=True, exist_ok=True)

    for repo_id, filename, target_name in PIPER_VOICE_FILES:
        print(f"[precache] Piper voice: {filename} ...", flush=True)
        downloaded = Path(hf_hub_download(repo_id=repo_id, filename=filename))
        target = voice_dir / target_name
        if downloaded.resolve() != target.resolve():
            shutil.copyfile(downloaded, target)
        print(f"[precache] OK: {target}", flush=True)


def main():
    cache_sentence_transformers()
    cache_easyocr()
    cache_faster_whisper()
    cache_piper_voices()
    print("[precache] Tous les modeles lourds sont en cache.", flush=True)


if __name__ == "__main__":
    main()
