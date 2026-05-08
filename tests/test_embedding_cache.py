"""
Unit tests for the embedding LRU cache in app.services.embedding_service.
"""

import unittest

from app.services.embedding_service import _EmbeddingCache


class TestEmbeddingCache(unittest.TestCase):
    def test_put_and_get(self):
        cache = _EmbeddingCache(maxsize=10)
        vec = [0.1, 0.2, 0.3]
        cache.put("hello", 768, vec)
        self.assertEqual(cache.get("hello", 768), vec)

    def test_miss_returns_none(self):
        cache = _EmbeddingCache(maxsize=10)
        self.assertIsNone(cache.get("missing", 768))

    def test_different_dim_different_key(self):
        cache = _EmbeddingCache(maxsize=10)
        cache.put("test", 768, [1.0])
        cache.put("test", 384, [2.0])
        self.assertEqual(cache.get("test", 768), [1.0])
        self.assertEqual(cache.get("test", 384), [2.0])

    def test_eviction_at_maxsize(self):
        cache = _EmbeddingCache(maxsize=3)
        cache.put("a", 768, [1.0])
        cache.put("b", 768, [2.0])
        cache.put("c", 768, [3.0])
        cache.put("d", 768, [4.0])  # should evict "a"
        self.assertIsNone(cache.get("a", 768))
        self.assertEqual(cache.get("d", 768), [4.0])

    def test_lru_ordering(self):
        cache = _EmbeddingCache(maxsize=3)
        cache.put("a", 768, [1.0])
        cache.put("b", 768, [2.0])
        cache.put("c", 768, [3.0])
        # Access "a" to make it recently used
        cache.get("a", 768)
        # Insert "d" — should evict "b" (oldest untouched)
        cache.put("d", 768, [4.0])
        self.assertIsNone(cache.get("b", 768))
        self.assertEqual(cache.get("a", 768), [1.0])

    def test_stats(self):
        cache = _EmbeddingCache(maxsize=10)
        cache.put("x", 768, [1.0])
        cache.get("x", 768)  # hit
        cache.get("y", 768)  # miss
        stats = cache.stats
        self.assertEqual(stats["size"], 1)
        self.assertEqual(stats["hits"], 1)
        self.assertEqual(stats["misses"], 1)
        self.assertAlmostEqual(stats["hit_rate"], 0.5)

    def test_overwrite_same_key(self):
        cache = _EmbeddingCache(maxsize=10)
        cache.put("x", 768, [1.0])
        cache.put("x", 768, [2.0])
        self.assertEqual(cache.get("x", 768), [2.0])
        self.assertEqual(cache.stats["size"], 1)

    def test_empty_cache_stats(self):
        cache = _EmbeddingCache(maxsize=5)
        stats = cache.stats
        self.assertEqual(stats["size"], 0)
        self.assertEqual(stats["hits"], 0)
        self.assertEqual(stats["misses"], 0)
        self.assertAlmostEqual(stats["hit_rate"], 0.0)


if __name__ == "__main__":
    unittest.main()
