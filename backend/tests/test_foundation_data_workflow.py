import argparse
import unittest

from scripts.prepare_foundation_data import build_workflow


class FoundationDataWorkflowTests(unittest.TestCase):
    def test_mvp_profile_includes_downloads_and_training_steps(self) -> None:
        steps = build_workflow(
            argparse.Namespace(
                profile="mvp",
                worldclim_models=["MPI-ESM1-2-HR"],
                worldclim_scenarios=["ssp245"],
                worldclim_periods=["2041-2060"],
                worldclim_variables=["tmax"],
                cities=["bengaluru"],
                training_locations=["Whitefield, Bengaluru"],
            ),
        )

        self.assertEqual(
            [step.name for step in steps],
            [
                "worldclim-cmip6-future",
                "worldclim-baseline",
                "worldcover-city-tiles",
                "harvest-ml-features",
                "train-ml-model",
            ],
        )
        self.assertIn("Whitefield, Bengaluru", steps[-2].command)

    def test_ml_only_profile_skips_network_downloads(self) -> None:
        steps = build_workflow(
            argparse.Namespace(
                profile="ml-only",
                worldclim_models=[],
                worldclim_scenarios=[],
                worldclim_periods=[],
                worldclim_variables=[],
                cities=[],
                training_locations=["Mumbai"],
            ),
        )

        self.assertEqual(
            [step.name for step in steps],
            ["harvest-ml-features", "train-ml-model"],
        )
        self.assertFalse(any(step.needs_network for step in steps))


if __name__ == "__main__":
    unittest.main()
