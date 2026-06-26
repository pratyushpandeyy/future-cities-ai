import os

from app.models.schemas import (
    ClimateFeatureVector,
    ClimateRasterSample,
    EngineeredFeature,
    FeatureBuildRequest,
    SpatialResolutionResponse,
)
from app.services.climate_data.climate_data_broker import (
    sample_climate_data,
)
from app.services.dataset_registry import available_dataset_keys
from app.services.environmental_data import (
    get_environmental_context_for_features,
)
from app.services.spatial_resolution import resolve_spatial_context


FEATURE_SCHEMA_VERSION = "climate_features_v1"

REGION_DEFAULTS = {
    "tropical_humid": {
        "humidity": 78,
        "vegetation": 0.48,
        "water_stress": 0.55,
        "coastal": 0.9,
        "elevation": 40,
    },
    "mediterranean": {
        "humidity": 58,
        "vegetation": 0.42,
        "water_stress": 0.68,
        "coastal": 0.45,
        "elevation": 380,
    },
    "arid": {
        "humidity": 30,
        "vegetation": 0.14,
        "water_stress": 0.9,
        "coastal": 0.25,
        "elevation": 280,
    },
    "temperate_oceanic": {
        "humidity": 74,
        "vegetation": 0.66,
        "water_stress": 0.3,
        "coastal": 0.55,
        "elevation": 120,
    },
    "continental": {
        "humidity": 52,
        "vegetation": 0.46,
        "water_stress": 0.5,
        "coastal": 0.12,
        "elevation": 300,
    },
    "highland": {
        "humidity": 60,
        "vegetation": 0.55,
        "water_stress": 0.48,
        "coastal": 0.05,
        "elevation": 850,
    },
}


