import argparse
import json
import re
import statistics
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

DEFAULT_QUESTIONS = [
    "Quelles sont les obligations du gerant d'une SARL en Tunisie ?",
    "Quelles formalites sont obligatoires pour constituer une SARL en Tunisie ?",
    "Dans quels cas la responsabilite du gerant peut-elle etre engagee ?",
    "Quelle est la procedure de dissolution d'une societe commerciale ?",
    "Quels documents doivent etre conserves par une societe ?",
    "Quelles sont les regles de convocation des associes en SARL ?",
    "Comment se fait l'immatriculation au registre de commerce ?",
    "Quelles sanctions en cas de non-respect des obligations comptables ?",
    "Quelles sont les conditions de cession des parts sociales ?",
    "Le gerant peut-il engager la societe vis-a-vis des tiers ?",
    "ما هي واجبات مدير الشركة ذات المسؤولية المحدودة ؟",
    "ما هي اجراءات تأسيس شركة في تونس ؟",
    "Quels sont les droits des salaries en cas de licenciement ?",
    "Quelles obligations de publication legale pour les societes ?",
    "Quels sont les delais de depot des etats financiers ?",
    "Quelle difference entre SARL, SA et SUARL selon le code tunisien ?",
    "Quelles sont les obligations fiscales principales d'une societe ?",
    "Quelles clauses doivent figurer dans les statuts d'une SARL ?",
    "Quelles sont les responsabilites civiles et penales du gerant ?",
    "Comment contester une decision de gestion prise par le gerant ?",
]

ARTICLE_REF_RE = re.compile(r"(?:Article|Art\.?|article|الفصل|فصل|المادة)\s*([0-9]+)", re.IGNORECASE)


@dataclass
class EvalRow:
    model: str
    question: str
    ok: bool
    status_code: int
    elapsed_ms: float
    chunks_used: int
    answer_len: int
    answer_refs: int
    unsupported_refs: int
    error: str


def _extract_source_article_refs(sources: list[dict[str, Any]]) -> set[str]:
    refs: set[str] = set()
    for source in sources or []:
        section = str(source.get("section") or "")
        for m in ARTICLE_REF_RE.finditer(section):
            refs.add(m.group(1))
    return refs


def _extract_answer_article_refs(answer: str) -> set[str]:
    refs: set[str] = set()
    for m in ARTICLE_REF_RE.finditer(answer or ""):
        refs.add(m.group(1))
    return refs


def _load_questions(path: Path | None) -> list[str]:
    if path is None:
        return list(DEFAULT_QUESTIONS)

    content = path.read_text(encoding="utf-8").splitlines()
    questions = [line.strip() for line in content if line.strip() and not line.strip().startswith("#")]
    if not questions:
        raise ValueError(f"No questions found in {path}")
    return questions


def _evaluate_one(
    client: httpx.Client,
    base_url: str,
    model: str,
    question: str,
    top_k: int,
    temperature: float,
    timeout_s: float,
) -> EvalRow:
    url = f"{base_url.rstrip('/')}/api/v1/ask"
    payload = {
        "question": question,
        "top_k": top_k,
        "temperature": temperature,
        "history": [],
        "llm_model": model,
    }

    t0 = time.perf_counter()
    try:
        response = client.post(url, json=payload, timeout=timeout_s)
        elapsed_ms = (time.perf_counter() - t0) * 1000
        status_code = int(response.status_code)

        if status_code != 200:
            return EvalRow(
                model=model,
                question=question,
                ok=False,
                status_code=status_code,
                elapsed_ms=elapsed_ms,
                chunks_used=0,
                answer_len=0,
                answer_refs=0,
                unsupported_refs=0,
                error=f"HTTP {status_code}",
            )

        data = response.json()
        answer = str(data.get("answer") or "")
        sources = data.get("sources") or []

        source_refs = _extract_source_article_refs(sources)
        answer_refs = _extract_answer_article_refs(answer)
        unsupported_refs = answer_refs.difference(source_refs)

        return EvalRow(
            model=model,
            question=question,
            ok=True,
            status_code=status_code,
            elapsed_ms=elapsed_ms,
            chunks_used=int(data.get("chunks_used") or 0),
            answer_len=len(answer),
            answer_refs=len(answer_refs),
            unsupported_refs=len(unsupported_refs),
            error="",
        )
    except Exception as exc:  # noqa: BLE001
        elapsed_ms = (time.perf_counter() - t0) * 1000
        return EvalRow(
            model=model,
            question=question,
            ok=False,
            status_code=0,
            elapsed_ms=elapsed_ms,
            chunks_used=0,
            answer_len=0,
            answer_refs=0,
            unsupported_refs=0,
            error=f"{type(exc).__name__}: {exc}",
        )


