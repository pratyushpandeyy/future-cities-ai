from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class GeoTiffPointSample:
    value: float
    row: int
    column: int
    band: int
    crs: str
    nodata: float | None


def sample_geotiff_point(
    path: Path,
    *,
    latitude: float,
    longitude: float,
    band: int,
) -> GeoTiffPointSample | None:
    try:
        import rasterio
        from rasterio.warp import transform
    except ImportError:
        return None

    with rasterio.open(path) as dataset:
        if band < 1 or band > dataset.count:
            raise ValueError(
                f"Band {band} is outside this raster's 1-{dataset.count} range",
            )

        x, y = longitude, latitude

        if dataset.crs and dataset.crs.to_string() != "EPSG:4326":
            transformed_x, transformed_y = transform(
                "EPSG:4326",
                dataset.crs,
                [longitude],
                [latitude],
            )
            x, y = transformed_x[0], transformed_y[0]

        if not (
            dataset.bounds.left <= x <= dataset.bounds.right
            and dataset.bounds.bottom <= y <= dataset.bounds.top
        ):
            return None

        row, column = dataset.index(x, y)
        sampled = next(
            dataset.sample([(x, y)], indexes=band, masked=True),
        )[0]

        if getattr(sampled, "mask", False):
            return None

        value = float(sampled)

        if dataset.nodata is not None and value == float(dataset.nodata):
            return None

        return GeoTiffPointSample(
            value=value,
            row=row,
            column=column,
            band=band,
            crs=dataset.crs.to_string() if dataset.crs else "unknown",
            nodata=float(dataset.nodata) if dataset.nodata is not None else None,
        )
