"""Deep verification of chunk quality - Arabic and French."""
import asyncio
import re
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("ENVIRONMENT", "development")

from motor.motor_asyncio import AsyncIOMotorClient
from app.config import get_settings


KNOWN_OCR_ERRORS = [
    "باالقاكون", "باالقانون", "المؤسسسة", "المؤسسسات", "واحااك",
    "بطاةاللايف", "التاسيسي", "التاسيسئ", "الاعضاءء", "المختصف",
    "الاملية", "يتقزر", "فلللمبوع", "فيلللم",
]


async def verify():
    settings = get_settings()
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[settings.mongodb_db_name]

    issues = {
        "stray_zero_mid": 0,
        "stray_digits_eol": 0,
        "isolated_single_letter": 0,
        "triple_consecutive_chars": 0,
        "broken_word_sequences": 0,
        "fused_words_gt20": 0,
        "noise_symbols": 0,
        "orphan_parentheses": 0,
        "publisher_remnant": 0,
        "page_number_prefix": 0,
        "known_ocr_errors": 0,
        "double_dots": 0,
    }

    broken_samples = []
    fused_samples = []
    noise_samples = []
    ocr_err_samples = []

    total_ar = 0
    all_chunks = await db["chunks"].find(
        {"language": "ar"},
        {"text": 1, "page_number": 1, "document_id": 1, "_id": 0},
    ).to_list(length=None)

    for c in all_chunks:
        text = c.get("text", "")
        page = c.get("page_number", "?")
        doc_id = (c.get("document_id") or "?")[:8]
        tag = f"d={doc_id} p={page}"
        total_ar += 1

        # Stray zeros between Arabic words
        z = len(re.findall(r"(?<=[؀-ۿ])\s+0\s+(?=[؀-ۿ])", text))
        issues["stray_zero_mid"] += z

        # Stray digits at end of line
        issues["stray_digits_eol"] += len(
            re.findall(r"(?<=[؀-ۿ])[.\s]+\d{1,2}\s*$", text, re.MULTILINE)
        )

        # Isolated single Arabic letters between words (min 2-char words on each side)
        iso = re.findall(
            r"(?<=[؀-ۿ]{2})\s+([؀-ۿ])\s+(?=[؀-ۿ]{2})",
            text,
        )
        issues["isolated_single_letter"] += len(iso)
        if iso and len(broken_samples) < 5:
            for m in re.finditer(
                r".{0,20}(?<=[؀-ۿ]{2})\s+[؀-ۿ]\s+[؀-ۿ]{2}.{0,20}",
                text,
            ):
                broken_samples.append((tag, m.group().strip()))
                break

        # Triple consecutive Arabic characters
        tc = re.findall(r"([؀-ۿ])\1{2,}", text)
        issues["triple_consecutive_chars"] += len(tc)

        # Sequences of 3+ single-char Arabic words (broken word)
        words = text.split()
        for i in range(len(words) - 2):
            chunk3 = words[i : i + 3]
            if all(
                len(w) == 1 and re.match(r"[؀-ۿ]", w) for w in chunk3
            ):
                issues["broken_word_sequences"] += 1
                if len(broken_samples) < 5:
                    ctx = " ".join(words[max(0, i - 2) : i + 5])
                    broken_samples.append((tag, f"[3 single-char] {ctx}"))
                break

        # Fused words: Arabic words > 20 chars
        for w in words:
            if len(w) > 20 and re.match(r"^[؀-ۿ]+$", w):
                issues["fused_words_gt20"] += 1
                if len(fused_samples) < 5:
                    fused_samples.append((tag, w))
                break

        # Noise symbols
        noise_chars = re.findall(r"[#@&\^~`]", text)
        if noise_chars:
            issues["noise_symbols"] += 1
            if len(noise_samples) < 5:
                for m in re.finditer(r".{0,15}[#@&\^~`].{0,15}", text):
                    noise_samples.append((tag, m.group().strip()))
                    break

        # Orphan parentheses between Arabic
        issues["orphan_parentheses"] += len(
            re.findall(
                r"(?<=[؀-ۿ])\s*[\(\)]\s*(?=[؀-ۿ])", text
            )
        )

        # Page number prefix
        if re.match(r"^\d{1,3}\s*\n", text):
            issues["page_number_prefix"] += 1

        # Publisher remnant
        if re.search(
            r"المطبعة\s+الرسمية|"
            r"منشورات\s+المطبعة|"
            r"[Ii]mprimerie\s+[Oo]fficielle",
            text,
        ):
            issues["publisher_remnant"] += 1

        # Known OCR errors
        for err in KNOWN_OCR_ERRORS:
            if err in text:
                issues["known_ocr_errors"] += 1
                if len(ocr_err_samples) < 5:
                    idx = text.index(err)
                    ctx = text[max(0, idx - 20) : idx + len(err) + 20]
                    ocr_err_samples.append((tag, f"'{err}' in: ...{ctx}..."))
                break

        # Double dots/periods (OCR artifact)
        issues["double_dots"] += len(re.findall(r"\.\s*\.\s*\.", text))

    print(f"Total Arabic chunks: {total_ar}")
    print()
    print("=" * 60)
    print("  VERIFICATION APPROFONDIE - CHUNKS ARABES")
    print("=" * 60)

    for k, v in issues.items():
        icon = "+" if v == 0 else "!"
        status = "PROPRE" if v == 0 else f"{v} restant(s)"
        print(f"  [{icon}] {k:.<40} {status}")

    if broken_samples:
        print("\n  --- Mots casses / lettres isolees ---")
        for tag, s in broken_samples[:5]:
            print(f"    {tag}: {s}")

    if fused_samples:
        print("\n  --- Mots fusionnes (>20 chars) ---")
        for tag, s in fused_samples[:5]:
            print(f"    {tag}: {s}")

    if noise_samples:
        print("\n  --- Symboles parasites ---")
        for tag, s in noise_samples[:5]:
            print(f"    {tag}: {s}")

    if ocr_err_samples:
        print("\n  --- Erreurs OCR connues ---")
        for tag, s in ocr_err_samples[:5]:
            print(f"    {tag}: {s}")

    # French chunks check
    print("\n" + "=" * 60)
    print("  VERIFICATION - CHUNKS FRANCAIS")
    print("=" * 60)

    fr_issues = {"page_num": 0, "publisher": 0, "too_short": 0, "duplicates": 0}
    fr_texts = {}
    fr_chunks = await db["chunks"].find(
        {"language": "fr"}, {"text": 1, "_id": 0}
    ).to_list(length=None)

    for c in fr_chunks:
        text = c.get("text", "").strip()
        if re.match(r"^\d{1,3}\s*\n", text):
            fr_issues["page_num"] += 1
        if re.search(r"[Ii]mprimerie\s+[Oo]fficielle", text):
            fr_issues["publisher"] += 1
        if len(text) < 30:
            fr_issues["too_short"] += 1
        norm = re.sub(r"\s+", " ", text.lower())
        fr_texts[norm] = fr_texts.get(norm, 0) + 1

    fr_issues["duplicates"] = sum(v - 1 for v in fr_texts.values() if v > 1)

    print(f"  Total French chunks: {len(fr_chunks)}")
    for k, v in fr_issues.items():
        icon = "+" if v == 0 else "!"
        status = "PROPRE" if v == 0 else f"{v} restant(s)"
        print(f"  [{icon}] {k:.<40} {status}")

    # Final verdict
    total = sum(issues.values()) + sum(fr_issues.values())
    print("\n" + "=" * 60)
    if total == 0:
        print("  VERDICT FINAL: DONNEES 100%% PROPRES")
    else:
        print(f"  VERDICT FINAL: {total} artefact(s) mineur(s) restant(s)")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(verify())
