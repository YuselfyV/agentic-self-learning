import unittest
from unittest.mock import patch

from agentic_self_learning import SelfLearningPipeline


class PipelineTest(unittest.TestCase):
    def test_pipeline_generates_answers_and_evaluates_them(self):
        result = SelfLearningPipeline().run("capitales")

        self.assertIn("<question>", result.generated_question.question)
        self.assertIn("<answer>", result.answer.answer)
        self.assertEqual(result.evaluation.conclusion, "correct")
        self.assertEqual(result.evaluation.score, 1.0)

    def test_pipeline_answers_existing_question(self):
        result = SelfLearningPipeline().answer_existing_question("What is the capital of Colombia?")

        self.assertEqual(result.answer.answer, "<answer>Bogota</answer>")
        self.assertTrue(result.evaluation.question_is_solvable)

    def test_pipeline_can_use_wikipedia_source(self):
        search_payload = {
            "query": {
                "search": [
                    {
                        "pageid": 123,
                        "title": "Bogota",
                    }
                ]
            }
        }
        extract_payload = {
            "query": {
                "pages": {
                    "123": {
                        "extract": "Bogota is the capital and largest city of Colombia."
                    }
                }
            }
        }

        with patch("agentic_self_learning.tools.retrieval.WikipediaRetrievalTool._get") as fake_get:
            fake_get.side_effect = [search_payload, extract_payload]
            result = SelfLearningPipeline(source="wikipedia").answer_existing_question(
                "What is the capital of Colombia?"
            )

        self.assertEqual(result.answer.answer, "<answer>Bogota</answer>")
        self.assertEqual(result.answer.evidence[0].document.metadata["source"], "wikipedia")


if __name__ == "__main__":
    unittest.main()
