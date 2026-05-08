"""
Export service — generate downloadable files from compliance data.

Supports:
  • Excel (.xlsx) via openpyxl
  • CSV fallback (no extra dependency)
"""

from __future__ import annotations

import csv
import io
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


async def export_roadmap_file(
    db: Any,
    profile_id: str,
    *,
    format: str = "xlsx",
) -> tuple[bytes, str, str]:
    """
    Generate an export file for the compliance roadmap.

    Returns (content_bytes, media_type, filename).
    """
    from app.services.roadmap_service import generate_roadmap

    roadmap = await generate_roadmap(db, profile_id)
    profile_name = roadmap.get("profile_name", profile_id)[:40]
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    plan = roadmap.get("ordered_plan", [])

    headers = [
        "Position",
        "Action ID",
        "Loi",
        "Article",
        "Modalité",
        "Action précise",
        "Conditions",
        "Preuve",
        "Criticité",
        "Score",
        "Dépendances",
    ]

    rows = []
    for item in plan:
        rows.append([
            item.get("position", ""),
            item.get("action_id", ""),
            item.get("loi_code", ""),
            item.get("article_key", ""),
            item.get("modalite", ""),
            item.get("action_precise", ""),
            " | ".join(item.get("conditions") or []),
            item.get("preuve", ""),
            item.get("criticality_level", ""),
            item.get("criticality_score", ""),
            ", ".join(item.get("depends_on_ids") or []),
        ])

    safe_name = "".join(c if c.isalnum() or c in " _-" else "_" for c in profile_name).strip()

    if format == "xlsx":
        return _to_xlsx(headers, rows, safe_name, timestamp, roadmap)
    else:
        return _to_csv(headers, rows, safe_name, timestamp)


def _to_csv(
    headers: list[str],
    rows: list[list],
    safe_name: str,
    timestamp: str,
) -> tuple[bytes, str, str]:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(headers)
    writer.writerows(rows)
    content = buf.getvalue().encode("utf-8-sig")  # BOM for Excel compatibility
    filename = f"roadmap_{safe_name}_{timestamp}.csv"
    return content, "text/csv; charset=utf-8", filename


def _to_xlsx(
    headers: list[str],
    rows: list[list],
    safe_name: str,
    timestamp: str,
    roadmap: dict,
) -> tuple[bytes, str, str]:
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment
    except ImportError:
        logger.warning("openpyxl not installed — falling back to CSV export")
        return _to_csv(headers, rows, safe_name, timestamp)

    wb = Workbook()

    # ── Summary sheet ──
    ws_summary = wb.active
    ws_summary.title = "Résumé"
    ws_summary.append(["Feuille de route de conformité"])
    ws_summary.append(["Profil", roadmap.get("profile_name", "")])
    ws_summary.append(["Total actions", roadmap.get("total_actions", 0)])
    by_level = roadmap.get("by_level", {})
    ws_summary.append(["Critique", by_level.get("critique", 0)])
    ws_summary.append(["Importante", by_level.get("importante", 0)])
    ws_summary.append(["Secondaire", by_level.get("secondaire", 0)])
    gen = roadmap.get("generated_at")
    ws_summary.append(["Généré le", str(gen) if gen else timestamp])

    title_font = Font(bold=True, size=14)
    ws_summary["A1"].font = title_font

    # ── Plan sheet ──
    ws_plan = wb.create_sheet("Plan d'action")
    ws_plan.append(headers)

    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF")
    for col_idx, _ in enumerate(headers, 1):
        cell = ws_plan.cell(row=1, column=col_idx)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center")

    level_colors = {
        "critique": "FFC7CE",
        "importante": "FFEB9C",
        "secondaire": "C6EFCE",
    }

    for row_idx, row in enumerate(rows, 2):
        ws_plan.append(row)
        level = row[8] if len(row) > 8 else ""
        if level in level_colors:
            fill = PatternFill(start_color=level_colors[level], end_color=level_colors[level], fill_type="solid")
            for col_idx in range(1, len(row) + 1):
                ws_plan.cell(row=row_idx, column=col_idx).fill = fill

    # Auto-width columns
    for col in ws_plan.columns:
        max_len = 0
        col_letter = col[0].column_letter
        for cell in col:
            try:
                if cell.value:
                    max_len = max(max_len, len(str(cell.value)))
            except Exception:
                pass
        ws_plan.column_dimensions[col_letter].width = min(max_len + 2, 50)

    buf = io.BytesIO()
    wb.save(buf)
    content = buf.getvalue()
    filename = f"roadmap_{safe_name}_{timestamp}.xlsx"
    media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return content, media_type, filename
