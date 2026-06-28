# Future Cities AI - Current Project State

Last updated: 2026-05-26

This file is the restart context for Future Cities AI. If a chat session dies or context is lost, start here before changing code.

## North Star

Future Cities AI is intended to become a high-granularity GeoAI climate habitability platform.

The target user flow is:

```text
User enters a place, future year, warming scenario, and personal constraints
-> system geocodes the place
-> system resolves the place to POI/locality/admin boundary/climate grid cells
-> system fetches climate and urban datasets
-> feature engineering builds a model-ready vector
-> ML predicts future habitability/risk scores
-> AI explains the quantitative results in human language
-> frontend visualizes maps, overlays, timelines, comparisons, and recommendations
```

The long-term product should support high-granularity comparison inside large cities, such as Whitefield vs Koramangala, Bandra vs Powai, or neighborhoods/POIs within Varanasi.

## Current Architecture

The repo is a monorepo:

```text
future-cities-ai/
  frontend/   Next.js, TypeScript, Tailwind, Mapbox GL
  backend/    FastAPI, Pydantic, SQLAlchemy/PostGIS-ready services
  docs/       project memory and architecture notes
```

The app currently runs as two servers:

```text
Frontend: http://localhost:3000
Backend:  http://127.0.0.1:8000
```

Frontend API calls use:

```text
frontend/lib/api/mockClient.ts
```

Despite the name `mockClient`, it now calls the FastAPI backend over HTTP.

## What Is Real Today

These parts are real code paths, not just static UI:

- FastAPI backend with multiple route modules.
- Frontend-to-backend HTTP integration through `fetch()`.
- Mapbox map integration in the frontend.
- Real geocoding service layer using backend-held provider keys when configured.
- PostGIS-ready SQLAlchemy database foundation.
- Administrative boundary model and seed/local GeoJSON lookup.
- Database/local/simulated boundary fallback order.
- Hierarchical boundary resolution: locality/POI -> district -> city -> region -> country.
- Generic GeoJSON boundary importer for geoBoundaries/GADM/OSM/Overture-style files.
- Optional online OSM/Nominatim polygon fallback that caches successful boundaries into PostGIS.
- Climate raster sampling interface using a small demo grid.
- Climate surface API returning grid-like GeoJSON cells for map rendering.
- Climate cell inspection endpoint.
- Scenario scoring endpoint.
- Comparison endpoint.
- AI explanation endpoint with template fallback and optional LLM path.
- Saved scenarios model/service/routes.
- Timeline playback endpoint and frontend controls.
- Climate interaction engine.
- Personalized recommendation engine.
- Natural Language Climate Advisor endpoint and frontend panel.

## What Is Still Simulated Or Prototype-Level

These parts are intentionally not yet production-grade:

- Global boundary coverage.
- Full POI-to-locality/ward/grid-cell spatial resolution.
- Real CMIP6/downscaled climate ingestion.
- Real flood depth/probability datasets.
- Real vegetation/NDVI datasets.
- Real humidity/wet-bulb datasets.
- Real water stress datasets.
- Real urban density / built-up area datasets.
- Trained ML model for habitability scoring.
- Scientific uncertainty modeling.
- Production vector tile or raster tile serving.
- User accounts and authentication.
- Production data refresh/versioning.

Current climate scores are deterministic and model-shaped, but still mostly formula-driven with demo raster blending.

## Backend Routes Added So Far

Main route registration:

```text
backend/app/main.py
```

Important route files:

```text
backend/app/api/routes/health.py
backend/app/api/routes/search.py
backend/app/api/routes/region.py
backend/app/api/routes/scenario.py
backend/app/api/routes/climate.py
backend/app/api/routes/explain.py
backend/app/api/routes/recommendations.py
backend/app/api/routes/saved_scenarios.py
backend/app/api/routes/advisor.py
backend/app/api/routes/admin.py
```

Important endpoints:

```text
GET  /health
GET  /api/search
POST /api/spatial/resolve
GET  /api/datasets
GET  /api/datasets/{dataset_key}
POST /api/features/build
GET  /api/region-boundary
POST /api/scenario/score
POST /api/scenario/compare
GET  /api/climate/raster-sample
GET  /api/climate/surface
GET  /api/climate/cell-detail
GET  /api/climate/timeline
POST /api/climate/composite-risk
POST /api/explain
POST /api/recommendations
POST /api/advisor/query
POST /api/scenarios/save
GET  /api/scenarios
GET  /api/scenarios/{id}
DELETE /api/scenarios/{id}
GET  /api/admin/boundaries
GET  /api/admin/boundaries/{id}
```

## Backend Services Added So Far

Core services:

```text
backend/app/services/geocoding.py
backend/app/services/simulation.py
backend/app/services/boundaries.py
backend/app/services/boundary_resolution.py
backend/app/services/online_boundaries.py
backend/app/services/climate_engine.py
backend/app/services/ai_explanation.py
backend/app/services/recommendation_engine.py
backend/app/services/advisor_parser.py
backend/app/services/advisor_engine.py
backend/app/services/saved_scenarios.py
backend/app/services/climate_timeline.py
backend/app/services/climate_interaction_engine.py
```