def build_climate_feature_vector(
    payload: FeatureBuildRequest,
    spatial: SpatialResolutionResponse | None = None,
) -> ClimateFeatureVector:
    spatial = spatial or resolve_spatial_context(payload.query)
    climate_region = spatial.climate_region_type or infer_climate_region(
        spatial.resolved_location.climate_zone,
    )
    defaults = REGION_DEFAULTS.get(climate_region, REGION_DEFAULTS["continental"])
    year_factor = max(0.0, payload.year - 2025) / 75
    warming_factor = max(0.0, payload.warming_level - 1.0) / 3
    season = payload.season.strip().lower()
    place_type = (spatial.resolved_location.place_type or "").lower()
    month = representative_month(payload.season, spatial.resolved_location.latitude)
    climate_samples = load_climate_features(
        latitude=spatial.resolved_location.latitude,
        longitude=spatial.resolved_location.longitude,
        year=payload.year,
        scenario=payload.climate_scenario,
        month=month,
        model=payload.climate_model,
    )
    future_tmax = climate_samples.get("tmax")
    future_tmin = climate_samples.get("tmin")
    future_precipitation = climate_samples.get("prec")
    future_humidity = climate_samples.get("humidity")
    future_wind = climate_samples.get("wind_speed")
    future_solar = climate_samples.get("solar_radiation")
    environmental = get_environmental_context_for_features(
        latitude=spatial.resolved_location.latitude,
        longitude=spatial.resolved_location.longitude,
    )
    heat_sample = (
        normalize_temperature_heat(future_tmax.sampled_value)
        if future_tmax
        else spatial.climate_sampled_value
    )

    heat_stress = (
        clamp(heat_sample)
        if heat_sample is not None
        else clamp(0.42 + warming_factor * 0.36 + year_factor * 0.12)
    )
    urban_density = infer_urban_density(place_type, spatial.resolved_location.city)
    precipitation_anomaly = (
        18 * warming_factor
        + (24 if season == "monsoon" else -8 if season == "summer" else 4)
    )

    features = {
        "temperature_anomaly_c": fallback_feature(
            round(payload.warming_level * (0.82 + heat_stress * 0.28), 3),
            "degC",
            "scenario-derived temperature anomaly proxy",
        ),
        "heat_stress_index": EngineeredFeature(
            value=round(heat_stress, 4),
            unit="normalized_0_1",
            source=(
                future_tmax.raster_source
                if future_tmax
                else spatial.climate_sample_source or "deterministic heat fallback"
            ),
            dataset_key=(
                "worldclim_cmip6"
                if future_tmax
                else "demo_heat_stress_grid_v0"
                if spatial.climate_sampled_value is not None
                else None
            ),
            is_fallback=future_tmax is None,
            confidence=(
                "high"
                if future_tmax
                else "medium"
                if spatial.climate_sampled_value is not None
                else "low"
            ),
        ),
        "precipitation_anomaly_pct": fallback_feature(
            round(precipitation_anomaly, 3),
            "percent",
            "season and warming precipitation proxy",
        ),
        "relative_humidity_pct": fallback_feature(
            round(
                future_humidity.sampled_value
                if future_humidity
                else defaults["humidity"] + warming_factor * 3,
                3,
            ),
            "percent",
            (
                "NASA NEX-GDDP-CMIP6 monthly relative humidity"
                if future_humidity
                else f"{climate_region} regional humidity prior"
            ),
        ),
        "vegetation_index": fallback_feature(
            round(
                clamp(
                    (
                        environmental.green_cover_proxy
                        if environmental.green_cover_proxy is not None
                        else defaults["vegetation"]
                    )
                    - warming_factor * 0.09,
                ),
                4,
            ),
            "normalized_0_1",
            (
                "ESA WorldCover point-class green-cover proxy"
                if environmental.green_cover_proxy is not None
                else f"{climate_region} vegetation prior"
            ),
        ),
        "water_stress_index": fallback_feature(
            round(
                clamp(
                    defaults["water_stress"]
                    + warming_factor * 0.16
                    + (0.08 if season == "summer" else -0.05 if season == "monsoon" else 0),
                ),
                4,
            ),
            "normalized_0_1",
            f"{climate_region} water-stress prior",
        ),
        "urban_density_index": fallback_feature(
            (
                max(urban_density, 0.85)
                if environmental.built_up_proxy == 1.0
                else urban_density
            ),
            "normalized_0_1",
            (
                "place-type prior adjusted by ESA WorldCover built-up class"
                if environmental.built_up_proxy is not None
                else f"place-type prior: {place_type or 'unknown'}"
            ),
        ),
        "coastal_exposure_index": fallback_feature(
            defaults["coastal"],
            "normalized_0_1",
            f"{climate_region} coastal-exposure prior",
        ),
        "elevation_m": fallback_feature(
            (
                environmental.elevation.value
                if environmental.elevation
                else defaults["elevation"]
            ),
            "meters",
            (
                "Copernicus DEM 30m remote COG"
                if environmental.elevation
                else f"{climate_region} elevation prior"
            ),
        ),
        "future_time_index": EngineeredFeature(
            value=round(year_factor, 4),
            unit="normalized_0_1",
            source="scenario input",
            is_fallback=False,
            confidence="high",
        ),
        "warming_level_c": EngineeredFeature(
            value=payload.warming_level,
            unit="degC",
            source="scenario input",
            is_fallback=False,
            confidence="high",
        ),
    }
    add_climate_sample_feature(
        features,
        "future_monthly_tmax_c",
        future_tmax,
    )
    add_climate_sample_feature(
        features,
        "future_monthly_tmin_c",
        future_tmin,
    )
    add_climate_sample_feature(
        features,
        "future_monthly_precipitation_mm",
        future_precipitation,
    )
    add_climate_sample_feature(
        features,
        "future_monthly_relative_humidity_pct",
        future_humidity,
    )
    add_climate_sample_feature(
        features,
        "future_monthly_wind_speed_m_s",
        future_wind,
    )
    add_climate_sample_feature(
        features,
        "future_monthly_solar_radiation_w_m2",
        future_solar,
    )
    mark_environmental_feature_real(
        features,
        "relative_humidity_pct",
        future_humidity is not None,
        "nex_gddp_cmip6",
    )
    mark_environmental_feature_real(
        features,
        "elevation_m",
        environmental.elevation is not None,
        "copernicus_dem",
    )
    mark_environmental_feature_real(
        features,
        "vegetation_index",
        environmental.land_cover is not None,
        "esa_worldcover",
    )
    mark_environmental_feature_real(
        features,
        "urban_density_index",
        environmental.land_cover is not None,
        "esa_worldcover",
    )
    fallback_feature_names = [
        name for name, feature in features.items() if feature.is_fallback
    ]
    completeness = round(
        (len(features) - len(fallback_feature_names)) / len(features),
        3,
    )

    return ClimateFeatureVector(
        input_query=payload.query.strip(),
        place_id=spatial.place_id,
        resolved_name=spatial.resolved_location.location_name,
        latitude=spatial.resolved_location.latitude,
        longitude=spatial.resolved_location.longitude,
        resolution_level=spatial.resolution_level,
        year=payload.year,
        warming_level=payload.warming_level,
        season=payload.season,
        time_of_day=payload.time_of_day,
        climate_region_type=climate_region,
        features=features,
        available_dataset_keys=available_dataset_keys(),
        fallback_feature_names=fallback_feature_names,
        data_completeness=completeness,
        confidence=feature_confidence(completeness, spatial.confidence),
        feature_schema_version=FEATURE_SCHEMA_VERSION,
    )


