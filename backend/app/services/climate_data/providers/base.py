from dataclasses import dataclass
from typing import Protocol

from app.models.schemas import ClimateRasterSample


@dataclass(frozen=True)
class ClimateDataRequest:
    latitude: float
    longitude: float
    year: int
    month: int
    scenario: str
    variable: str
    model: str | None = None
    resolution: str = "2.5m"


class ClimateDataProvider(Protocol):
    name: str

    def sample(
        self,
        request: ClimateDataRequest,
    ) -> ClimateRasterSample | None:
        ...
