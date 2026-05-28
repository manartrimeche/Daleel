"""
Étape 2 — Construction du dataset de fine-tuning.

Produit un JSONL de paires `(query, positive)` au format :
    {"query": str, "positive": str, "language": "fr|ar|en", "source": "feedback|synthetic", "article_key": str}

Trois sources combinées :

  A. `qa_feedback` (humain)
     - On traite chaque feedback validé comme signal positif :
       query = question, positive = article_versions actif dont `article_key`
       apparaît dans `corrected_answer` OU chunks associés au document source.

  B. Synthétique via Ollama/Qwen (fort volume)
     - Pour chaque article, on demande à Qwen de générer N questions
       juridiques auxquelles cet article répond. Plus rapide et bien plus
       volumineux que l'annotation humaine.

  C. Heuristique titre / heading (bootstrap sans LLM)
     - On fabrique une "question triviale" à partir du heading/section.
     - À utiliser uniquement si A et B sont indisponibles.

## Pourquoi une paire (query, positive) ?
`MultipleNegativesRankingLoss` (MNR) utilise les autres exemples du batch
comme négatifs implicites. Donc on ne fournit PAS de négatifs explicites ;
il faut juste des couples positifs propres et diversifiés.

## Dédoublonnage et exclusion de l'eval
Pour éviter le leakage : si `--eval` est fourni, toute query du train set
dont la similarité Jaccard avec une query d'eval dépasse `--dedup-threshold`
est supprimée.

## Équilibrage bilingue FR/AR
Les batches MNR sont plus sains si toutes les langues coexistent. On mélange
juste les exemples (ou on stratifie par langue en option) — le shuffling
standard du DataLoader fait le reste.

Usage :
    python training/02_build_train_set.py --output training/data/train_set.jsonl --synthetic
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

import httpx
from pymongo import MongoClient


DEFAULT_DATA_DIR = Path(__file__).parent / "data"

_TOKEN_RE = re.compile(r"[\u0600-\u06FF\w]+", re.UNICODE)
_ARTICLE_REF_RE = re.compile(
    r"(?:Article|Art\.?|article|الفصل|فصل|المادة)\s*([0-9]+(?:\s*bis|\s*ter)?)",
    re.IGNORECASE,
)


# ── MongoDB helpers ─────────────────────────────────────────────────────────


def _mongo_db():
    url = os.environ.get("DALEEL_MONGODB_URL", "mongodb://localhost:27017")
    name = os.environ.get("DALEEL_MONGODB_DB_NAME", "daleel")
    return MongoClient(url)[name]


# ── Dédoublonnage Jaccard ───────────────────────────────────────────────────


def _jaccard(a: str, b: str) -> float:
    ta = {t.lower() for t in _TOKEN_RE.findall(a) if len(t) > 2}
    tb = {t.lower() for t in _TOKEN_RE.findall(b) if len(t) > 2}
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def _load_eval_queries(eval_path: Path) -> list[str]:
    if not eval_path.exists():
        return []
    out = []
    for line in eval_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            if row.get("query"):
                out.append(row["query"])
    return out


def _filter_leakage(
    pairs: list[dict], eval_queries: list[str], threshold: float
) -> list[dict]:
    if not eval_queries:
        return pairs
    kept = []
    removed = 0
    for p in pairs:
        if any(_jaccard(p["query"], q) >= threshold for q in eval_queries):
            removed += 1
            continue
        kept.append(p)
    if removed:
        print(f"[dedup] {removed} paires écartées (leakage vs eval set)")
    return kept


# ── Source A : qa_feedback ──────────────────────────────────────────────────


def build_from_feedback(articles_by_key: dict[str, dict]) -> list[dict]:
    """Extrait des paires depuis `qa_feedback`.

    On parcourt corrected_answer pour trouver des références d'articles.
    Si l'article_key est reconstructible via le document source → paire créée.
    """
    db = _mongo_db()
    out: list[dict] = []
    skipped = 0

    # Précharger lois: doc_id -> loi_code n'est pas trivial. On prend la
    # stratégie : matcher par numéro d'article + langue, puis choisir le plus
    # probable via le loi_code le plus fréquent pour ce numéro. Si ambigu, skip.
    # Indexer les articles par "numero -> [article_key,...]".
    by_num: dict[str, list[str]] = {}
    for key, art in articles_by_key.items():
        # article_key format: "CT-Art-95" -> extraire "95"
        m = re.search(r"Art-(\d+(?:bis|ter)?)", key)
        if m:
            by_num.setdefault(m.group(1), []).append(key)

    for fb in db["qa_feedback"].find({}):
        question = (fb.get("question") or "").strip()
        answer = fb.get("corrected_answer") or ""
        if not question or not answer:
            continue
        refs = {m.group(1).replace(" ", "") for m in _ARTICLE_REF_RE.finditer(answer)}
        if not refs:
            skipped += 1
            continue
        for ref in refs:
            candidates = by_num.get(ref, [])
            # Si un seul match → paire sans ambiguïté
            if len(candidates) == 1:
                art = articles_by_key[candidates[0]]
                out.append({
                    "query": question,
                    "positive": art["text"],
                    "language": fb.get("language") or art.get("language") or "fr",
                    "source": "feedback",
                    "article_key": candidates[0],
                })
    print(f"[feedback] {len(out)} paires extraites ({skipped} feedbacks sans ref d'article)")
    return out


# ── Source B : génération synthétique via Ollama/Qwen ──────────────────────


_PROMPT_SYNTH_FR = """Tu es un juriste tunisien. À partir de l'article juridique ci-dessous,
génère exactement {n} questions courtes et naturelles qu'un praticien pourrait poser
et dont la reponse se trouve dans cet article.

