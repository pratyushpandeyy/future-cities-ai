from app.services.environmental_data import get_environmental_context_for_features
from app.services.providers.feature_provider import FeatureValue, clamp


class EnvironmentProvider:
    """Retrieves land, elevation, vegetation, and physical exposure features."""

    def get_features(
        self,
        *,
        latitude: float,
        longitude: float,
        climate_region_type: str,
        defaults: dict[str, float],
        warming_factor: float,
    ) -> dict[str, FeatureValue]:
        context = get_environmental_context_for_features(
            latitude=latitude,
            longitude=longitude,
        )
        features: dict[str, FeatureValue] = {}

        if context.land_cover:
            features["land_cover_class"] = FeatureValue(
                name="land_cover_class",
                value=context.land_cover.value,
                unit=context.land_cover.unit,
                dataset="esa_worldcover",
                provider=context.land_cover.provider,
                retrieval_mode="local_or_remote_raster",
                confidence=context.land_cover.confidence,
                fallback=False,
                raw_source=context.land_cover.source_url,
                metadata={"category": context.land_cover.category},
            )

        vegetation_value = (
            context.green_cover_proxy
            if context.green_cover_proxy is not None
            else defaults["vegetation"]
        )
        features["vegetation_index"] = FeatureValue(
            name="vegetation_index",
            value=round(clamp(vegetation_value - warming_factor * 0.09), 4),
            unit="normalized_0_1",
            dataset="esa_worldcover" if context.green_cover_proxy is not None else None,
            provider=(
                "esa_worldcover_2021"
                if context.green_cover_proxy is not None
                else "regional_environment_prior"
            ),
            retrieval_mode=(
                "land_cover_proxy"
                if context.green_cover_proxy is not None
                else "deterministic_fallback"
            ),
            confidence="medium" if context.green_cover_proxy is not None else "low",
            fallback=context.green_cover_proxy is None,
            raw_source=(
                "WorldCover green-cover class proxy"
                if context.green_cover_proxy is not None
                else f"{climate_region_type} vegetation prior"
            ),
        )

        features["built_up_proxy"] = FeatureValue(
            name="built_up_proxy",
            value=context.built_up_proxy if context.built_up_proxy is not None else 0.0,
            unit="binary_0_1",
            dataset="esa_worldcover" if context.built_up_proxy is not None else None,
            provider=(
                "esa_worldcover_2021"
                if context.built_up_proxy is not None
                else "regional_environment_prior"
            ),
            retrieval_mode=(
                "land_cover_proxy"
                if context.built_up_proxy is not None
                else "deterministic_fallback"
            ),
            confidence="medium" if context.built_up_proxy is not None else "low",
            fallback=context.built_up_proxy is None,
            raw_source="WorldCover built-up class proxy",
        )

        features["coastal_exposure_index"] = FeatureValue(
            name="coastal_exposure_index",
            value=defaults["coastal"],
            unit="normalized_0_1",
            dataset=None,
            provider="regional_environment_prior",
            retrieval_mode="deterministic_fallback",
            confidence="low",
            fallback=True,
            raw_source=f"{climate_region_type} coastal-exposure prior",
        )

        features["elevation_m"] = FeatureValue(
            name="elevation_m",
            value=context.elevation.value if context.elevation else defaults["elevation"],
            unit="meters",
            dataset="copernicus_dem" if context.elevation else None,
            provider=(
                context.elevation.provider
                if context.elevation
                else "regional_environment_prior"
            ),
            retrieval_mode="remote_cog" if context.elevation else "deterministic_fallback",
            confidence="medium" if context.elevation else "low",
            fallback=context.elevation is None,
            raw_source=(
                context.elevation.source_url
                if context.elevation
                else f"{climate_region_type} elevation prior"
            ),
        )

        features["slope_index"] = FeatureValue(
            name="slope_index",
            value=0.1,
            unit="normalized_0_1",
            dataset=None,
            provider="terrain_proxy_placeholder",
            retrieval_mode="deterministic_fallback",
            confidence="low",
            fallback=True,
            raw_source="Slope proxy placeholder until DEM neighborhood sampling is enabled",
        )

        return features

