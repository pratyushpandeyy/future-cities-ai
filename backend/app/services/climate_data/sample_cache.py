import hashlib
import json
from pathlib import Path

from app.models.schemas import ClimateRasterSample
from app.services.climate_data.providers.base import ClimateDataRequest


BACKEND_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CACHE_DIR = BACKEND_ROOT / "data" / "cache" / "climate_samples"
CACHE_VERSION = "v1"


class ClimateSampleCache:
    def __init__(self, cache_dir: Path = DEFAULT_CACHE_DIR) -> None:
        self.cache_dir = cache_dir

    def get(
        self,
        request: ClimateDataRequest,
        *,
        scope: str = "default",
    ) -> ClimateRasterSample | None:
        path = self.path_for(request, scope=scope)

        if not path.is_file():
            return None

        try:
            sample = ClimateRasterSample.model_validate_json(
                path.read_text(encoding="utf-8"),
            )
        except (OSError, ValueError):
            return None

        return sample.model_copy(update={"cache_hit": True})

    def put(
        self,
        request: ClimateDataRequest,
        sample: ClimateRasterSample,
        *,
        scope: str = "default",
    ) -> None:
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        path = self.path_for(request, scope=scope)
        temporary_path = path.with_suffix(".tmp")
        temporary_path.write_text(
            sample.model_dump_json(indent=2),
            encoding="utf-8",
        )
        temporary_path.replace(path)

    def path_for(
        self,
        request: ClimateDataRequest,
        *,
        scope: str = "default",
    ) -> Path:
        payload = {
            "version": CACHE_VERSION,
            "scope": scope,
            "latitude": round(request.latitude, 5),
            "longitude": round(request.longitude, 5),
            "year": request.year,
            "month": request.month,
            "scenario": request.scenario,
            "variable": request.variable,
            "model": request.model,
            "resolution": request.resolution,
        }
        digest = hashlib.sha256(
            json.dumps(payload, sort_keys=True).encode("utf-8"),
        ).hexdigest()
        return self.cache_dir / f"{digest}.json"
