from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_WORLDCLIM_ROOT = (
    BACKEND_ROOT / "data" / "raw" / "worldclim" / "cmip6"
)
SUPPORTED_PERIODS = (
    (2021, 2040, "2021-2040"),
    (2041, 2060, "2041-2060"),
    (2061, 2080, "2061-2080"),
    (2081, 2100, "2081-2100"),
)
PREFERRED_MODELS = ("MPI-ESM1-2-HR", "MIROC6", "CNRM-CM6-1")


def period_for_year(year: int) -> str:
    for start_year, end_year, period in SUPPORTED_PERIODS:
        if start_year <= year <= end_year:
            return period

    raise ValueError("WorldClim future data supports years from 2021 to 2100")


def worldclim_filename(
    *,
    resolution: str,
    variable: str,
    model: str,
    scenario: str,
    period: str,
) -> str:
    return (
        f"wc2.1_{resolution}_{variable}_{model}_{scenario}_{period}.tif"
    )


def find_worldclim_file(
    *,
    year: int,
    scenario: str,
    variable: str,
    model: str | None = None,
    resolution: str = "2.5m",
    data_root: Path = DEFAULT_WORLDCLIM_ROOT,
) -> tuple[Path, str, str] | None:
    period = period_for_year(year)
    models = ordered_models(model)

    for candidate_model in models:
        filename = worldclim_filename(
            resolution=resolution,
            variable=variable,
            model=candidate_model,
            scenario=scenario,
            period=period,
        )
        path = (
            data_root
            / resolution
            / candidate_model
            / scenario
            / period
            / filename
        )

        if path.is_file() and path.stat().st_size > 0:
            return path, candidate_model, period

    return None


def ordered_models(requested_model: str | None) -> tuple[str, ...]:
    if not requested_model:
        return PREFERRED_MODELS

    return (
        requested_model,
        *(model for model in PREFERRED_MODELS if model != requested_model),
    )
