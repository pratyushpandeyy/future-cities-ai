# Future Cities AI - Learning Log

Use this file after every session. The goal is to keep the project understandable while it grows.

## 2026-06-25 - WorldClim CMIP6 Downloader

### File Recap

- `dataset_registry.py` catalogs datasets and their storage locations.
- `feature_engineering.py` converts available samples into ML-ready features.
- The new downloader populates the raw object/file-storage side of that architecture.

### Added

- Resumable WorldClim CMIP6 downloader CLI.
- URL generation for model/scenario/period/variable combinations.
- Concurrent downloads, retries, `.part` resume files, skip-existing behavior,
  force mode, dry-run, and JSON manifest.
- Git ignore rule for `backend/data/raw/`.
- Two URL/matrix tests.

### Default Download Matrix

```text
3 models x 2 SSPs x 4 periods x 3 variables = 72 GeoTIFF files
```

### Preserved

- No downloads start automatically.
- Existing APIs and scoring behavior are unchanged.
- Raw climate files remain outside Git.

### Verification

```text
python -m unittest backend.tests.test_worldclim_downloader -v
python scripts/download_worldclim_cmip6.py --dry-run
```

## 2026-06-24 - Dataset Registry And Feature Engineering V1

### File Recap

- `models.py` describes persistent SQL tables.
- `schemas.py` describes validated HTTP/service data contracts.
- `main.py` creates FastAPI and registers route modules.
- `seed_boundaries.py` initializes tables and seed metadata.
- `spatial_resolution.py` combines place, boundary, and climate-cell resolution.

### Before

- Climate data availability was implicit in loader code.
- There was no catalog describing providers, formats, variables, coverage, or status.
- The climate engine directly mixed scenario inputs, regional assumptions, and one demo heat sample.
- There was no stable feature contract for training/inference.

### Added

- `ClimateDataset` SQLAlchemy model.
- Built-in dataset catalog with current and planned sources.
- Dataset list/detail endpoints.
- `ClimateFeatureVector` and per-feature provenance schemas.
- Feature engineering service.
- `POST /api/features/build`.
- Five additional registry/feature/API tests.

### New Flow

```text
query + scenario
-> spatial_resolution.py
-> dataset registry
-> feature_engineering.py
-> standardized climate_features_v1 vector
-> upcoming ML model
```

### Spring Boot Mental Model

```text
ClimateDataset              ~= JPA @Entity
ClimateDatasetRecord        ~= response DTO
FeatureBuildRequest         ~= request DTO
feature_engineering.py      ~= @Service
data_pipeline.py            ~= @RestController
BUILTIN_DATASETS            ~= seed/config catalog
```

### Real Versus Fallback

Dataset-backed today:

- demo heat-stress grid
- user scenario inputs

Explicit fallback features today:

- temperature anomaly proxy
- precipitation anomaly proxy
- humidity
- vegetation
- water stress
- urban density
- coastal exposure
- elevation

Each response identifies fallback fields instead of presenting them as observed data.

### Verification

```text
python -m compileall backend/app backend/tests
python -m unittest backend.tests.test_spatial_resolution backend.tests.test_data_pipeline -v
```

All nine tests passed.

## 2026-06-24 - Spatial Resolution V1

### Before

- Search returned a temporary geocoder result.
- Boundary lookup geocoded the same text again.
- Scenario scoring geocoded the same text again.
- There was no database model for searched places.
- Place, boundary, and climate-cell context were returned through separate flows.

### Added

- `Place` SQLAlchemy model.
- `SpatialResolveRequest` and `SpatialResolutionResponse` Pydantic schemas.
- `spatial_resolution.py` orchestration service.
- `POST /api/spatial/resolve`.
- Boundary service support for receiving an already-resolved `LocationResult`.
- Four deterministic service, persistence, and API tests.

### New Flow

