import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.services import boundaries


class BoundaryCatalogTests(unittest.TestCase):
    def tearDown(self) -> None:
        boundaries.local_boundary_catalog.cache_clear()

    def test_catalog_matches_common_geoboundaries_properties(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            boundary_path = Path(directory) / "varanasi_adm2.geojson"
            boundary_path.write_text(
                json.dumps(
                    {
                        "type": "FeatureCollection",
                        "features": [
                            {
                                "type": "Feature",
                                "properties": {
                                    "shapeName": "Varanasi",
                                    "shapeGroup": "IND",
                                },
                                "geometry": {
                                    "type": "Polygon",
                                    "coordinates": [
                                        [
                                            [82.8, 25.5],
                                            [83.2, 25.5],
                                            [83.2, 25.1],
                                            [82.8, 25.1],
                                            [82.8, 25.5],
                                        ],
                                    ],
                                },
                            },
                        ],
                    },
                ),
                encoding="utf-8",
            )

            with patch("app.services.boundaries.BOUNDARY_DIR", Path(directory)):
                boundaries.local_boundary_catalog.cache_clear()
                match = boundaries.find_catalog_boundary_file(
                    "search request for varanasi uttar pradesh india",
                )

            self.assertEqual(match, ("varanasi_adm2.geojson", "varanasi"))


if __name__ == "__main__":
    unittest.main()
