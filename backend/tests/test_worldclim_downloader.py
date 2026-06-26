import tempfile
import unittest
from pathlib import Path

from scripts.download_worldclim_cmip6 import (
    build_download_plan,
    worldclim_filename,
)


class WorldClimDownloaderTests(unittest.TestCase):
    def test_builds_official_worldclim_filename(self) -> None:
        filename = worldclim_filename(
            model="MPI-ESM1-2-HR",
            scenario="ssp245",
            period="2041-2060",
            variable="tmax",
            resolution="2.5m",
        )

        self.assertEqual(
            filename,
            "wc2.1_2.5m_tmax_MPI-ESM1-2-HR_ssp245_2041-2060.tif",
        )

    def test_builds_expected_matrix_and_directory_layout(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            plan = build_download_plan(
                models=["MPI-ESM1-2-HR"],
                scenarios=["ssp245", "ssp585"],
                periods=["2021-2040", "2041-2060"],
                variables=["tmin", "tmax", "prec"],
                resolution="2.5m",
                output_dir=Path(directory),
            )

        self.assertEqual(len(plan), 12)
        self.assertEqual(
            plan[0].url,
            (
                "https://geodata.ucdavis.edu/cmip6/2.5m/"
                "MPI-ESM1-2-HR/ssp245/"
                "wc2.1_2.5m_tmin_MPI-ESM1-2-HR_ssp245_2021-2040.tif"
            ),
        )
        self.assertEqual(
            plan[-1].destination.name,
            "wc2.1_2.5m_prec_MPI-ESM1-2-HR_ssp585_2041-2060.tif",
        )


if __name__ == "__main__":
    unittest.main()
