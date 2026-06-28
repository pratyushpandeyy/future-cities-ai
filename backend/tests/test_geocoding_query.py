import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.models.schemas import LocationResult
from app.services.geocoding import build_geocoder_query, geocode_location


class GeocodingQueryTests(unittest.TestCase):
    def test_parent_location_disambiguates_locality_query(self):
        self.assertEqual(
            build_geocoder_query("Whitefield", "Bengaluru, Karnataka"),
            "Whitefield, Bengaluru, Karnataka",
        )

    def test_parent_location_is_not_duplicated(self):
        self.assertEqual(
            build_geocoder_query("Whitefield, Bengaluru", "Bengaluru"),
            "Whitefield, Bengaluru",
        )

    def test_search_suggestions_endpoint_returns_geocoded_options(self):
        suggestion = LocationResult(
            location_name="Whitefield",
            region="Karnataka",
            climate_zone="Geocoded regional climate cell",
            latitude=12.9698,
            longitude=77.75,
            locality="Whitefield",
            district="Bengaluru Urban",
            city="Bengaluru",
            country="India",
            hierarchy_label="Whitefield / Bengaluru Urban / Bengaluru / Karnataka / India",
            place_type="neighborhood",
            geocoder_provider="mapbox",
            known=True,
            extrapolated=False,
            location_id="mapbox-whitefield",
        )

        with patch(
            "app.api.routes.search.geocode_location_suggestions",
            return_value=[suggestion],
        ):
            client = TestClient(app)
            response = client.get(
                "/api/search/suggestions",
                params={"query": "white", "parent_location": "Bengaluru"},
            )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body[0]["location_name"], "Whitefield")
        self.assertEqual(body[0]["city"], "Bengaluru")
        self.assertEqual(body[0]["place_type"], "neighborhood")

    def test_seeded_locality_prevents_bad_whitefield_fallback(self):
        result = geocode_location("Whitefield, Bengaluru")

        self.assertIsNotNone(result)
        self.assertEqual(result.location_name, "Whitefield")
        self.assertEqual(result.city, "Bengaluru")
        self.assertAlmostEqual(result.latitude, 12.9698)
        self.assertAlmostEqual(result.longitude, 77.7499)
        self.assertEqual(result.geocoder_provider, "seeded_locality")


if __name__ == "__main__":
    unittest.main()
