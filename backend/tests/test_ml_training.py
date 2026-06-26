import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

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
            self.assertEqual(status.model_version, "trained_linear_adjustment_v1")
            self.assertGreater(status.training_row_count or 0, 0)
            self.assertIn("heat_adjustment_mae", status.metrics)

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
                "trained_linear_adjustment_v1",
            )
            self.assertEqual(
                prediction.model_type,
                "trained_linear_regression_artifact",
            )
            self.assertFalse(prediction.fallback_used)


if __name__ == "__main__":
    unittest.main()
