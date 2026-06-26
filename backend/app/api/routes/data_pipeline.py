from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    ClimateDatasetRecord,
    ClimateFeatureVector,
    FeatureBuildRequest,
)
from app.services.dataset_registry import get_dataset, list_datasets
from app.services.feature_engineering import build_climate_feature_vector


router = APIRouter(prefix="/api", tags=["data-pipeline"])


@router.get("/datasets", response_model=list[ClimateDatasetRecord])
def datasets() -> list[ClimateDatasetRecord]:
    return list_datasets()


@router.get("/datasets/{dataset_key}", response_model=ClimateDatasetRecord)
def dataset_detail(dataset_key: str) -> ClimateDatasetRecord:
    dataset = get_dataset(dataset_key)

    if dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found")

    return dataset


@router.post("/features/build", response_model=ClimateFeatureVector)
def build_features(payload: FeatureBuildRequest) -> ClimateFeatureVector:
    return build_climate_feature_vector(payload)
