"""Shared resumable download helpers for large scientific datasets."""

from __future__ import annotations

import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


USER_AGENT = "FutureCitiesAI-DataDownloader/1.0"


@dataclass(frozen=True)
class DownloadItem:
    dataset: str
    key: str
    url: str
    destination: Path
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass
class DownloadResult:
    dataset: str
    key: str
    url: str
    destination: str
    status: str
    bytes_downloaded: int = 0
    error: str | None = None
    metadata: dict[str, object] = field(default_factory=dict)


def run_downloads(
    items: list[DownloadItem],
    *,
    workers: int,
    retries: int,
    timeout: int,
    force: bool,
) -> list[DownloadResult]:
    results = []

    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_item = {
            executor.submit(
                download_item,
                item,
                retries=retries,
                timeout=timeout,
                force=force,
            ): item
            for item in items
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
                f"[{completed_count}/{len(items)}] {result.status}: "
                f"{result.key} {detail}",
                flush=True,
            )

    return results


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

    error = "Unknown download error"

    for attempt in range(retries + 1):
        try:
            downloaded_bytes = download_with_resume(
                item.url,
                partial_path,
                timeout=timeout,
                label=item.key,
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
            delay = min(2**attempt, 30)
            print(
                f"Retrying {item.key} in {delay}s "
                f"({attempt + 1}/{retries})...",
                flush=True,
            )
            time.sleep(delay)

    return result_for(item, status="failed", error=error)


def download_with_resume(
    url: str,
    partial_path: Path,
    *,
    timeout: int,
    label: str,
) -> int:
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
            last_reported_bytes = existing_bytes
            last_reported_at = time.monotonic()

            while chunk := response.read(1024 * 1024):
                output.write(chunk)
                current_bytes = output.tell()
                now = time.monotonic()

                if (
                    current_bytes - last_reported_bytes >= 64 * 1024 * 1024
                    or now - last_reported_at >= 30
                ):
                    print(
                        f"Downloading {label}: {human_size(current_bytes)}",
                        flush=True,
                    )
                    last_reported_bytes = current_bytes
                    last_reported_at = now

    return partial_path.stat().st_size


def result_for(
    item: DownloadItem,
    *,
    status: str,
    bytes_downloaded: int = 0,
    error: str | None = None,
) -> DownloadResult:
    return DownloadResult(
        dataset=item.dataset,
        key=item.key,
        url=item.url,
        destination=str(item.destination),
        status=status,
        bytes_downloaded=bytes_downloaded,
        error=error,
        metadata=item.metadata,
    )


def write_manifest(
    output_dir: Path,
    *,
    source: str,
    items: list[DownloadItem],
    results: list[DownloadResult],
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "download_manifest.json"
    manifest = {
        "generated_at": datetime.now(UTC).isoformat(),
        "source": source,
        "planned_file_count": len(items),
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


def print_plan(items: list[DownloadItem]) -> None:
    print(f"Planned files: {len(items)}")

    for item in items:
        print(f"- {item.key}: {item.url}")
        print(f"  -> {item.destination}")


def human_size(byte_count: int) -> str:
    size = float(byte_count)

    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024 or unit == "TB":
            return f"{size:.1f} {unit}"
        size /= 1024

    return f"{size:.1f} TB"
