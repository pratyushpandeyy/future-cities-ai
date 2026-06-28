from app.services.ml_training import FEATURE_DEFAULTS

TARGET_SOURCE = "raster_anchored_proxy_labels_v1"


def derive_training_targets(
    features: dict[str, float],
    *,
    data_completeness: float = 0.0,
) -> dict[str, float]:
    complete_features = dict(FEATURE_DEFAULTS)
    complete_features.update(features)

    heat = heat_adjustment_target(complete_features)
    flood = flood_adjustment_target(complete_features)
    water = water_stress_target(complete_features, heat)
    comfort = comfort_adjustment_target(complete_features, heat)
    livability = livability_adjustment_target(
        features=complete_features,
        heat=heat,
        flood=flood,
        water=water,
        data_completeness=data_completeness,
    )

    return {
        "heat_adjustment": round(heat, 4),
        "flood_adjustment": round(flood, 4),
        "comfort_adjustment": round(comfort, 4),
        "water_stress_adjustment": round(water, 4),
        "livability_adjustment": round(livability, 4),
    }


def heat_adjustment_target(features: dict[str, float]) -> float:
    future_tmax = features["future_monthly_tmax_c"]
    heat_index = features["heat_stress_index"]
    urban_density = features["urban_density_index"]
    humidity = features["relative_humidity_pct"]

    return (
        (future_tmax - 26.0) * 0.95
        + (heat_index - 0.5) * 18.0
        + urban_density * 3.2
        + max(0.0, humidity - 60.0) * 0.045
        + features["warming_level_c"] * 1.15
    )


def flood_adjustment_target(features: dict[str, float]) -> float:
    precipitation_anomaly = max(0.0, features["precipitation_anomaly_pct"])
    monthly_precipitation = max(0.0, features["future_monthly_precipitation_mm"] - 80.0)

    return (
        precipitation_anomaly * 0.11
        + monthly_precipitation * 0.028
        + features["coastal_exposure_index"] * 4.5
        + features["urban_density_index"] * 2.2
    )


def water_stress_target(features: dict[str, float], heat: float) -> float:
    dry_signal = max(0.0, -features["precipitation_anomaly_pct"]) * 0.08

    return (
        features["water_stress_index"] * 7.5
        + max(0.0, heat) * 0.14
        + dry_signal
        + features["future_time_index"] * 2.0
    )


def comfort_adjustment_target(features: dict[str, float], heat: float) -> float:
    green_buffer = features["vegetation_index"] * 6.0
    wind_buffer = min(4.0, features["future_monthly_wind_speed_m_s"] * 0.7)

    return -(
        max(0.0, heat) * 0.5
        + max(0.0, features["relative_humidity_pct"] - 50.0) * 0.045
        + features["urban_density_index"] * 1.9
        - green_buffer
        - wind_buffer
    )


def livability_adjustment_target(
    *,
    features: dict[str, float],
    heat: float,
    flood: float,
    water: float,
    data_completeness: float,
) -> float:
    green_buffer = features["vegetation_index"] * 0.9
    confidence_penalty = max(0.0, 0.5 - data_completeness) * 1.5

    return -(
        max(0.0, heat) * 0.18
        + max(0.0, flood) * 0.12
        + water * 0.15
        - green_buffer
        + confidence_penalty
    )
