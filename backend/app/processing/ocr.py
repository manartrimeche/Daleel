"""
OCR engine — Tesseract (primary, fast) with EasyOCR fallback.
"""

import shutil
import os
import logging
from pathlib import Path
from typing import Optional

from app.config import get_settings
from app.processing.text_utils import clean_text

logger = logging.getLogger(__name__)
settings = get_settings()

# ── Tesseract ──

_tesseract_available: Optional[bool] = None


def _resolve_tesseract_cmd() -> str | None:
    configured_path = (settings.tesseract_path or "").strip()
    if configured_path and os.path.isfile(configured_path):
        return configured_path

    env_path = shutil.which("tesseract")
    if env_path:
        return env_path

    common_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ]
    for candidate in common_paths:
        if os.path.isfile(candidate):
            return candidate

    return None


def _check_tesseract() -> bool:
    global _tesseract_available
    if _tesseract_available is not None:
        return _tesseract_available
    try:
        import pytesseract
        tesseract_cmd = _resolve_tesseract_cmd()
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        pytesseract.get_tesseract_version()
        _tesseract_available = True
        logger.info("Tesseract OCR engine found")
    except Exception:
        _tesseract_available = False
        logger.warning("Tesseract not available — will use EasyOCR (slower)")
    return _tesseract_available


def _ocr_tesseract(image, hint_arabic: bool = True) -> str:
    import pytesseract
    from PIL import Image
    if not isinstance(image, Image.Image):
        image = Image.fromarray(image)
    lang = "ara+fra" if hint_arabic else "fra+eng"
    # --psm 3: fully automatic page segmentation (better for Arabic multi-line)
    # --oem 3: LSTM neural net engine for better Arabic recognition
    text = pytesseract.image_to_string(image, lang=lang, config="--psm 3 --oem 3")
    return text or ""


# ── EasyOCR (lazy-loaded) ──

_ocr_reader_arabic = None
_ocr_reader_latin = None


def _load_reader(lang_list: list):
    try:
        import easyocr
        logger.info(f"Loading EasyOCR model {lang_list} …")
        reader = easyocr.Reader(lang_list, gpu=False, verbose=False)
        logger.info("EasyOCR ready.")
        return reader
    except ImportError:
        logger.error("easyocr is not installed. OCR will be skipped.")
        return None


def _get_ocr_reader(arabic: bool = True):
    global _ocr_reader_arabic, _ocr_reader_latin
    if arabic:
        if _ocr_reader_arabic is None:
            _ocr_reader_arabic = _load_reader(["ar", "en"])
        return _ocr_reader_arabic
    else:
        if _ocr_reader_latin is None:
            _ocr_reader_latin = _load_reader(["fr", "en"])
        return _ocr_reader_latin


# ── Public API ──

def ocr_image_array(img_array, hint_arabic: bool = True) -> str:
    """OCR a numpy image array. Tesseract first, EasyOCR fallback."""
    if _check_tesseract():
        try:
            text = clean_text(_ocr_tesseract(img_array, hint_arabic))
            if text and len(text.strip()) > 10:
                return text
        except Exception as e:
            logger.warning("  Tesseract failed: %s", e)

    reader = _get_ocr_reader(arabic=hint_arabic)
    if reader is None:
        return ""
    results = reader.readtext(img_array, detail=0, paragraph=True)
    text = "\n".join(results)
    if not text.strip():
        fallback = _get_ocr_reader(arabic=not hint_arabic)
        if fallback:
            results = fallback.readtext(img_array, detail=0, paragraph=True)
            text = "\n".join(results)
    return text


def ocr_image_file(file_path: Path, hint_arabic: bool = True) -> str:
    """OCR an image file."""
    if _check_tesseract():
        try:
            from PIL import Image
            img = Image.open(str(file_path))
            text = clean_text(_ocr_tesseract(img, hint_arabic))
            if text and len(text.strip()) > 10:
                return text
        except Exception as e:
            logger.warning("  Tesseract failed on file: %s", e)

    reader = _get_ocr_reader(arabic=hint_arabic)
    if reader is None:
        return ""
    results = reader.readtext(str(file_path), detail=0, paragraph=True)
    text = "\n".join(results)
    if not text.strip():
        fallback = _get_ocr_reader(arabic=not hint_arabic)
        if fallback:
            results = fallback.readtext(str(file_path), detail=0, paragraph=True)
            text = "\n".join(results)
    return text
