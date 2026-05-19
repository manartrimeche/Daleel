"""
Tests for the Case Document Service.

Covers:
- Document role validation
- Helper functions (image detection, scanned PDF detection)
- Schemas and enums
- Basic service imports
"""

import pytest
from datetime import datetime, timezone, date

from app.services import case_document_service
from app.case_schemas import DOCUMENT_ROLES


# ─────────────────────────────────────────────────────────────
# Document Role Tests
# ─────────────────────────────────────────────────────────────

def test_document_roles_defined():
    """Verify all expected document roles are defined."""
    expected_roles = [
        "incoming_request",
        "evidence",
        "policy",
        "contract",
        "authority_notice",
        "draft_response",
        "other",
    ]
    for role in expected_roles:
        assert role in DOCUMENT_ROLES, f"Role {role} not found in DOCUMENT_ROLES"


def test_document_roles_validation():
    """Test that all document roles are valid strings."""
    for role in DOCUMENT_ROLES:
        assert isinstance(role, str)
        assert len(role) > 0
        assert role.islower()


# ─────────────────────────────────────────────────────────────
# Helper Function Tests
# ─────────────────────────────────────────────────────────────

def test_is_image_file_detection():
    """Test image file detection for OCR triggering."""
    image_files = ["photo.png", "scan.jpg", "document.jpeg", "image.tiff", "scan.bmp", "pic.gif"]
    non_image_files = ["document.pdf", "file.docx", "text.txt", "data.csv"]

    for filename in image_files:
        assert case_document_service._is_image_file(filename), f"{filename} should be detected as image"

    for filename in non_image_files:
        assert not case_document_service._is_image_file(filename), f"{filename} should not be detected as image"


def test_is_scanned_pdf_detection_short_text():
    """Test scanned PDF detection for short text."""
    # Very short text indicates scanned PDF
    short_text = "Page 1"
    assert case_document_service._is_scanned_pdf("doc.pdf", short_text), "Short text should be detected as scanned"


def test_is_scanned_pdf_detection_control_chars():
    """Test scanned PDF detection for garbled text with control characters."""
    # Garbled text with control characters indicates scanned PDF
    garbled_text = "Scanned \x00\x01\x02 content"
    assert case_document_service._is_scanned_pdf("doc.pdf", garbled_text), "Control chars should be detected as scanned"


def test_is_scanned_pdf_detection_normal():
    """Test that normal text is not detected as scanned."""
    # Must be at least 100 chars to not trigger the short-text check
    normal_text = (
        "This is a normal PDF document with substantial text content that goes on for many characters. "
        "It contains multiple sentences with proper grammar and no garbled or control characters. "
        "The text is clearly extractable from the PDF and indicates a properly formatted document."
    )
    assert not case_document_service._is_scanned_pdf("doc.pdf", normal_text), "Normal text should not be scanned"


def test_is_scanned_pdf_non_pdf():
    """Test that non-PDF files are not scanned PDFs."""
    assert not case_document_service._is_scanned_pdf("image.png", "some text")
    assert not case_document_service._is_scanned_pdf("doc.txt", "some text")


def test_is_scanned_pdf_empty():
    """Test scanned PDF detection with empty/None content."""
    assert not case_document_service._is_scanned_pdf("doc.pdf", None)
    assert not case_document_service._is_scanned_pdf("doc.pdf", "")


# ─────────────────────────────────────────────────────────────
# Serializer Tests
# ─────────────────────────────────────────────────────────────

def test_case_doc_analysis_to_dict():
    """Test serialization of case document with analysis."""
    doc = {
        "id": "doc_123",
        "case_id": "case_456",
        "document_id": "orig_789",
        "role": "contract",
        "label": "Test Contract",
        "attached_by": "user@test.com",
        "attached_at": datetime.now(timezone.utc),
        "analysis": {"document_type": "contract", "summary": "Test"},
    }

    result = case_document_service._case_doc_analysis_to_dict(doc)

    assert result["id"] == "doc_123"
    assert result["case_id"] == "case_456"
    assert result["role"] == "contract"
    assert result["label"] == "Test Contract"
    assert result["analysis"] is not None


def test_case_doc_analysis_to_dict_defaults():
    """Test serialization with default values."""
    doc = {"id": "doc_123"}  # Minimal doc

    result = case_document_service._case_doc_analysis_to_dict(doc)

    assert result["id"] == "doc_123"
    assert result["role"] == "other"  # Default role
    assert result["label"] is None
    assert result["analysis"] is None


def test_doc_analysis_result_to_dict():
    """Test serialization of document analysis results."""
    doc = {
        "document_id": "orig_789",
        "case_document_id": "doc_123",
        "document_type": "contract",
        "summary": "A test contract",
        "entities": {"parties": ["A", "B"]},
        "obligations": [],
        "deadlines": [],
        "parties": ["Company A"],
        "legal_references": [],
        "confidence": 0.85,
        "analyzed_at": datetime.now(timezone.utc),
        "ocr_used": False,
    }

    result = case_document_service._doc_analysis_result_to_dict(doc)

    assert result["document_type"] == "contract"
    assert result["confidence"] == 0.85
    assert result["ocr_used"] is False


