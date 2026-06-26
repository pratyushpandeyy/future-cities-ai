import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.models.schemas import ClimateRasterSample
from app.services.climate_data.climate_data_broker import (
    ClimateDataBroker,
    climate_data_broker_status,
)
from app.services.climate_data.providers.base import ClimateDataRequest
from app.services.climate_data.providers.nasa_nex_cog import (
    nasa_cog_url,
    normalize_nasa_value,
)
from app.services.climate_data.sample_cache import ClimateSampleCache


REQUEST = ClimateDataRequest(
    latitude=41.0082,
    longitude=28.9784,
    year=2050,
    month=7,
    scenario="ssp245",
    variable="tmax",
)


class FakeProvider:
    name = "fake"
    calls = 0

    def sample(self, request: ClimateDataRequest) -> ClimateRasterSample:
        self.__class__.calls += 1
        return ClimateRasterSample(
            sampled_value=31.5,
            grid_cell_id="fake-cell",
            raster_source="fake",
            dataset_name="Fake climate source",
            dataset_resolution="test",
            layer_type=request.variable,
            unit="degC",
            variable=request.variable,
        )


class ClimateDataBrokerTests(unittest.TestCase):
    def setUp(self) -> None:
        FakeProvider.calls = 0

    def test_uses_provider_then_persistent_cache(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            cache = ClimateSampleCache(Path(directory))

            with patch.dict(
                "app.services.climate_data.climate_data_broker.PROVIDERS",
                {"fake": FakeProvider},
                clear=True,
            ):
                broker = ClimateDataBroker(
                    provider_order=("fake",),
                    cache=cache,
                )
                first = broker.sample(REQUEST, allow_demo_fallback=False)
                second = broker.sample(REQUEST, allow_demo_fallback=False)

        self.assertEqual(FakeProvider.calls, 1)
        self.assertFalse(first.cache_hit)
        self.assertTrue(second.cache_hit)
        self.assertEqual(second.provider, "fake")

    def test_provider_order_is_part_of_cache_identity(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            cache = ClimateSampleCache(Path(directory))
            first_path = cache.path_for(REQUEST, scope="local_worldclim")
            second_path = cache.path_for(REQUEST, scope="nasa_nex_cog")

        self.assertNotEqual(first_path, second_path)

    def test_status_exposes_local_and_remote_providers(self) -> None:
        status = climate_data_broker_status()
        provider_names = {provider.name for provider in status.providers}

        self.assertIn("local_worldclim", provider_names)
        self.assertIn("nasa_nex_cog", provider_names)


class NasaNexCogTests(unittest.TestCase):
    def test_builds_verified_public_monthly_cog_url(self) -> None:
        self.assertEqual(
            nasa_cog_url(
                variable="tasmax",
                scenario="ssp245",
                year=2050,
                month=7,
            ),
            (
                "https://nex-gddp-cmip6-cog.s3.us-west-2.amazonaws.com/"
                "monthly/CMIP6_ensemble_median/tasmax/"
                "tasmax_month_ensemble-median_ssp245_205007.tif"
            ),
        )

    def test_converts_kelvin_to_celsius(self) -> None:
        value, unit = normalize_nasa_value(303.59, "tasmax")

        self.assertAlmostEqual(value, 30.44, places=2)
        self.assertEqual(unit, "degC")


if __name__ == "__main__":
    unittest.main()
