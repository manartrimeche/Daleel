"""Tests for loi_service — serialiser helpers."""

from app.services.loi_service import _loi_to_dict, _article_to_dict, _version_to_dict


class TestLoiToDict:
    def test_full_loi(self):
        loi = {
            "id": "l1",
            "code": "CT",
            "name": "Code du travail",
            "jurisdiction": "tunisia",
            "language": "fr",
            "description": "Loi régissant le travail",
            "version_label": "v2",
            "created_at": "2026-01-01",
            "updated_at": "2026-05-01",
        }
        result = _loi_to_dict(loi, total_articles=42)
        assert result["id"] == "l1"
        assert result["code"] == "CT"
        assert result["total_articles"] == 42
        assert result["jurisdiction"] == "tunisia"

    def test_empty_loi(self):
        result = _loi_to_dict({})
        assert result["id"] is None
        assert result["code"] is None
        assert result["total_articles"] is None

    def test_extra_fields_ignored(self):
        result = _loi_to_dict({"id": "l1", "extra": "val"})
        assert "extra" not in result


class TestArticleToDict:
    def test_full_article(self):
        article = {
            "id": "a1",
            "loi_id": "l1",
            "article_key": "Art. 14",
            "article_number": 14,
            "article_heading": "Durée du travail",
            "hierarchy_titre": "Titre I",
            "hierarchy_chapitre": "Chapitre 2",
            "hierarchy_section": "Section 1",
            "created_at": "2026-01-01",
        }
        result = _article_to_dict(article, active_version_id="v1", total_versions=3)
        assert result["id"] == "a1"
        assert result["article_key"] == "Art. 14"
        assert result["hierarchy"]["titre"] == "Titre I"
        assert result["active_version_id"] == "v1"
        assert result["total_versions"] == 3

    def test_missing_hierarchy(self):
        result = _article_to_dict({})
        assert result["hierarchy"] == {
            "titre": None,
            "chapitre": None,
            "section": None,
        }


class TestVersionToDict:
    def test_full_version(self):
        version = {
            "id": "v1",
            "article_id": "a1",
            "version_num": 2,
            "text": "L'employeur doit...",
            "status": "active",
            "language": "fr",
            "source_document_id": "d1",
            "source_pages": [1, 2],
            "effective_date": "2026-01-01",
            "created_at": "2026-01-01",
        }
        result = _version_to_dict(version, article_key="Art. 14", total_exigences=5, total_actions=3)
        assert result["id"] == "v1"
        assert result["article_key"] == "Art. 14"
        assert result["total_exigences"] == 5
        assert result["source_pages"] == [1, 2]

    def test_null_source_pages_returns_empty(self):
        result = _version_to_dict({"source_pages": None})
        assert result["source_pages"] == []

    def test_empty_version(self):
        result = _version_to_dict({})
        assert result["id"] is None
        assert result["source_pages"] == []
        assert result["total_exigences"] is None
