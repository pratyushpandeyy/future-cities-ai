import unittest
from unittest.mock import patch

from app.models.schemas import LocationResult
from app.services.boundaries import get_region_boundary
from app.services.online_boundaries import geojson_from_nominatim_payload


TEST_LOCATION = LocationResult(
    location_name="Testville",
    region="Test State",
    climate_zone="Geocoded regional climate cell",
    latitude=10.0,
    longitude=20.0,
    locality=None,
    district="Test District",
    city="Testville",
    country="Testland",
    hierarchy_label="Testville / Test District / Test State / Testland",
    place_type="place",
    geocoder_provider="nominatim",
    known=True,
    extrapolated=False,
    location_id="osm-relation-123",
)


class OnlineBoundaryTests(unittest.TestCase):
    def test_extracts_polygon_geojson_from_nominatim_payload(self) -> None:
        geojson = geojson_from_nominatim_payload(
            [
                {
                    "name": "Testville",
                    "display_name": "Testville, Testland",
                    "osm_id": 123,
                    "osm_type": "relation",
                    "class": "boundary",
                    "type": "administrative",
                    "geojson": sample_polygon_geometry(),
                },
            ],
        )

        self.assertIsNotNone(geojson)
        self.assertEqual(geojson["type"], "FeatureCollection")
        self.assertEqual(
            geojson["features"][0]["properties"]["source"],
            "nominatim_openstreetmap",
        )

    @patch("app.services.boundaries.is_database_configured", return_value=False)
    @patch("app.services.boundaries.find_boundary_file", return_value=(None, "no local"))
    @patch("app.services.boundaries.find_database_boundary", return_value=(None, "no db"))
    @patch("app.services.boundaries.fetch_online_boundary")
    def test_region_boundary_uses_online_polygon_before_simulated_fallback(
        self,
        fetch_online_boundary,
        _find_database_boundary,
        _find_boundary_file,
        _is_database_configured,
    ) -> None:
        fetch_online_boundary.return_value = (
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {"name": "Testville"},
                        "geometry": sample_polygon_geometry(),
                    },
                ],
            },
            "online OSM/Nominatim polygon match: city=Testville",
        )

        result = get_region_boundary("Testville", TEST_LOCATION)

        self.assertEqual(result.boundary_source, "online_osm")
        self.assertEqual(result.boundary_name, "Testville")
        self.assertEqual(len(result.polygon), 5)


def sample_polygon_geometry() -> dict[str, object]:
    return {
        "type": "Polygon",
        "coordinates": [
            [
                [19.5, 10.5],
                [20.5, 10.5],
                [20.5, 9.5],
                [19.5, 9.5],
                [19.5, 10.5],
            ],
        ],
    }


if __name__ == "__main__":
    unittest.main()