Climate data services:

```text
backend/app/services/climate_data/climate_raster_service.py
backend/app/services/climate_data/climate_surface_service.py
backend/app/services/climate_data/loaders/json_grid_loader.py
backend/app/services/climate_data/processors/grid_sampler.py
```

Database files:

```text
backend/app/db/config.py
backend/app/db/session.py
backend/app/db/models.py
backend/scripts/seed_boundaries.py
backend/scripts/import_boundaries.py
backend/scripts/download_geoboundaries.py
```

## Spatial Resolution V1

Added on 2026-06-24:

```text
backend/app/services/spatial_resolution.py
backend/app/api/routes/spatial.py
backend/tests/test_spatial_resolution.py
```

The `Place` database model stores normalized geocoder results, coordinates,
hierarchy metadata, provider metadata, bounding boxes, and Point GeoJSON.

`POST /api/spatial/resolve` accepts:

```json
{
  "query": "Whitefield"
}
```

It combines:

```text
location geocoding
+ optional Place persistence
+ boundary resolution
+ nearest demo climate grid sample
+ confidence/fallback metadata
```

This endpoint is additive. Existing search, scenario, comparison, and frontend
flows are preserved. It is the foundation for later migrating those flows from
repeated text geocoding to stable `place_id` references.

Current limitation: the Place point is stored as GeoJSON rather than a native
PostGIS geometry column. Native spatial columns/indexes are a planned upgrade.

## Dataset Registry And Feature Engineering V1

Added on 2026-06-24:

```text
backend/app/services/dataset_registry.py
backend/app/services/feature_engineering.py
backend/app/api/routes/data_pipeline.py
backend/tests/test_data_pipeline.py
docs/DATA_SOURCES_AND_STORAGE.md
```

The `ClimateDataset` database model catalogs dataset metadata and storage URIs.
Large raster/NetCDF/GeoParquet files are intentionally not stored inside ordinary
database rows.

`POST /api/features/build` converts:

```text
spatial resolution
+ scenario year/warming/season
+ available climate sample
+ explicit regional fallbacks
```

into `climate_features_v1`, a stable numeric contract for the upcoming ML model.
Each feature records source, unit, dataset key, confidence, and whether it is a
fallback.

## Frontend Files To Know

Main map state and orchestration:

```text
frontend/app/map/page.tsx
```

Backend API client:

```text
frontend/lib/api/mockClient.ts
```

Mapbox rendering:

```text
frontend/components/MapboxView.tsx
```

Right-side intelligence panel:

```text
frontend/components/IntelligencePanel.tsx
```

Top controls:

```text
frontend/components/SearchScenarioBar.tsx
```

Overlay simulation/types:

```text
frontend/lib/climateOverlaySimulation.ts
```

## Important Current Product Flows

### Search Flow

```text
SearchScenarioBar
-> frontend/app/map/page.tsx searchRegion()
-> frontend/lib/api/mockClient.ts searchLocation()
-> GET /api/search
-> backend geocoding/simulation service
-> selectedCity + regionalMapping update
-> map flies to location
-> region boundary request starts
```

### Boundary Flow

```text
regionalMapping changes
-> getRegionBoundary()
-> GET /api/region-boundary
-> boundary service builds geocoder hierarchy
-> boundary service checks database from specific to broad
-> fallback to local GeoJSON
-> fallback to online OSM/Nominatim polygon lookup and DB cache
-> fallback to simulated polygon
-> MapboxView renders boundary/overlay
```

### Scenario Score Flow

```text
location/year/warming/season/layers change
-> getScenarioScore()
-> POST /api/scenario/score
-> spatial_resolution resolves the place and climate context once
-> feature_engineering builds the stable climate_features_v1 vector
-> ml_inference calculates deterministic baseline adjustments
-> climate_engine blends model adjustments with regional rules
-> real WorldClim raster metadata is returned when available
-> frontend panel updates
```

Current model boundary:

- `backend/app/services/ml_inference.py`
- model version: `deterministic_linear_baseline_v1`
- model type: deterministic weighted baseline, not a trained production model
- replacement path: preserve `ClimateFeatureVector` and
  `ClimateModelPrediction`, then replace the inference implementation with a
  serialized trained model

Scenario responses now report:

- scoring source
- model version and confidence
- feature schema version
- model input names
- sampled raster metadata

### Remote Climate Data Broker

The climate feature pipeline no longer directly depends on local WorldClim
files. It requests values through:

```text
ClimateDataBroker
-> local WorldClim provider
-> NASA NEX-GDDP-CMIP6 remote COG provider
-> disk sample cache
-> optional demo fallback
```

Important files:

