import math
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from app.models.schemas import EnvironmentalContext, EnvironmentalSample


BACKEND_ROOT = Path(__file__).resolve().parents[2]
COPERNICUS_DEM_BASE = (
    "https://copernicus-dem-30m.s3.eu-central-1.amazonaws.com"
)
WORLD_COVER_BASE = (
    "https://esa-worldcover.s3.eu-central-1.amazonaws.com/"
    "v200/2021/map"
)
WORLD_COVER_CLASSES = {
    10: "tree_cover",
    20: "shrubland",
    30: "grassland",
    40: "cropland",
    50: "built_up",
    60: "bare_sparse_vegetation",
    70: "snow_ice",
    80: "permanent_water",
    90: "herbaceous_wetland",
    95: "mangroves",
    100: "moss_lichen",
}


@dataclass(frozen=True)
class RasterPointResult:
    value: float
    row: int
    column: int


@lru_cache(maxsize=4096)
def get_environmental_context(
    *,
    latitude: float,
    longitude: float,
) -> EnvironmentalContext:
    elevation = sample_copernicus_elevation(latitude, longitude)
    land_cover = sample_worldcover(latitude, longitude)

    return EnvironmentalContext(
        latitude=latitude,
        longitude=longitude,
        elevation=elevation,
        land_cover=land_cover,
        green_cover_proxy=green_cover_proxy(land_cover),
        built_up_proxy=built_up_proxy(land_cover),
        providers_used=[
            sample.provider
            for sample in (elevation, land_cover)
            if sample is not None
        ],
    )


def get_environmental_context_for_features(
    *,
    latitude: float,
    longitude: float,
) -> EnvironmentalContext:
    if os.getenv("REMOTE_ENVIRONMENTAL_FEATURES_ENABLED", "false").lower() not in {
        "1",
        "true",
        "yes",
    }:
        land_cover = sample_worldcover(latitude, longitude, allow_remote=False)
        return EnvironmentalContext(
            latitude=latitude,
            longitude=longitude,
            land_cover=land_cover,
            green_cover_proxy=green_cover_proxy(land_cover),
            built_up_proxy=built_up_proxy(land_cover),
            providers_used=[land_cover.provider] if land_cover else [],
        )

    return get_environmental_context(
        latitude=latitude,
        longitude=longitude,
    )


def sample_copernicus_elevation(
    latitude: float,
    longitude: float,
) -> EnvironmentalSample | None:
    tile = copernicus_dem_tile(latitude, longitude)
    url = copernicus_dem_url(tile)
    result = sample_remote_raster(url, latitude, longitude)

    if not result:
        return None

    return EnvironmentalSample(
        variable="elevation",
        value=round(result.value, 3),
        unit="meters",
        provider="copernicus_dem_30m",
        source_url=url,
        resolution="30m",
        grid_cell_id=f"cop-dem:{tile}:r{result.row}:c{result.column}",
        confidence="high",
    )


def sample_worldcover(
    latitude: float,
    longitude: float,
    *,
    allow_remote: bool = True,
) -> EnvironmentalSample | None:
    tile = worldcover_tile(latitude, longitude)
    local_path = worldcover_local_path(tile)
    if local_path.exists():
        source = str(local_path)
    elif allow_remote:
        source = worldcover_url(tile)
    else:
        return None

    result = sample_raster_source(source, latitude, longitude)

    if not result:
        return None

    class_code = int(round(result.value))
    class_name = WORLD_COVER_CLASSES.get(class_code, "unknown")

    return EnvironmentalSample(
        variable="land_cover",
        value=float(class_code),
        unit="class_code",
        provider="esa_worldcover_2021",
        source_url=source,
        resolution="10m",
        grid_cell_id=f"worldcover:{tile}:r{result.row}:c{result.column}",
        confidence="high",
        category=class_name,
    )


def sample_remote_raster(
    url: str,
    latitude: float,
    longitude: float,
) -> RasterPointResult | None:
    return sample_raster_source(url, latitude, longitude)


def sample_raster_source(
    source: str,
    latitude: float,
    longitude: float,
) -> RasterPointResult | None:
    try:
        import rasterio
    except ImportError:
        return None

    try:
        if source.startswith(("http://", "https://")):
            env_options = {
                "GDAL_DISABLE_READDIR_ON_OPEN": "EMPTY_DIR",
                "GDAL_HTTP_CONNECTTIMEOUT": "10",
                "GDAL_HTTP_TIMEOUT": "60",
                "GDAL_HTTP_MAX_RETRY": "2",
                "CPL_VSIL_CURL_ALLOWED_EXTENSIONS": ".tif",
            }
        else:
            env_options = {}

        with rasterio.Env(**env_options):
            with rasterio.open(source) as dataset:
                row, column = dataset.index(longitude, latitude)
                value = float(
                    next(
                        dataset.sample(
                            [(longitude, latitude)],
                            indexes=1,
                            masked=True,
                        ),
                    )[0],
                )
    except (OSError, RuntimeError, ValueError):
        return None

    if math.isnan(value):
        return None

    return RasterPointResult(value=value, row=row, column=column)


def copernicus_dem_tile(latitude: float, longitude: float) -> str:
    lat = math.floor(latitude)
    lon = math.floor(longitude)
    return (
        f"{'N' if lat >= 0 else 'S'}{abs(lat):02d}_00_"
        f"{'E' if lon >= 0 else 'W'}{abs(lon):03d}_00"
    )


def copernicus_dem_url(tile: str) -> str:
    directory = f"Copernicus_DSM_COG_10_{tile}_DEM"
    filename = f"Copernicus_DSM_COG_10_{tile}_DEM.tif"
    return f"{COPERNICUS_DEM_BASE}/{directory}/{filename}"


def worldcover_tile(latitude: float, longitude: float) -> str:
    lat = math.floor(latitude / 3) * 3
    lon = math.floor(longitude / 3) * 3
    return (
        f"{'N' if lat >= 0 else 'S'}{abs(lat):02d}"
        f"{'E' if lon >= 0 else 'W'}{abs(lon):03d}"
    )


def worldcover_url(tile: str) -> str:
    filename = f"ESA_WorldCover_10m_2021_v200_{tile}_Map.tif"
    return f"{WORLD_COVER_BASE}/{filename}"


def worldcover_local_path(tile: str) -> Path:
    filename = f"ESA_WorldCover_10m_2021_v200_{tile}_Map.tif"
    return BACKEND_ROOT / "data" / "raw" / "esa_worldcover" / "v200" / "2021" / filename


def green_cover_proxy(
    land_cover: EnvironmentalSample | None,
) -> float | None:
    if not land_cover:
        return None

    return {
        "tree_cover": 1.0,
        "mangroves": 1.0,
        "shrubland": 0.7,
        "grassland": 0.65,
        "cropland": 0.45,
        "herbaceous_wetland": 0.75,
        "moss_lichen": 0.35,
        "built_up": 0.05,
        "bare_sparse_vegetation": 0.08,
        "permanent_water": 0.0,
        "snow_ice": 0.0,
    }.get(land_cover.category or "", 0.3)


def built_up_proxy(
    land_cover: EnvironmentalSample | None,
) -> float | None:
    if not land_cover:
        return None

    return 1.0 if land_cover.category == "built_up" else 0.0
