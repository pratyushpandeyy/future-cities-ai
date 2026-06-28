import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.models import AdministrativeBoundary
from app.db.session import Base
from app.models.schemas import LocationResult
from app.services.boundaries import match_database_boundary
from app.services.boundary_resolution import boundary_search_hierarchy


WHITEFIELD = LocationResult(
    location_name="Whitefield",
    region="Karnataka",
    climate_zone="Geocoded regional climate cell",
    latitude=12.9698,
    longitude=77.7499,
    locality="Whitefield",
    district="Bengaluru Urban",
    city="Bengaluru",
    country="India",
    hierarchy_label="Whitefield / Bengaluru Urban / Bengaluru / Karnataka / India",
    place_type="neighborhood",
    geocoder_provider="mapbox",
    known=True,
    extrapolated=False,
    location_id="neighborhood.whitefield",
)


class BoundaryResolutionTests(unittest.TestCase):
    def test_search_hierarchy_preserves_specific_to_broad_order(self) -> None:
        hierarchy = boundary_search_hierarchy("Whitefield", WHITEFIELD)

        self.assertEqual(hierarchy[0].level, "input")
        self.assertEqual(hierarchy[0].value, "Whitefield")
        self.assertEqual([candidate.level for candidate in hierarchy[:5]], [
            "input",
            "district",
            "city",
            "region",
            "country",
        ])

    def test_database_boundary_prefers_specific_city_alias_over_state(self) -> None:
        engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        session_factory = sessionmaker(bind=engine)
        Base.metadata.create_all(bind=engine)

        with session_factory() as session:
            session.add_all(
                [
                    AdministrativeBoundary(
                        name="Karnataka",
                        aliases=["karnataka", "india"],
                        country="India",
                        region_type="state",
                        climate_region_type="highland",
                        source="test",
                        geometry_geojson=sample_geojson(),
                    ),
                    AdministrativeBoundary(
                        name="Bengaluru Urban",
                        aliases=["bengaluru urban", "bengaluru", "whitefield"],
                        country="India",
                        region_type="urban_district",
                        climate_region_type="highland",
                        source="test",
                        geometry_geojson=sample_geojson(),
                    ),
                ],
            )
            session.commit()

            boundary, reason = match_database_boundary(session, "Whitefield", WHITEFIELD)

        self.assertIsNotNone(boundary)
        self.assertEqual(boundary.name, "Bengaluru Urban")
        self.assertIn("database hierarchy", reason)
        self.assertIn("whitefield", reason.lower())


def sample_geojson() -> dict[str, object]:
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"name": "Sample"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [77.5, 13.1],
                            [77.9, 13.1],
                            [77.9, 12.8],
                            [77.5, 12.8],
                            [77.5, 13.1],
                        ],
                    ],
                },
            },
        ],
    }


if __name__ == "__main__":
    unittest.main()
