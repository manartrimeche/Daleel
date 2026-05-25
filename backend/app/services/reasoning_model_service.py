"""
Reasoning Model Service — Track 2.

Façade unique pour les modèles fine-tunés de classification et d'extraction.
Tous les appelants (`domain_router`, `case_conversation_service`,
`compliance_case_orchestrator`) doivent passer par ce module.

DESIGN
------
- Chargement paresseux (lazy) du modèle au premier appel.
- Si le modèle n'est pas configuré (env var absente) ou indisponible, chaque
  fonction retourne `(None, 0.0)` ou un dict vide — l'appelant doit prévoir
  un fallback (le scoring lexical existant pour le router, le LLM générique
  pour l'extraction, etc.).
- Toutes les fonctions sont synchronisées + non bloquantes côté DB ; elles
  peuvent être enveloppées dans `asyncio.to_thread` si besoin.

ENV VARS
--------
    DALEEL_REASONING_MODEL_PATH=./training/models/daleel-reasoning-v1
    DALEEL_REASONING_CONFIDENCE_THRESHOLD=0.7

EXEMPLE D'INTÉGRATION
---------------------
    # Dans domain_router.route_question :
    pred_domain, conf = reasoning_model_service.classify_domain(question)
    if pred_domain and conf >= settings.reasoning_confidence_threshold:
        return RouteResult(domain=pred_domain, ...)
    # sinon → continue avec le scoring lexical existant.
"""
from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import Any, Optional

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


# ─────────────────────────────────────────────────────────────
# Référentiels (DOIVENT correspondre à reasoning_finetune.py)
# ─────────────────────────────────────────────────────────────

DOMAINS = ["labor", "data_protection", "corporate", "credit_info", "investment", "other"]
CASE_TYPES = ["question", "complaint", "incident", "data_subject_request", "audit", "other"]
RISK_LEVELS = ["low", "medium", "high"]


# ─────────────────────────────────────────────────────────────
# Lazy loader
# ─────────────────────────────────────────────────────────────

_MODEL_CACHE: dict[str, Any] = {}


def _model_path() -> Optional[Path]:
    raw = os.getenv("DALEEL_REASONING_MODEL_PATH", "").strip()
    if not raw:
        return None
    p = Path(raw)
    return p if p.exists() else None


def _confidence_threshold() -> float:
    return float(getattr(settings, "reasoning_confidence_threshold", 0.7))


def is_enabled() -> bool:
    raw = os.getenv("DALEEL_REASONING_MODEL_PATH", "").strip()
    return bool(raw) and os.path.exists(raw)


def _load_model() -> Optional[dict[str, Any]]:
    """Charge le modèle XLM-R + tokenizer + têtes une seule fois."""
    if "ready" in _MODEL_CACHE:
        return _MODEL_CACHE.get("model")
    _MODEL_CACHE["ready"] = True

    path = _model_path()
    if path is None:
        logger.info("reasoning_model_service disabled (DALEEL_REASONING_MODEL_PATH not set)")
        _MODEL_CACHE["model"] = None
        return None

    try:
        import torch
        from transformers import AutoTokenizer, AutoModel
        from torch import nn

        # The reasoning bundle is loaded from DALEEL_REASONING_MODEL_PATH only.
        tok = AutoTokenizer.from_pretrained(str(path), local_files_only=True)  # nosec B615
        encoder = AutoModel.from_pretrained(str(path), local_files_only=True)  # nosec B615
        hid = encoder.config.hidden_size

        class MultiHead(nn.Module):
            def __init__(self):
                super().__init__()
                self.encoder = encoder
                self.head_domain = nn.Linear(hid, len(DOMAINS))
                self.head_case   = nn.Linear(hid, len(CASE_TYPES))
                self.head_risk   = nn.Linear(hid, len(RISK_LEVELS))
            def forward(self, **kwargs):
                pooled = self.encoder(**kwargs).last_hidden_state[:, 0]
                return self.head_domain(pooled), self.head_case(pooled), self.head_risk(pooled)

        model = MultiHead()
        state = torch.load(path / "model.pt", map_location="cpu", weights_only=True)
        model.load_state_dict(state)
        model.eval()

        _MODEL_CACHE["model"] = {"tok": tok, "model": model, "torch": torch}
        logger.info("reasoning_model_service: model loaded from %s", path)
        return _MODEL_CACHE["model"]
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to load reasoning model: %s", exc)
        _MODEL_CACHE["model"] = None
        return None