def fallback_feature(value: float, unit: str, source: str) -> EngineeredFeature:
    return EngineeredFeature(
        value=float(value),
        unit=unit,
        source=source,
        is_fallback=True,
        confidence="low",
    )


def infer_climate_region(climate_zone: str) -> str:
    normalized = climate_zone.lower()

    if "tropical" in normalized or "humid" in normalized:
        return "tropical_humid"
    if "mediterranean" in normalized:
        return "mediterranean"
    if "arid" in normalized or "desert" in normalized:
        return "arid"
    if "maritime" in normalized or "oceanic" in normalized:
        return "temperate_oceanic"
    if "plateau" in normalized or "highland" in normalized:
        return "highland"

    return "continental"


def infer_urban_density(place_type: str, city: str | None) -> float:
    if place_type in {"neighborhood", "locality", "address", "poi"}:
        return 0.78
    if place_type in {"place", "city", "district", "borough"}:
        return 0.68
    if city:
        return 0.62

    return 0.42


def feature_confidence(completeness: float, spatial_confidence: str) -> str:
    if completeness >= 0.7 and spatial_confidence == "high":
        return "high"
    if completeness >= 0.35 and spatial_confidence in {"high", "medium"}:
        return "medium"

    return "low"


def clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def representative_month(season: str, latitude: float) -> int:
    normalized = season.strip().lower()
    northern_months = {
        "winter": 1,
        "spring": 4,
        "summer": 7,
        "monsoon": 8,
        "autumn": 10,
        "fall": 10,
    }
    month = northern_months.get(normalized, 7)

    if latitude < 0 and normalized in {"winter", "summer"}:
        return 7 if normalized == "winter" else 1

    return month


def load_climate_features(
    *,
    latitude: float,
    longitude: float,
    year: int,
    scenario: str,
    month: int,
    model: str | None,
) -> dict[str, ClimateRasterSample]:
    samples: dict[str, ClimateRasterSample] = {}

    variables = ["tmax", "tmin", "prec"]

    if os.getenv("EXTENDED_CLIMATE_FEATURES_ENABLED", "false").lower() in {
        "1",
        "true",
        "yes",
    }:
        variables.extend(
            ["humidity", "wind_speed", "solar_radiation"],
        )

    for variable in variables:
        sample = sample_climate_data(
            latitude=latitude,
            longitude=longitude,
            year=year,
            scenario=scenario,
            variable=variable,
            month=month,
            model=model,
            allow_demo_fallback=False,
        )

        if sample:
            samples[variable] = sample

    return samples


def normalize_temperature_heat(temperature_c: float) -> float:
    return clamp((temperature_c - 15) / 30)


def add_climate_sample_feature(
    features: dict[str, EngineeredFeature],
    name: str,
    sample: ClimateRasterSample | None,
) -> None:
    if sample is None:
        return

    features[name] = EngineeredFeature(
        value=sample.sampled_value,
        unit=sample.unit or "unknown",
        source=(
            f"{sample.provider or sample.raster_source}; {sample.model}; "
            f"{sample.scenario}; {sample.period}; month {sample.month}"
        ),
        dataset_key=(
            "worldclim_cmip6"
            if sample.provider == "local_worldclim"
            else "nex_gddp_cmip6"
        ),
        is_fallback=False,
        confidence="high",
    )


def mark_environmental_feature_real(
    features: dict[str, EngineeredFeature],
    name: str,
    available: bool,
    dataset_key: str,
) -> None:
    if not available:
        return

    features[name] = features[name].model_copy(
        update={
            "dataset_key": dataset_key,
            "is_fallback": False,
            "confidence": "medium",
        },
    )
