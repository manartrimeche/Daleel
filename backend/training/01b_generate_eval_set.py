"""
Étape 1bis — Génération automatique d'un eval set + filtrage anti-leakage.

Génère un eval set en stratifiant l'échantillonnage par (document × langue) pour
garantir une couverture équilibrée des 6 documents juridiques.

Pour chaque chunk sélectionné :
  - Demande à Qwen de produire UNE question juridique précise dont la reponse
    se trouve dans ce chunk (température plus haute pour diversité).
  - Marque le `chunk_id` comme `positive_article_keys` gold.

Puis filtre `train_set.jsonl` pour retirer toute paire dont le `article_key`
(= chunk_id) apparaît dans l'eval — leakage strict éliminé.

Pourquoi générer plutôt qu'annoter à la main :
  - Avec 4634 paires train, l'effet du fine-tuning sera visible avec un eval
    de 25-30 questions, même générées par le même LLM.
  - Cela permet d'avancer rapidement et de mesurer une tendance.
  - LIMITE : les questions reflètent le style Qwen, pas un humain. Pour le PFE
    final, idéalement compléter avec 10-20 questions humaines écrites à la main.

Usage :
    python training/01b_generate_eval_set.py --per-bucket 5
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
    # Retirer numérotation type "1." ou "Q1:"
    q = re.sub(r"^(?:\d+[\.\)]\s*|Q\d+\s*:?\s*|Question\s*:?\s*)", "", q, flags=re.IGNORECASE)
    # Garder seulement la première phrase si reponse trop verbeuse
    q = q.split("\n")[0].strip()
    return q


def stratified_sample(articles: list[dict], per_bucket: int, seed: int = 42) -> list[dict]:
    """Échantillonne `per_bucket` chunks par bucket (loi_code, language)."""
    buckets: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for art in articles:
        # Filtrer chunks trop courts/longs/peu denses
        text = art.get("text", "")
        if len(text) < 200 or len(text) > 3000:
            continue
        # Heuristique simple : éviter les chunks qui semblent être des tables / sommaires
        if text.count("\n") > 30 or text.count(".") < 3:
            continue
        key = (art.get("loi_code", "UNKNOWN"), art.get("language", "fr"))
        buckets[key].append(art)

    rng = random.Random(seed)
    sampled: list[dict] = []
    for key, items in buckets.items():
        rng.shuffle(items)
        sampled.extend(items[:per_bucket])
    print(f"[sample] {len(sampled)} chunks échantillonnés depuis {len(buckets)} buckets")
    for key, items in buckets.items():
        print(f"    {key}: {min(per_bucket, len(items))}/{len(items)} disponibles")
    return sampled


def main() -> None:
    parser = argparse.ArgumentParser(description="Génère un eval set automatique stratifié")
    parser.add_argument("--articles", default=str(DEFAULT_DATA_DIR / "articles.jsonl"), type=Path)
    parser.add_argument("--train", default=str(DEFAULT_DATA_DIR / "train_set.jsonl"), type=Path)
    parser.add_argument("--output", default=str(DEFAULT_DATA_DIR / "eval_set.jsonl"), type=Path)
    parser.add_argument("--train-output", default=str(DEFAULT_DATA_DIR / "train_set_filtered.jsonl"), type=Path,
                        help="Train set filtré (sans les chunks d'eval)")
    parser.add_argument("--per-bucket", type=int, default=5,
                        help="Nombre de chunks à échantillonner par (document, langue)")
    parser.add_argument("--ollama-model", default="qwen2.5:7b")
    parser.add_argument("--ollama-url", default="http://localhost:11434")
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    articles = [json.loads(line) for line in args.articles.read_text(encoding="utf-8").splitlines() if line.strip()]
    print(f"[load] {len(articles)} chunks dans le corpus")

    sample = stratified_sample(articles, args.per_bucket, args.seed)

    eval_rows: list[dict] = []
    eval_chunk_ids: set[str] = set()
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
            continue
        eval_rows.append({
            "query": q,
            "language": lang,
            "positive_article_keys": [art["article_key"]],
            "domain": art.get("loi_code"),
            "_chunk_preview": art["text"][:200],
        })
        eval_chunk_ids.add(art["article_key"])
        if i % 5 == 0:
            print(f"  [{i}/{len(sample)}] OK -> {q[:80]}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as f:
        for row in eval_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"\n[OK] {len(eval_rows)} questions eval sauvegardées dans {args.output}")

    # ── Filtrage du train set ───────────────────────────────────────
    if args.train.exists():
        train = [json.loads(line) for line in args.train.read_text(encoding="utf-8").splitlines() if line.strip()]
        before = len(train)
        train_filtered = [p for p in train if p.get("article_key") not in eval_chunk_ids]
        removed = before - len(train_filtered)
        with args.train_output.open("w", encoding="utf-8") as f:
            for p in train_filtered:
                f.write(json.dumps(p, ensure_ascii=False) + "\n")
        print(f"[filter] {before} -> {len(train_filtered)} paires train (retiré {removed} chunks d'eval)")
        print(f"[filter] Sauvegardé dans {args.train_output}")
    else:
        print(f"[skip] {args.train} introuvable — pas de filtrage")


if __name__ == "__main__":
    main()
