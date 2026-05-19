"""Batch-clean Arabic OCR noise in JSON/JSONL datasets.

Usage:
  python training/clean_all_datasets.py --root training/data --dry-run
  python training/clean_all_datasets.py --root training/data --write
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Any

# Allow running this script directly from the repository root.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.processing.text_utils import clean_arabic_ocr_text


@dataclass
class FileStats:
    path: Path
    changed_lines: int = 0
    changed_strings: int = 0
    total_strings: int = 0


def _contains_arabic(text: str) -> bool:
    return any("\u0600" <= ch <= "\u06FF" for ch in text)


def _clean_string(value: str, ta_marbuta_form: str) -> tuple[str, bool]:
    if not value or not _contains_arabic(value):
        return value, False
    cleaned = clean_arabic_ocr_text(value, ta_marbuta_form=ta_marbuta_form)
    return cleaned, cleaned != value


def _clean_obj(obj: Any, ta_marbuta_form: str, stats: FileStats) -> Any:
    if isinstance(obj, str):
        stats.total_strings += 1
        cleaned, changed = _clean_string(obj, ta_marbuta_form)
        if changed:
            stats.changed_strings += 1
        return cleaned
    if isinstance(obj, list):
        return [_clean_obj(item, ta_marbuta_form, stats) for item in obj]
    if isinstance(obj, dict):
        return {key: _clean_obj(val, ta_marbuta_form, stats) for key, val in obj.items()}
    return obj


def _process_jsonl(path: Path, write: bool, ta_marbuta_form: str) -> FileStats:
    stats = FileStats(path=path)
    out_lines: list[str] = []

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            raw = line.rstrip("\n")
            if not raw.strip():
                out_lines.append("")
                continue

            obj = json.loads(raw)
            before = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
            cleaned_obj = _clean_obj(obj, ta_marbuta_form, stats)
            after = json.dumps(cleaned_obj, ensure_ascii=False, separators=(",", ":"))
            if after != before:
                stats.changed_lines += 1
            out_lines.append(after)

    if write and stats.changed_lines > 0:
        path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")

    return stats


def _process_json(path: Path, write: bool, ta_marbuta_form: str) -> FileStats:
    stats = FileStats(path=path)

    with path.open("r", encoding="utf-8") as f:
        obj = json.load(f)

    before = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    cleaned_obj = _clean_obj(obj, ta_marbuta_form, stats)
    after = json.dumps(cleaned_obj, ensure_ascii=False, separators=(",", ":"))

    if after != before:
        stats.changed_lines = 1
        if write:
            path.write_text(
                json.dumps(cleaned_obj, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Clean Arabic OCR noise across dataset files.")
    parser.add_argument("--root", type=Path, default=Path("training/data"))
    parser.add_argument("--write", action="store_true", help="Write changes to disk.")
    parser.add_argument("--dry-run", action="store_true", help="Compute stats without writing.")
    parser.add_argument(
        "--ta-marbuta-form",
        choices=("ة", "ه"),
        default="ة",
        help="Normalization target for ta marbuta.",
    )
    args = parser.parse_args()

    if args.write and args.dry_run:
        raise SystemExit("Use either --write or --dry-run, not both.")

    write = args.write and not args.dry_run

    patterns = ("*.jsonl", "*.json")
    files: list[Path] = []
    for pattern in patterns:
        files.extend(sorted(args.root.rglob(pattern)))

    if not files:
        print(f"No dataset files found under {args.root}")
        return

    all_stats: list[FileStats] = []
    for path in files:
        if path.suffix.lower() == ".jsonl":
            st = _process_jsonl(path, write=write, ta_marbuta_form=args.ta_marbuta_form)
        else:
            st = _process_json(path, write=write, ta_marbuta_form=args.ta_marbuta_form)
        all_stats.append(st)

    changed_files = [s for s in all_stats if s.changed_lines > 0]
    total_changed_lines = sum(s.changed_lines for s in all_stats)
    total_changed_strings = sum(s.changed_strings for s in all_stats)
    total_strings = sum(s.total_strings for s in all_stats)

    mode = "WRITE" if write else "DRY-RUN"
    print(f"[{mode}] files scanned: {len(all_stats)}")
    print(f"[{mode}] files changed: {len(changed_files)}")
    print(f"[{mode}] changed lines/items: {total_changed_lines}")
    print(f"[{mode}] changed strings: {total_changed_strings}/{total_strings}")

    if changed_files:
        print("\nTop changed files:")
        for st in sorted(changed_files, key=lambda x: x.changed_lines, reverse=True)[:20]:
            rel = st.path.as_posix()
            print(f"- {rel}: lines/items={st.changed_lines}, strings={st.changed_strings}")


if __name__ == "__main__":
    main()
