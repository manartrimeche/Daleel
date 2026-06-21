"""
Étape 0 — Réextraction des PDF arabes via OCR (Tesseract).

Les PDF arabes de l'IORT utilisent des polices CMap personnalisées
qui empêchent PyMuPDF et pdfminer d'extraire le texte correctement
(texte inversé ou glyphes substitués). Ce script réextrait le texte
via OCR page par page, segmente en articles, et met à jour articles.jsonl.

Usage :
    python training/00_reextract_arabic_ocr.py
    python training/00_reextract_arabic_ocr.py --dpi 200  # plus rapide, moins précis
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
import uuid
from pathlib import Path

import fitz  # PyMuPDF — for PDF→image conversion only
import pytesseract
from PIL import Image


DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
TRAINING_DATA_DIR = Path(__file__).resolve().parent / "data"

ARABIC_PDFS = [
    "مجلة الشركات التجارية.pdf",
    "مجلـة الشغـل.pdf",
]

LOI_CODE_MAP = {
    "مجلة الشركات التجارية.pdf": "مجلة الشركات التجارية",
    "مجلـة الشغـل.pdf": "مجلة الشغل",
}

ARTICLE_PATTERN = re.compile(
    r"(?:^|\n)\s*(?:الفصل|المادة)\s+(\d+[\s\-]*(?:مكرر|ثالثا|رابعا|خامسا)?)",
    re.MULTILINE,
)


def ocr_pdf(pdf_path: str, dpi: int = 200, start_page: int = 0) -> list[str]:
    """Extract text from each page of a PDF via Tesseract OCR.

    Robust to per-page failures (logs error, continues). Flushes stdout
    every page to allow live progress monitoring from a redirected file.
    """
    import sys

    doc = fitz.open(pdf_path)
    pages_text: list[str] = []
    n_pages = doc.page_count
    t_start = time.time()

    for i in range(start_page, n_pages):
        t_page = time.time()
        try:
            page = doc[i]
            pix = page.get_pixmap(dpi=dpi)
            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            text = pytesseract.image_to_string(img, lang="ara", config="--psm 6", timeout=60)
            pages_text.append(text)
        except Exception as exc:
            print(f"  [{i+1}/{n_pages}] ERROR: {exc!r}", flush=True)
            pages_text.append("")
            continue

        elapsed_page = time.time() - t_page
        if (i + 1) % 5 == 0 or i == n_pages - 1:
            total_elapsed = time.time() - t_start
            rate = (i + 1 - start_page) / total_elapsed if total_elapsed > 0 else 0
            eta = (n_pages - i - 1) / rate if rate > 0 else 0
            print(
                f"  [{i+1}/{n_pages}] OK in {elapsed_page:.1f}s "
                f"(avg {1/rate:.1f}s/page, ETA {eta/60:.1f}min)",
                flush=True,
            )
        sys.stdout.flush()

    doc.close()
    return pages_text


def segment_articles(full_text: str, loi_code: str) -> list[dict]:
    """Split OCR'd text into individual articles."""
    splits = list(ARTICLE_PATTERN.finditer(full_text))
    articles = []

    for idx, match in enumerate(splits):
        start = match.start()
        end = splits[idx + 1].start() if idx + 1 < len(splits) else len(full_text)
        article_text = full_text[start:end].strip()

        if len(article_text) < 30:
            continue

        article_num = match.group(1).strip()
        articles.append({
            "article_key": str(uuid.uuid4()),
            "loi_code": loi_code,
            "language": "ar",
            "heading": f"الفصل {article_num}",
            "text": article_text,
        })

    return articles


def update_articles_jsonl(new_ar_articles: list[dict], articles_path: Path) -> None:
    """Replace corrupted Arabic articles in articles.jsonl with OCR'd ones."""
    existing = []
    if articles_path.exists():
        existing = [
            json.loads(line)
            for line in articles_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    fr_articles = [a for a in existing if a.get("language") != "ar"]
    print(f"  Kept {len(fr_articles)} non-Arabic articles")
    print(f"  Removed {len(existing) - len(fr_articles)} old Arabic articles")
    print(f"  Adding {len(new_ar_articles)} new OCR'd Arabic articles")

    combined = fr_articles + new_ar_articles
    backup = articles_path.with_suffix(".jsonl.bak2")
    if articles_path.exists():
        if backup.exists():
            backup.unlink()
        articles_path.rename(backup)
        print(f"  Backup saved to {backup}")

    with articles_path.open("w", encoding="utf-8") as f:
        for art in combined:
            f.write(json.dumps(art, ensure_ascii=False) + "\n")

    print(f"  Wrote {len(combined)} articles to {articles_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Re-extract Arabic PDFs via OCR")
    parser.add_argument("--dpi", type=int, default=300)
    parser.add_argument("--articles-out", type=Path,
                        default=TRAINING_DATA_DIR / "articles.jsonl")
    args = parser.parse_args()

    all_ar_articles: list[dict] = []

    for pdf_name in ARABIC_PDFS:
        pdf_path = DATA_DIR / pdf_name
        if not pdf_path.exists():
            for f in os.listdir(DATA_DIR):
                if any(c in f for c in ["الشغ", "الشركات"]) and pdf_name.split(".")[0][:5] in f:
                    pdf_path = DATA_DIR / f
                    break

        if not pdf_path.exists():
            print(f"SKIP: {pdf_name} not found in {DATA_DIR}")
            continue

        loi_code = LOI_CODE_MAP.get(pdf_name, pdf_name)
        print(f"\n{'='*60}")
        print(f"Processing: {pdf_name} ({loi_code})")
        print(f"{'='*60}")

        t0 = time.time()
        pages = ocr_pdf(str(pdf_path), dpi=args.dpi)
        elapsed = time.time() - t0
        print(f"  OCR completed in {elapsed:.0f}s ({len(pages)} pages)")

        full_text = "\n\n".join(pages)
        articles = segment_articles(full_text, loi_code)
        print(f"  Segmented into {len(articles)} articles")

        if articles:
            print(f"  Sample article: {articles[0]['heading']}")
            print(f"    Text preview: {articles[0]['text'][:120]}...")

        all_ar_articles.extend(articles)

        # Save intermediate results after each PDF (defense in depth)
        intermediate_path = TRAINING_DATA_DIR / "articles_ar_ocr.jsonl"
        with intermediate_path.open("w", encoding="utf-8") as f:
            for art in all_ar_articles:
                f.write(json.dumps(art, ensure_ascii=False) + "\n")
        print(f"  Intermediate save: {len(all_ar_articles)} articles in {intermediate_path}")

    print(f"\n{'='*60}")
    print(f"Total Arabic articles extracted: {len(all_ar_articles)}")
    print(f"{'='*60}")

    update_articles_jsonl(all_ar_articles, args.articles_out)
    print("\nDone! Next steps:")
    print("  1. python training/01b_generate_eval_set.py  (regenerate eval)")
    print("  2. python training/02_build_train_set.py      (rebuild train)")
    print("  3. python training/04_finetune_embeddings.py  (retrain)")
    print("  4. python training/03_evaluate_retrieval.py   (re-evaluate)")


if __name__ == "__main__":
    main()
