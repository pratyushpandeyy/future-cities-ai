import unittest

from app.services.environmental_data import (
    copernicus_dem_tile,
    copernicus_dem_url,
    green_cover_proxy,
    worldcover_tile,
    worldcover_url,
)
from app.models.schemas import EnvironmentalSample


class EnvironmentalDataTests(unittest.TestCase):
    def test_builds_copernicus_dem_tile_and_url(self) -> None:
        tile = copernicus_dem_tile(41.0082, 28.9784)

        self.assertEqual(tile, "N41_00_E028_00")
        self.assertEqual(
            copernicus_dem_url(tile),
            (
                "https://copernicus-dem-30m.s3.eu-central-1.amazonaws.com/"
                "Copernicus_DSM_COG_10_N41_00_E028_00_DEM/"
                "Copernicus_DSM_COG_10_N41_00_E028_00_DEM.tif"
            ),
        )

    def test_builds_worldcover_three_degree_tile(self) -> None:
        tile = worldcover_tile(12.9716, 77.5946)

        self.assertEqual(tile, "N12E075")
        self.assertIn(
            "ESA_WorldCover_10m_2021_v200_N12E075_Map.tif",
            worldcover_url(tile),
        )

    def test_tree_cover_has_high_green_proxy(self) -> None:
        sample = EnvironmentalSample(
            variable="land_cover",
            value=10,
            unit="class_code",
            provider="esa_worldcover_2021",
            source_url="test",
            resolution="10m",
            grid_cell_id="cell",
            confidence="high",
            category="tree_cover",
        )

        self.assertEqual(green_cover_proxy(sample), 1.0)


if __name__ == "__main__":
    unittest.main()
