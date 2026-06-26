import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.models.schemas import (
    EnvironmentalContext,
    FeatureBuildRequest,
    LocationResult,
    SpatialResolutionResponse,
)
from app.services.dataset_registry import get_dataset, list_datasets
from app.services.feature_engineering import build_climate_feature_vector


WHITEFIELD_SPATIAL = SpatialResolutionResponse(
    input_query="Whitefield",
    place_persisted=False,
    resolved_location=LocationResult(
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
    ),
    resolution_level="locality",
    boundary_name="Bengaluru Urban / Bangalore",
    boundary_source="real_geojson",
    climate_region_type="highland",
    climate_grid_cell_id="FC-RAS-KA-001",
    climate_sampled_value=0.62,
    climate_sample_source="sampled_mock_scientific_grid",
    dataset_name="Future Cities AI demo heat stress grid v0",
    dataset_resolution="5 degree demo grid",
    confidence="high",
    fallback_used=False,
)
EMPTY_ENVIRONMENT = EnvironmentalContext(
    latitude=12.9698,
    longitude=77.7499,
)


class DatasetRegistryTests(unittest.TestCase):
    def test_builtin_registry_contains_demo_and_future_sources(self) -> None:
        dataset_keys = {dataset.dataset_key for dataset in list_datasets()}

        self.assertIn("demo_heat_stress_grid_v0", dataset_keys)
        self.assertIn("nex_gddp_cmip6", dataset_keys)
        self.assertIn("geoboundaries", dataset_keys)

    def test_get_dataset_returns_none_for_unknown_key(self) -> None:
        self.assertIsNone(get_dataset("not-a-real-dataset"))


class FeatureEngineeringTests(unittest.TestCase):
    @patch(
        "app.services.feature_engineering.get_environmental_context_for_features",
        return_value=EMPTY_ENVIRONMENT,
    )
    @patch(
        "app.services.feature_engineering.sample_climate_data",
        return_value=None,
    )
    @patch(
        "app.services.feature_engineering.resolve_spatial_context",
        return_value=WHITEFIELD_SPATIAL,
    )
    def test_builds_stable_model_feature_contract(
        self,
        _resolve_spatial,
        _worldclim_sample,
        _environmental,
    ) -> None:
        result = build_climate_feature_vector(
            FeatureBuildRequest(
                query="Whitefield",
                year=2050,
                warming_level=2.7,
                season="Summer",
                time_of_day="Afternoon",
            ),
        )

        self.assertEqual(result.feature_schema_version, "climate_features_v1")
        self.assertEqual(result.climate_region_type, "highland")
        self.assertEqual(
            result.features["heat_stress_index"].dataset_key,
            "demo_heat_stress_grid_v0",
        )
        self.assertTrue(result.features["heat_stress_index"].is_fallback)
        self.assertIn("relative_humidity_pct", result.fallback_feature_names)
        self.assertGreater(result.features["temperature_anomaly_c"].value, 2.0)


class DataPipelineRouteTests(unittest.TestCase):
    @patch(
        "app.api.routes.data_pipeline.build_climate_feature_vector",
    )
    def test_feature_endpoint_returns_vector(self, build_features) -> None:
        build_features.return_value = build_climate_feature_vector_response()
        client = TestClient(app)

        response = client.post(
            "/api/features/build",
            json={
                "query": "Whitefield",
                "year": 2050,
                "warming_level": 2.7,
                "season": "Summer",
                "time_of_day": "Afternoon",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["feature_schema_version"], "climate_features_v1")

    def test_dataset_endpoint_lists_registry(self) -> None:
        client = TestClient(app)

        response = client.get("/api/datasets")

        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.json()), 5)


def build_climate_feature_vector_response():
    from app.models.schemas import ClimateFeatureVector, EngineeredFeature

    return ClimateFeatureVector(
        input_query="Whitefield",
        resolved_name="Whitefield",
        latitude=12.9698,
        longitude=77.7499,
        resolution_level="locality",
        year=2050,
        warming_level=2.7,
        season="Summer",
        time_of_day="Afternoon",
        climate_region_type="highland",
        features={
            "heat_stress_index": EngineeredFeature(
                value=0.62,
                unit="normalized_0_1",
                source="sampled_mock_scientific_grid",
                dataset_key="demo_heat_stress_grid_v0",
                is_fallback=False,
                confidence="medium",
            ),
        },
        available_dataset_keys=["demo_heat_stress_grid_v0"],
        fallback_feature_names=[],
        data_completeness=1.0,
        confidence="high",
        feature_schema_version="climate_features_v1",
    )


if __name__ == "__main__":
    unittest.main()