- `backend/app/services/climate_data/climate_data_broker.py`
- `backend/app/services/climate_data/providers/base.py`
- `backend/app/services/climate_data/providers/local_worldclim.py`
- `backend/app/services/climate_data/providers/nasa_nex_cog.py`
- `backend/app/services/climate_data/sample_cache.py`

The NASA provider reads public monthly global Cloud Optimized GeoTIFFs by HTTP
range request. It does not download and store the entire source collection.

### Environmental And Urban Context

Added:

- Copernicus DEM 30m remote elevation sampling
- ESA WorldCover 10m remote land-cover sampling
- Overture Maps building/POI bbox access
- Overture bbox subset download script
- optional extended NASA humidity, wind, and radiation variables

The environmental feature integration is disabled by default because remote
10m/30m raster latency can be noticeable during interactive slider changes.
It can be enabled with:

```text
REMOTE_ENVIRONMENTAL_FEATURES_ENABLED=true
EXTENDED_CLIMATE_FEATURES_ENABLED=true
OVERTURE_ENABLED=true
```

Verified live on 2026-06-25:

- Istanbul elevation: 36.572 meters from Copernicus DEM
- Istanbul land cover: built-up from ESA WorldCover
- Bengaluru land cover: built-up from ESA WorldCover

Overture access is implemented, but its public release query returned an
upstream S3/STAC error during verification. The service reports
`available=false` rather than blocking or crashing the application.

### Climate Surface Flow

```text
MapboxView sees active overlay + boundary
-> getClimateSurface()
-> GET /api/climate/surface
-> backend samples demo raster grid into surface cells
-> frontend renders Mapbox GeoJSON fill layer
```

### WorldClim GeoTIFF Sampling Flow

```text
lat/lon + year + scenario + month + variable
-> GET /api/climate/raster-sample
-> worldclim_locator maps the year to a 20-year WorldClim period
-> locator chooses a completed .tif and ignores active .tif.part files
-> geotiff_sampler reads the requested monthly raster band
-> climate_raster_service normalizes units and returns source metadata
-> the demo JSON grid remains available as fallback
```

Implemented files:

- `backend/app/services/climate_data/loaders/worldclim_locator.py`
- `backend/app/services/climate_data/processors/geotiff_sampler.py`
- `backend/app/services/climate_data/climate_raster_service.py`
- `backend/tests/test_worldclim_raster.py`

Additional resumable data acquisition scripts:

- `backend/scripts/download_worldclim_baseline.py`
- `backend/scripts/download_worldcover_bbox.py`
- `backend/scripts/download_ghsl.py`
- `backend/scripts/download_utils.py`

These scripts provide dry-run plans, confirmation guards, retries, resumable
`.part` files, completed-file skipping, and download manifests.

Feature engineering now attempts to add real future monthly maximum
temperature, minimum temperature, and precipitation. Temperature anomaly
fields remain explicit proxies until a historical baseline is ingested.

### Cell Detail Flow

```text
User clicks rendered climate surface cell
-> MapboxView sends grid_cell_id
-> getClimateCellDetail()
-> GET /api/climate/cell-detail
-> Technical tab shows sampled value/explanation
```

### Natural Language Advisor Flow

```text
User types query + chips in Climate Advisor tab
-> queryClimateAdvisor()
-> POST /api/advisor/query
-> advisor_parser extracts location/year/warming/constraints
-> advisor_engine scores primary location
-> recommendation engine ranks alternatives
-> AI explanation service writes human explanation
-> frontend shows interpreted query, risks, recommendations, Apply to Map
```

## Recent Major Feature Batch

The latest large batch added:

- climate surface generation
- climate cell inspection
- timeline playback
- AI explanation service
- composite climate interaction engine
- future relocation recommendation engine
- saved scenarios persistence
- natural language Climate Advisor
- frontend panel tabs for advisor, system interactions, saved scenarios, technical metadata
- Mapbox cleanup fix for comparison-mode remounts

## Known Issues / Watch Points

- `frontend/lib/api/mockClient.ts` should eventually be renamed because it now calls real backend APIs.
- Frontend typecheck/lint may need local Node/npm availability.
- Some docs are stale and should defer to this file.
- The app has grown quickly; prefer small changes with explanation logs.
- Keep `backend/.env` and `frontend/.env.local` uncommitted.
- Comparison mode previously crashed due to unsafe Mapbox cleanup; `MapboxView.tsx` now uses a safer layer guard.

## Next Strategic Step

Continue the real spatial/data foundation:

1. Add native PostGIS Point/Polygon geometry and spatial indexes.
2. Add database migration tooling instead of relying only on `create_all`.
3. Migrate search/scenario requests toward stable `place_id` references.
4. Complete the WorldClim matrix and ingest a historical baseline.
5. Add training data export, a trainable ML baseline, and model registry.
6. Replace deterministic inference weights with a validated serialized model.
7. Replace the current map surface generator with data-backed raster features.
