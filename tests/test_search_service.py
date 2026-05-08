"""
Unit tests for app.services.search_service — cosine similarity, language filter parsing.
"""

import unittest
import numpy as np

from app.services.search_service import _cosine_similarity, _parse_language_filter


class TestCosineSimilarity(unittest.TestCase):
    def test_identical_vectors(self):
        v = [1.0, 0.0, 0.0]
        self.assertAlmostEqual(_cosine_similarity(v, v), 1.0, places=5)

    def test_orthogonal_vectors(self):
        a = [1.0, 0.0, 0.0]
        b = [0.0, 1.0, 0.0]
        self.assertAlmostEqual(_cosine_similarity(a, b), 0.0, places=5)

    def test_opposite_vectors(self):
        a = [1.0, 0.0]
        b = [-1.0, 0.0]
        self.assertAlmostEqual(_cosine_similarity(a, b), -1.0, places=5)

    def test_zero_vector_returns_zero(self):
        a = [0.0, 0.0]
        b = [1.0, 2.0]
        self.assertAlmostEqual(_cosine_similarity(a, b), 0.0, places=5)

    def test_similar_vectors_high_score(self):
        a = [1.0, 2.0, 3.0]
        b = [1.1, 2.1, 3.1]
        score = _cosine_similarity(a, b)
        self.assertGreater(score, 0.99)

    def test_high_dimensional_vectors(self):
        rng = np.random.default_rng(42)
        a = rng.standard_normal(768).tolist()
        b = rng.standard_normal(768).tolist()
        score = _cosine_similarity(a, b)
        self.assertGreaterEqual(score, -1.0)
        self.assertLessEqual(score, 1.0)


class TestParseLanguageFilter(unittest.TestCase):
    def test_none_returns_empty(self):
        self.assertEqual(_parse_language_filter(None), [])

    def test_empty_string_returns_empty(self):
        self.assertEqual(_parse_language_filter(""), [])

    def test_single_language(self):
        self.assertEqual(_parse_language_filter("fr"), ["fr"])

    def test_multi_language(self):
        result = _parse_language_filter("ar+fr")
        self.assertEqual(result, ["ar", "fr"])

    def test_deduplicates(self):
        result = _parse_language_filter("fr+fr+ar")
        self.assertEqual(result, ["fr", "ar"])

    def test_strips_whitespace(self):
        result = _parse_language_filter(" ar + fr ")
        self.assertEqual(result, ["ar", "fr"])


if __name__ == "__main__":
    unittest.main()
