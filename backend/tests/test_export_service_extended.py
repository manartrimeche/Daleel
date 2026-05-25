"""Tests for export_service — export_roadmap_file with mocked roadmap."""

import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timezone

from app.services.export_service import export_roadmap_file, _to_xlsx


MOCK_ROADMAP = {
    "profile_id": "p1",
    "profile_name": "ACME Corporation",
    "total_actions": 2,
    "by_level": {"critique": 1, "importante": 1, "secondaire": 0},
    "ordered_plan": [
        {
            "position": 1,
            "action_id": "act-1",
            "loi_code": "CT",
            "article_key": "Art. 14",
            "modalite": "obligation",
            "action_precise": "Remettre un contrat de travail",
            "conditions": ["dès le premier salarié"],
            "preuve": "Contrat signé",
            "criticality_level": "critique",
            "criticality_score": 0.92,
            "depends_on_ids": [],
        },
        {
            "position": 2,
            "action_id": "act-2",
            "loi_code": "CT",
            "article_key": "Art. 95",
            "modalite": "interdiction",
            "action_precise": "Interdiction du travail de nuit",
            "conditions": None,
            "preuve": "Registre horaires",
            "criticality_level": "importante",
            "criticality_score": 0.65,
            "depends_on_ids": ["act-1"],
        },
    ],
    "generated_at": datetime(2026, 5, 25, tzinfo=timezone.utc),
}


@pytest.mark.asyncio
async def test_export_csv_format():
    with patch(
        "app.services.roadmap_service.generate_roadmap",
        new_callable=AsyncMock,
        return_value=MOCK_ROADMAP,
    ):
        content, media_type, filename = await export_roadmap_file(
            db=None, profile_id="p1", format="csv"
        )
    assert isinstance(content, bytes)
    assert "text/csv" in media_type
    assert filename.endswith(".csv")
    decoded = content.decode("utf-8-sig")
    assert "Art. 14" in decoded
    assert "Art. 95" in decoded
    assert "act-1" in decoded


@pytest.mark.asyncio
async def test_export_xlsx_falls_back_to_csv_without_openpyxl():
    with patch(
        "app.services.roadmap_service.generate_roadmap",
        new_callable=AsyncMock,
        return_value=MOCK_ROADMAP,
    ):
        content, media_type, filename = await export_roadmap_file(
            db=None, profile_id="p1", format="xlsx"
        )
    assert isinstance(content, bytes)
    if "text/csv" in media_type:
        assert filename.endswith(".csv")
    else:
        assert filename.endswith(".xlsx")


@pytest.mark.asyncio
async def test_export_empty_roadmap():
    empty_roadmap = {
        **MOCK_ROADMAP,
        "ordered_plan": [],
        "total_actions": 0,
    }
    with patch(
        "app.services.roadmap_service.generate_roadmap",
        new_callable=AsyncMock,
        return_value=empty_roadmap,
    ):
        content, media_type, filename = await export_roadmap_file(
            db=None, profile_id="p1", format="csv"
        )
    assert isinstance(content, bytes)
    decoded = content.decode("utf-8-sig")
    lines = decoded.strip().split("\n")
    assert len(lines) == 1


@pytest.mark.asyncio
async def test_export_with_organization_id():
    with patch(
        "app.services.roadmap_service.generate_roadmap",
        new_callable=AsyncMock,
        return_value=MOCK_ROADMAP,
    ) as mock_gen:
        await export_roadmap_file(
            db=None, profile_id="p1", format="csv", organization_id="org-1"
        )
    mock_gen.assert_called_once_with(None, "p1", organization_id="org-1")


@pytest.mark.asyncio
async def test_export_long_profile_name_truncated():
    long_roadmap = {
        **MOCK_ROADMAP,
        "profile_name": "A" * 100,
    }
    with patch(
        "app.services.roadmap_service.generate_roadmap",
        new_callable=AsyncMock,
        return_value=long_roadmap,
    ):
        _, _, filename = await export_roadmap_file(
            db=None, profile_id="p1", format="csv"
        )
    name_part = filename.replace("roadmap_", "").rsplit("_", 1)[0]
    assert len(name_part) <= 40


def test_to_xlsx_without_openpyxl():
    headers = ["A", "B"]
    rows = [[1, 2]]
    content, media_type, filename = _to_xlsx(headers, rows, "test", "20260525", {})
    if "text/csv" in media_type:
        assert filename.endswith(".csv")
