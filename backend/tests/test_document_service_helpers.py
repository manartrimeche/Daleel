"""Unit tests for document_service.py helper functions.

These functions are pure / side-effect free and easy to test in isolation.
"""

from app.services import document_service as ds


# ─────────────────────────────────────────────────────────────
# _doc_to_out
# ─────────────────────────────────────────────────────────────

class TestDocToOut:
    def test_none_returns_none(self):
        assert ds._doc_to_out(None) is None

    def test_basic_mapping(self):
        doc = {
            "id": "doc-1",
            "filename": "test.pdf",
            "file_type": "pdf",
            "status": "ready",
            "language": "fr",
            "created_at": "2024-01-01",
            "updated_at": "2024-01-02",
            "total_chunks": 5,
            "total_pages": 10,
            "file_hash": "abc123",
            "error_message": None,
        }
        out = ds._doc_to_out(doc)
        assert out["id"] == "doc-1"
        assert out["filename"] == "test.pdf"
        assert out["total_chunks"] == 5
        assert "_id" not in out

    def test_missing_fields_default_to_none(self):
        out = ds._doc_to_out({"id": "doc-1"})
        assert out["filename"] is None
        assert out["total_chunks"] is None


# ─────────────────────────────────────────────────────────────
# _chunk_to_out
# ─────────────────────────────────────────────────────────────

class TestChunkToOut:
    def test_basic_mapping(self):
        chunk = {
            "id": "c-1",
            "document_id": "doc-1",
            "text": "some text",
            "page_number": 3,
            "section": "Article 5",
            "language": "fr",
            "embedding_id": "emb-1",
        }
        out = ds._chunk_to_out(chunk)
        assert out["id"] == "c-1"
        assert out["page_number"] == 3
        assert "_id" not in out


# ─────────────────────────────────────────────────────────────
# _raw_page_to_out
# ─────────────────────────────────────────────────────────────

class TestRawPageToOut:
    def test_basic_mapping(self):
        page = {
            "id": "rp-1",
            "document_id": "doc-1",
            "page_number": 1,
            "raw_text": "raw text",
            "ocr_used": True,
            "extracted_at": "2024-01-01",
        }
        out = ds._raw_page_to_out(page)
        assert out["ocr_used"] is True
        assert out["raw_text"] == "raw text"


# ─────────────────────────────────────────────────────────────
# _source_to_out
# ─────────────────────────────────────────────────────────────

class TestSourceToOut:
    def test_basic_mapping(self):
        source = {
            "id": "s-1",
            "document_id": "doc-1",
            "source_path": "/uploads/source.pdf",
            "file_hash": "hash123",
            "language": "fr",
            "uploaded_at": "2024-01-01",
        }
        out = ds._source_to_out(source)
        assert out["source_path"] == "/uploads/source.pdf"
        assert out["file_hash"] == "hash123"


# ─────────────────────────────────────────────────────────────
# _cleaned_text_to_out
# ─────────────────────────────────────────────────────────────

class TestCleanedTextToOut:
    def test_basic_mapping(self):
        cleaned = {
            "id": "ct-1",
            "document_id": "doc-1",
            "page_number": 2,
            "cleaned_text": "cleaned text",
            "transformation_rules": ["strip_spaces"],
            "cleaned_at": "2024-01-01",
        }
        out = ds._cleaned_text_to_out(cleaned)
        assert out["cleaned_text"] == "cleaned text"
        assert out["transformation_rules"] == ["strip_spaces"]


# ─────────────────────────────────────────────────────────────
# _exigence_to_out
# ─────────────────────────────────────────────────────────────

class TestExigenceToOut:
    def test_basic_mapping(self):
        ex = {
            "id": "ex-1",
            "document_id": "doc-1",
            "page_number": 1,
            "article_reference": "Art. 5",
            "exigence_type": "obligation",
            "text": "must do X",
            "confidence_score": 0.95,
            "source_citation": "page 1",
            "extracted_at": "2024-01-01",
        }
        out = ds._exigence_to_out(ex)
        assert out["exigence_type"] == "obligation"
        assert out["confidence_score"] == 0.95


# ─────────────────────────────────────────────────────────────
# _normalize_for_match
# ─────────────────────────────────────────────────────────────

class TestNormalizeForMatch:
    def test_lowercase(self):
        assert ds._normalize_for_match("ABC") == "abc"

    def test_arabic_diacritics_removed(self):
        # shadda, fatha, etc. should be stripped
        assert ds._normalize_for_match("مُحامٍ") == "محام"

    def test_nfkc_normalisation(self):
        # Full-width numbers → half-width
        assert ds._normalize_for_match("ＡＢＣ") == "abc"


# ─────────────────────────────────────────────────────────────
# _extract_article_refs
# ─────────────────────────────────────────────────────────────

class TestExtractArticleRefs:
    def test_french_article_refs(self):
        text = "Article 95 et Article 15 sont concernés."
        refs = ds._extract_article_refs(text)
        assert "95" in refs
        assert "15" in refs

    def test_arabic_article_refs(self):
        text = "الفصل 95 والفصل 15"
        refs = ds._extract_article_refs(text)
        assert "95" in refs
        assert "15" in refs

    def test_no_refs(self):
        assert ds._extract_article_refs("Aucun article mentionné.") == set()


# ─────────────────────────────────────────────────────────────
# _token_overlap_score
# ─────────────────────────────────────────────────────────────

class TestTokenOverlapScore:
    def test_perfect_match(self):
        assert ds._token_overlap_score("hello world", "hello world") == 1.0

    def test_partial_match(self):
        score = ds._token_overlap_score("hello world foo", "hello world bar")
        # shared = hello, world (2/3 candidate tokens)
        assert abs(score - 2 / 3) < 0.01

    def test_no_overlap(self):
        assert ds._token_overlap_score("abc", "xyz") == 0.0

    def test_short_words_ignored(self):
        # tokens < 3 chars are ignored
        assert ds._token_overlap_score("a b c", "a b c d e f") == 0.0


# ─────────────────────────────────────────────────────────────
# _is_grounded_exigence
# ─────────────────────────────────────────────────────────────

class TestIsGroundedExigence:
    def test_valid_obligation(self):
        exigence = {"type": "obligation", "text": "must do X immediately"}
        assert ds._is_grounded_exigence(exigence, "some context with must do X immediately") is True

    def test_invalid_type(self):
        exigence = {"type": "invalid", "text": "something"}
        assert ds._is_grounded_exigence(exigence, "context") is False

    def test_missing_text(self):
        exigence = {"type": "obligation", "text": ""}
        assert ds._is_grounded_exigence(exigence, "context") is False
