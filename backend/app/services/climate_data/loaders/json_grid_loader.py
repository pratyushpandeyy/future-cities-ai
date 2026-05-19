import json
from functools import lru_cache
from pathlib import Path
from typing import Any


CLIMATE_DATA_DIR = Path(__file__).resolve().parents[4] / "data" / "climate"


@lru_cache(maxsize=8)
def load_demo_grid(layer_type: str) -> dict[str, Any] | None:
    dataset_by_layer = {
        "heat_stress": "demo_heat_stress_grid.json",
        "temperature_anomaly": "demo_heat_stress_grid.json",
    }
    dataset_name = dataset_by_layer.get(layer_type)

    if not dataset_name:
        return None

    dataset_path = CLIMATE_DATA_DIR / dataset_name

    if not dataset_path.exists():
        return None

    with dataset_path.open("r", encoding="utf-8") as file:
        return json.load(file)
