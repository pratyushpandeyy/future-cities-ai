import tempfile
import unittest
from pathlib import Path

from app.services.climate_data.loaders.worldclim_locator import (
    find_worldclim_file,
    period_for_year,
    worldclim_filename,
)
from app.services.climate_data.processors.geotiff_sampler import (
    sample_geotiff_point,
)


class WorldClimLocatorTests(unittest.TestCase):
    def test_maps_year_to_worldclim_period(self) -> None:
        self.assertEqual(period_for_year(2030), "2021-2040")
        self.assertEqual(period_for_year(2050), "2041-2060")
        self.assertEqual(period_for_year(2090), "2081-2100")

    def test_finds_only_completed_tif_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            filename = worldclim_filename(
                resolution="2.5m",
                variable="tmax",
                model="MIROC6",
                scenario="ssp245",
                period="2041-2060",
            )
            path = (
                root
                / "2.5m"
                / "MIROC6"
                / "ssp245"
                / "2041-2060"
                / filename
            )
            path.parent.mkdir(parents=True)
            path.write_bytes(b"completed")

            found = find_worldclim_file(
                year=2050,
                scenario="ssp245",
                variable="tmax",
                model="MPI-ESM1-2-HR",
                data_root=root,
            )

            self.assertIsNotNone(found)
            self.assertEqual(found[0], path)
            self.assertEqual(found[1], "MIROC6")


class GeoTiffSamplerTests(unittest.TestCase):
    def test_samples_requested_month_band(self) -> None:
        try:
            import numpy
            import rasterio
            from rasterio.transform import from_origin
        except ImportError:
            self.skipTest("rasterio and numpy are required for GeoTIFF test")

        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "monthly.tif"
            data = numpy.zeros((12, 2, 2), dtype="float32")
            data[6, :, :] = 315

            with rasterio.open(
                path,
                "w",
                driver="GTiff",
                height=2,
                width=2,
                count=12,
                dtype="float32",
                crs="EPSG:4326",
                transform=from_origin(0, 2, 1, 1),
                nodata=-9999,
            ) as dataset:
                dataset.write(data)

            sample = sample_geotiff_point(
                path,
                latitude=1.5,
                longitude=0.5,
                band=7,
            )

            self.assertIsNotNone(sample)
            self.assertEqual(sample.value, 315)
            self.assertEqual(sample.row, 0)
            self.assertEqual(sample.column, 0)
            self.assertEqual(sample.band, 7)


if __name__ == "__main__":
    unittest.main()