def _summarize(rows: list[EvalRow]) -> dict[str, Any]:
    by_model: dict[str, list[EvalRow]] = {}
    for row in rows:
        by_model.setdefault(row.model, []).append(row)

    summary: dict[str, Any] = {}
    for model, items in by_model.items():
        ok_items = [x for x in items if x.ok]
        summary[model] = {
            "total": len(items),
            "success": len(ok_items),
            "success_rate": round((len(ok_items) / max(1, len(items))) * 100, 2),
            "avg_latency_ms": round(statistics.mean([x.elapsed_ms for x in items]), 2),
            "p95_latency_ms": round(statistics.quantiles([x.elapsed_ms for x in items], n=20)[-1], 2)
            if len(items) >= 2
            else round(items[0].elapsed_ms if items else 0.0, 2),
            "avg_chunks_used": round(statistics.mean([x.chunks_used for x in ok_items]), 2) if ok_items else 0.0,
            "avg_answer_len": round(statistics.mean([x.answer_len for x in ok_items]), 2) if ok_items else 0.0,
            "avg_unsupported_refs": round(statistics.mean([x.unsupported_refs for x in ok_items]), 4) if ok_items else 0.0,
            "total_unsupported_refs": int(sum(x.unsupported_refs for x in ok_items)),
            "errors": [x.error for x in items if not x.ok][:10],
        }
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="A/B benchmark for Daleel /api/v1/ask across multiple Ollama models")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="API base URL")
    parser.add_argument("--models", nargs="+", required=True, help="Model names to compare (e.g. qwen2.5:7b llama3.1:8b)")
    parser.add_argument("--questions-file", default="", help="Optional text file (one question per line)")
    parser.add_argument("--top-k", type=int, default=8)
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--timeout", type=float, default=420.0)
    parser.add_argument("--max-questions", type=int, default=0, help="Use only the first N questions (0 = all)")
    parser.add_argument("--output", default="tests/benchmark_results.json")
    args = parser.parse_args()

    questions = _load_questions(Path(args.questions_file)) if args.questions_file else list(DEFAULT_QUESTIONS)
    if args.max_questions and args.max_questions > 0:
        questions = questions[: args.max_questions]

    rows: list[EvalRow] = []
    with httpx.Client() as client:
        for model in args.models:
            print(f"\n=== Testing model: {model} ===")
            for i, question in enumerate(questions, 1):
                print(f"[{i:02d}/{len(questions)}] {question[:90]}")
                row = _evaluate_one(
                    client=client,
                    base_url=args.base_url,
                    model=model,
                    question=question,
                    top_k=args.top_k,
                    temperature=args.temperature,
                    timeout_s=args.timeout,
                )
                rows.append(row)
                if row.ok:
                    print(
                        f"  OK  {row.elapsed_ms:.0f}ms | chunks={row.chunks_used} | unsupported_refs={row.unsupported_refs}"
                    )
                else:
                    print(f"  ERR {row.error}")

    summary = _summarize(rows)
    output_payload = {
        "config": {
            "base_url": args.base_url,
            "models": args.models,
            "top_k": args.top_k,
            "temperature": args.temperature,
            "timeout": args.timeout,
            "questions_count": len(questions),
        },
        "summary": summary,
        "rows": [row.__dict__ for row in rows],
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n=== Summary ===")
    for model, stats in summary.items():
        print(
            f"{model}: success={stats['success']}/{stats['total']} "
            f"({stats['success_rate']}%) | avg={stats['avg_latency_ms']}ms | "
            f"p95={stats['p95_latency_ms']}ms | unsupported_refs(avg)={stats['avg_unsupported_refs']}"
        )

    ranking = sorted(
        summary.items(),
        key=lambda kv: (
            -kv[1]["success_rate"],
            kv[1]["avg_unsupported_refs"],
            kv[1]["avg_latency_ms"],
        ),
    )
    print("\n=== Ranking (best first) ===")
    for i, (model, stats) in enumerate(ranking, 1):
        print(
            f"{i}. {model} | success_rate={stats['success_rate']} | "
            f"unsupported_refs(avg)={stats['avg_unsupported_refs']} | avg_latency_ms={stats['avg_latency_ms']}"
        )

    print(f"\nSaved report: {out_path}")


if __name__ == "__main__":
    main()
