"""Download a resumable matrix of WorldClim CMIP6 GeoTIFF files.

Example test download:

    python scripts/download_worldclim_cmip6.py \
        --models MPI-ESM1-2-HR \
        --scenarios ssp245 \
        --periods 2041-2060 \
        --variables tmax

Example MVP matrix:

    python scripts/download_worldclim_cmip6.py --confirm
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


BASE_URL = "https://geodata.ucdavis.edu/cmip6"
DEFAULT_MODELS = ["MPI-ESM1-2-HR", "MIROC6", "CNRM-CM6-1"]
DEFAULT_SCENARIOS = ["ssp245", "ssp585"]
DEFAULT_PERIODS = ["2021-2040", "2041-2060", "2061-2080", "2081-2100"]
DEFAULT_VARIABLES = ["tmin", "tmax", "prec"]
SUPPORTED_RESOLUTIONS = {"30s", "2.5m", "5m", "10m"}
SUPPORTED_SCENARIOS = {"ssp126", "ssp245", "ssp370", "ssp585"}
SUPPORTED_PERIODS = set(DEFAULT_PERIODS)
SUPPORTED_VARIABLES = {"tmin", "tmax", "prec", "bioc"}
SCRIPT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = SCRIPT_ROOT / "data" / "raw" / "worldclim" / "cmip6"
USER_AGENT = "FutureCitiesAI-WorldClim-Downloader/1.0"


@dataclass(frozen=True)
class DownloadItem:
    model: str
    scenario: str
    period: str
    variable: str
    resolution: str
    url: str
    destination: Path


@dataclass
class DownloadResult:
    model: str
    scenario: str
    period: str
    variable: str
    resolution: str
    url: str
    destination: str
    status: str
    bytes_downloaded: int = 0
    error: str | None = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Download WorldClim CMIP6 future climate GeoTIFFs with retries, "
            "resume support, concurrency, and a JSON manifest."
        ),
    )
    parser.add_argument("--models", nargs="+", default=DEFAULT_MODELS)
    parser.add_argument("--scenarios", nargs="+", default=DEFAULT_SCENARIOS)
    parser.add_argument("--periods", nargs="+", default=DEFAULT_PERIODS)
    parser.add_argument("--variables", nargs="+", default=DEFAULT_VARIABLES)
    parser.add_argument(
        "--resolution",
        default="2.5m",
        choices=sorted(SUPPORTED_RESOLUTIONS),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
    )
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the download plan without downloading files.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Redownload files that already exist.",
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Required when downloading more than one file.",
    )

    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    invalid_scenarios = set(args.scenarios) - SUPPORTED_SCENARIOS
    invalid_periods = set(args.periods) - SUPPORTED_PERIODS
    invalid_variables = set(args.variables) - SUPPORTED_VARIABLES

    if invalid_scenarios:
        raise ValueError(f"Unsupported scenarios: {sorted(invalid_scenarios)}")
    if invalid_periods:
        raise ValueError(f"Unsupported periods: {sorted(invalid_periods)}")
    if invalid_variables:
        raise ValueError(f"Unsupported variables: {sorted(invalid_variables)}")
    if not args.models:
        raise ValueError("At least one model is required.")
    if args.workers < 1 or args.workers > 8:
        raise ValueError("--workers must be between 1 and 8.")
    if args.retries < 0:
        raise ValueError("--retries cannot be negative.")
    if args.timeout < 10:
        raise ValueError("--timeout must be at least 10 seconds.")


def build_download_plan(
    *,
    models: list[str],
    scenarios: list[str],
    periods: list[str],
    variables: list[str],
    resolution: str,
    output_dir: Path,
) -> list[DownloadItem]:
    plan = []

    for model in models:
        for scenario in scenarios:
            for period in periods:
                for variable in variables:
                    filename = worldclim_filename(
                        model=model,
                        scenario=scenario,
                        period=period,
                        variable=variable,
                        resolution=resolution,
                    )
                    url = (
                        f"{BASE_URL}/{resolution}/{model}/{scenario}/{filename}"
                    )
                    destination = (
                        output_dir
                        / resolution
                        / model
                        / scenario
                        / period
                        / filename
                    )
                    plan.append(
                        DownloadItem(
                            model=model,
                            scenario=scenario,
                            period=period,
                            variable=variable,
                            resolution=resolution,
                            url=url,
                            destination=destination,
                        ),
                    )

    return plan


def worldclim_filename(
    *,
    model: str,
    scenario: str,
    period: str,
    variable: str,
    resolution: str,
) -> str:
    return (
        f"wc2.1_{resolution}_{variable}_{model}_{scenario}_{period}.tif"
    )


def download_item(
    item: DownloadItem,
    *,
    retries: int,
    timeout: int,
    force: bool,
) -> DownloadResult:
    destination = item.destination
    partial_path = destination.with_suffix(f"{destination.suffix}.part")
    destination.parent.mkdir(parents=True, exist_ok=True)

    if destination.exists() and destination.stat().st_size > 0 and not force:
        return result_for(
            item,
            status="skipped_existing",
            bytes_downloaded=destination.stat().st_size,
        )

    if force:
        destination.unlink(missing_ok=True)
        partial_path.unlink(missing_ok=True)

    for attempt in range(retries + 1):
        try:
            downloaded_bytes = download_with_resume(
                item.url,
                partial_path,
                timeout=timeout,
            )
            os.replace(partial_path, destination)

            return result_for(
                item,
                status="downloaded",
                bytes_downloaded=downloaded_bytes,
            )
        except HTTPError as exc:
            if exc.code == 416 and partial_path.exists():
                os.replace(partial_path, destination)
                return result_for(
                    item,
                    status="downloaded",
                    bytes_downloaded=destination.stat().st_size,
                )
            error = f"HTTP {exc.code}: {exc.reason}"
        except (URLError, TimeoutError, OSError) as exc:
            error = str(exc)

        if attempt < retries:
            time.sleep(min(2**attempt, 8))

    return result_for(item, status="failed", error=error)


def download_with_resume(url: str, partial_path: Path, *, timeout: int) -> int:
    existing_bytes = partial_path.stat().st_size if partial_path.exists() else 0
    headers = {"User-Agent": USER_AGENT}

    if existing_bytes:
        headers["Range"] = f"bytes={existing_bytes}-"

    request = Request(url, headers=headers)

    with urlopen(request, timeout=timeout) as response:
        response_status = getattr(response, "status", 200)
        append = existing_bytes > 0 and response_status == 206
        mode = "ab" if append else "wb"

        if existing_bytes and not append:
            existing_bytes = 0

        with partial_path.open(mode) as output:
            shutil.copyfileobj(response, output, length=1024 * 1024)

    return partial_path.stat().st_size


def result_for(
    item: DownloadItem,
    *,
    status: str,
    bytes_downloaded: int = 0,
    error: str | None = None,
) -> DownloadResult:
    return DownloadResult(
        model=item.model,
        scenario=item.scenario,
        period=item.period,
        variable=item.variable,
        resolution=item.resolution,
        url=item.url,
        destination=str(item.destination),
        status=status,
        bytes_downloaded=bytes_downloaded,
        error=error,
    )


def print_plan(plan: list[DownloadItem]) -> None:
    print(f"Planned files: {len(plan)}")

    for item in plan:
        print(
            f"- {item.model} / {item.scenario} / {item.period} / "
            f"{item.variable} -> {item.destination}"
        )


def write_manifest(
    output_dir: Path,
    *,
    plan: list[DownloadItem],
    results: list[DownloadResult],
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "download_manifest.json"
    manifest = {
        "generated_at": datetime.now(UTC).isoformat(),
        "source": "WorldClim CMIP6",
        "base_url": BASE_URL,
        "planned_file_count": len(plan),
        "result_counts": status_counts(results),
        "results": [asdict(result) for result in results],
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )

    return manifest_path


def status_counts(results: list[DownloadResult]) -> dict[str, int]:
    counts: dict[str, int] = {}

    for result in results:
        counts[result.status] = counts.get(result.status, 0) + 1

    return counts


def human_size(byte_count: int) -> str:
    size = float(byte_count)

    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024 or unit == "TB":
            return f"{size:.1f} {unit}"
        size /= 1024

    return f"{size:.1f} TB"


def main() -> int:
    args = parse_args()

    try:
        validate_args(args)
    except ValueError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2

    plan = build_download_plan(
        models=args.models,
        scenarios=args.scenarios,
        periods=args.periods,
        variables=args.variables,
        resolution=args.resolution,
        output_dir=args.output_dir.resolve(),
    )
    print_plan(plan)

    if args.dry_run:
        print("Dry run complete. No files were downloaded.")
        return 0

    if len(plan) > 1 and not args.confirm:
        print(
            "\nRefusing a multi-file download without --confirm. "
            "Run with --dry-run first, then add --confirm.",
            file=sys.stderr,
        )
        return 2

    results = []

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        future_to_item = {
            executor.submit(
                download_item,
                item,
                retries=args.retries,
                timeout=args.timeout,
                force=args.force,
            ): item
            for item in plan
        }

        for completed_count, future in enumerate(
            as_completed(future_to_item),
            start=1,
        ):
            result = future.result()
            results.append(result)
            detail = (
                human_size(result.bytes_downloaded)
                if result.bytes_downloaded
                else result.error or ""
            )
            print(
                f"[{completed_count}/{len(plan)}] {result.status}: "
                f"{result.model}/{result.scenario}/{result.period}/"
                f"{result.variable} {detail}"
            )

    manifest_path = write_manifest(
        args.output_dir.resolve(),
        plan=plan,
        results=results,
    )
    counts = status_counts(results)
    print(f"Manifest: {manifest_path}")
    print(f"Summary: {counts}")

    return 1 if counts.get("failed", 0) else 0


if __name__ == "__main__":
    raise SystemExit(main())
