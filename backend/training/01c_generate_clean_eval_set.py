"""Étape 1ter — Génération d'un eval set SANS FUITE par construction.

Différence avec 01b: au lieu de générer l'eval puis de filtrer le train a
posteriori (ce qui ne corrige pas un modèle déjà entraîné), ce script
échantillonne UNIQUEMENT parmi les articles jamais vus à l'entraînement
(article_key absent de train_set.jsonl). Le modèle fine-tuné existant peut
donc être réévalué directement: zéro fuite, aucun réentraînement requis.

Cible: 30 questions fr + 20 questions ar, stratifiées par (loi_code, langue),
générées par qwen2.5:7b. Sortie: eval_set_clean.jsonl (n'écrase pas l'éval
actuelle).

Usage:
    python training/01c_generate_clean_eval_set.py --n-fr 30 --n-ar 20
"""

from __future__ import annotations

import argparse
import json
import random
import re
from collections import defaultdict
from pathlib import Path

import httpx

DEFAULT_DATA_DIR = Path(__file__).parent / "data"

_PROMPT_FR = """Tu es un juriste tunisien. À partir du passage juridique ci-dessous, génère UNE seule
question précise et naturelle qu'un praticien pourrait poser, et dont la reponse se trouve
explicitement dans ce passage.

Réponds UNIQUEMENT avec le texte de la question (pas de guillemets, pas de numérotation, pas de markdown).

Passage :
{text}
"""

_PROMPT_AR = """أنت خبير قانوني تونسي. من النص القانوني أدناه، قم بإنشاء سؤال واحد محدد وطبيعي
يمكن لممارس قانوني طرحه، بحيث تكون إجابته موجودة بشكل صريح في هذا النص.

أجب فقط بنص السؤال (بدون علامات اقتباس، بدون ترقيم، بدون markdown).

النص :
{text}
"""


def _call_ollama(prompt: str, model: str, base_url: str, temperature: float = 0.7) -> str:
    url = f"{base_url.rstrip('/')}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": temperature, "num_predict": 200},
    }
    with httpx.Client(timeout=120.0) as client:
        r = client.post(url, json=payload)
        r.raise_for_status()
        return r.json().get("response", "")


def _clean_question(raw: str) -> str:
    q = raw.strip().strip('"').strip("'").strip()
    q = re.sub(r"^(?:\d+[\.\)]\s*|Q\d+\s*:?\s*|Question\s*:?\s*)", "", q, flags=re.IGNORECASE)
    q = q.split("\n")[0].strip()
    return q


def _is_quality_chunk(art: dict) -> bool:
    text = art.get("text", "")
    if len(text) < 200 or len(text) > 3000:
        return False
    if text.count("\n") > 30 or text.count(".") < 3:
        return False
    return True


def sample_unused(articles: list[dict], used_keys: set[str], language: str,
                  target: int, seed: int) -> list[dict]:
    """Échantillonne `target` chunks de la langue donnée, jamais vus à
    l'entraînement, répartis le plus uniformément possible par loi_code."""
    buckets: dict[str, list[dict]] = defaultdict(list)
    for art in articles:
        if art.get("language") != language:
            continue
        if art.get("article_key") in used_keys:
            continue  # ← exclusion stricte des articles d'entraînement
        if not _is_quality_chunk(art):
            continue
        buckets[art.get("loi_code", "UNKNOWN")].append(art)

    rng = random.Random(seed)
    for items in buckets.values():
        rng.shuffle(items)

    # Round-robin sur les buckets pour une couverture équilibrée
    sampled: list[dict] = []
    keys = list(buckets.keys())
    rng.shuffle(keys)
    idx = 0
    while len(sampled) < target and any(buckets[k] for k in keys):
        k = keys[idx % len(keys)]
        if buckets[k]:
            sampled.append(buckets[k].pop())
        idx += 1
    print(f"[sample-{language}] {len(sampled)}/{target} chunks depuis {len(keys)} documents")
    for k in keys:
        used = sum(1 for s in sampled if s.get("loi_code") == k)
        if used:
            print(f"    {k}: {used}")
    return sampled


def main() -> None:
    parser = argparse.ArgumentParser(description="Génère un eval set sans fuite")
    parser.add_argument("--articles", default=str(DEFAULT_DATA_DIR / "articles.jsonl"), type=Path)
    parser.add_argument("--train", default=str(DEFAULT_DATA_DIR / "train_set.jsonl"), type=Path)
    parser.add_argument("--output", default=str(DEFAULT_DATA_DIR / "eval_set_clean.jsonl"), type=Path)
    parser.add_argument("--n-fr", type=int, default=30)
    parser.add_argument("--n-ar", type=int, default=20)
    parser.add_argument("--ollama-model", default="qwen2.5:7b")
    parser.add_argument("--ollama-url", default="http://localhost:11434")
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    articles = [json.loads(line) for line in args.articles.read_text(encoding="utf-8").splitlines() if line.strip()]
    train = [json.loads(line) for line in args.train.read_text(encoding="utf-8").splitlines() if line.strip()]
    used_keys = {p.get("article_key") for p in train}
    print(f"[load] {len(articles)} articles, {len(used_keys)} articles vus à l'entraînement (exclus)")

    sample = (
        sample_unused(articles, used_keys, "fr", args.n_fr, args.seed)
        + sample_unused(articles, used_keys, "ar", args.n_ar, args.seed)
    )

    eval_rows: list[dict] = []
    for i, art in enumerate(sample, 1):
        lang = art.get("language", "fr")
        prompt = (_PROMPT_AR if lang == "ar" else _PROMPT_FR).format(text=art["text"])
        try:
            raw = _call_ollama(prompt, args.ollama_model, args.ollama_url, args.temperature)
        except Exception as exc:  # noqa: BLE001
            print(f"  [{i}/{len(sample)}] {art['article_key'][:12]} ERR: {exc}")
            continue
        q = _clean_question(raw)
        if len(q) < 12:
            print(f"  [{i}/{len(sample)}] question trop courte, ignorée")
            continue
        eval_rows.append({
            "query": q,
            "language": lang,
            "positive_article_keys": [art["article_key"]],
            "domain": art.get("loi_code"),
            "_chunk_preview": art["text"][:200],
        })
        print(f"  [{i}/{len(sample)}] ({lang}) {q[:80]}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as f:
        for row in eval_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    n_fr = sum(1 for r in eval_rows if r["language"] == "fr")
    n_ar = sum(1 for r in eval_rows if r["language"] == "ar")
    print(f"\n[OK] {len(eval_rows)} questions ({n_fr} fr / {n_ar} ar) -> {args.output}")

    # Garantie anti-fuite: vérification finale
    leak = {k for r in eval_rows for k in r["positive_article_keys"]} & used_keys
    print(f"[verif] articles gold présents dans le train: {len(leak)} (doit être 0)")


if __name__ == "__main__":
    main()
