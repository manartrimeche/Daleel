"""
File text extraction utility for the chat upload (ask-with-document) endpoint.
"""

import logging
import re
import tempfile
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt", ".png", ".jpg", ".jpeg", ".webp"}
ALLOWED_MIMES = {
    ".pdf": {"application/pdf"},
    ".docx": {"application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
    ".doc": {"application/msword"},
    ".txt": {"text/plain"},
    ".png": {"image/png"},
    ".jpg": {"image/jpeg"},
    ".jpeg": {"image/jpeg"},
    ".webp": {"image/webp"},
}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
DEFAULT_MAX_CHARS = 12_000

_ERROR_RESULT = {"text": "", "truncated": False, "page_count": 0, "ocr_used": False}


def _sanitize_filename(raw: str) -> str:
    """Strip path traversal, dot-files, and control characters from a user-supplied filename."""
    name = Path(raw).name
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)
    name = name.lstrip(".")
    return name[:255] or "upload"


async def extract_text_from_upload(
    file_bytes: bytes,
    filename: str,
    max_chars: int = DEFAULT_MAX_CHARS,
    content_type: str | None = None,
) -> dict:
    """Extract text from an uploaded file.

    Returns dict with keys:
      - text: extracted text (truncated to max_chars)
      - truncated: bool — whether the text was truncated
      - page_count: number of pages extracted
      - ocr_used: bool
      - error: optional error message
    """
    from app.processing.extractor import extract_pdf, extract_docx, extract_txt

    filename = _sanitize_filename(filename)
    ext = Path(filename).suffix.lower()

    if ext not in ALLOWED_EXTENSIONS:
        return {**_ERROR_RESULT, "error": f"Type de fichier non supporté : {ext}"}

    if content_type:
        allowed_mimes = ALLOWED_MIMES.get(ext, set())
        if allowed_mimes and content_type not in allowed_mimes and content_type != "application/octet-stream":
            logger.warning("MIME mismatch: ext=%s content_type=%s file=%s", ext, content_type, filename)
            return {**_ERROR_RESULT, "error": f"Le type MIME ne correspond pas à l'extension {ext}."}

    if len(file_bytes) > MAX_FILE_SIZE:
        return {**_ERROR_RESULT, "error": "Fichier trop volumineux (max 50 Mo)."}

    extracted_text = ""
    page_count = 0
    ocr_used = False
    tmp_path: Optional[Path] = None

    try:
        # Write to temp file for extractors that need a file path
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            tmp.write(file_bytes)
            tmp_path = Path(tmp.name)

        if ext == ".pdf":
            pages = extract_pdf(tmp_path, original_filename=filename)
            extracted_text = "\n\n".join(p["text"] for p in pages if p.get("text"))
            page_count = len(pages)
            ocr_used = any(p.get("ocr_used") for p in pages)

        elif ext in (".docx", ".doc"):
            pages = extract_docx(tmp_path, original_filename=filename)
            extracted_text = "\n\n".join(p["text"] for p in pages if p.get("text"))
            page_count = len(pages)

        elif ext == ".txt":
            pages = extract_txt(tmp_path, original_filename=filename)
            extracted_text = "\n\n".join(p["text"] for p in pages if p.get("text"))
            page_count = 1

        elif ext in (".png", ".jpg", ".jpeg", ".webp"):
            from app.services.case_document_service import extract_text_with_ocr
            ocr_result = await extract_text_with_ocr(file_bytes, filename)
            extracted_text = ocr_result.get("text", "")
            ocr_used = True
            page_count = 1

    except Exception as e:
        logger.error("Document extraction failed for '%s': %s", filename, e, exc_info=True)
        return {**_ERROR_RESULT, "error": "Impossible d'extraire le texte du document."}
    finally:
        # Always clean up temp file
        if tmp_path:
            try:
                tmp_path.unlink()
            except Exception:
                pass

    if not extracted_text or len(extracted_text.strip()) < 10:
        return {
            "text": "",
            "truncated": False,
            "page_count": page_count,
            "ocr_used": ocr_used,
            "error": "Le document semble vide ou illisible.",
        }

    # Truncate intelligently at paragraph boundary
    truncated = False
    if len(extracted_text) > max_chars:
        # Find the last paragraph break before max_chars
        cut_point = extracted_text.rfind("\n\n", 0, max_chars)
        if cut_point < max_chars * 0.5:
            # No good paragraph break found, cut at last newline
            cut_point = extracted_text.rfind("\n", 0, max_chars)
        if cut_point < max_chars * 0.5:
            # No newline either, hard cut
            cut_point = max_chars
        extracted_text = extracted_text[:cut_point] + "\n\n[… document tronqué …]"
        truncated = True

    return {
        "text": extracted_text,
        "truncated": truncated,
        "page_count": page_count,
        "ocr_used": ocr_used,
        "error": None,
    }
