"""Tests for reranker — RerankingService pure methods, constants, and async behavior."""

import os
from unittest.mock import patch, MagicMock

import pytest

from app.services.reranker import RerankingService


class TestConstants:
    def test_model_name(self):
        assert "cross-encoder" in RerankingService.MODEL_NAME

    def test_min_rerank_score(self):
        assert RerankingService.MIN_RERANK_SCORE == -2.0


class TestScorePairs:
    def test_returns_empty_when_model_is_none(self):
        svc = object.__new__(RerankingService)
        svc._model = None
        assert svc._score_pairs([("q", "d")]) == []

    def test_calls_model_predict(self):
        svc = object.__new__(RerankingService)
        mock_model = MagicMock()
        mock_model.predict.return_value = [0.8, -1.5]
        svc._model = mock_model
        pairs = [("query", "doc1"), ("query", "doc2")]
        scores = svc._score_pairs(pairs)
        assert scores == [0.8, -1.5]
        mock_model.predict.assert_called_once_with(pairs)


class TestInit:
    def test_enabled_from_env_true(self):
        with patch("app.services.reranker.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(enable_cross_encoder=False)
            with patch.dict(os.environ, {"ENABLE_CROSS_ENCODER": "true"}):
                svc = RerankingService()
        assert svc.enabled is True

    def test_enabled_from_env_false(self):
        with patch("app.services.reranker.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(enable_cross_encoder=True)
            with patch.dict(os.environ, {"ENABLE_CROSS_ENCODER": "false"}):
                svc = RerankingService()
        assert svc.enabled is False

    def test_enabled_from_settings_when_no_env(self):
        with patch("app.services.reranker.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(enable_cross_encoder=True)
            env = os.environ.copy()
            env.pop("ENABLE_CROSS_ENCODER", None)
            with patch.dict(os.environ, env, clear=True):
                svc = RerankingService()
        assert svc.enabled is True
        assert svc._model is None
        assert svc._load_attempted is False


class TestRerank:
    @pytest.mark.asyncio
    async def test_empty_chunks_returns_empty(self):
        svc = object.__new__(RerankingService)
        svc.enabled = True
        svc._model = None
        svc._load_attempted = False
        svc._load_failed = False
        result = await svc.rerank("query", [])
        assert result == []

    @pytest.mark.asyncio
    async def test_disabled_returns_chunks_unchanged(self):
        svc = object.__new__(RerankingService)
        svc.enabled = False
        svc._model = None
        svc._load_attempted = False
        svc._load_failed = False
        import asyncio
        svc._load_lock = asyncio.Lock()
        chunks = [{"text": "hello"}]
        result = await svc.rerank("query", chunks)
        assert result == chunks

    @pytest.mark.asyncio
    async def test_failed_load_returns_chunks_unchanged(self):
        svc = object.__new__(RerankingService)
        svc.enabled = True
        svc._model = None
        svc._load_attempted = True
        svc._load_failed = True
        import asyncio
        svc._load_lock = asyncio.Lock()
        chunks = [{"text": "doc1"}, {"text": "doc2"}]
        result = await svc.rerank("query", chunks)
        assert result == chunks

    @pytest.mark.asyncio
    async def test_rerank_sorts_by_score(self, monkeypatch):
        monkeypatch.setenv("ENABLE_CROSS_ENCODER", "true")
        with patch("app.services.reranker.get_settings") as ms:
            ms.return_value = MagicMock(enable_cross_encoder=True)
            svc = RerankingService()

        chunks = [
            {"id": "a", "text": "alpha"},
            {"id": "b", "text": "beta"},
            {"id": "c", "text": "gamma"},
        ]
        score_map = {"alpha": 0.1, "beta": 0.9, "gamma": 0.4}

        async def _fake_loaded():
            return True
        monkeypatch.setattr(svc, "_ensure_model_loaded", _fake_loaded)
        monkeypatch.setattr(
            svc,
            "_score_pairs",
            lambda pairs: [score_map[text] for _, text in pairs],
        )

        ranked = await svc.rerank("query", chunks)
        assert [c["id"] for c in ranked] == ["b", "c", "a"]

    @pytest.mark.asyncio
    async def test_rerank_limits_to_20(self, monkeypatch):
        monkeypatch.setenv("ENABLE_CROSS_ENCODER", "true")
        with patch("app.services.reranker.get_settings") as ms:
            ms.return_value = MagicMock(enable_cross_encoder=True)
            svc = RerankingService()

        chunks = [{"id": i, "text": f"chunk-{i}"} for i in range(25)]

        async def _fake_loaded():
            return True
        monkeypatch.setattr(svc, "_ensure_model_loaded", _fake_loaded)
        monkeypatch.setattr(
            svc,
            "_score_pairs",
            lambda pairs: [float(i) for i, _ in enumerate(pairs)],
        )

        ranked = await svc.rerank("query", chunks)
        assert len(ranked) == 20

    @pytest.mark.asyncio
    async def test_rerank_filters_low_scores(self, monkeypatch):
        monkeypatch.setenv("ENABLE_CROSS_ENCODER", "true")
        with patch("app.services.reranker.get_settings") as ms:
            ms.return_value = MagicMock(enable_cross_encoder=True)
            svc = RerankingService()

        chunks = [
            {"id": "good", "text": "relevant"},
            {"id": "bad", "text": "irrelevant"},
        ]

        async def _fake_loaded():
            return True
        monkeypatch.setattr(svc, "_ensure_model_loaded", _fake_loaded)
        monkeypatch.setattr(svc, "_score_pairs", lambda pairs: [5.0, -5.0])

        ranked = await svc.rerank("query", chunks)
        assert len(ranked) == 1
        assert ranked[0]["id"] == "good"

    @pytest.mark.asyncio
    async def test_rerank_all_below_threshold_returns_top3(self, monkeypatch):
        monkeypatch.setenv("ENABLE_CROSS_ENCODER", "true")
        with patch("app.services.reranker.get_settings") as ms:
            ms.return_value = MagicMock(enable_cross_encoder=True)
            svc = RerankingService()

        chunks = [{"id": i, "text": f"c-{i}"} for i in range(5)]

        async def _fake_loaded():
            return True
        monkeypatch.setattr(svc, "_ensure_model_loaded", _fake_loaded)
        monkeypatch.setattr(svc, "_score_pairs", lambda pairs: [-5.0] * len(pairs))

        ranked = await svc.rerank("query", chunks)
        assert len(ranked) == 3
