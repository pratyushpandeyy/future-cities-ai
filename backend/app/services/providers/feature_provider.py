from dataclasses import dataclass, field

from app.models.schemas import EngineeredFeature


@dataclass(frozen=True)
class FeatureValue:
    name: str
    value: float
    unit: str
    dataset: str | None
    provider: str
    retrieval_mode: str
    confidence: str
    fallback: bool
    raw_source: str | None = None
    metadata: dict[str, object] = field(default_factory=dict)

    def source_label(self) -> str:
        parts = [self.provider, self.retrieval_mode]
        if self.raw_source:
            parts.append(self.raw_source)

        return " / ".join(part for part in parts if part)

    def to_engineered_feature(self) -> EngineeredFeature:
        return EngineeredFeature(
            value=float(self.value),
            unit=self.unit,
            source=self.source_label(),
            dataset_key=self.dataset,
            is_fallback=self.fallback,
            confidence=self.confidence,
        )


@dataclass(frozen=True)
class FeaturePackage:
    climate: dict[str, FeatureValue] = field(default_factory=dict)
    environment: dict[str, FeatureValue] = field(default_factory=dict)
    socioeconomic: dict[str, FeatureValue] = field(default_factory=dict)
    derived: dict[str, FeatureValue] = field(default_factory=dict)

    def by_name(self) -> dict[str, FeatureValue]:
        merged: dict[str, FeatureValue] = {}
        merged.update(self.climate)
        merged.update(self.environment)
        merged.update(self.socioeconomic)
        merged.update(self.derived)
        return merged


def build_feature_package(
    *,
    latitude: float,
    longitude: float,
    year: int,
    warming_level: float,
    scenario: str,
    season: str,
    month: int,
    model: str | None,
    climate_region_type: str,
    defaults: dict[str, float],
    place_type: str,
    city: str | None,
    year_factor: float,
    warming_factor: float,
) -> FeaturePackage:
    from app.services.providers.climate_provider import ClimateProvider
    from app.services.providers.environment_provider import EnvironmentProvider
    from app.services.providers.socioeconomic_provider import SocioeconomicProvider

    climate = ClimateProvider().get_features(
        latitude=latitude,
        longitude=longitude,
        year=year,
        scenario=scenario,
        month=month,
        model=model,
    )
    environment = EnvironmentProvider().get_features(
        latitude=latitude,
        longitude=longitude,
        climate_region_type=climate_region_type,
        defaults=defaults,
        warming_factor=warming_factor,
    )
    socioeconomic = SocioeconomicProvider().get_features(
        place_type=place_type,
        city=city,
        built_up_proxy=environment.get("built_up_proxy"),
    )
    derived = {
        "future_time_index": FeatureValue(
            name="future_time_index",
            value=round(year_factor, 4),
            unit="normalized_0_1",
            dataset=None,
            provider="scenario_input",
            retrieval_mode="user_selected_year",
            confidence="high",
            fallback=False,
        ),
        "warming_level_c": FeatureValue(
            name="warming_level_c",
            value=warming_level,
            unit="degC",
            dataset=None,
            provider="scenario_input",
            retrieval_mode="user_selected_warming_level",
            confidence="high",
            fallback=False,
        ),
        "water_stress_index": FeatureValue(
            name="water_stress_index",
            value=round(
                clamp(
                    defaults["water_stress"]
                    + warming_factor * 0.16
                    + (0.08 if season == "summer" else -0.05 if season == "monsoon" else 0),
                ),
                4,
            ),
            unit="normalized_0_1",
            dataset=None,
            provider="regional_climate_prior",
            retrieval_mode="deterministic_fallback",
            confidence="low",
            fallback=True,
            raw_source=f"{climate_region_type} water-stress prior",
        ),
    }

    return FeaturePackage(
        climate=climate,
        environment=environment,
        socioeconomic=socioeconomic,
        derived=derived,
    )


def clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))

