import unittest

from app.models.schemas import AdvisorQueryRequest, RAGQueryRequest
from app.services.advisor_engine import answer_advisor_query
from app.services.rag_retrieval import retrieve_climate_knowledge


class RAGRetrievalTests(unittest.TestCase):
    def test_retrieves_health_and_heat_context(self):
        response = retrieve_climate_knowledge(
            RAGQueryRequest(
                query_text=(
                    "I live in Whitefield and have asthma. How bad will heat get "
                    "by 2050?"
                ),
                location="Whitefield",
                season="Summer",
                risks=["High", "respiratory sensitivity"],
                max_chunks=3,
            ),
        )

        self.assertEqual(response.retrieval_mode, "local_tfidf_vector_rag_v1")
        self.assertGreaterEqual(len(response.chunks), 1)
        self.assertTrue(
            any(
                "health" in {tag.lower() for tag in chunk.tags}
                or "respiratory" in {tag.lower() for tag in chunk.tags}
                for chunk in response.chunks
            ),
        )

    def test_advisor_response_includes_retrieved_knowledge(self):
        response = answer_advisor_query(
            AdvisorQueryRequest(
                query_text=(
                    "I live in Whitefield and have asthma. How bad will summers "
                    "get by 2050 if warming reaches +2.7C?"
                ),
                selected_preferences=["Asthma / respiratory sensitivity"],
            ),
        )

        self.assertGreaterEqual(len(response.retrieved_knowledge), 1)
        self.assertIn("Retrieved local RAG evidence", response.rag_grounding_summary)
        self.assertIn(
            "Research context retrieved",
            response.human_explanation.human_summary,
        )

    def test_advisor_explicit_comparison_locations_are_scored(self):
        response = answer_advisor_query(
            AdvisorQueryRequest(
                query_text=(
                    "I live in Whitefield and have asthma. Should I consider "
                    "Pune or Manchester by 2050?"
                ),
                selected_preferences=["Asthma / respiratory sensitivity"],
            ),
        )
        comparison_names = {
            location.location_name for location in response.suggested_comparison_locations
        }

        self.assertIn("Pune", comparison_names)
        self.assertIn("Manchester", comparison_names)


if __name__ == "__main__":
    unittest.main()
