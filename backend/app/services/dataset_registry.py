from pathlib import Path

from sqlalchemy.exc import SQLAlchemyError

from app.db.models import ClimateDataset
from app.db.session import SessionLocal, is_database_configured
from app.models.schemas import ClimateDatasetRecord


BUILTIN_DATASETS = [
    ClimateDatasetRecord(
        dataset_key="demo_heat_stress_grid_v0",
        name="Future Cities AI demo heat stress grid v0",
        category="heat",
        provider="Future Cities AI",
        storage_uri="backend/data/climate/demo_heat_stress_grid.json",
        data_format="json_grid",
        spatial_resolution="5 degree demo grid",
        temporal_resolution="static",
        variables=["normalized_heat_stress_index"],
        geographic_coverage="selected global sample cells",
        status="available_demo",
        license_name="project_internal",
        attribution="Future Cities AI prototype data",
    ),
    ClimateDatasetRecord(
        dataset_key="nex_gddp_cmip6",
        name="NASA NEX-GDDP-CMIP6",
        category="climate_projection",
        provider="NASA NCCS",
        source_url="https://www.nccs.nasa.gov/data-collections/nex-gddp-cmip6/",
        data_format="netcdf4",
        spatial_resolution="0.25 degree",
        temporal_resolution="daily",
        start_year=1950,
        end_year=2100,
        variables=["tas", "tasmax", "tasmin", "pr", "hurs", "sfcWind"],
        scenarios=["historical", "ssp126", "ssp245", "ssp370", "ssp585"],
        geographic_coverage="global land, 60S to 90N",
        status="available_remote",
        attribution="NASA Earth Exchange Global Daily Downscaled Projections",
    ),
    ClimateDatasetRecord(
        dataset_key="era5_land",
        name="ERA5-Land",
        category="historical_baseline",
        provider="Copernicus Climate Data Store / ECMWF",
        source_url="https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land",
        data_format="grib",
        spatial_resolution="0.1 degree, native 9 km",
        temporal_resolution="hourly",
        start_year=1950,
        variables=[
            "2m_temperature",
            "2m_dewpoint_temperature",
            "total_precipitation",
            "soil_water",
            "surface_solar_radiation",
        ],
        geographic_coverage="global land",
        status="planned_download",
        license_name="CC-BY",
        attribution="Copernicus Climate Change Service / ECMWF",
    ),
    ClimateDatasetRecord(
        dataset_key="worldclim_cmip6",
        name="WorldClim CMIP6 downscaled future climate",
        category="climate_projection",
        provider="WorldClim",
        source_url="https://www.worldclim.org/data/cmip6/cmip6climate.html",
        data_format="geotiff",
        spatial_resolution="10m, 5m, 2.5m, or 30 arc-seconds",
        temporal_resolution="monthly 20-year climatologies",
        start_year=2021,
        end_year=2100,
        variables=["tmin", "tmax", "precipitation"],
        scenarios=["ssp126", "ssp245", "ssp370", "ssp585"],
        geographic_coverage="global land",
        status="recommended_mvp_download",
        attribution="WorldClim v2.1 calibrated CMIP6 projections",
    ),
    ClimateDatasetRecord(
        dataset_key="copernicus_dem",
        name="Copernicus DEM GLO-30",
        category="terrain",
        provider="European Space Agency / Copernicus",
        source_url="https://registry.opendata.aws/copernicus-dem/",
        data_format="cloud_optimized_geotiff",
        spatial_resolution="30 meters",
        temporal_resolution="static",
        variables=["elevation"],
        geographic_coverage="global land",
        status="available_remote",
        attribution="Copernicus DEM GLO-30",
    ),
    ClimateDatasetRecord(
        dataset_key="esa_worldcover",
        name="ESA WorldCover 2021 v200",
        category="land_cover",
        provider="European Space Agency",
        source_url="https://esa-worldcover.org/en/data-access",
        data_format="cloud_optimized_geotiff",
        spatial_resolution="10 meters",
        temporal_resolution="2021 epoch",
        start_year=2021,
        end_year=2021,
        variables=["land_cover_class"],
        geographic_coverage="global",
        status="available_remote",
        attribution="ESA WorldCover project 2021",
    ),
    ClimateDatasetRecord(
        dataset_key="overture_maps",
        name="Overture Maps Foundation data",
        category="places_urban_form",
        provider="Overture Maps Foundation",
        source_url="https://docs.overturemaps.org/getting-data/",
        data_format="cloud_geoparquet",
        spatial_resolution="feature geometry",
        temporal_resolution="release based",
        variables=["places", "buildings", "addresses", "land_use"],
        geographic_coverage="global",
        status="available_remote",
        attribution="Overture Maps Foundation",
    ),
    ClimateDatasetRecord(
        dataset_key="geoboundaries",
        name="geoBoundaries global administrative boundaries",
        category="administrative_boundaries",
        provider="William & Mary geoLab",
        source_url="https://www.geoboundaries.org/",
        data_format="geojson_shapefile",
        spatial_resolution="administrative units",
        temporal_resolution="release based",
        variables=["ADM0", "ADM1", "ADM2", "ADM3", "ADM4"],
        geographic_coverage="global",
        status="recommended_mvp_download",
        license_name="CC BY 4.0",
        attribution="geoBoundaries",
    ),
    ClimateDatasetRecord(
        dataset_key="overture_places_buildings",
        name="Overture Maps places and buildings",
        category="places_urban_form",
        provider="Overture Maps Foundation",
        source_url="https://docs.overturemaps.org/getting-data/",
        data_format="geoparquet",
        spatial_resolution="feature geometry",
        temporal_resolution="release based",
        variables=["places", "buildings", "addresses", "categories"],
        geographic_coverage="global",
        status="recommended_bbox_download",
        attribution="Overture Maps Foundation",
    ),
    ClimateDatasetRecord(
        dataset_key="ghsl_builtup_population",
        name="Global Human Settlement Layer",
        category="urban_density",
        provider="European Commission Joint Research Centre",
        source_url="https://human-settlement.emergency.copernicus.eu/download.php",
        data_format="geotiff_vector",
        spatial_resolution="product dependent",
        temporal_resolution="multi-epoch",
        variables=["built_up_surface", "population_grid", "settlement_model"],
        geographic_coverage="global",
        status="recommended_mvp_download",
        attribution="European Commission, GHSL",
    ),
    ClimateDatasetRecord(
        dataset_key="worldpop_population",
        name="WorldPop population and density",
        category="population_density",
        provider="WorldPop, University of Southampton",
        source_url="https://www.worldpop.org/datacatalog/",
        data_format="geotiff_csv",
        spatial_resolution="product dependent, high-resolution gridded",
        temporal_resolution="annual/product dependent",
        variables=["population_count", "population_density", "future_population"],
        geographic_coverage="global",
        status="optional_download",
        attribution="WorldPop",
    ),
]
WORLDCLIM_RAW_ROOT = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "raw"
    / "worldclim"
    / "cmip6"
)
EXPECTED_MVP_WORLDCLIM_FILES = 72


