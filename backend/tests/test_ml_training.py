import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.models.schemas import ClimateFeatureHarvestRequest
from app.services.feature_harvesting import harvest_climate_training_features
from app.models.schemas import ClimateFeatureVector, EngineeredFeature
from app.services.ml_inference import predict_climate_adjustments
from app.services.ml_training import (
    FEATURE_NAMES,
    get_model_status,
    train_climate_adjustment_model,
)


class ClimateModelTrainingTests(unittest.TestCase):
    def test_trains_and_reports_model_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "model.json"
            result = train_climate_adjustment_model(path, overwrite=True)
            status = get_model_status(path)

            self.assertTrue(path.exists())
            self.assertTrue(result.trained)
            self.assertEqual(status.model_version, "trained_linear_adjustment_v2")
            self.assertGreater(status.training_row_count or 0, 0)
            self.assertIn("heat_adjustment_mae", status.metrics)
            self.assertIn("heat_adjustment_validation_mae", status.metrics)
            self.assertIn("heat_adjustment_validation_r2", status.metrics)

    def test_inference_uses_trained_artifact_when_available(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "model.json"
            train_climate_adjustment_model(path, overwrite=True)
            features = ClimateFeatureVector(
                input_query="Istanbul",
                resolved_name="Istanbul",
                latitude=41.0,
                longitude=29.0,
                resolution_level="city",
                year=2050,
                warming_level=2.7,
                season="Summer",
                time_of_day="Afternoon",
                climate_region_type="mediterranean",
                features={
                    name: EngineeredFeature(
                        value=0.5 if name not in {"relative_humidity_pct"} else 58,
                        unit="test",
                        source="test",
                        is_fallback=False,
                        confidence="high",
                    )
                    for name in FEATURE_NAMES
                },
                available_dataset_keys=[],
                fallback_feature_names=[],
                data_completeness=1.0,
                confidence="high",
                feature_schema_version="test",
            )

            with patch("app.services.ml_training.DEFAULT_MODEL_PATH", path):
                prediction = predict_climate_adjustments(features)

            self.assertEqual(
                prediction.model_version,
                "trained_linear_adjustment_v2",
            )
            self.assertEqual(
                prediction.model_type,
                "trained_linear_regression_artifact",
            )
            self.assertFalse(prediction.fallback_used)

    @patch("app.services.feature_harvesting.build_climate_feature_vector")
    def test_harvested_features_can_train_model(self, build_features) -> None:
        build_features.return_value = climate_feature_vector_fixture()

        with tempfile.TemporaryDirectory() as directory:
            feature_path = Path(directory) / "features.json"
            model_path = Path(directory) / "model.json"
            harvest = harvest_climate_training_features(
                ClimateFeatureHarvestRequest(
                    locations=["Whitefield"],
                    years=[2050],
                    warming_levels=[2.7],
                    seasons=["Summer"],
                    output_path=str(feature_path),
                    overwrite=True,
                ),
            )
            result = train_climate_adjustment_model(
                model_path,
                training_data_path=feature_path,
                overwrite=True,
            )

            self.assertEqual(harvest.row_count, 1)
            self.assertTrue(feature_path.exists())
            self.assertIn("raster_anchored_proxy_labels_v1", result.training_source)
            self.assertEqual(result.training_row_count, 1)
            self.assertTrue(model_path.exists())


def climate_feature_vector_fixture() -> ClimateFeatureVector:
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
            name: EngineeredFeature(
                value=0.5 if name not in {"relative_humidity_pct"} else 62,
                unit="test",
                source="test",
                is_fallback=False,
                confidence="high",
            )
            for name in FEATURE_NAMES
        },
        available_dataset_keys=[],
        fallback_feature_names=[],
        data_completeness=1.0,
        confidence="high",
        feature_schema_version="climate_features_v1",
    )


if __name__ == "__main__":
    unittest.main()
