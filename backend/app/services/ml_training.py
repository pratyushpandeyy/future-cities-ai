import json
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean

from app.models.schemas import (
    ClimateFeatureVector,
    ClimateModelStatus,
    ClimateModelTrainingResponse,
)


BACKEND_ROOT = Path(__file__).resolve().parents[2]
MODEL_DIR = BACKEND_ROOT / "data" / "models"
DEFAULT_MODEL_PATH = MODEL_DIR / "climate_adjustment_model_v1.json"
TRAINED_MODEL_VERSION = "trained_linear_adjustment_v1"
MODEL_TYPE = "ordinary_least_squares_linear_regression"

FEATURE_NAMES = [
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
]

FEATURE_DEFAULTS = {
    "heat_stress_index": 0.5,
    "precipitation_anomaly_pct": 0.0,
    "relative_humidity_pct": 55.0,
    "vegetation_index": 0.45,
    "water_stress_index": 0.5,
    "urban_density_index": 0.5,
    "coastal_exposure_index": 0.3,
    "future_time_index": 0.35,
    "warming_level_c": 2.0,
    "future_monthly_tmax_c": 27.0,
    "future_monthly_precipitation_mm": 70.0,
    "future_monthly_wind_speed_m_s": 2.5,
}

TARGET_NAMES = [
    "heat_adjustment",
    "flood_adjustment",
    "comfort_adjustment",
    "water_stress_adjustment",
    "livability_adjustment",
]