```text
query
-> resolve location once
-> optionally persist/update Place
-> resolve boundary using the same LocationResult
-> sample nearest climate cell
-> return one observable spatial context
```

### Preserved

- Existing `/api/search` behavior.
- Existing scenario and comparison APIs.
- Existing frontend behavior.
- Existing database/local GeoJSON/simulated boundary fallback.

### C++ Mental Model

```text
Place SQLAlchemy model       ~= persistent entity struct/class
Pydantic request/response    ~= transport structs with validation
spatial_resolution.py        ~= orchestration/service class
spatial.py route             ~= thin HTTP controller
```

### Tradeoffs

- Place Point geometry is currently stored as GeoJSON JSON, not native PostGIS geometry.
- There is no migration framework yet; the seed script's `Base.metadata.create_all()` creates new tables.
- The endpoint works without a database but reports `place_persisted=false`.
- The climate sample still comes from the ten-cell demo JSON grid.
- Existing frontend/scenario flows do not use `place_id` yet.

### Verification

```text
python -m compileall backend/app backend/tests
python -m unittest backend.tests.test_spatial_resolution -v
```

All four tests passed.

## 2026-05-26 - Project Control Reset

### What We Clarified

- The target product is a real high-granularity GeoAI climate habitability platform, not only a demo.
- Users should be able to search POIs, neighborhoods, localities, cities, and regions.
- The system should eventually compare places inside large cities.
- Real datasets should eventually include climate projections, flood, heat, vegetation, humidity, water stress, urban density, coastal exposure, and boundaries.
- AI should explain computed facts, not invent scores.
- ML should produce quantitative future scores from engineered features.

### What Exists Today

- Next.js frontend.
- FastAPI backend.
- Frontend-backend API integration.
- Mapbox map.
- Real geocoding path when configured.
- PostGIS-ready database foundation.
- Boundary lookup with database/local/simulated fallback.
- Demo raster grid sampling.
- Deterministic climate scoring.
- Climate surface rendering.
- Cell inspection.
- AI explanation.
- Recommendation engine.
- Natural Language Climate Advisor.
- Saved scenarios.
- Timeline playback.
- Composite risk interactions.

### What Is Still Simulated

- Full global boundary coverage.
- Real CMIP6/downscaled climate data.
- Full ML model.
- Full POI-to-ward/neighborhood matching.
- Real flood/vegetation/humidity/water-stress datasets.

### Next Best Step

Start converting the project from prototype-shaped to real-platform-shaped:

1. Add clearer project docs.
2. Add place/POI database model.
3. Add spatial resolution service.
4. Add feature engineering service.
5. Add ML inference interface.

### Session Rule Going Forward

Each 1-hour session should produce:

- one concept understood
- one small build/change
- one manual test
- one learning-log update

## 2026-06-25 - Real WorldClim Point Sampling

### What Changed

- Added a WorldClim file locator that maps a selected year to one of four
  20-year future periods.
- Added a Rasterio processor that samples one latitude/longitude from a
  GeoTIFF.
- Monthly WorldClim files contain 12 bands: January is band 1 and December is
  band 12.
- Added sample metadata for model, SSP scenario, period, month, variable,
  units, source file, and raster row/column.
- Feature engineering can now consume real future `tmax`, `tmin`, and
  precipitation values when completed files exist.
- `.tif.part` files are ignored because they are incomplete downloads.

### Spring Boot Analogy

- `worldclim_locator.py`: repository/storage adapter that locates a resource.
- `geotiff_sampler.py`: low-level data-access component.
- `climate_raster_service.py`: service coordinating real data and fallback.
- `climate.py`: controller/router exposing the HTTP endpoint.

### Important Scientific Distinction

A projected future temperature is not automatically a temperature anomaly.
Calculating an anomaly also requires a historical baseline for the same place
and month. Until that baseline is ingested, anomaly fields remain clearly
labeled formula-derived proxies.

### Verification

