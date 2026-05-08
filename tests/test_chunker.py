"""
Unit tests for app.processing.chunker — section splitting, sliding chunks, record building.
"""

import unittest

from app.processing.chunker import (
    ChunkingService,
    split_sections,
    sliding_chunks,
    make_chunk_id,
    build_records,
)


class TestSplitSections(unittest.TestCase):
    def test_no_headings_returns_whole_text(self):
        text = "Just a plain paragraph without any section headings."
        sections = split_sections(text)
        self.assertEqual(len(sections), 1)
        self.assertEqual(sections[0][0], "")
        self.assertEqual(sections[0][1], text)

    def test_french_article_heading(self):
        text = "Preamble text.\nArticle 12\nContent of article twelve."
        sections = split_sections(text)
        # Should have preamble + article
        headings = [h for h, _ in sections]
        self.assertIn("preamble", headings)
        self.assertTrue(any("Article 12" in h for h in headings))

    def test_arabic_heading(self):
        text = "مقدمة النص.\nالفصل 5\nمحتوى الفصل الخامس."
        sections = split_sections(text)
        self.assertTrue(len(sections) >= 2)

    def test_multiple_sections(self):
        text = "Article 1\nFirst.\nArticle 2\nSecond.\nArticle 3\nThird."
        sections = split_sections(text)
        # Should have 3 articles
        article_sections = [s for h, s in sections if h.startswith("Article")]
        self.assertEqual(len(article_sections), 3)

    def test_numbered_heading(self):
        text = "Section 1\nSome text.\nSection 2\nMore text."
        sections = split_sections(text)
        self.assertTrue(len(sections) >= 2)


class TestSlidingChunks(unittest.TestCase):
    def test_short_text_single_chunk(self):
        text = "This is a short sentence."
        chunks = sliding_chunks(text, size=500, overlap=50, min_len=5)
        self.assertEqual(len(chunks), 1)

    def test_respects_min_len(self):
        text = "Hi."
        chunks = sliding_chunks(text, size=500, overlap=50, min_len=100)
        self.assertEqual(len(chunks), 0)

    def test_long_text_produces_multiple_chunks(self):
        sentences = ["This is sentence number %d." % i for i in range(100)]
        text = " ".join(sentences)
        chunks = sliding_chunks(text, size=200, overlap=50, min_len=10)
        self.assertGreater(len(chunks), 1)

    def test_overlap_creates_repeated_content(self):
        sentences = ["Sentence %d is about topic %d." % (i, i) for i in range(50)]
        text = " ".join(sentences)
        chunks = sliding_chunks(text, size=150, overlap=60, min_len=10)
        # With overlap, adjacent chunks should share some text
        if len(chunks) >= 2:
            words_0 = set(chunks[0].split())
            words_1 = set(chunks[1].split())
            self.assertTrue(len(words_0 & words_1) > 0)


class TestMakeChunkId(unittest.TestCase):
    def test_deterministic(self):
        id1 = make_chunk_id("source.pdf", 1, 0)
        id2 = make_chunk_id("source.pdf", 1, 0)
        self.assertEqual(id1, id2)

    def test_different_inputs_different_ids(self):
        id1 = make_chunk_id("source.pdf", 1, 0)
        id2 = make_chunk_id("source.pdf", 1, 1)
        self.assertNotEqual(id1, id2)

    def test_id_length(self):
        cid = make_chunk_id("test", 1, 0)
        self.assertEqual(len(cid), 14)


