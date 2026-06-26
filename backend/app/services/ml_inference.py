from app.models.schemas import ClimateFeatureVector, ClimateModelPrediction
from app.services.ml_training import (
    TRAINED_MODEL_VERSION,
    predict_with_trained_model,
)


MODEL_VERSION = "deterministic_linear_baseline_v1"


def predict_climate_adjustments(
    features: ClimateFeatureVector,
) -> ClimateModelPrediction:
    trained_prediction = predict_with_trained_model(features)

    if trained_prediction:
        inputs_used = [name for name in trained_inputs() if name in features.features]
        return ClimateModelPrediction(
            heat_adjustment=trained_prediction["heat_adjustment"],
            flood_adjustment=trained_prediction["flood_adjustment"],
            comfort_adjustment=trained_prediction["comfort_adjustment"],
            water_stress_adjustment=trained_prediction["water_stress_adjustment"],
            livability_adjustment=trained_prediction["livability_adjustment"],
            model_version=TRAINED_MODEL_VERSION,
            model_type="trained_linear_regression_artifact",
            confidence=features.confidence,
            inputs_used=inputs_used,
            fallback_used=features.data_completeness < 0.5,
        )

    heat = feature_value(features, "heat_stress_index", 0.5)
    precipitation = feature_value(features, "precipitation_anomaly_pct", 0.0)
    humidity = feature_value(features, "relative_humidity_pct", 55.0) / 100
    vegetation = feature_value(features, "vegetation_index", 0.45)
    water_stress = feature_value(features, "water_stress_index", 0.5)
    urban_density = feature_value(features, "urban_density_index", 0.5)
    coastal_exposure = feature_value(features, "coastal_exposure_index", 0.3)
    future_tmax = optional_feature_value(features, "future_monthly_tmax_c")
    future_precipitation = optional_feature_value(
        features,
        "future_monthly_precipitation_mm",
    )
    future_wind = optional_feature_value(
        features,
        "future_monthly_wind_speed_m_s",
    )

    heat_signal = (heat - 0.5) * 20

    if future_tmax is not None:
        heat_signal += (future_tmax - 25) * 0.9

    flood_signal = (
        max(0.0, precipitation) * 0.08
        + coastal_exposure * 5
        + urban_density * 3
    )

    if future_precipitation is not None:
        flood_signal += max(0.0, future_precipitation - 80) * 0.025

    green_buffer = vegetation * 6
    wind_buffer = min(4.0, (future_wind or 0) * 0.7)
    comfort_adjustment = -(
        heat_signal * 0.55
        + humidity * 3
        + urban_density * 2
        - green_buffer
        - wind_buffer
    )
    water_adjustment = water_stress * 7 + max(0.0, heat_signal) * 0.18
    livability_adjustment = -(
        max(0.0, heat_signal) * 0.18
        + max(0.0, flood_signal) * 0.12
        + water_adjustment * 0.16
        - green_buffer * 0.12
    )
    inputs_used = [
        name
        for name in (
            "heat_stress_index",
            "precipitation_anomaly_pct",
            "relative_humidity_pct",
            "vegetation_index",
            "water_stress_index",
            "urban_density_index",
            "coastal_exposure_index",
            "future_monthly_tmax_c",
            "future_monthly_precipitation_mm",
            "future_monthly_relative_humidity_pct",
            "future_monthly_wind_speed_m_s",
            "future_monthly_solar_radiation_w_m2",
        )
        if name in features.features
    ]

    return ClimateModelPrediction(
        heat_adjustment=round(heat_signal, 3),
        flood_adjustment=round(flood_signal, 3),
        comfort_adjustment=round(comfort_adjustment, 3),
        water_stress_adjustment=round(water_adjustment, 3),
        livability_adjustment=round(livability_adjustment, 3),
        model_version=MODEL_VERSION,
        model_type="deterministic_linear_baseline",
        confidence=features.confidence,
        inputs_used=inputs_used,
        fallback_used=features.data_completeness < 0.5,
    )


def feature_value(
    features: ClimateFeatureVector,
    name: str,
    default: float,
) -> float:
    feature = features.features.get(name)
    return float(feature.value) if feature else default


def optional_feature_value(
    features: ClimateFeatureVector,
    name: str,
) -> float | None:
    feature = features.features.get(name)
    return float(feature.value) if feature else None


def trained_inputs() -> tuple[str, ...]:
    return (
        "heat_stress_index",
        "precipitation_anomaly_pct",
        "relative_humidity_pct",
        "vegetation_index",
        "water_stress_index",
        "urban_density_index",
        "coastal_exposure_index",
        "future_time_index",
        "warming_level_c",
        "future_monthly_tmax_c",
        "future_monthly_precipitation_mm",
        "future_monthly_wind_speed_m_s",
    )
