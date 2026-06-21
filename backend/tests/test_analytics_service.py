"""Tests for analytics_service — aggregate metrics."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services import analytics_service


class _FakeAggCursor:
    def __init__(self, rows):
        self._rows = rows

    def to_list(self, length=None):
        f = AsyncMock(return_value=self._rows)
        return f()


class _FakeAsyncIter:
    def __init__(self, items):
        self._items = list(items)
        self._idx = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self._idx >= len(self._items):
            raise StopAsyncIteration
        item = self._items[self._idx]
        self._idx += 1
        return item


def _make_db(qa_rows=None, satisfaction_rows=None, profiles=None, total_exigences=0, applicability_agg=None, chat_history_rows=None):
    db = MagicMock()

    # chat_history is the primary source for get_qa_daily_counts;
    # qa_feedback is only used as a fallback when chat_history is empty.
    chat_history = MagicMock()
    chat_history.aggregate.return_value = _FakeAggCursor(
        chat_history_rows if chat_history_rows is not None else (qa_rows or [])
    )

    qa_feedback = MagicMock()
    qa_feedback.aggregate.return_value = _FakeAggCursor(qa_rows or [])
    qa_feedback.count_documents = AsyncMock(return_value=0)

    company_profiles = MagicMock()
    company_profiles.find.return_value = MagicMock()
    company_profiles.find.return_value.to_list = AsyncMock(return_value=profiles or [])

    exigences = MagicMock()
    exigences.count_documents = AsyncMock(return_value=total_exigences)

    exigence_applicabilities = MagicMock()
    exigence_applicabilities.aggregate.return_value = _FakeAsyncIter(applicability_agg or [])

    def getitem(self, name):
        return {
            "chat_history": chat_history,
            "qa_feedback": qa_feedback,
            "company_profiles": company_profiles,
            "exigences": exigences,
            "exigence_applicabilities": exigence_applicabilities,
        }.get(name, MagicMock())

    db.__getitem__ = getitem
    return db


@pytest.mark.asyncio
async def test_get_qa_daily_counts_returns_formatted():
    db = _make_db(qa_rows=[
        {"_id": "2026-05-01", "count": 5},
        {"_id": "2026-05-02", "count": 12},
    ])
    result = await analytics_service.get_qa_daily_counts(db, days=7)
    assert len(result) == 2
    assert result[0] == {"date": "2026-05-01", "count": 5}
    assert result[1] == {"date": "2026-05-02", "count": 12}


@pytest.mark.asyncio
async def test_get_qa_daily_counts_empty():
    db = _make_db(qa_rows=[])
    result = await analytics_service.get_qa_daily_counts(db, days=30)
    assert result == []


@pytest.mark.asyncio
async def test_get_satisfaction_over_time():
    db = _make_db()
    db["qa_feedback"].aggregate.return_value = _FakeAggCursor([
        {"_id": "2026-05-01", "avg_rating": 4.567, "count": 3},
    ])
    result = await analytics_service.get_satisfaction_over_time(db, days=7)
    assert len(result) == 1
    assert result[0]["avg_rating"] == 4.57
    assert result[0]["count"] == 3


@pytest.mark.asyncio
async def test_get_compliance_coverage_no_exigences():
    profiles = [{"id": "p1", "name": "ACME"}]
    db = _make_db(profiles=profiles, total_exigences=0)
    result = await analytics_service.get_compliance_coverage(db)
    assert len(result) == 1
    assert result[0]["coverage_pct"] == 0
    assert result[0]["total"] == 0


@pytest.mark.asyncio
async def test_get_compliance_coverage_with_data():
    profiles = [{"id": "p1", "name": "ACME"}, {"id": "p2", "name": "Corp"}]
    agg = [{"_id": "p1", "applicable": 8}]
    db = _make_db(profiles=profiles, total_exigences=20, applicability_agg=agg)
    result = await analytics_service.get_compliance_coverage(db)
    assert len(result) == 2
    acme = next(r for r in result if r["profile_id"] == "p1")
    assert acme["coverage_pct"] == 40.0
    assert acme["applicable"] == 8
    corp = next(r for r in result if r["profile_id"] == "p2")
    assert corp["coverage_pct"] == 0
    assert corp["applicable"] == 0


@pytest.mark.asyncio
async def test_get_full_analytics_aggregates_all():
    db = _make_db(
        qa_rows=[],
        profiles=[{"id": "p1", "name": "Test"}],
        total_exigences=0,
    )
    db["qa_feedback"].aggregate.side_effect = [
        _FakeAggCursor([{"_id": "2026-05-01", "count": 3}]),
        _FakeAggCursor([{"_id": "2026-05-01", "avg_rating": 4.5, "count": 2}]),
    ]
    result = await analytics_service.get_full_analytics(db, days=7)
    assert "qa_daily" in result
    assert "satisfaction" in result
    assert "coverage" in result
    assert result["period_days"] == 7
