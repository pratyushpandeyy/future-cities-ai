import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.models import Place
from app.db.session import Base
from app.main import app
from app.models.schemas import (
    ClimateRasterSample,
    LocationResult,
    RegionBoundaryResponse,
)
from app.services.spatial_resolution import persist_place, resolve_spatial_context


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
    geocoder_metadata={"mapbox_id": "neighborhood.whitefield"},
    known=True,
    extrapolated=False,
    location_id="neighborhood.whitefield",
)

WHITEFIELD_BOUNDARY = RegionBoundaryResponse(
    location=WHITEFIELD,
    boundary_source="real_geojson",
    boundary_name="Bengaluru Urban / Bangalore",
    boundary_match_reason="local GeoJSON alias match: whitefield",
    climate_region_type="highland",
    polygon=[
        [77.5, 13.1],
        [77.9, 13.1],
        [77.9, 12.8],
        [77.5, 12.8],
        [77.5, 13.1],
    ],
)

WHITEFIELD_SAMPLE = ClimateRasterSample(
    sampled_value=0.62,
    grid_cell_id="FC-RAS-KA-001",
    raster_source="sampled_mock_scientific_grid",
    dataset_name="Future Cities AI demo heat stress grid v0",
    dataset_resolution="5 degree demo grid",
    layer_type="heat_stress",
)


class SpatialResolutionServiceTests(unittest.TestCase):
    @patch(
        "app.services.spatial_resolution.sample_climate_raster",
        return_value=WHITEFIELD_SAMPLE,
    )
    @patch(
        "app.services.spatial_resolution.get_region_boundary",
        return_value=WHITEFIELD_BOUNDARY,
    )
    @patch(
        "app.services.spatial_resolution.persist_place",
        return_value=(None, False, "Database disabled for test."),
    )
    @patch(
        "app.services.spatial_resolution.resolve_location",
        return_value=WHITEFIELD,
    )
    def test_resolves_location_boundary_and_climate_cell(
        self,
        _resolve_location,
        _persist_place,
        _get_region_boundary,
        _sample_climate_raster,
    ) -> None:
        result = resolve_spatial_context("Whitefield")

        self.assertEqual(result.resolution_level, "locality")
        self.assertEqual(result.boundary_name, "Bengaluru Urban / Bangalore")
        self.assertEqual(result.climate_grid_cell_id, "FC-RAS-KA-001")
        self.assertEqual(result.confidence, "high")
        self.assertFalse(result.fallback_used)

    def test_persist_place_reuses_provider_identity(self) -> None:
        engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        session_factory = sessionmaker(bind=engine)
        Base.metadata.create_all(bind=engine)

        with (
            patch(
                "app.services.spatial_resolution.is_database_configured",
                return_value=True,
            ),
            patch(
                "app.services.spatial_resolution.SessionLocal",
                session_factory,
            ),
        ):
            first_id, first_persisted, _ = persist_place(WHITEFIELD)
            second_id, second_persisted, _ = persist_place(WHITEFIELD)

        with session_factory() as session:
            place_count = session.query(Place).count()

        self.assertTrue(first_persisted)
        self.assertTrue(second_persisted)
        self.assertEqual(first_id, second_id)
        self.assertEqual(place_count, 1)


class SpatialResolutionRouteTests(unittest.TestCase):
    @patch(
        "app.api.routes.spatial.resolve_spatial_context",
    )
    def test_endpoint_returns_spatial_context(self, resolve_context) -> None:
        resolve_context.return_value = resolve_spatial_context_response()
        client = TestClient(app)

        response = client.post("/api/spatial/resolve", json={"query": "Whitefield"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["resolution_level"], "locality")
        self.assertEqual(
            response.json()["climate_grid_cell_id"],
            "FC-RAS-KA-001",
        )

    def test_endpoint_rejects_empty_query(self) -> None:
        client = TestClient(app)

        response = client.post("/api/spatial/resolve", json={"query": ""})

        self.assertEqual(response.status_code, 422)


def resolve_spatial_context_response():
    from app.models.schemas import SpatialResolutionResponse

    return SpatialResolutionResponse(
        input_query="Whitefield",
        place_persisted=False,
        resolved_location=WHITEFIELD,
        resolution_level="locality",
        boundary_name="Bengaluru Urban / Bangalore",
        boundary_source="real_geojson",
        boundary_match_reason="local GeoJSON alias match: whitefield",
        climate_region_type="highland",
        climate_grid_cell_id="FC-RAS-KA-001",
        climate_sampled_value=0.62,
        climate_sample_source="sampled_mock_scientific_grid",
        dataset_name="Future Cities AI demo heat stress grid v0",
        dataset_resolution="5 degree demo grid",
        confidence="high",
        fallback_used=False,
        resolution_notes=["Database disabled for test."],
    )


if __name__ == "__main__":
    unittest.main()
