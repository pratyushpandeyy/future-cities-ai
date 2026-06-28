import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.download_geoboundaries import (
    BoundaryMetadataUnavailable,
    build_download_items,
    parse_csv_arg,
    resolve_countries,
    select_download_url,
)


class GeoBoundariesDownloaderTests(unittest.TestCase):
    def test_parse_csv_arg_normalizes_country_codes(self) -> None:
        self.assertEqual(parse_csv_arg("ind, gbr,TUR"), ["IND", "GBR", "TUR"])

    def test_country_preset_can_be_overridden_by_explicit_countries(self) -> None:
        self.assertEqual(resolve_countries("top100-population", "ind,esp"), ["IND", "ESP"])

    def test_top100_country_preset_contains_priority_demo_markets(self) -> None:
        countries = resolve_countries("top100-population", "")

        self.assertIn("IND", countries)
        self.assertIn("GBR", countries)
        self.assertIn("TUR", countries)
        self.assertIn("ESP", countries)
        self.assertEqual(len(countries), 100)

    def test_selects_simplified_geojson_when_requested(self) -> None:
        metadata = {
            "gjDownloadURL": "https://example.com/full.geojson",
            "simplifiedGeometryGeoJSON": "https://example.com/simple.geojson",
        }

        self.assertEqual(
            select_download_url(metadata, simplified=True),
            "https://example.com/simple.geojson",
        )

    @patch("scripts.download_geoboundaries.fetch_boundary_metadata")
    def test_builds_download_items_for_country_and_admin_level(self, metadata) -> None:
        metadata.return_value = {
            "boundaryID": "IND-ADM2-123",
            "boundaryName": "India",
            "admUnitCount": "736",
            "boundaryLicense": "Open Data Commons Open Database License 1.0",
            "boundarySource": "lgdirectory.gov.in",
            "gjDownloadURL": "https://example.com/full.geojson",
            "simplifiedGeometryGeoJSON": "https://example.com/simple.geojson",
        }

        items = build_download_items(
            countries=["IND"],
            admin_levels=["ADM2"],
            product="gbOpen",
            output_dir=Path("data/raw/geoboundaries"),
            simplified=True,
            timeout=10,
            strict_metadata=False,
        )

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].key, "IND/ADM2")
        self.assertEqual(items[0].url, "https://example.com/simple.geojson")
        self.assertEqual(items[0].metadata["unit_count"], "736")
        self.assertTrue(str(items[0].destination).endswith("geoBoundaries-IND-ADM2_simplified.geojson"))

    @patch("scripts.download_geoboundaries.fetch_boundary_metadata")
    def test_skips_missing_country_admin_level_metadata(self, metadata) -> None:
        def fake_metadata(**kwargs):
            if kwargs["iso3"] == "ARE":
                raise BoundaryMetadataUnavailable("geoBoundaries metadata not found")

            return {
                "boundaryID": "IND-ADM2-123",
                "boundaryName": "India",
                "admUnitCount": "736",
                "gjDownloadURL": "https://example.com/full.geojson",
                "simplifiedGeometryGeoJSON": "https://example.com/simple.geojson",
            }

        metadata.side_effect = fake_metadata

        items = build_download_items(
            countries=["IND", "ARE"],
            admin_levels=["ADM2"],
            product="gbOpen",
            output_dir=Path("data/raw/geoboundaries"),
            simplified=True,
            timeout=10,
            strict_metadata=False,
        )

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].key, "IND/ADM2")


if __name__ == "__main__":
    unittest.main()