class TestChunkingService(unittest.TestCase):
    def test_semantic_split_french(self):
        text = (
            "Article 1\n" + ("Texte juridique. " * 40)
            + "\nArticle 2\n" + ("Autre disposition. " * 40)
        )
        chunker = ChunkingService(max_size=5000, overlap=200, min_chunk_size=50)
        chunks = chunker.chunk_text(text, "fr")
        self.assertEqual(len(chunks), 2)
        self.assertTrue(all(c["metadata"]["source_article"] for c in chunks))
        self.assertTrue(all(not c["metadata"]["is_forced_split"] for c in chunks))
        self.assertEqual([c["metadata"]["chunk_index"] for c in chunks], [0, 1])

    def test_semantic_split_arabic(self):
        text = (
            "الفصل 1\n" + ("نص قانوني " * 60)
            + "\nالمادة 2\n" + ("نص قانوني " * 60)
        )
        chunker = ChunkingService(max_size=5000, overlap=200, min_chunk_size=50)
        chunks = chunker.chunk_text(text, "ar")
        self.assertEqual(len(chunks), 2)
        self.assertTrue(any(c["metadata"]["source_article"] for c in chunks))
        self.assertTrue(any(c["metadata"]["source_section"] for c in chunks))

    def test_semantic_split_english(self):
        text = (
            "Section 1\n" + ("Legal text. " * 50)
            + "\nChapter 2\n" + ("More legal text. " * 50)
        )
        chunker = ChunkingService(max_size=5000, overlap=200, min_chunk_size=50)
        chunks = chunker.chunk_text(text, "en")
        self.assertEqual(len(chunks), 2)
        self.assertTrue(all(c["metadata"]["source_section"] for c in chunks))

    def test_forced_split_with_overlap(self):
        text = "Article 1\n" + ("A" * 800)
        chunker = ChunkingService(max_size=200, overlap=50, min_chunk_size=50)
        chunks = chunker.chunk_text(text, "en")
        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(c["metadata"]["is_forced_split"] for c in chunks))
        self.assertEqual(chunks[0]["text"][-50:], chunks[1]["text"][:50])

    def test_fallback_sliding_when_no_headings(self):
        text = "Plain text without headings. " * 80
        chunker = ChunkingService(max_size=200, overlap=50, min_chunk_size=50)
        chunks = chunker.chunk_text(text, "fr")
        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(c["metadata"]["source_article"] is None for c in chunks))
        self.assertTrue(all(c["metadata"]["source_section"] is None for c in chunks))
        self.assertTrue(all(c["metadata"]["is_forced_split"] for c in chunks))

    def test_min_chunk_size_merging(self):
        text = "Article 1\n" + ("Petit texte. " * 5) + "\nArticle 2\n" + ("Petit texte. " * 5)
        chunker = ChunkingService(max_size=5000, overlap=200, min_chunk_size=200)
        chunks = chunker.chunk_text(text, "fr")
        self.assertEqual(len(chunks), 1)
        self.assertGreater(len(chunks[0]["text"]), 100)

    def test_arabic_ala_asas_heading(self):
        text = "على أساس القانون عدد 1\n" + ("نص قانوني " * 40)
        chunker = ChunkingService(max_size=5000, overlap=200, min_chunk_size=50)
        chunks = chunker.chunk_text(text, "ar")
        self.assertEqual(len(chunks), 1)
        self.assertIsNone(chunks[0]["metadata"]["source_article"])
        self.assertTrue(chunks[0]["metadata"]["source_section"])

    def test_mixed_language_headings_unknown_language(self):
        text = (
            "Article 1\n" + ("Texte juridique. " * 30)
            + "\nالمادة 2\n" + ("نص قانوني " * 30)
        )
        chunker = ChunkingService(max_size=5000, overlap=200, min_chunk_size=50)
        chunks = chunker.chunk_text(text, "")
        self.assertEqual(len(chunks), 2)
        self.assertTrue(all(c["metadata"]["source_article"] for c in chunks))


class TestBuildRecords(unittest.TestCase):
    def test_basic_build(self):
        pages = [
            {"text": "Article 1\nLe gérant doit respecter les statuts de la société commerciale.", "page": 1, "ocr_used": False},
        ]
        records = build_records(pages, "test.pdf", chunk_size=5000, chunk_overlap=100)
        self.assertGreater(len(records), 0)
        rec = records[0]
        self.assertIn("id", rec)
        self.assertIn("text", rec)
        self.assertIn("metadata", rec)
        self.assertEqual(rec["metadata"]["source"], "test.pdf")
        self.assertEqual(rec["metadata"]["page"], 1)

    def test_empty_pages_produce_no_records(self):
        pages = [{"text": "", "page": 1, "ocr_used": False}]
        records = build_records(pages, "empty.pdf")
        self.assertEqual(len(records), 0)

    def test_ocr_flag_propagated(self):
        pages = [
            {"text": "الفصل 1\nنص قانوني طويل بما فيه الكفاية لتجاوز الحد الأدنى للطول", "page": 1, "ocr_used": True},
        ]
        records = build_records(pages, "scanned.pdf", chunk_size=5000, chunk_overlap=100)
        if records:
            self.assertTrue(records[0]["metadata"]["ocr_used"])


if __name__ == "__main__":
    unittest.main()
