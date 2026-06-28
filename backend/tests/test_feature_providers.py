import unittest

from app.services.providers.feature_provider import FeaturePackage, FeatureValue
from app.services.providers.socioeconomic_provider import SocioeconomicProvider


class FeatureProviderTests(unittest.TestCase):
    def test_feature_value_converts_to_engineered_feature(self) -> None:
        value = FeatureValue(
            name="future_monthly_tmax_c",
            value=31.5,
            unit="degC",
            dataset="worldclim_cmip6",
            provider="local_worldclim",
            retrieval_mode="local_raster",
            confidence="high",
            fallback=False,
            raw_source="MPI-ESM1-2-HR / ssp245",
        )

        engineered = value.to_engineered_feature()

        self.assertEqual(engineered.value, 31.5)
        self.assertEqual(engineered.dataset_key, "worldclim_cmip6")
        self.assertFalse(engineered.is_fallback)
        self.assertIn("local_worldclim", engineered.source)

    def test_feature_package_merges_provider_groups(self) -> None:
        climate = FeatureValue(
            name="heatwave_proxy_index",
            value=0.7,
            unit="normalized_0_1",
            dataset="worldclim_cmip6",
            provider="local_worldclim",
            retrieval_mode="local_raster",
            confidence="medium",
            fallback=False,
        )
        environment = FeatureValue(
            name="vegetation_index",
            value=0.3,
            unit="normalized_0_1",
            dataset="esa_worldcover",
            provider="esa_worldcover_2021",
            retrieval_mode="land_cover_proxy",
            confidence="medium",
            fallback=False,
        )

        package = FeaturePackage(
            climate={climate.name: climate},
            environment={environment.name: environment},
        )

        self.assertEqual(
            set(package.by_name()),
            {"heatwave_proxy_index", "vegetation_index"},
        )

    def test_socioeconomic_provider_uses_worldcover_built_up_signal(self) -> None:
        built_up = FeatureValue(
            name="built_up_proxy",
            value=1.0,
            unit="binary_0_1",
            dataset="esa_worldcover",
            provider="esa_worldcover_2021",
            retrieval_mode="land_cover_proxy",
            confidence="medium",
            fallback=False,
        )

        features = SocioeconomicProvider().get_features(
            place_type="neighborhood",
            city="Bengaluru",
            built_up_proxy=built_up,
        )

        self.assertGreaterEqual(features["urban_density_index"].value, 0.85)
        self.assertFalse(features["urban_density_index"].fallback)
        self.assertTrue(features["population_density_index"].fallback)


if __name__ == "__main__":
    unittest.main()

