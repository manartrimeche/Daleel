import time

from app.services.llm_cache import LLMCache


def test_cache_miss_returns_none_on_empty_cache():
    cache = LLMCache(ttl_seconds=3600, max_size=10)
    assert cache.get("What is labor law?", [{"id": "c1"}]) is None


def test_cache_hit_returns_answer_after_set():
    cache = LLMCache(ttl_seconds=3600, max_size=10)
    chunks = [{"id": "c1", "text": "chunk one"}]
    cache.set("Question", chunks, "Cached answer")
    assert cache.get("Question", chunks) == "Cached answer"


def test_ttl_expiry_returns_none_after_expiry():
    cache = LLMCache(ttl_seconds=1, max_size=10)
    chunks = [{"id": "c1"}]
    cache.set("Question", chunks, "Old answer")
    time.sleep(1.1)
    assert cache.get("Question", chunks) is None


def test_max_size_evicts_oldest_entries():
    cache = LLMCache(ttl_seconds=3600, max_size=5)
    for i in range(6):
        cache.set(f"q{i}", [{"id": f"c{i}"}], f"a{i}")
    assert len(cache._store) == 5
    assert cache.get("q0", [{"id": "c0"}]) is None
    assert cache.get("q5", [{"id": "c5"}]) == "a5"


def test_invalidate_all_clears_cache():
    cache = LLMCache(ttl_seconds=3600, max_size=10)
    cache.set("Question", [{"id": "c1"}], "answer")
    assert len(cache._store) == 1
    cache.invalidate_all()
    assert len(cache._store) == 0


def test_same_question_different_chunks_different_key():
    cache = LLMCache(ttl_seconds=3600, max_size=10)
    q = "same question"
    chunks_a = [{"id": "A"}]
    chunks_b = [{"id": "B"}]
    key_a = cache._make_key(q, chunks_a)
    key_b = cache._make_key(q, chunks_b)
    assert key_a != key_b
