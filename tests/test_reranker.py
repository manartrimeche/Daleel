import pytest

from app.services.reranker import RerankingService


@pytest.mark.asyncio
async def test_rerank_returns_chunks_sorted_by_score(monkeypatch):
    monkeypatch.setenv("ENABLE_CROSS_ENCODER", "true")
    service = RerankingService()

    chunks = [
        {"id": "a", "text": "alpha"},
        {"id": "b", "text": "beta"},
        {"id": "c", "text": "gamma"},
    ]
    score_by_text = {"alpha": 0.1, "beta": 0.9, "gamma": 0.4}

    monkeypatch.setattr(service, "_ensure_model_loaded", lambda: True)
    monkeypatch.setattr(
        service,
        "_score_pairs",
        lambda pairs: [score_by_text[text] for _, text in pairs],
    )

    ranked = await service.rerank("query", chunks)

    assert [chunk["id"] for chunk in ranked] == ["b", "c", "a"]
    assert [chunk["rerank_score"] for chunk in ranked] == [0.9, 0.4, 0.1]


@pytest.mark.asyncio
async def test_rerank_handles_empty_chunk_list(monkeypatch):
    monkeypatch.setenv("ENABLE_CROSS_ENCODER", "true")
    service = RerankingService()

    result = await service.rerank("query", [])

    assert result == []


@pytest.mark.asyncio
async def test_rerank_limits_to_20_chunks(monkeypatch):
    monkeypatch.setenv("ENABLE_CROSS_ENCODER", "true")
    service = RerankingService()

    chunks = [{"id": i, "text": f"chunk-{i}"} for i in range(25)]

    monkeypatch.setattr(service, "_ensure_model_loaded", lambda: True)
    monkeypatch.setattr(
        service,
        "_score_pairs",
        lambda pairs: [float(i) for i, _ in enumerate(pairs)],
    )

    ranked = await service.rerank("query", chunks)

    assert len(ranked) == 20
    assert ranked[0]["id"] == 19
    assert ranked[-1]["id"] == 0


@pytest.mark.asyncio
async def test_rerank_fallback_when_feature_disabled(monkeypatch):
    monkeypatch.setenv("ENABLE_CROSS_ENCODER", "false")
    service = RerankingService()

    chunks = [{"id": "x", "text": "one"}, {"id": "y", "text": "two"}]
    result = await service.rerank("query", chunks)

    assert service.is_available() is False
    assert result == chunks
    assert all("rerank_score" not in chunk for chunk in result)
