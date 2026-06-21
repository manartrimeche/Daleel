"""Tests for exigence_match_service."""

from unittest.mock import AsyncMock, patch

import numpy as np
import pytest

from app.services import exigence_match_service as svc


@pytest.fixture(autouse=True)
def _clear_cache():
    svc._exigence_cache.clear()
    yield
    svc._exigence_cache.clear()


def test_cosine_similarity_basic():
    a = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    b = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    assert svc._cosine_similarity(a, b) == pytest.approx(1.0)

    c = np.array([0.0, 1.0, 0.0], dtype=np.float32)
    assert svc._cosine_similarity(a, c) == pytest.approx(0.0)


def test_cosine_similarity_zero_vector():
    a = np.array([0.0, 0.0, 0.0], dtype=np.float32)
    b = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    assert svc._cosine_similarity(a, b) == 0.0


def test_detect_language_arabic():
    assert svc._detect_language("ما هي العقوبات المنصوص عليها") == "ar"


def test_detect_language_french_default():
    assert svc._detect_language("Quelles sont les obligations ?") == "fr"


def test_invalidate_cache_specific_document_drops_all_language_variants():
    svc._exigence_cache["doc1:fr"] = [({"x": 1}, np.zeros(3, dtype=np.float32))]
    svc._exigence_cache["doc1:ar"] = [({"x": 2}, np.zeros(3, dtype=np.float32))]
    svc._exigence_cache["doc2:fr"] = [({"x": 3}, np.zeros(3, dtype=np.float32))]

    svc.invalidate_cache("doc1")

    assert "doc1:fr" not in svc._exigence_cache
    assert "doc1:ar" not in svc._exigence_cache
    assert "doc2:fr" in svc._exigence_cache


def test_invalidate_cache_no_arg_clears_all():
    svc._exigence_cache["doc1:fr"] = [({"x": 1}, np.zeros(3, dtype=np.float32))]
    svc._exigence_cache["doc2:fr"] = [({"x": 2}, np.zeros(3, dtype=np.float32))]

    svc.invalidate_cache()

    assert svc._exigence_cache == {}


@pytest.mark.asyncio
async def test_match_exigences_empty_when_no_exigences():
    svc._exigence_cache["__all__:fr"] = []
    with patch.object(svc, "embed_text_async", new=AsyncMock(return_value=[0.1, 0.2, 0.3])):
        results = await svc.match_exigences("test query", language="fr")
    assert results == []


@pytest.mark.asyncio
async def test_match_exigences_ranks_by_similarity_and_filters_min_score():
    # Two cached exigences: one aligned with query embedding, one orthogonal.
    aligned_vec = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    orthogonal_vec = np.array([0.0, 1.0, 0.0], dtype=np.float32)
    svc._exigence_cache["__all__:fr"] = [
        (
            {
                "text": "Article aligné",
                "exigence_type": "obligation",
                "article_reference": "Art. 1",
                "document_id": "d1",
                "page_number": 1,
                "confidence_score": 0.9,
            },
            aligned_vec,
        ),
        (
            {
                "text": "Article orthogonal",
                "exigence_type": "obligation",
                "article_reference": "Art. 2",
                "document_id": "d1",
                "page_number": 2,
                "confidence_score": 0.8,
            },
            orthogonal_vec,
        ),
    ]

    with patch.object(svc, "embed_text_async", new=AsyncMock(return_value=[1.0, 0.0, 0.0])):
        results = await svc.match_exigences("query", language="fr", min_score=0.5)

    assert len(results) == 1
    assert results[0]["article"] == "Art. 1"
    assert results[0]["type"] == "Obligation"
    assert results[0]["relevance_score"] == pytest.approx(1.0)
    assert "criticality_level" in results[0]


@pytest.mark.asyncio
async def test_match_exigences_filters_by_type():
    vec = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    svc._exigence_cache["__all__:fr"] = [
        (
            {
                "text": "Obligation A",
                "exigence_type": "obligation",
                "article_reference": "Art. 1",
                "document_id": "d1",
                "page_number": 1,
            },
            vec,
        ),
        (
            {
                "text": "Sanction B",
                "exigence_type": "sanction",
                "article_reference": "Art. 2",
                "document_id": "d1",
                "page_number": 2,
            },
            vec,
        ),
    ]

    with patch.object(svc, "embed_text_async", new=AsyncMock(return_value=[1.0, 0.0, 0.0])):
        results = await svc.match_exigences(
            "query", language="fr", exigence_type="sanction", min_score=0.1,
        )

    assert len(results) == 1
    assert results[0]["type"] == "Sanction"
