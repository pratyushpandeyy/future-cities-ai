from fastapi import APIRouter, HTTPException
from pathlib import Path

from app.models.schemas import (
    ClimateDatasetRecord,
    ClimateFeatureCacheExportRequest,
    ClimateFeatureCacheExportResponse,
    ClimateFeatureCacheRecord,
    ClimateFeatureCacheStats,
    ClimateFeatureHarvestRequest,
    ClimateFeatureHarvestResponse,
    ClimateFeatureVector,
    ClimateModelStatus,
    ClimateModelTrainingRequest,
    ClimateModelTrainingResponse,
    FeatureBuildRequest,
)
from app.services.dataset_registry import get_dataset, list_datasets
from app.services.feature_cache import (
    cache_feature_vector,
    export_feature_cache_training_dataset,
    feature_cache_stats,
    list_feature_cache_records,
)
from app.services.feature_engineering import build_climate_feature_vector
from app.services.feature_harvesting import harvest_climate_training_features
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
    feature_vector = build_climate_feature_vector(payload)
    cache_feature_vector(
        feature_vector,
        climate_scenario=payload.climate_scenario,
        climate_model=payload.climate_model,
    )
    return feature_vector


@router.get("/features/cache", response_model=list[ClimateFeatureCacheRecord])
def feature_cache(limit: int = 100) -> list[ClimateFeatureCacheRecord]:
    return list_feature_cache_records(limit=limit)


@router.get("/features/cache/stats", response_model=ClimateFeatureCacheStats)
def feature_cache_summary() -> ClimateFeatureCacheStats:
    return feature_cache_stats()


@router.post(
    "/features/cache/export",
    response_model=ClimateFeatureCacheExportResponse,
)
def export_feature_cache(
    payload: ClimateFeatureCacheExportRequest,
) -> ClimateFeatureCacheExportResponse:
    output_path = (
        Path(payload.output_path)
        if payload.output_path
        else Path("data/models/cached_feature_training_dataset_v1.json")
    )
    return ClimateFeatureCacheExportResponse(
        **export_feature_cache_training_dataset(output_path),
    )


@router.post("/features/harvest", response_model=ClimateFeatureHarvestResponse)
def harvest_features(
    payload: ClimateFeatureHarvestRequest,
) -> ClimateFeatureHarvestResponse:
    return harvest_climate_training_features(payload)


@router.get("/model/status", response_model=ClimateModelStatus)
def model_status() -> ClimateModelStatus:
    return get_model_status()


@router.post("/model/train", response_model=ClimateModelTrainingResponse)
def train_model(
    payload: ClimateModelTrainingRequest,
) -> ClimateModelTrainingResponse:
    return train_climate_adjustment_model(
        output_path=Path(payload.output_path) if payload.output_path else None,
        training_data_path=(
            Path(payload.training_data_path) if payload.training_data_path else None
        ),
        overwrite=payload.overwrite,
    )
