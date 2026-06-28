import unittest

from app.models.schemas import ClimateFeatureVector, EngineeredFeature
from app.services.ml_inference import predict_climate_adjustments


def feature(value: float, unit: str = "normalized_0_1") -> EngineeredFeature:
    return EngineeredFeature(
        value=value,
        unit=unit,
        source="test",
        dataset_key="worldclim_cmip6",
        is_fallback=False,
        confidence="high",
    )


class ClimateModelInferenceTests(unittest.TestCase):
    def test_real_temperature_increases_heat_adjustment(self) -> None:
        moderate = build_vector(27)
        hot = build_vector(39)

        moderate_prediction = predict_climate_adjustments(moderate)
        hot_prediction = predict_climate_adjustments(hot)

        self.assertGreater(
            hot_prediction.heat_adjustment,
            moderate_prediction.heat_adjustment,
        )
        self.assertLess(
            hot_prediction.livability_adjustment,
            moderate_prediction.livability_adjustment,
        )
        self.assertEqual(
            hot_prediction.model_version,
            "trained_linear_adjustment_v2",
        )

    def test_prediction_is_deterministic(self) -> None:
        vector = build_vector(34)

        first = predict_climate_adjustments(vector)
        second = predict_climate_adjustments(vector)

        self.assertEqual(first, second)


def build_vector(future_tmax: float) -> ClimateFeatureVector:
    features = {
        "heat_stress_index": feature(0.64),
        "precipitation_anomaly_pct": feature(12, "percent"),
        "relative_humidity_pct": feature(68, "percent"),
        "vegetation_index": feature(0.35),
        "water_stress_index": feature(0.61),
        "urban_density_index": feature(0.78),
        "coastal_exposure_index": feature(0.7),
        "future_monthly_tmax_c": feature(future_tmax, "degC"),
        "future_monthly_precipitation_mm": feature(95, "mm_per_month"),
    }

    return ClimateFeatureVector(
        input_query="Test City",
        resolved_name="Test City",
        latitude=10,
        longitude=20,
        resolution_level="city",
        year=2050,
        warming_level=2.7,
        season="Summer",
        time_of_day="Afternoon",
        climate_region_type="tropical_humid",
        features=features,
        available_dataset_keys=["worldclim_cmip6"],
        fallback_feature_names=[],
        data_completeness=1,
        confidence="high",
        feature_schema_version="climate_features_v1",
    )


if __name__ == "__main__":
    unittest.main()
