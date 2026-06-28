import os

from app.models.schemas import ClimateRasterSample
from app.services.climate_data.climate_data_broker import sample_climate_data
from app.services.providers.feature_provider import FeatureValue


VARIABLE_FEATURE_MAP = {
    "tmax": ("future_monthly_tmax_c", "maximum temperature"),
    "tmin": ("future_monthly_tmin_c", "minimum temperature"),
    "prec": ("future_monthly_precipitation_mm", "precipitation"),
    "humidity": ("future_monthly_relative_humidity_pct", "relative humidity"),
    "wind_speed": ("future_monthly_wind_speed_m_s", "wind speed"),
    "solar_radiation": ("future_monthly_solar_radiation_w_m2", "solar radiation"),
}


class ClimateProvider:
    """Retrieves future climate variables from climate-raster providers."""

    def get_features(
        self,
        *,
        latitude: float,
        longitude: float,
        year: int,
        scenario: str,
        month: int,
        model: str | None,
    ) -> dict[str, FeatureValue]:
        features: dict[str, FeatureValue] = {}
        samples: dict[str, ClimateRasterSample] = {}

        for variable in self.variables():
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

            if not sample:
                continue

            samples[variable] = sample
            name, label = VARIABLE_FEATURE_MAP[variable]
            features[name] = self.sample_to_feature(name, sample, label)

        tmax = samples.get("tmax")
        if tmax:
            features["heatwave_proxy_index"] = FeatureValue(
                name="heatwave_proxy_index",
                value=round(clamp((tmax.sampled_value - 28) / 14), 4),
                unit="normalized_0_1",
                dataset=dataset_key(tmax),
                provider=tmax.provider or "climate_provider",
                retrieval_mode=retrieval_mode(tmax),
                confidence="medium",
                fallback=False,
                raw_source="monthly tmax heatwave proxy",
                metadata=sample_metadata(tmax),
            )

        return features

    def variables(self) -> list[str]:
        variables = ["tmax", "tmin", "prec"]

        if os.getenv("EXTENDED_CLIMATE_FEATURES_ENABLED", "false").lower() in {
            "1",
            "true",
            "yes",
        }:
            variables.extend(["humidity", "wind_speed", "solar_radiation"])

        return variables

    def sample_to_feature(
        self,
        name: str,
        sample: ClimateRasterSample,
        label: str,
    ) -> FeatureValue:
        return FeatureValue(
            name=name,
            value=sample.sampled_value,
            unit=sample.unit or "unknown",
            dataset=dataset_key(sample),
            provider=sample.provider or "climate_provider",
            retrieval_mode=retrieval_mode(sample),
            confidence="high",
            fallback=sample.is_fallback,
            raw_source=(
                f"{label}; {sample.model}; {sample.scenario}; "
                f"{sample.period}; month {sample.month}"
            ),
            metadata=sample_metadata(sample),
        )


def dataset_key(sample: ClimateRasterSample) -> str | None:
    if sample.provider == "local_worldclim":
        return "worldclim_cmip6"
    if sample.provider == "nasa_nex_cog":
        return "nex_gddp_cmip6"
    if sample.provider == "demo_grid":
        return "demo_heat_stress_grid_v0"

    return None


def retrieval_mode(sample: ClimateRasterSample) -> str:
    if sample.provider == "local_worldclim":
        return "local_raster"
    if sample.provider == "nasa_nex_cog":
        return "remote_cloud_raster"
    if sample.provider == "demo_grid":
        return "demo_grid_fallback"

    return sample.raster_source


def sample_metadata(sample: ClimateRasterSample) -> dict[str, object]:
    return {
        "grid_cell_id": sample.grid_cell_id,
        "dataset_name": sample.dataset_name,
        "dataset_resolution": sample.dataset_resolution,
        "model": sample.model,
        "scenario": sample.scenario,
        "period": sample.period,
        "month": sample.month,
        "source_path": sample.source_path,
        "cache_hit": sample.cache_hit,
    }


def clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))