def list_datasets() -> list[ClimateDatasetRecord]:
    database_records = load_database_datasets()

    if database_records:
        return database_records

    return runtime_builtin_datasets()


def get_dataset(dataset_key: str) -> ClimateDatasetRecord | None:
    normalized_key = dataset_key.strip().lower()

    for dataset in list_datasets():
        if dataset.dataset_key.lower() == normalized_key:
            return dataset

    return None


def available_dataset_keys() -> list[str]:
    return [
        dataset.dataset_key
        for dataset in list_datasets()
        if dataset.status in {
            "available",
            "available_demo",
            "available_remote",
            "partial",
        }
    ]


def runtime_builtin_datasets() -> list[ClimateDatasetRecord]:
    records = [dataset.model_copy(deep=True) for dataset in BUILTIN_DATASETS]
    completed_files = (
        sum(1 for _ in WORLDCLIM_RAW_ROOT.rglob("*.tif"))
        if WORLDCLIM_RAW_ROOT.exists()
        else 0
    )

    for record in records:
        if record.dataset_key != "worldclim_cmip6":
            continue

        record.storage_uri = str(WORLDCLIM_RAW_ROOT)

        if completed_files >= EXPECTED_MVP_WORLDCLIM_FILES:
            record.status = "available"
        elif completed_files:
            record.status = "partial"
        else:
            record.status = "planned_download"

    return records


def sync_builtin_datasets() -> int:
    if not is_database_configured() or SessionLocal is None:
        return 0

    synced = 0

    try:
        with SessionLocal() as session:
            for record in BUILTIN_DATASETS:
                dataset = (
                    session.query(ClimateDataset)
                    .filter(ClimateDataset.dataset_key == record.dataset_key)
                    .one_or_none()
                )

                if dataset is None:
                    dataset = ClimateDataset(dataset_key=record.dataset_key)
                    session.add(dataset)

                update_dataset(dataset, record)
                synced += 1

            session.commit()
    except SQLAlchemyError:
        return 0

    return synced


def load_database_datasets() -> list[ClimateDatasetRecord]:
    if not is_database_configured() or SessionLocal is None:
        return []

    try:
        with SessionLocal() as session:
            datasets = (
                session.query(ClimateDataset)
                .order_by(ClimateDataset.category, ClimateDataset.name)
                .all()
            )

            return [dataset_to_record(dataset) for dataset in datasets]
    except SQLAlchemyError:
        return []


def update_dataset(
    dataset: ClimateDataset,
    record: ClimateDatasetRecord,
) -> None:
    dataset.name = record.name
    dataset.category = record.category
    dataset.provider = record.provider
    dataset.source_url = record.source_url
    dataset.storage_uri = record.storage_uri
    dataset.data_format = record.data_format
    dataset.spatial_resolution = record.spatial_resolution
    dataset.temporal_resolution = record.temporal_resolution
    dataset.start_year = record.start_year
    dataset.end_year = record.end_year
    dataset.variables = record.variables
    dataset.scenarios = record.scenarios
    dataset.geographic_coverage = record.geographic_coverage
    dataset.status = record.status
    dataset.license_name = record.license_name
    dataset.attribution = record.attribution


def dataset_to_record(dataset: ClimateDataset) -> ClimateDatasetRecord:
    return ClimateDatasetRecord(
        id=dataset.id,
        dataset_key=dataset.dataset_key,
        name=dataset.name,
        category=dataset.category,
        provider=dataset.provider,
        source_url=dataset.source_url,
        storage_uri=dataset.storage_uri,
        data_format=dataset.data_format,
        spatial_resolution=dataset.spatial_resolution,
        temporal_resolution=dataset.temporal_resolution,
        start_year=dataset.start_year,
        end_year=dataset.end_year,
        variables=dataset.variables,
        scenarios=dataset.scenarios,
        geographic_coverage=dataset.geographic_coverage,
        status=dataset.status,
        license_name=dataset.license_name,
        attribution=dataset.attribution,
    )
