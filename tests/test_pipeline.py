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

    def test_spanish_capital_question_uses_all_wikipedia_evidence(self):
        search_payload = {
            "query": {
                "search": [
                    {"pageid": 1, "title": "Departamentos de Colombia"},
                    {"pageid": 2, "title": "Distrito capital"},
                    {"pageid": 3, "title": "Bogotá"},
                ]
            }
        }
        extract_payload = {
            "query": {
                "pages": {
                    "1": {"extract": "Colombia tiene departamentos y un distrito capital."},
                    "2": {"extract": "Un distrito capital es una sede de gobierno."},
                    "3": {"extract": "Bogotá es la capital de la República de Colombia."},
                }
            }
        }

        with patch("agentic_self_learning.tools.retrieval.WikipediaRetrievalTool._get") as fake_get:
            fake_get.side_effect = [search_payload, extract_payload]
            result = SelfLearningPipeline(source="wikipedia", wikipedia_language="es").answer_existing_question(
                "Cual es la capital de Colombia"
            )

        self.assertEqual(result.answer.answer, "<answer>Bogotá</answer>")
        self.assertEqual(result.evaluation.conclusion, "correct")


if __name__ == "__main__":
    unittest.main()
