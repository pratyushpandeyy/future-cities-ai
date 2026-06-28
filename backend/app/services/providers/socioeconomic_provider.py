from app.services.providers.feature_provider import FeatureValue


class SocioeconomicProvider:
    """Provides population, infrastructure, healthcare, GDP, and urban proxies."""

    def get_features(
        self,
        *,
        place_type: str,
        city: str | None,
        built_up_proxy: FeatureValue | None,
    ) -> dict[str, FeatureValue]:
        base_urban_density = infer_urban_density(place_type, city)
        built_up_available = built_up_proxy is not None and not built_up_proxy.fallback
        urban_density = (
            max(base_urban_density, 0.85)
            if built_up_available and built_up_proxy.value == 1.0
            else base_urban_density
        )
        features = {
            "urban_density_index": FeatureValue(
                name="urban_density_index",
                value=round(urban_density, 4),
                unit="normalized_0_1",
                dataset="esa_worldcover" if built_up_available else None,
                provider=(
                    "place_type_prior_adjusted_by_worldcover"
                    if built_up_available
                    else "place_type_prior"
                ),
                retrieval_mode=(
                    "land_cover_adjusted_proxy"
                    if built_up_available
                    else "deterministic_fallback"
                ),
                confidence="medium" if built_up_available else "low",
                fallback=not built_up_available,
                raw_source=f"place-type prior: {place_type or 'unknown'}",
            ),
            "population_density_index": FeatureValue(
                name="population_density_index",
                value=round(min(1.0, urban_density + 0.08), 4),
                unit="normalized_0_1",
                dataset=None,
                provider="socioeconomic_placeholder",
                retrieval_mode="deterministic_fallback",
                confidence="low",
                fallback=True,
                raw_source="Population density placeholder until GHSL ingestion is enabled",
            ),
            "infrastructure_proxy_index": FeatureValue(
                name="infrastructure_proxy_index",
                value=round(min(1.0, urban_density + 0.05), 4),
                unit="normalized_0_1",
                dataset=None,
                provider="socioeconomic_placeholder",
                retrieval_mode="deterministic_fallback",
                confidence="low",
                fallback=True,
                raw_source="Infrastructure proxy placeholder",
            ),
            "healthcare_access_index": FeatureValue(
                name="healthcare_access_index",
                value=0.58 if city else 0.45,
                unit="normalized_0_1",
                dataset=None,
                provider="socioeconomic_placeholder",
                retrieval_mode="deterministic_fallback",
                confidence="low",
                fallback=True,
                raw_source="Healthcare access placeholder",
            ),
            "gdp_proxy_index": FeatureValue(
                name="gdp_proxy_index",
                value=0.55 if city else 0.42,
                unit="normalized_0_1",
                dataset=None,
                provider="socioeconomic_placeholder",
                retrieval_mode="deterministic_fallback",
                confidence="low",
                fallback=True,
                raw_source="GDP proxy placeholder",
            ),
        }

        return features


def infer_urban_density(place_type: str, city: str | None) -> float:
    if place_type in {"neighborhood", "locality", "address", "poi"}:
        return 0.78
    if place_type in {"place", "city", "district", "borough"}:
        return 0.68
    if city:
        return 0.62

    return 0.42

