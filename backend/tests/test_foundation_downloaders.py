import tempfile
import unittest
from pathlib import Path

from scripts.download_ghsl import build_download_plan as build_ghsl_plan
from scripts.download_worldclim_baseline import (
    build_download_plan as build_worldclim_baseline_plan,
)
from scripts.download_worldcover_bbox import (
    build_download_plan as build_worldcover_plan,
    tile_ids_for_bbox,
)


class WorldClimBaselineDownloaderTests(unittest.TestCase):
    def test_builds_historical_and_elevation_urls(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            plan = build_worldclim_baseline_plan(
                variables=["tmax", "elev"],
                resolution="2.5m",
                output_dir=Path(directory),
            )

        self.assertEqual(len(plan), 2)
        self.assertEqual(
            plan[0].url,
            (
                "https://geodata.ucdavis.edu/climate/worldclim/2_1/base/"
                "wc2.1_2.5m_tmax.zip"
            ),
        )
        self.assertEqual(plan[1].destination.name, "wc2.1_2.5m_elev.zip")


class WorldCoverDownloaderTests(unittest.TestCase):
    def test_maps_bengaluru_bbox_to_expected_three_degree_tile(self) -> None:
        self.assertEqual(
            tile_ids_for_bbox(77.2, 12.7, 77.9, 13.2),
            ["N12E075"],
        )

    def test_bbox_crossing_tile_boundary_returns_all_tiles(self) -> None:
        self.assertEqual(
            tile_ids_for_bbox(-3.2, 52.9, 0.2, 54.2),
            ["N51W006", "N51W003", "N51E000", "N54W006", "N54W003", "N54E000"],
        )

    def test_worldcover_plan_deduplicates_shared_tiles(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            plan = build_worldcover_plan(
                bboxes=[
                    (77.2, 12.7, 77.9, 13.2),
                    (77.4, 12.8, 77.8, 13.1),
                ],
                output_dir=Path(directory),
            )

        self.assertEqual(len(plan), 1)
        self.assertIn("N12E075", plan[0].url)


class GhslDownloaderTests(unittest.TestCase):
    def test_builds_selected_product_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            plan = build_ghsl_plan(
                products=["built_surface"],
                output_dir=Path(directory),
            )

        self.assertEqual(len(plan), 1)
        self.assertEqual(plan[0].key, "built_surface")
        self.assertIn("GHS_BUILT_S_E2020", plan[0].url)


if __name__ == "__main__":
    unittest.main()
