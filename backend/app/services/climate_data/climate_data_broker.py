import os

from app.models.schemas import (
    ClimateDataBrokerStatus,
    ClimateProviderStatus,
    ClimateRasterSample,
)
from app.services.climate_data.climate_raster_service import sample_demo_grid
from app.services.climate_data.providers.base import ClimateDataRequest
from app.services.climate_data.providers.local_worldclim import (
    LocalWorldClimProvider,
)
from app.services.climate_data.providers.nasa_nex_cog import (
    NasaNexCogProvider,
)
from app.services.climate_data.sample_cache import ClimateSampleCache


PROVIDERS = {
    "local_worldclim": LocalWorldClimProvider,
    "nasa_nex_cog": NasaNexCogProvider,
}
DEFAULT_PROVIDER_ORDER = ("local_worldclim", "nasa_nex_cog")


class ClimateDataBroker:
    def __init__(
        self,
        *,
        provider_order: tuple[str, ...] | None = None,
        cache: ClimateSampleCache | None = None,
    ) -> None:
        self.provider_order = provider_order or configured_provider_order()
        self.cache = cache or ClimateSampleCache()

    def sample(
        self,
        request: ClimateDataRequest,
        *,
        allow_demo_fallback: bool = True,
    ) -> ClimateRasterSample | None:
        cache_scope = ",".join(self.provider_order)
        cached = self.cache.get(request, scope=cache_scope)

        if cached:
            return cached

        for provider_name in self.provider_order:
            provider_class = PROVIDERS.get(provider_name)

            if not provider_class:
                continue

            sample = provider_class().sample(request)

            if sample:
                enriched = sample.model_copy(
                    update={
                        "provider": provider_name,
                        "cache_hit": False,
                    },
                )
                self.cache.put(
                    request,
                    enriched,
                    scope=cache_scope,
                )
                return enriched

        if not allow_demo_fallback:
            return None

        fallback = sample_demo_grid(
            request.latitude,
            request.longitude,
            "heat_stress",
        )

        if not fallback:
            return None

        return fallback.model_copy(
            update={
                "provider": "demo_grid",
                "cache_hit": False,
            },
        )


def configured_provider_order() -> tuple[str, ...]:
    configured = os.getenv(
        "CLIMATE_DATA_PROVIDER_ORDER",
        ",".join(DEFAULT_PROVIDER_ORDER),
    )
    return tuple(
        provider.strip()
        for provider in configured.split(",")
        if provider.strip()
    )


def sample_climate_data(
    *,
    latitude: float,
    longitude: float,
    year: int,
    month: int,
    scenario: str,
    variable: str,
    model: str | None = None,
    resolution: str = "2.5m",
    allow_demo_fallback: bool = True,
) -> ClimateRasterSample | None:
    return ClimateDataBroker().sample(
        ClimateDataRequest(
            latitude=latitude,
            longitude=longitude,
            year=year,
            month=month,
            scenario=scenario,
            variable=variable,
            model=model,
            resolution=resolution,
        ),
        allow_demo_fallback=allow_demo_fallback,
    )


def climate_data_broker_status() -> ClimateDataBrokerStatus:
    broker = ClimateDataBroker()
    cache_directory = broker.cache.cache_dir
    cache_entry_count = (
        sum(1 for _ in cache_directory.glob("*.json"))
        if cache_directory.exists()
        else 0
    )

    return ClimateDataBrokerStatus(
        provider_order=list(broker.provider_order),
        cache_directory=str(cache_directory),
        cache_entry_count=cache_entry_count,
        providers=[
            ClimateProviderStatus(
                name="local_worldclim",
                kind="local_geotiff",
                enabled="local_worldclim" in broker.provider_order,
                description=(
                    "Downloaded WorldClim CMIP6 20-year monthly climatologies"
                ),
            ),
            ClimateProviderStatus(
                name="nasa_nex_cog",
                kind="remote_cloud_optimized_geotiff",
                enabled="nasa_nex_cog" in broker.provider_order,
                description=(
                    "Public NASA NEX-GDDP-CMIP6 monthly ensemble median COGs"
                ),
            ),
        ],
    )
