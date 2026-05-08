"""Diagnostic minimal pour isoler le crash silencieux."""
import sys
import os

# Désactive tout import lazy de datasets/pyarrow côté sentence-transformers
os.environ["SENTENCE_TRANSFORMERS_HOME"] = os.path.abspath("training/models/cache")

print("[D0] Python démarré", flush=True)

try:
    import torch
    print(f"[D1] torch OK | cuda available: {torch.cuda.is_available()}", flush=True)
except Exception as e:
    print(f"[D1] torch ERREUR: {e}", flush=True)
    sys.exit(1)

try:
    from transformers import AutoTokenizer, AutoModel
    print("[D2] transformers import OK", flush=True)
except Exception as e:
    print(f"[D2] transformers ERREUR: {e}", flush=True)
    sys.exit(1)

try:
    print("[D3] Import sentence_transformers...", flush=True)
    from sentence_transformers import SentenceTransformer
    print("[D4] sentence_transformers import OK", flush=True)
except Exception as e:
    print(f"[D4] sentence_transformers ERREUR: {e}", flush=True)
    sys.exit(1)

MODEL = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"

try:
    print("[D5] Chargement tokenizer...", flush=True)
    tok = AutoTokenizer.from_pretrained(MODEL)
    print("[D6] Tokenizer OK", flush=True)
except Exception as e:
    print(f"[D6] Tokenizer ERREUR: {e}", flush=True)
    sys.exit(1)

try:
    print("[D7] Chargement model CPU...", flush=True)
    model = SentenceTransformer(MODEL, device="cpu")
    print("[D8] SentenceTransformer CPU OK", flush=True)
except Exception as e:
    print(f"[D8] SentenceTransformer CPU ERREUR: {e}", flush=True)
    sys.exit(1)

try:
    print("[D9] Test encode CPU...", flush=True)
    vec = model.encode("test", show_progress_bar=False)
    print(f"[D10] Encode CPU OK | shape={vec.shape}", flush=True)
except Exception as e:
    print(f"[D10] Encode CPU ERREUR: {e}", flush=True)
    sys.exit(1)

if torch.cuda.is_available():
    try:
        print("[D11] Déplacement CUDA...", flush=True)
        model = model.to("cuda")
        print("[D12] .to(cuda) OK", flush=True)
    except Exception as e:
        print(f"[D12] .to(cuda) ERREUR: {e}", flush=True)
        sys.exit(1)

    try:
        print("[D13] Test encode CUDA...", flush=True)
        vec = model.encode("test", show_progress_bar=False)
        print(f"[D14] Encode CUDA OK | shape={vec.shape} | device={vec.device if hasattr(vec, 'device') else 'numpy'}", flush=True)
    except Exception as e:
        print(f"[D14] Encode CUDA ERREUR: {e}", flush=True)
        sys.exit(1)
else:
    print("[D11] CUDA non disponible, skip tests GPU", flush=True)

print("\n=== TOUS LES TESTS OK ===", flush=True)