def test_doc_analysis_result_to_dict_defaults():
    """Test analysis result serialization with defaults."""
    doc = {"document_id": "orig_789"}  # Minimal doc

    result = case_document_service._doc_analysis_result_to_dict(doc)

    assert result["document_type"] == "unknown"  # Default
    assert result["summary"] == ""  # Default
    assert result["entities"] == {}  # Default
    assert result["confidence"] == 0.0  # Default
    assert result["ocr_used"] is False  # Default


# ─────────────────────────────────────────────────────────────
# Document Classification Tests (with proper mocking)
# ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_classify_document_empty_text():
    """Test classification handles empty text gracefully."""
    result = await case_document_service.classify_document("", "auto")

    assert result["document_type"] == "unknown"
    assert result["confidence"] == 0.0


@pytest.mark.asyncio
async def test_classify_document_whitespace_only():
    """Test classification handles whitespace-only text."""
    result = await case_document_service.classify_document("   \n\t  ", "fr")

    assert result["document_type"] == "unknown"
    assert result["confidence"] == 0.0


# ─────────────────────────────────────────────────────────────
# Entity Extraction Tests (with proper mocking)
# ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_extract_entities_empty_text():
    """Test entity extraction handles empty text."""
    result = await case_document_service.extract_entities("", "fr")

    assert result["parties"] == []
    assert result["dates"] == []
    assert result["deadlines"] == []
    assert result["obligations"] == []
    assert result["legal_references"] == []
    assert result["monetary_amounts"] == []
    assert result["confidence"] == 0.0


@pytest.mark.asyncio
async def test_extract_entities_whitespace_only():
    """Test entity extraction handles whitespace-only text."""
    result = await case_document_service.extract_entities("   \n\t  ", "fr")

    assert result["parties"] == []
    assert result["confidence"] == 0.0


# ─────────────────────────────────────────────────────────────
# JSON Parsing Tests
# ─────────────────────────────────────────────────────────────

def test_extract_json_from_markdown_code_block():
    """Test extracting JSON from markdown code block."""
    text = """```json
{"key": "value", "number": 42}
```"""
    result = case_document_service._extract_json_from_response(text)

    assert result == {"key": "value", "number": 42}


def test_extract_json_plain():
    """Test extracting plain JSON."""
    text = '{"key": "value", "number": 42}'
    result = case_document_service._extract_json_from_response(text)

    assert result == {"key": "value", "number": 42}


def test_extract_json_invalid():
    """Test handling invalid JSON."""
    text = "This is not JSON"
    result = case_document_service._extract_json_from_response(text)

    assert result == {}


def test_extract_json_partial():
    """Test extracting JSON from text with extra content."""
    text = '```json\n{"result": "success"}\n```'
    result = case_document_service._extract_json_from_response(text)

    assert result == {"result": "success"}


# ─────────────────────────────────────────────────────────────
# Date Parsing Tests
# ─────────────────────────────────────────────────────────────

def test_parse_flexible_date_iso():
    """Test parsing ISO date format."""
    result = case_document_service._parse_flexible_date("2024-01-15")

    assert result == date(2024, 1, 15)


def test_parse_flexible_date_french():
    """Test parsing French date format."""
    result = case_document_service._parse_flexible_date("15 janvier 2024")

    assert result == date(2024, 1, 15)


def test_parse_flexible_date_french_short():
    """Test parsing French short date format."""
    result = case_document_service._parse_flexible_date("15/01/2024")

    assert result == date(2024, 1, 15)


def test_parse_flexible_date_invalid():
    """Test parsing invalid date returns None."""
    result = case_document_service._parse_flexible_date("not a date")

    assert result is None


def test_parse_flexible_date_none():
    """Test parsing None returns None."""
    result = case_document_service._parse_flexible_date(None)

    assert result is None


# ─────────────────────────────────────────────────────────────
# Constants Validation
# ─────────────────────────────────────────────────────────────

def test_document_types_defined():
    """Verify DOCUMENT_TYPES contains expected values."""
    expected_types = [
        "legal_opinion",
        "regulatory_filing",
        "court_decision",
        "contract",
        "policy_document",
        "unknown",
    ]
    for doc_type in expected_types:
        assert doc_type in case_document_service.DOCUMENT_TYPES, f"Type {doc_type} not found"


def test_document_roles_order():
    """Verify first role is incoming_request (most common)."""
    assert DOCUMENT_ROLES[0] == "incoming_request"


# ─────────────────────────────────────────────────────────────
# Integration Smoke Tests
# ─────────────────────────────────────────────────────────────

def test_module_imports():
    """Test that all required modules are importable."""
    # These should not raise
    assert case_document_service.DOCUMENT_ROLES is not None
    assert case_document_service.DOCUMENT_TYPES is not None
    assert callable(case_document_service._is_image_file)
    assert callable(case_document_service._is_scanned_pdf)
    assert callable(case_document_service.classify_document)
    assert callable(case_document_service.extract_entities)