def train_climate_adjustment_model(
    output_path: Path | None = None,
    *,
    overwrite: bool = False,
) -> ClimateModelTrainingResponse:
    path = output_path or DEFAULT_MODEL_PATH

    if path.exists() and not overwrite:
        status = get_model_status(path)
        return ClimateModelTrainingResponse(
            **status.model_dump(),
            message=(
                "Model artifact already exists. Pass overwrite=true or use the "
                "training script --overwrite flag to retrain it."
            ),
        )

    rows = build_training_rows()
    coefficients, metrics = fit_linear_models(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    artifact = {
        "model_version": TRAINED_MODEL_VERSION,
        "model_type": MODEL_TYPE,
        "trained_at": datetime.now(UTC).isoformat(),
        "training_row_count": len(rows),
        "feature_names": FEATURE_NAMES,
        "feature_defaults": FEATURE_DEFAULTS,
        "target_names": TARGET_NAMES,
        "coefficients": coefficients,
        "metrics": metrics,
        "notes": [
            "Synthetic supervised baseline trained from expert rule targets.",
            "Replace training_rows with real CMIP6, observed heat, flood, and urban outcome labels when available.",
            "The serving API is stable so future model artifacts can replace this baseline without changing frontend calls.",
        ],
    }
    path.write_text(json.dumps(artifact, indent=2), encoding="utf-8")

    return ClimateModelTrainingResponse(
        model_version=TRAINED_MODEL_VERSION,
        model_type=MODEL_TYPE,
        artifact_path=str(path),
        trained=True,
        trained_at=artifact["trained_at"],
        training_row_count=len(rows),
        feature_names=FEATURE_NAMES,
        target_names=TARGET_NAMES,
        metrics=metrics,
        notes=artifact["notes"],
        message="Trained climate adjustment model artifact.",
    )


def get_model_status(path: Path | None = None) -> ClimateModelStatus:
    artifact_path = path or DEFAULT_MODEL_PATH

    if not artifact_path.exists():
        return ClimateModelStatus(
            model_version="deterministic_linear_baseline_v1",
            model_type="formula_fallback",
            artifact_path=str(artifact_path),
            trained=False,
            notes=[
                "No trained artifact found. Backend will use deterministic formula fallback.",
                "Run backend/scripts/train_climate_model.py to create the local model artifact.",
            ],
        )

    artifact = load_model_artifact(artifact_path)
    return ClimateModelStatus(
        model_version=str(artifact["model_version"]),
        model_type=str(artifact["model_type"]),
        artifact_path=str(artifact_path),
        trained=True,
        trained_at=str(artifact.get("trained_at")),
        training_row_count=int(artifact.get("training_row_count", 0)),
        feature_names=list(artifact.get("feature_names", [])),
        target_names=list(artifact.get("target_names", [])),
        metrics={
            str(key): float(value)
            for key, value in dict(artifact.get("metrics", {})).items()
        },
        notes=[str(note) for note in artifact.get("notes", [])],
    )


def load_model_artifact(path: Path | None = None) -> dict[str, object]:
    artifact_path = path or DEFAULT_MODEL_PATH
    return json.loads(artifact_path.read_text(encoding="utf-8"))


def predict_with_trained_model(
    features: ClimateFeatureVector,
    path: Path | None = None,
) -> dict[str, float] | None:
    artifact_path = path or DEFAULT_MODEL_PATH

    if not artifact_path.exists():
        return None

    artifact = load_model_artifact(artifact_path)
    feature_names = list(artifact["feature_names"])
    defaults = dict(artifact["feature_defaults"])
    vector = [1.0]

    for name in feature_names:
        feature = features.features.get(str(name))
        vector.append(float(feature.value) if feature else float(defaults[name]))

    predictions: dict[str, float] = {}
    coefficients = dict(artifact["coefficients"])

    for target in TARGET_NAMES:
        weights = [float(value) for value in coefficients[target]]
        predictions[target] = round(dot(vector, weights), 3)

    return predictions


def build_training_rows() -> list[dict[str, dict[str, float]]]:
    rows: list[dict[str, dict[str, float]]] = []
    climate_profiles = [
        {
            "heat_stress_index": 0.74,
            "relative_humidity_pct": 78,
            "vegetation_index": 0.36,
            "water_stress_index": 0.62,
            "urban_density_index": 0.88,
            "coastal_exposure_index": 0.92,
            "future_monthly_tmax_c": 32,
            "future_monthly_precipitation_mm": 180,
            "future_monthly_wind_speed_m_s": 2.4,
        },
        {
            "heat_stress_index": 0.58,
            "relative_humidity_pct": 58,
            "vegetation_index": 0.42,
            "water_stress_index": 0.68,
            "urban_density_index": 0.74,
            "coastal_exposure_index": 0.46,
            "future_monthly_tmax_c": 34,
            "future_monthly_precipitation_mm": 28,
            "future_monthly_wind_speed_m_s": 3.1,
        },
        {
            "heat_stress_index": 0.36,
            "relative_humidity_pct": 74,
            "vegetation_index": 0.64,
            "water_stress_index": 0.32,
            "urban_density_index": 0.62,
            "coastal_exposure_index": 0.55,
            "future_monthly_tmax_c": 24,
            "future_monthly_precipitation_mm": 95,
            "future_monthly_wind_speed_m_s": 4.0,
        },
        {
            "heat_stress_index": 0.46,
            "relative_humidity_pct": 60,
            "vegetation_index": 0.52,
            "water_stress_index": 0.48,
            "urban_density_index": 0.68,
            "coastal_exposure_index": 0.08,
            "future_monthly_tmax_c": 29,
            "future_monthly_precipitation_mm": 120,
            "future_monthly_wind_speed_m_s": 2.1,
        },
        {
            "heat_stress_index": 0.82,
            "relative_humidity_pct": 35,
            "vegetation_index": 0.16,
            "water_stress_index": 0.9,
            "urban_density_index": 0.58,
            "coastal_exposure_index": 0.22,
            "future_monthly_tmax_c": 40,
            "future_monthly_precipitation_mm": 8,
            "future_monthly_wind_speed_m_s": 3.5,
        },
    ]
    years = [2030, 2050, 2070, 2090]
    warmings = [1.5, 2.0, 2.7, 3.5]
    seasons = {
        "summer": {"precipitation_anomaly_pct": -8, "season_heat": 0.12},
        "monsoon": {"precipitation_anomaly_pct": 24, "season_heat": 0.02},
        "winter": {"precipitation_anomaly_pct": 4, "season_heat": -0.08},
    }

    for profile in climate_profiles:
        for year in years:
            for warming in warmings:
                for season in seasons.values():
                    features = dict(FEATURE_DEFAULTS)
                    features.update(profile)
                    features["future_time_index"] = round((year - 2025) / 75, 4)
                    features["warming_level_c"] = warming
                    features["heat_stress_index"] = clamp(
                        features["heat_stress_index"]
                        + (warming - 1.5) * 0.07
                        + season["season_heat"],
                    )
                    features["precipitation_anomaly_pct"] = (
                        season["precipitation_anomaly_pct"] + warming * 4
                    )
                    features["future_monthly_tmax_c"] += (warming - 1.5) * 1.4
                    features["future_monthly_precipitation_mm"] *= (
                        1 + features["precipitation_anomaly_pct"] / 100
                    )
                    rows.append(
                        {
                            "features": features,
                            "targets": synthetic_targets(features),
                        },
                    )

    return rows


def synthetic_targets(features: dict[str, float]) -> dict[str, float]:
    heat_signal = (
        (features["heat_stress_index"] - 0.5) * 22
        + (features["future_monthly_tmax_c"] - 25) * 0.85
        + features["urban_density_index"] * 3
        + features["warming_level_c"] * 1.4
    )
    flood_signal = (
        max(0, features["precipitation_anomaly_pct"]) * 0.09
        + max(0, features["future_monthly_precipitation_mm"] - 85) * 0.025
        + features["coastal_exposure_index"] * 5
        + features["urban_density_index"] * 2.5
    )
    green_buffer = features["vegetation_index"] * 6.5
    wind_buffer = min(4.0, features["future_monthly_wind_speed_m_s"] * 0.65)
    water = (
        features["water_stress_index"] * 7
        + max(0, heat_signal) * 0.17
        + features["future_time_index"] * 2.2
    )
    comfort = -(
        heat_signal * 0.52
        + features["relative_humidity_pct"] * 0.035
        + features["urban_density_index"] * 2.1
        - green_buffer
        - wind_buffer
    )
    livability = -(
        max(0, heat_signal) * 0.18
        + max(0, flood_signal) * 0.12
        + water * 0.16
        - green_buffer * 0.13
    )

    return {
        "heat_adjustment": heat_signal,
        "flood_adjustment": flood_signal,
        "comfort_adjustment": comfort,
        "water_stress_adjustment": water,
        "livability_adjustment": livability,
    }


def fit_linear_models(
    rows: list[dict[str, dict[str, float]]],
) -> tuple[dict[str, list[float]], dict[str, float]]:
    try:
        import numpy as np
    except ImportError as exc:
        raise RuntimeError(
            "numpy is required to train the climate adjustment model",
        ) from exc

    x = np.array(
        [
            [1.0, *[row["features"][feature] for feature in FEATURE_NAMES]]
            for row in rows
        ],
        dtype=float,
    )
    coefficients: dict[str, list[float]] = {}
    metrics: dict[str, float] = {}

    for target in TARGET_NAMES:
        y = np.array([row["targets"][target] for row in rows], dtype=float)
        beta, *_ = np.linalg.lstsq(x, y, rcond=None)
        predicted = x @ beta
        errors = [abs(float(actual - pred)) for actual, pred in zip(y, predicted)]
        coefficients[target] = [round(float(value), 8) for value in beta]
        metrics[f"{target}_mae"] = round(mean(errors), 4)

    return coefficients, metrics


def dot(left: list[float], right: list[float]) -> float:
    return sum(left_value * right_value for left_value, right_value in zip(left, right))


def clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))
