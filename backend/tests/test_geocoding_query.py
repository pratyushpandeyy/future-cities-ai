import unittest

from app.services.geocoding import build_geocoder_query


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


if __name__ == "__main__":
    unittest.main()
