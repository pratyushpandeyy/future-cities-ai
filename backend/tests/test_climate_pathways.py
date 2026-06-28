import unittest

from app.services.simulation import select_climate_scenario


class ClimatePathwayMappingTests(unittest.TestCase):
    def test_default_scenario_tracks_warming_level(self):
        self.assertEqual(
            select_climate_scenario(warming_level=1.7, requested_scenario="ssp245"),
            "ssp126",
        )
        self.assertEqual(
            select_climate_scenario(warming_level=2.7, requested_scenario="ssp245"),
            "ssp245",
        )
        self.assertEqual(
            select_climate_scenario(warming_level=3.1, requested_scenario="ssp245"),
            "ssp370",
        )
        self.assertEqual(
            select_climate_scenario(warming_level=3.7, requested_scenario="ssp245"),
            "ssp585",
        )

    def test_explicit_scenario_is_respected(self):
        self.assertEqual(
            select_climate_scenario(warming_level=1.7, requested_scenario="ssp585"),
            "ssp585",
        )


if __name__ == "__main__":
    unittest.main()
