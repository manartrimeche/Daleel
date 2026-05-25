"""Tests for export_service — CSV and xlsx export."""

import csv
import io
from app.services.export_service import _to_csv


class TestCsvExport:
    def test_csv_output_has_headers(self):
        headers = ["Position", "Action ID", "Criticité"]
        rows = [[1, "act-1", "critique"], [2, "act-2", "importante"]]
        content, media_type, filename = _to_csv(headers, rows, "test", "20260525")
        assert "text/csv" in media_type
        assert filename == "roadmap_test_20260525.csv"
        decoded = content.decode("utf-8-sig")
        reader = csv.reader(io.StringIO(decoded))
        header_row = next(reader)
        assert header_row == headers
        data_rows = list(reader)
        assert len(data_rows) == 2

    def test_csv_empty_rows(self):
        content, _, _ = _to_csv(["A", "B"], [], "empty", "20260101")
        decoded = content.decode("utf-8-sig")
        lines = decoded.strip().split("\n")
        assert len(lines) == 1

    def test_csv_special_characters(self):
        headers = ["Nom"]
        rows = [["Société à responsabilité limitée, SARL"]]
        content, _, _ = _to_csv(headers, rows, "special", "20260101")
        decoded = content.decode("utf-8-sig")
        assert "Société" in decoded
        assert "SARL" in decoded

    def test_csv_filename_sanitized(self):
        _, _, filename = _to_csv(["A"], [], "Test Corp", "20260525")
        assert filename == "roadmap_Test Corp_20260525.csv"

    def test_csv_content_is_bytes(self):
        content, _, _ = _to_csv(["A"], [[1]], "t", "d")
        assert isinstance(content, bytes)
