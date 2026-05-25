"""Tests for article_segmenter — pure helper functions and segmentation."""

from app.processing.article_segmenter import (
    _norm_num,
    _chars_to_pages,
    _make_article_key,
    _detect_language,
    build_page_map,
    segment_text_into_articles,
)


class TestNormNum:
    def test_western_digits_unchanged(self):
        assert _norm_num("123") == "123"

    def test_arabic_indic_digits(self):
        assert _norm_num("٩٥") == "95"

    def test_mixed(self):
        assert _norm_num("١2٣") == "123"

    def test_strips_whitespace(self):
        assert _norm_num("  42  ") == "42"


class TestCharsToPages:
    def test_single_page(self):
        page_map = [(0, 100, 1)]
        assert _chars_to_pages(10, 50, page_map) == [1]

    def test_spanning_two_pages(self):
        page_map = [(0, 100, 1), (100, 200, 2)]
        assert _chars_to_pages(90, 110, page_map) == [1, 2]

    def test_no_overlap(self):
        page_map = [(0, 100, 1)]
        assert _chars_to_pages(200, 300, page_map) == []

    def test_empty_page_map(self):
        assert _chars_to_pages(0, 100, []) == []

    def test_multiple_pages(self):
        page_map = [(0, 50, 1), (50, 100, 2), (100, 150, 3)]
        assert _chars_to_pages(0, 150, page_map) == [1, 2, 3]


class TestMakeArticleKey:
    def test_simple(self):
        assert _make_article_key("CT", "95") == "CT-Art-95"

    def test_with_bis(self):
        assert _make_article_key("CT", "95 bis") == "CT-Art-95bis"

    def test_lowercased_code(self):
        assert _make_article_key("ct", "14") == "CT-Art-14"

    def test_strips_whitespace(self):
        assert _make_article_key("CS", "  12  ") == "CS-Art-12"


class TestDetectLanguage:
    def test_french_text(self):
        assert _detect_language("L'employeur est tenu de respecter le droit du travail") == "fr"

    def test_arabic_text(self):
        assert _detect_language("يجب على المشغل احترام قانون الشغل") == "ar"

    def test_empty_text(self):
        assert _detect_language("") == "unknown"

    def test_numbers_only(self):
        assert _detect_language("12345") == "unknown"

    def test_mixed_text(self):
        result = _detect_language("Article الفصل mixed texte عربي français")
        assert result in ("fr", "ar", "fr+ar")


class TestBuildPageMap:
    def test_empty_input(self):
        text, page_map = build_page_map([])
        assert text == ""
        assert page_map == []

    def test_single_page(self):
        pages = [{"page_number": 1, "cleaned_text": "Hello world"}]
        text, page_map = build_page_map(pages)
        assert "Hello world" in text
        assert len(page_map) == 1
        assert page_map[0][2] == 1

    def test_multiple_pages(self):
        pages = [
            {"page_number": 1, "cleaned_text": "Page one"},
            {"page_number": 2, "cleaned_text": "Page two"},
        ]
        text, page_map = build_page_map(pages)
        assert "Page one" in text
        assert "Page two" in text
        assert len(page_map) == 2
        assert page_map[0][0] == 0
        assert page_map[1][0] == page_map[0][1]

    def test_none_cleaned_text(self):
        pages = [{"page_number": 1, "cleaned_text": None}]
        text, page_map = build_page_map(pages)
        assert len(page_map) == 1

    def test_orm_object(self):
        class FakePage:
            page_number = 3
            cleaned_text = "ORM text"
        text, page_map = build_page_map([FakePage()])
        assert "ORM text" in text
        assert page_map[0][2] == 3


class TestSegmentTextIntoArticles:
    def test_empty_text(self):
        assert segment_text_into_articles("", "CT", [], "fr") == []

    def test_whitespace_only(self):
        assert segment_text_into_articles("   \n  ", "CT", [], "fr") == []

    def test_no_articles_found(self):
        result = segment_text_into_articles("Just some random text", "CT", [(0, 20, 1)], "fr")
        assert result == []

    def test_single_french_article(self):
        text = "Article 14\nL'employeur doit respecter les conditions de travail."
        page_map = [(0, len(text), 1)]
        result = segment_text_into_articles(text, "CT", page_map, "fr")
        assert len(result) == 1
        assert result[0]["article_number"] == "14"
        assert result[0]["article_key"] == "CT-Art-14"

    def test_multiple_articles(self):
        text = "Article 1\nPremier article.\n\nArticle 2\nDeuxième article."
        page_map = [(0, len(text), 1)]
        result = segment_text_into_articles(text, "CT", page_map, "fr")
        assert len(result) == 2

    def test_arabic_article(self):
        text = "الفصل 1\nنص الفصل الأول.\n\nالفصل 2\nنص الفصل الثاني."
        page_map = [(0, len(text), 1)]
        result = segment_text_into_articles(text, "CT", page_map, "ar")
        assert len(result) >= 1

    def test_mixed_language(self):
        text = "Article 1\nTexte français.\n\nالفصل 2\nنص عربي."
        page_map = [(0, len(text), 1)]
        result = segment_text_into_articles(text, "CT", page_map, "fr+ar")
        assert len(result) >= 1

    def test_article_with_hierarchy(self):
        text = "Titre I\nDispositions générales\n\nChapitre 1\nPrincipes\n\nArticle 1\nTexte de l'article."
        page_map = [(0, len(text), 1)]
        result = segment_text_into_articles(text, "CT", page_map, "fr")
        assert len(result) >= 1
        if result:
            assert result[0].get("hierarchy") is not None
