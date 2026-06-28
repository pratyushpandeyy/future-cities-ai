import unittest

from app.models.schemas import CandidateScreenRequest, RecommendationRequest
from app.services.recommendation_engine import generate_recommendations
from app.services.recommendation_engine import screen_candidate_locations


class RecommendationEngineTests(unittest.TestCase):
    def test_recommendations_include_ranking_breakdown(self):
        response = generate_recommendations(
            RecommendationRequest(
                current_location="Whitefield",
                target_year=2050,
                warming_tolerance=2.7,
                heat_sensitivity=82,
                respiratory_sensitivity=86,
                flood_risk_tolerance=28,
                outdoor_lifestyle_preference=52,
                urban_vs_quieter_preference="balanced",
                coastal_preference="inland",
                family_elderly_sensitivity=44,
                remote_work_flexibility=46,
            ),
        )

        self.assertGreaterEqual(len(response.recommended_regions), 1)
        breakdown = response.recommended_regions[0].ranking_breakdown

        self.assertIn("livability_component", breakdown)
        self.assertIn("resilience_component", breakdown)
        self.assertIn("risk_penalty", breakdown)

    def test_inland_preference_penalizes_coastal_regions(self):
        response = generate_recommendations(
            RecommendationRequest(
                current_location="Mumbai",
                target_year=2050,
                warming_tolerance=2.7,
                heat_sensitivity=70,
                respiratory_sensitivity=50,
                flood_risk_tolerance=20,
                outdoor_lifestyle_preference=65,
                urban_vs_quieter_preference="balanced",
                coastal_preference="inland",
                family_elderly_sensitivity=40,
                remote_work_flexibility=55,
            ),
        )
        top_regions = " ".join(
            region.region_name.lower() for region in response.recommended_regions
        )

        self.assertNotIn("coastal region", top_regions)

    def test_candidate_screen_ranks_user_supplied_locations(self):
        response = screen_candidate_locations(
            CandidateScreenRequest(
                current_location="Whitefield",
                target_year=2050,
                warming_tolerance=2.7,
                heat_sensitivity=82,
                respiratory_sensitivity=86,
                flood_risk_tolerance=28,
                outdoor_lifestyle_preference=52,
                urban_vs_quieter_preference="balanced",
                coastal_preference="inland",
                family_elderly_sensitivity=44,
                remote_work_flexibility=46,
                candidate_locations=["Pune", "Manchester", "Chennai"],
            ),
        )
        names = [candidate.location_name for candidate in response.ranked_candidates]

        self.assertEqual(set(names), {"Pune", "Manchester", "Chennai"})
        self.assertGreaterEqual(
            response.ranked_candidates[0].suitability_score,
            response.ranked_candidates[-1].suitability_score,
        )
        self.assertIn("ML adjustment", response.screening_note)


if __name__ == "__main__":
    unittest.main()