Réponds UNIQUEMENT avec un JSON array de chaînes : ["q1", "q2", ...]
Aucun commentaire, aucune numérotation, aucun markdown.

Article ({article_key}) :
{text}
"""

_PROMPT_SYNTH_AR = """أنت خبير قانوني تونسي. من النص القانوني أدناه، قم بإنشاء {n} أسئلة قصيرة وطبيعية
يمكن لممارس قانوني طرحها، بحيث تكون الإجابات موجودة في هذا النص.

أجب فقط بصيغة JSON array مكون من نصوص: ["q1", "q2", ...]
لا تعليقات، لا ترقيم، لا markdown.

المادة ({article_key}):
{text}
"""


def _call_ollama(prompt: str, model: str, base_url: str, timeout: float = 120.0) -> str:
    url = f"{base_url.rstrip('/')}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.4, "num_predict": 512},
    }
    with httpx.Client(timeout=timeout) as client:
        r = client.post(url, json=payload)
        r.raise_for_status()
        return r.json().get("response", "")


def _extract_json_array(raw: str) -> list[str]:
    # Tolérant : on cherche le premier '[' et le dernier ']'
    start = raw.find("[")
    end = raw.rfind("]")
    if start < 0 or end <= start:
        return []
    try:
        arr = json.loads(raw[start : end + 1])
        return [str(x).strip() for x in arr if isinstance(x, str) and x.strip()]
    except json.JSONDecodeError:
        return []


def build_synthetic(
    articles: list[dict],
    per_article: int,
    model: str,
    base_url: str,
    max_articles: int | None = None,
) -> list[dict]:
    out: list[dict] = []
    subset = articles[:max_articles] if max_articles else articles
    for i, art in enumerate(subset, 1):
        lang = art.get("language") or "fr"
        text = art.get("text", "").strip()
        if len(text) < 80 or len(text) > 4000:
            continue
        template = _PROMPT_SYNTH_AR if lang == "ar" else _PROMPT_SYNTH_FR
        prompt = template.format(n=per_article, article_key=art["article_key"], text=text)
        try:
            raw = _call_ollama(prompt, model, base_url)
        except Exception as exc:  # noqa: BLE001
            print(f"  [{i}/{len(subset)}] {art['article_key']} ERR: {exc}")
            continue
        questions = _extract_json_array(raw)
        if not questions:
            continue
        for q in questions[:per_article]:
            if len(q) < 10:
                continue
            out.append({
                "query": q,
                "positive": text,
                "language": lang,
                "source": "synthetic",
                "article_key": art["article_key"],
            })
        if i % 10 == 0:
            print(f"  [{i}/{len(subset)}] {art['article_key']} — total pairs={len(out)}")
    print(f"[synthetic] {len(out)} paires générées")
    return out


# ── Source C : heuristique heading (fallback) ──────────────────────────────


def build_heuristic(articles: list[dict]) -> list[dict]:
    out = []
    for art in articles:
        heading = (art.get("heading") or "").strip()
        if not heading or len(heading) < 15:
            continue
        # Ex: "Article 95 — De l'obligation de sécurité" -> "Obligation de sécurité ?"
        m = re.search(r"[—:\-]\s*(.+)$", heading)
        if not m:
            continue
        topic = m.group(1).strip().rstrip(".")
        if len(topic) < 8:
            continue
        lang = art.get("language") or "fr"
        q = f"Que dit la loi concernant {topic} ?" if lang != "ar" else f"ماذا يقول القانون بشأن {topic} ؟"
        out.append({
            "query": q,
            "positive": art["text"],
            "language": lang,
            "source": "heuristic",
            "article_key": art["article_key"],
        })
    print(f"[heuristic] {len(out)} paires générées")
    return out


# ── Main ───────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(description="Build training set for embedding fine-tuning")
    parser.add_argument("--articles", default=str(DEFAULT_DATA_DIR / "articles.jsonl"),
                        help="Corpus articles (produit par 01_build_eval_set.py)")
    parser.add_argument("--output", default=str(DEFAULT_DATA_DIR / "train_set.jsonl"))
    parser.add_argument("--eval", default=str(DEFAULT_DATA_DIR / "eval_set.jsonl"),
                        help="Eval set pour exclusion anti-leakage")
    parser.add_argument("--feedback", action="store_true", help="Inclure la source qa_feedback")
    parser.add_argument("--synthetic", action="store_true", help="Inclure la génération via Ollama")
    parser.add_argument("--heuristic", action="store_true", help="Inclure la source heading-based")
    parser.add_argument("--synthetic-per-article", type=int, default=2,
                        help="Nombre de questions générées par article")
    parser.add_argument("--synthetic-max-articles", type=int, default=0,
                        help="Limite d'articles traités (0 = tous)")
    parser.add_argument("--ollama-model", default="qwen2.5:7b")
    parser.add_argument("--ollama-url", default=os.environ.get("DALEEL_LLM_BASE_URL", "http://localhost:11434"))
    parser.add_argument("--dedup-threshold", type=float, default=0.6,
                        help="Seuil Jaccard au-delà duquel on écarte une paire (leakage)")
    args = parser.parse_args()

    articles_path = Path(args.articles)
    if not articles_path.exists():
        print(f"[ERR] {articles_path} introuvable. Lance 01_build_eval_set.py d'abord.")
        sys.exit(1)

    articles = [json.loads(line) for line in articles_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    articles_by_key = {a["article_key"]: a for a in articles}
    print(f"[load] {len(articles)} articles chargés")

    # Si aucune source sélectionnée, activer toutes les sources disponibles par défaut
    if not (args.feedback or args.synthetic or args.heuristic):
        args.feedback = True
        args.heuristic = True
        print("[info] Aucune source spécifiée — activation feedback+heuristic par défaut")

    all_pairs: list[dict] = []
    if args.feedback:
        all_pairs.extend(build_from_feedback(articles_by_key))
    if args.synthetic:
        all_pairs.extend(build_synthetic(
            articles,
            per_article=args.synthetic_per_article,
            model=args.ollama_model,
            base_url=args.ollama_url,
            max_articles=args.synthetic_max_articles or None,
        ))
    if args.heuristic:
        all_pairs.extend(build_heuristic(articles))

    # Dédoublonnage exact (query+article_key)
    seen: set[tuple[str, str]] = set()
    uniq: list[dict] = []
    for p in all_pairs:
        key = (p["query"].lower().strip(), p["article_key"])
        if key in seen:
            continue
        seen.add(key)
        uniq.append(p)
    print(f"[dedup] {len(all_pairs)} -> {len(uniq)} paires uniques")

    # Filtrage anti-leakage eval
    eval_queries = _load_eval_queries(Path(args.eval))
    uniq = _filter_leakage(uniq, eval_queries, args.dedup_threshold)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for p in uniq:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")

    # Stats par langue / source
    by_lang: dict[str, int] = {}
    by_source: dict[str, int] = {}
    for p in uniq:
        by_lang[p["language"]] = by_lang.get(p["language"], 0) + 1
        by_source[p["source"]] = by_source.get(p["source"], 0) + 1

    print(f"\n[OK] {len(uniq)} paires sauvegardées dans {out_path}")
    print(f"    Par langue  : {by_lang}")
    print(f"    Par source  : {by_source}")


if __name__ == "__main__":
    main()