- All 14 backend tests pass.
- A real Istanbul July 2050 SSP2-4.5 sample returned:
  - maximum temperature: 30.9 C
  - minimum temperature: 21.2 C
  - precipitation: 23 mm/month

## 2026-06-25 - Feature-to-Model Scoring Contract

### Before

`POST /api/scenario/score` called the deterministic climate engine directly.
The real WorldClim feature vector existed, but scenario scoring did not use it.

### After

```text
scenario request
-> spatial resolution
-> feature engineering
-> deterministic baseline inference
-> regional climate engine
-> scenario response
```

The new `ml_inference.py` module accepts a stable `ClimateFeatureVector` and
returns `ClimateModelPrediction`. It currently uses transparent deterministic
weights. This is intentionally a model interface, not a claim that a trained
ML model already exists.

### Why Both Model and Rules Exist

- Feature/model layer learns or estimates quantitative relationships.
- Regional rules preserve domain behavior and provide a safe fallback.
- Later, a trained model can replace the inference function while the API,
  frontend, and feature contract remain stable.

### Circular Import Lesson

The first implementation imported the complete scoring pipeline at module
startup and created:

```text
boundaries -> simulation -> feature_engineering
-> spatial_resolution -> boundaries
```

Imports were moved inside `score_scenario()` so application modules initialize
first and the scoring pipeline loads only when used.

### Verification

- All 16 backend tests pass.
- A real Istanbul scenario response includes:
  - WorldClim July 2050 SSP2-4.5 raster sample
  - `feature_model_with_formula_fallback`
  - `deterministic_linear_baseline_v1`
  - `climate_features_v1`
  - exact model input names

## 2026-06-25 - Foundation Data Acquisition Toolkit

### Added

- WorldClim 1970-2000 historical climate and elevation downloader.
- ESA WorldCover bbox/city tile downloader.
- GHSL 2020 population and built-surface downloader.
- Shared resumable download utilities and manifests.

### Why Separate Scripts

The datasets have different storage and selection behavior:

- WorldClim baseline is a small set of global ZIP archives.
- WorldCover is enormous globally, so it is selected using 3-degree tiles.
- GHSL is global and several gigabytes, so it requires an explicit large-file
  confirmation flag.

### Verification

- Official URLs returned HTTP 200 on 2026-06-25.
- Six MVP WorldCover tiles were selected for the tested city set.
- All 21 backend tests pass.

## 2026-06-25 - Remote Climate Data Broker

### Architecture

```text
feature engineering
-> climate data broker
-> cache lookup
-> local WorldClim provider
-> remote NASA COG provider
-> cache successful sample
```

The provider interface separates the question "what climate value is needed?"
from "where is that value stored?".

### Why COG Matters

A Cloud Optimized GeoTIFF supports HTTP range requests. Rasterio/GDAL can read
the small byte ranges containing one requested pixel without downloading the
complete climate archive.

### Live Verification

Istanbul, July 2050, SSP2-4.5, maximum temperature:

```text
first request: 30.441 C, provider=nasa_nex_cog, cache_hit=false
second request: 30.441 C, provider=nasa_nex_cog, cache_hit=true
```

All 26 backend tests pass after this change.

## 2026-06-25 - Environmental And Urban Data Providers

### Added

- Copernicus DEM remote 30m elevation sampling.
- ESA WorldCover remote 10m land-cover sampling.
- Overture Maps bbox building and POI service.
- Overture bbox subset download script.
- NASA humidity, wind, solar, longwave, and specific-humidity mappings.

### Performance Decision

Climate sliders must remain responsive. High-resolution remote environmental
queries and extended climate variables are therefore opt-in for automatic
feature generation. They remain directly queryable and can later be
precomputed by background jobs.

### Live Results

- Istanbul: 36.572m elevation, built-up land cover.
- Bengaluru: built-up land cover.
- Overture client: safely reported an upstream release/S3 error.

### Verification

All 29 backend tests pass.