def _softmax_predict(text: str, head_name: str) -> tuple[Optional[str], float]:
    """Inférence générique multi-tête. Renvoie (label, confiance) ou (None, 0)."""
    bundle = _load_model()
    if bundle is None:
        return None, 0.0

    tok = bundle["tok"]
    model = bundle["model"]
    torch = bundle["torch"]
    enc = tok(text, truncation=True, max_length=256, padding=True, return_tensors="pt")
    with torch.no_grad():
        logits_dom, logits_case, logits_risk = model(**enc)
    mapping = {
        "domain": (logits_dom, DOMAINS),
        "case_type": (logits_case, CASE_TYPES),
        "risk": (logits_risk, RISK_LEVELS),
    }
    logits, labels = mapping[head_name]
    probs = torch.softmax(logits, dim=-1)[0]
    idx = int(probs.argmax().item())
    return labels[idx], float(probs[idx].item())


# ─────────────────────────────────────────────────────────────
# API publique : classification
# ─────────────────────────────────────────────────────────────

def classify_domain(text: str) -> tuple[Optional[str], float]:
    """Retourne (domain, confidence) ou (None, 0.0) si modèle indispo / texte vide.

    Appelé par `app/services/domain_router.py` AVANT le scoring lexical.
    Si confidence < threshold → l'appelant doit utiliser le fallback lexical.
    """
    if not text or len(text.strip()) < 5:
        return None, 0.0
    return _softmax_predict(text, "domain")


def classify_case_type(text: str) -> tuple[Optional[str], float]:
    """Retourne (case_type, confidence). Appelé par case_conversation_service."""
    if not text or len(text.strip()) < 5:
        return None, 0.0
    return _softmax_predict(text, "case_type")


def classify_risk(text: str) -> tuple[Optional[str], float]:
    """Retourne (risk_level, confidence). Appelé par compliance_case_orchestrator."""
    if not text or len(text.strip()) < 5:
        return None, 0.0
    return _softmax_predict(text, "risk")


# ─────────────────────────────────────────────────────────────
# API publique : extraction
# ─────────────────────────────────────────────────────────────

_DATE_RE = re.compile(r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2}|\bjanvier|\bfévrier|\bmars|\bavril|\bmai|\bjuin|\bjuillet|\baoût|\bseptembre|\boctobre|\bnovembre|\bdécembre)\w*\s*\d{0,4}", re.IGNORECASE)
_AMOUNT_RE = re.compile(r"\b\d+(?:[.,]\d+)?\s*(?:TND|DT|EUR|€|USD|\$|dinars?|euros?)\b", re.IGNORECASE)


def extract_facts(text: str) -> dict[str, Any]:
    """Extrait des faits structurés.

    Si le modèle fine-tuné est indispo, retombe sur des heuristiques regex
    minimales pour `dates` et `amounts` afin de garder une valeur exploitable.

    Returns:
        {
          "parties": [...],
          "dates": [...],
          "amounts": [...],
          "processing_type": "...",
          "legal_basis_keywords": [...],
          "_confidence": float,
          "_source": "model" | "regex_fallback"
        }
    """
    if not text:
        return _empty_facts(source="empty")

    bundle = _load_model()
    if bundle is None:
        return _regex_fallback_extraction(text)

    # ─── Modèle réel (à décommenter) ─────────────────────────────
    # Ici on attend qu'une 4e tête seq2seq OU un petit LLM JSON-only fournisse
    # un dict {parties, dates, amounts, processing_type, legal_basis_keywords}.
    # ...
    return _regex_fallback_extraction(text)


def _empty_facts(source: str = "empty") -> dict[str, Any]:
    return {
        "parties": [],
        "dates": [],
        "amounts": [],
        "processing_type": "",
        "legal_basis_keywords": [],
        "_confidence": 0.0,
        "_source": source,
    }


def _regex_fallback_extraction(text: str) -> dict[str, Any]:
    dates = list({m.group(0) for m in _DATE_RE.finditer(text)})
    amounts = list({m.group(0) for m in _AMOUNT_RE.finditer(text)})
    return {
        "parties": [],
        "dates": dates,
        "amounts": amounts,
        "processing_type": "",
        "legal_basis_keywords": [],
        "_confidence": 0.3 if (dates or amounts) else 0.0,
        "_source": "regex_fallback",
    }


# ─────────────────────────────────────────────────────────────
# Helper : décision « assez confiant pour trancher ? »
# ─────────────────────────────────────────────────────────────

def is_confident(confidence: float) -> bool:
    """True si la confiance dépasse le seuil configuré.

    À utiliser systématiquement par les appelants pour décider entre
    « accepter la prédiction » et « basculer en fallback / clarification ».
    """
    return confidence >= _confidence_threshold()
