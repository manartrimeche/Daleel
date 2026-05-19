"""
Unit tests for app.services.faiss_index — FAISS index manager.
"""

import unittest

import numpy as np

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False

from app.services.faiss_index import _parse_lang_filter


class TestParseLangFilter(unittest.TestCase):
    def test_none(self):
        self.assertEqual(_parse_lang_filter(None), [])

    def test_empty(self):
        self.assertEqual(_parse_lang_filter(""), [])

    def test_single(self):
        self.assertEqual(_parse_lang_filter("fr"), ["fr"])

    def test_multi(self):
        self.assertEqual(_parse_lang_filter("ar+fr"), ["ar", "fr"])

    def test_dedup(self):
        self.assertEqual(_parse_lang_filter("fr+fr"), ["fr"])


@unittest.skipUnless(FAISS_AVAILABLE, "faiss-cpu not installed")
class TestFaissBasicOperations(unittest.TestCase):
    def test_flat_ip_search(self):
        """Verify that FAISS IndexFlatIP works as expected for normalized vectors."""
        dim = 768
        n = 100
        rng = np.random.default_rng(42)

        # Create random normalized vectors
        data = rng.standard_normal((n, dim)).astype(np.float32)
        faiss.normalize_L2(data)

        index = faiss.IndexFlatIP(dim)
        index.add(data)
        self.assertEqual(index.ntotal, n)

        # Search with first vector — should return itself as top-1
        query = data[0:1].copy()
        scores, indices = index.search(query, 1)
        self.assertEqual(indices[0][0], 0)
        self.assertAlmostEqual(scores[0][0], 1.0, places=4)

    def test_dimension_mismatch_raises(self):
        index = faiss.IndexFlatIP(768)
        data = np.random.randn(1, 384).astype(np.float32)
        with self.assertRaises(Exception):
            index.add(data)

    def test_empty_index_search(self):
        index = faiss.IndexFlatIP(768)
        query = np.random.randn(1, 768).astype(np.float32)
        faiss.normalize_L2(query)
        scores, indices = index.search(query, 5)
        # Empty index returns -1 indices
        self.assertTrue(all(idx == -1 for idx in indices[0]))


if __name__ == "__main__":
    unittest.main()
