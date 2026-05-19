"""Test d'imports un par un."""
import sys

print("[I0] import os", flush=True)
import os

print("[I1] import torch", flush=True)
import torch

print("[I2] import torch.nn.functional", flush=True)
import torch.nn.functional as F

print("[I3] from torch.optim import AdamW", flush=True)
from torch.optim import AdamW

print("[I4] from tqdm import tqdm", flush=True)
from tqdm import tqdm

print("[I5] from transformers import get_linear_schedule_with_warmup", flush=True)
from transformers import get_linear_schedule_with_warmup

print("[I6] from sentence_transformers import SentenceTransformer", flush=True)
from sentence_transformers import SentenceTransformer

print("\n=== ALL IMPORTS OK ===", flush=True)
