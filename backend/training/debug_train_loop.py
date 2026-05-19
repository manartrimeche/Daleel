"""Simule une itération du training loop pour isoler le crash."""
import os
import sys

os.environ["SENTENCE_TRANSFORMERS_HOME"] = os.path.abspath("training/models/cache")

import torch
import torch.nn.functional as F
from sentence_transformers import SentenceTransformer
from torch.optim import AdamW
from tqdm import tqdm
from transformers import get_linear_schedule_with_warmup

MODEL = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"

def _mnr_loss(a, b, scale=20.0):
    scores = torch.matmul(a, b.T) * scale
    labels = torch.arange(len(scores), device=scores.device)
    return torch.nn.CrossEntropyLoss()(scores, labels)

print("[T0] Chargement model CPU...", flush=True)
model = SentenceTransformer(MODEL, device="cpu")
print("[T1] OK", flush=True)

print("[T2] Déplacement CUDA...", flush=True)
model = model.to("cuda")
# Fix device interne de SentenceTransformer
if hasattr(model, "_target_device"):
    model._target_device = torch.device("cuda")
print("[T3] OK", flush=True)

model.train()
print("[T4] model.train() OK", flush=True)

optimizer = AdamW(model.parameters(), lr=2e-5)
print("[T5] AdamW OK", flush=True)

scheduler = get_linear_schedule_with_warmup(optimizer, 10, 100)
print("[T6] scheduler OK", flush=True)

queries = ["Quelle est la durée du congé payé en Tunisie?", "Combien de jours de congé annuel?"]
positives = ["L'article 95 du code du travail prévoit 12 jours de congé payé.", "Le congé annuel est de 12 jours ouvrables."]

print("[T7] Tokenize...", flush=True)
q_features = model.tokenize(queries)
p_features = model.tokenize(positives)
print("[T8] OK", flush=True)

print("[T9] Move to CUDA...", flush=True)
for k in q_features:
    q_features[k] = q_features[k].to("cuda")
    p_features[k] = p_features[k].to("cuda")
print("[T10] OK", flush=True)

print("[T11] Forward pass...", flush=True)
q_out = model(q_features)
p_out = model(p_features)
print("[T12] Forward OK", flush=True)

print("[T13] Normalize...", flush=True)
q_emb = F.normalize(q_out["sentence_embedding"], p=2, dim=1)
p_emb = F.normalize(p_out["sentence_embedding"], p=2, dim=1)
print("[T14] OK", flush=True)

print("[T15] Loss...", flush=True)
loss = _mnr_loss(q_emb, p_emb)
print(f"[T16] Loss = {loss.item():.4f}", flush=True)

print("[T17] Backward...", flush=True)
optimizer.zero_grad()
loss.backward()
print("[T18] Backward OK", flush=True)

print("[T19] Clip grad...", flush=True)
torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
print("[T20] OK", flush=True)

print("[T21] Optimizer step...", flush=True)
optimizer.step()
scheduler.step()
print("[T22] OK", flush=True)

print("\n=== TRAIN LOOP TEST OK ===", flush=True)
