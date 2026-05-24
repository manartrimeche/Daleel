import unittest
from unittest.mock import AsyncMock, MagicMock


class MockCursor:
    def __init__(self, docs):
        self._docs = list(docs)
        self._index = 0

    def sort(self, *args, **kwargs):
        return self

    def skip(self, *args, **kwargs):
        return self

    def limit(self, *args, **kwargs):
        return self

    def __aiter__(self):
        self._index = 0
        return self

    async def __anext__(self):
        if self._index >= len(self._docs):
            raise StopAsyncIteration
        item = self._docs[self._index]
        self._index += 1
        return item


class TestFeedbackScope(unittest.IsolatedAsyncioTestCase):
    async def test_list_feedback_filters_by_organization(self):
        from app.services.feedback_service import list_feedback

        collection = MagicMock()
        collection.count_documents = AsyncMock(return_value=1)
        collection.find = MagicMock(return_value=MockCursor([{"id": "fb-1", "organization_id": "org-a"}]))
        db = {"qa_feedback": collection}

        items, total = await list_feedback(db, organization_id="org-a")

        expected = {"organization_id": "org-a"}
        collection.count_documents.assert_awaited_once_with(expected)
        collection.find.assert_called_once_with(expected, {"_id": 0})
        self.assertEqual(total, 1)
        self.assertEqual(items[0]["id"], "fb-1")

    async def test_relevant_feedback_examples_filters_by_organization(self):
        from app.services.feedback_service import get_relevant_feedback_examples

        collection = MagicMock()
        collection.find = MagicMock(
            return_value=MockCursor([
                {
                    "question": "controle cnss mensuel",
                    "corrected_answer": "Verifier les declarations CNSS.",
                    "language": "fr",
                    "rating": 5,
                    "organization_id": "org-a",
                }
            ])
        )
        db = {"qa_feedback": collection}

        examples = await get_relevant_feedback_examples(
            db,
            question="controle cnss",
            detected_lang="fr",
            organization_id="org-a",
        )

        collection.find.assert_called_once_with(
            {"organization_id": "org-a", "language": "fr"},
            {"_id": 0},
        )
        self.assertEqual(len(examples), 1)
        self.assertEqual(examples[0]["corrected_answer"], "Verifier les declarations CNSS.")

    async def test_best_feedback_match_accepts_pipeline_arguments(self):
        from app.services.feedback_service import get_best_feedback_match

        collection = MagicMock()
        collection.find = MagicMock(
            return_value=MockCursor([
                {
                    "id": "fb-1",
                    "question": "controle cnss mensuel",
                    "corrected_answer": "Verifier les declarations CNSS.",
                    "language": "fr",
                    "organization_id": "org-a",
                }
            ])
        )
        db = {"qa_feedback": collection}

        match = await get_best_feedback_match(
            db,
            question="controle cnss mensuel",
            detected_lang="fr",
            organization_id="org-a",
        )

        collection.find.assert_called_once_with(
            {"language": "fr", "organization_id": "org-a"},
            {"_id": 0},
        )
        self.assertIsNotNone(match)
        self.assertEqual(match["id"], "fb-1")


if __name__ == "__main__":
    unittest.main()
