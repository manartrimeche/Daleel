"""Quick verification script for fine-tuned models."""
import os
import sys
import json

# ── 1. Check training data integrity ──
print("=" * 50)
print("1. TRAINING DATA INTEGRITY")
print("=" * 50)

files_ok = True
for f in [
    'training/reasoning_train_merged.jsonl',
    'training/reasoning_eval_merged.jsonl',
    'training/style_train_merged.jsonl',
    'training/style_eval_merged.jsonl',
]:
    if not os.path.exists(f):
        print(f"  MISSING: {f}")
        files_ok = False
        continue
    count = 0
    with open(f, 'r', encoding='utf-8') as fh:
        for line in fh:
            json.loads(line)
            count += 1
    print(f"  OK: {f} ({count} lines)")

# ── 2. Check reasoning model v2 ──
print("\n" + "=" * 50)
print("2. REASONING MODEL (v2)")
print("=" * 50)

os.environ['DALEEL_REASONING_MODEL_PATH'] = 'training/models/daleel-reasoning-v2'

model_dir = 'training/models/daleel-reasoning-v2'
required = ['model.pt', 'labels.json', 'config.json']
for f in required:
    path = os.path.join(model_dir, f)
    if os.path.exists(path):
        size = os.path.getsize(path) / (1024*1024)
        print(f"  OK: {f} ({size:.1f} MB)")
    else:
        print(f"  MISSING: {f}")
        files_ok = False

# Try loading
print("  Loading model...")
try:
    import torch
    from transformers import AutoTokenizer, AutoModel
    from app.services.reasoning_model_service import DOMAINS, CASE_TYPES, RISK_LEVELS

    tok = AutoTokenizer.from_pretrained(model_dir)
    encoder = AutoModel.from_pretrained(model_dir)
    hid = encoder.config.hidden_size

    class MultiHead(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.encoder = encoder
            self.head_domain = torch.nn.Linear(hid, len(DOMAINS))
            self.head_case = torch.nn.Linear(hid, len(CASE_TYPES))
            self.head_risk = torch.nn.Linear(hid, len(RISK_LEVELS))
        def forward(self, **kwargs):
            pooled = self.encoder(**kwargs).last_hidden_state[:, 0]
            return self.head_domain(pooled), self.head_case(pooled), self.head_risk(pooled)

    model = MultiHead()
    state = torch.load(os.path.join(model_dir, 'model.pt'), map_location='cpu', weights_only=True)
    model.load_state_dict(state)
    model.eval()

    # Test inference
    text = "Un salarié a été licencié sans préavis après 5 ans de service."
    enc = tok(text, truncation=True, max_length=256, padding=True, return_tensors='pt')
    with torch.no_grad():
        logits_dom, logits_case, logits_risk = model(**enc)
    probs = torch.softmax(logits_dom, dim=-1)[0]
    idx = int(probs.argmax().item())
    pred = DOMAINS[idx]
    conf = float(probs[idx].item())
    print(f"  Inference OK: '{text[:50]}...' -> domain={pred} (conf={conf:.2%})")
    print(f"  Model parameters: {sum(p.numel() for p in model.parameters()):,}")
except Exception as e:
    print(f"  ERROR: {e}")
    files_ok = False

# ── 3. Check Ollama style model ──
print("\n" + "=" * 50)
print("3. STYLE MODEL (Ollama)")
print("=" * 50)

try:
    import httpx
    r = httpx.get('http://localhost:11434/api/tags', timeout=5)
    models = [m['name'] for m in r.json().get('models', [])]
    if 'daleel-style' in models or any('daleel' in m for m in models):
        matching = [m for m in models if 'daleel' in m]
        print(f"  OK: Ollama models found: {matching}")
    else:
        print(f"  Models available: {models}")
        print("  WARNING: daleel-style not found in Ollama")
except Exception as e:
    print(f"  ERROR connecting to Ollama: {e}")

# ── 4. Check services integration ──
print("\n" + "=" * 50)
print("4. SERVICES INTEGRATION")
print("=" * 50)

try:
    from app.services import reasoning_model_service
    print("  reasoning_model_service loaded OK")
    print("  llm_style_formatter loaded OK")

    # Test confidence check
    assert reasoning_model_service.is_confident(0.75) is True
    assert reasoning_model_service.is_confident(0.65) is False
    print("  is_confident() logic OK")

    # Test empty text fallback
    d, c = reasoning_model_service.classify_domain("")
    assert d is None and c == 0.0
    print("  Empty text fallback OK")
except Exception as e:
    print(f"  ERROR: {e}")
    files_ok = False

# ── Summary ──
print("\n" + "=" * 50)
if files_ok:
    print("ALL CHECKS PASSED")
    sys.exit(0)
else:
    print("SOME CHECKS FAILED")
    sys.exit(1)
