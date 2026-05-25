"""Tests for search_service — pure utility functions."""

import numpy as np
from app.services.search_service import (
    _parse_language_filter,
    _cosine_similarity,
    invalidate_embedding_dimension_cache,
    create_vector_index,
)
import pytest


class TestParseLanguageFilter:
    def test_none_returns_empty(self):
        assert _parse_language_filter(None) == []

    def test_empty_string_returns_empty(self):
        assert _parse_language_filter("") == []

    def test_single_language(self):
        assert _parse_language_filter("fr") == ["fr"]

    def test_multiple_languages(self):
        result = _parse_language_filter("fr+ar+en")
        assert result == ["fr", "ar", "en"]

    def test_deduplicates(self):
        result = _parse_language_filter("fr+fr+ar")
        assert result == ["fr", "ar"]

    def test_trims_whitespace(self):
        result = _parse_language_filter(" fr + ar ")
        assert result == ["fr", "ar"]

    def test_only_plus_returns_empty(self):
        assert _parse_language_filter("+") == []

    def test_preserves_order(self):
        result = _parse_language_filter("ar+fr+en")
        assert result == ["ar", "fr", "en"]


class TestCosineSimilarity:
    def test_identical_vectors(self):
        v = [1.0, 0.0, 0.0]
        assert abs(_cosine_similarity(v, v) - 1.0) < 1e-6

    def test_orthogonal_vectors(self):
        a = [1.0, 0.0]
        b = [0.0, 1.0]
        assert abs(_cosine_similarity(a, b)) < 1e-6

    def test_opposite_vectors(self):
        a = [1.0, 0.0]
        b = [-1.0, 0.0]
        assert abs(_cosine_similarity(a, b) - (-1.0)) < 1e-6

    def test_zero_vector(self):
        a = [0.0, 0.0]
        b = [1.0, 0.0]
        assert _cosine_similarity(a, b) == 0.0

    def test_general_case(self):
        a = [1.0, 2.0, 3.0]
        b = [4.0, 5.0, 6.0]
        expected = float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
        assert abs(_cosine_similarity(a, b) - expected) < 1e-6

    def test_high_dimensional(self):
        rng = np.random.default_rng(42)
        a = rng.standard_normal(768).tolist()
        b = rng.standard_normal(768).tolist()
        score = _cosine_similarity(a, b)
        assert -1.0 <= score <= 1.0

    def test_similar_vectors_high_score(self):
        a = [1.0, 2.0, 3.0]
        b = [1.01, 2.01, 3.01]
        assert _cosine_similarity(a, b) > 0.99


class TestInvalidateCache:
    def test_invalidate_sets_none(self):
        import app.services.search_service as mod
        mod._effective_stored_dim_cache = 768
        invalidate_embedding_dimension_cache()
        assert mod._effective_stored_dim_cache is None

    def test_invalidate_from_none(self):
        import app.services.search_service as mod
        mod._effective_stored_dim_cache = None
        invalidate_embedding_dimension_cache()
        assert mod._effective_stored_dim_cache is None


@pytest.mark.asyncio
async def test_create_vector_index_returns_not_applicable():
    from unittest.mock import MagicMock
    db = MagicMock()
    result = await create_vector_index(db)
    assert result["status"] == "not_applicable"
    assert "Python" in result["message"]
