"""Tests for recalculation_service — empty input branch."""

import pytest
from app.services.recalculation_service import recalculate_after_amendment
from unittest.mock import MagicMock


@pytest.mark.asyncio
async def test_empty_version_ids_returns_early():
    db = MagicMock()
    result = await recalculate_after_amendment(db, loi_id="l1", new_version_ids=[])
    assert result["versions_processed"] == 0
    assert result["exigences_extracted"] == 0
    assert result["actions_extracted"] == 0
    assert result["criticalities_computed"] == 0
    assert "No versions" in result["message"]


@pytest.mark.asyncio
async def test_empty_version_ids_returns_loi_id():
    db = MagicMock()
    result = await recalculate_after_amendment(db, loi_id="test-loi", new_version_ids=[])
    assert result["loi_id"] == "test-loi"
