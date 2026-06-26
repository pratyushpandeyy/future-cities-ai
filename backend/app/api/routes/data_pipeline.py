from fastapi import APIRouter, HTTPException
from pathlib import Path

from app.models.schemas import (
    ClimateDatasetRecord,
    ClimateFeatureVector,
    ClimateModelStatus,
    ClimateModelTrainingRequest,
    ClimateModelTrainingResponse,
    FeatureBuildRequest,
)
from app.services.dataset_registry import get_dataset, list_datasets
from app.services.feature_engineering import build_climate_feature_vector
from app.services.ml_training import get_model_status, train_climate_adjustment_model


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


@router.get("/model/status", response_model=ClimateModelStatus)
def model_status() -> ClimateModelStatus:
    return get_model_status()


@router.post("/model/train", response_model=ClimateModelTrainingResponse)
def train_model(
    payload: ClimateModelTrainingRequest,
) -> ClimateModelTrainingResponse:
    return train_climate_adjustment_model(
        output_path=Path(payload.output_path) if payload.output_path else None,
        overwrite=payload.overwrite,
    )
