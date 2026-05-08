"""Verify fine-tuning integration."""
import os, json, sys

# Check data files
for f in [
    'training/reasoning_train_merged.jsonl',
    'training/reasoning_eval_merged.jsonl',
    'training/style_train_merged.jsonl',
    'training/style_eval_merged.jsonl',
]:
    n = sum(1 for _ in open(f, 'r', encoding='utf-8'))
    print(f'OK: {f} ({n} lines)')

# Check model
mdir = 'training/models/daleel-reasoning-v2'
for f in ['model.pt', 'labels.json', 'config.json']:
    p = os.path.join(mdir, f)
    sz = os.path.getsize(p) / (1024*1024)
    print(f'OK: reasoning-v2/{f} ({sz:.1f} MB)')

# Check ollama
import httpx
try:
    r = httpx.get('http://localhost:11434/api/tags', timeout=5)
    models = [m['name'] for m in r.json().get('models', [])]
    daleel = [m for m in models if 'daleel' in m]
    print(f'OK: Ollama daleel models: {daleel}')
except Exception as e:
    print(f'ERROR: Ollama: {e}')

# Test services
from app.services import reasoning_model_service, llm_style_formatter
print('OK: reasoning_model_service imported')
print('OK: llm_style_formatter imported')

# Test confidence
assert reasoning_model_service.is_confident(0.75)
assert not reasoning_model_service.is_confident(0.65)
print('OK: confidence logic')

# Test empty fallback
d, c = reasoning_model_service.classify_domain('')
assert d is None and c == 0.0
print('OK: empty fallback')

print('\nALL CHECKS PASSED')
