import math
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

from app.models.schemas import ClimateRasterSample
from app.services.climate_data.providers.base import ClimateDataRequest


BASE_URL = (
    "https://nex-gddp-cmip6-cog.s3.us-west-2.amazonaws.com/"
    "monthly/CMIP6_ensemble_median"
)
VARIABLE_MAP = {
    "temperature": "tas",
    "tmax": "tasmax",
    "tmin": "tasmin",
    "prec": "pr",
    "humidity": "hurs",
    "specific_humidity": "huss",
    "wind_speed": "sfcWind",
    "solar_radiation": "rsds",
    "longwave_radiation": "rlds",
}
SUPPORTED_SCENARIOS = {"ssp245", "ssp585"}
BACKEND_ROOT = Path(__file__).resolve().parents[4]
REMOTE_COG_CACHE = BACKEND_ROOT / "data" / "cache" / "remote_cogs" / "nasa_nex"


class NasaNexCogProvider:
    name = "nasa_nex_gddp_cmip6_cog"

    def sample(
        self,
        request: ClimateDataRequest,
    ) -> ClimateRasterSample | None:
        remote_variable = VARIABLE_MAP.get(request.variable)

        if (
            not remote_variable
            or request.scenario not in SUPPORTED_SCENARIOS
            or not 1950 <= request.year <= 2100
        ):
            return None

        try:
            import rasterio
        except ImportError:
            return None

        url = nasa_cog_url(
            variable=remote_variable,
            scenario=request.scenario,
            year=request.year,
            month=request.month,
        )

        sampled = sample_rasterio_source(
            rasterio,
            url,
            request.latitude,
            request.longitude,
            remote=True,
        )

        if sampled is None:
            local_path = cache_remote_cog(url)

            if local_path:
                sampled = sample_rasterio_source(
                    rasterio,
                    str(local_path),
                    request.latitude,
                    request.longitude,
                    remote=False,
                )

        if sampled is None:
            return None

        raw_value, row, column = sampled

        if math.isnan(raw_value):
            return None

        value, unit = normalize_nasa_value(raw_value, remote_variable)

        return ClimateRasterSample(
            sampled_value=round(value, 3),
            grid_cell_id=(
                f"nasa-nex:ensemble-median:{request.scenario}:"
                f"{request.year}{request.month:02d}:{remote_variable}:"
                f"r{row}:c{column}"
            ),
            raster_source=self.name,
            dataset_name="NASA NEX-GDDP-CMIP6 monthly ensemble median COG",
            dataset_resolution="0.25 degree",
            layer_type=request.variable,
            unit=unit,
            variable=request.variable,
            model="CMIP6_ensemble_median",
            scenario=request.scenario,
            period=f"{request.year}-{request.month:02d}",
            month=request.month,
            source_path=url,
            is_fallback=False,
            provider=self.name,
            cache_hit=False,
        )


def nasa_cog_url(
    *,
    variable: str,
    scenario: str,
    year: int,
    month: int,
) -> str:
    filename = (
        f"{variable}_month_ensemble-median_"
        f"{scenario}_{year}{month:02d}.tif"
    )
    return f"{BASE_URL}/{variable}/{filename}"


def normalize_nasa_value(
    value: float,
    variable: str,
) -> tuple[float, str]:
    if variable in {"tasmax", "tasmin", "tas"}:
        return value - 273.15, "degC"
    if variable == "pr":
        return value, "mm_per_month"
    if variable == "hurs":
        return value, "percent"
    if variable == "huss":
        return value, "kg_per_kg"
    if variable == "sfcWind":
        return value, "m_per_s"
    if variable in {"rsds", "rlds"}:
        return value, "W_per_m2"

    return value, "unknown"


def sample_rasterio_source(
    rasterio,
    source: str,
    latitude: float,
    longitude: float,
    *,
    remote: bool,
) -> tuple[float, int, int] | None:
    environment = (
        {
            "GDAL_DISABLE_READDIR_ON_OPEN": "EMPTY_DIR",
            "GDAL_HTTP_CONNECTTIMEOUT": "8",
            "GDAL_HTTP_TIMEOUT": "15",
            "GDAL_HTTP_MAX_RETRY": "1",
            "CPL_VSIL_CURL_ALLOWED_EXTENSIONS": ".tif",
        }
        if remote
        else {}
    )

    try:
        with rasterio.Env(**environment):
            with rasterio.open(source) as dataset:
                if not (
                    dataset.bounds.left <= longitude <= dataset.bounds.right
                    and dataset.bounds.bottom <= latitude <= dataset.bounds.top
                ):
                    return None

                row, column = dataset.index(longitude, latitude)
                raw_value = float(
                    next(
                        dataset.sample(
                            [(longitude, latitude)],
                            indexes=1,
                        ),
                    )[0],
                )
                return raw_value, row, column
    except (OSError, RuntimeError):
        return None


def cache_remote_cog(url: str) -> Path | None:
    destination = REMOTE_COG_CACHE / Path(url).name

    if destination.is_file() and destination.stat().st_size > 0:
        return destination

    temporary = destination.with_suffix(".tif.part")
    destination.parent.mkdir(parents=True, exist_ok=True)

    try:
        request = Request(
            url,
            headers={"User-Agent": "FutureCitiesAI-ClimateProvider/1.0"},
        )

        with urlopen(request, timeout=45) as response:
            temporary.write_bytes(response.read())

        temporary.replace(destination)
        return destination
    except (OSError, TimeoutError, URLError):
        return None
