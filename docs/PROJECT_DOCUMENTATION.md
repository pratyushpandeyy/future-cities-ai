# Future Cities AI - Project Documentation

Last updated: 2026-06-28

This document summarizes what has been built so far, how the system works, what data it uses, what is real, what is simulated, and where the project should go next.

## 1. Product Summary

Future Cities AI is a geospatial climate intelligence platform.

The target experience is:

```text
User enters a place, future year, warming scenario, and personal constraints
-> backend resolves the place to coordinates and boundaries
-> system samples climate, land-cover, urban, and geographic data
-> feature engineering converts raw data into model-ready values
-> ML model predicts score adjustments and risk signals
-> AI/RAG layer explains results in human language
-> frontend visualizes maps, overlays, timelines, comparisons, and recommendations
```

The intended product is not a generic dashboard. It should feel like a cinematic GeoAI workspace for understanding future livability, climate risk, and relocation tradeoffs.

## 2. Monorepo Structure

The project is now a monorepo:

```text
future-cities-ai/
  frontend/   Next.js frontend, Mapbox UI, climate map workspace
  backend/    FastAPI backend, data services, ML, AI/RAG, PostGIS support
  docs/       architecture, walkthroughs, data notes, learning logs
```

Main runtime URLs:

```text
Frontend: http://localhost:3000
Backend:  http://127.0.0.1:8000
Swagger:  http://127.0.0.1:8000/docs
```

## 3. Frontend Overview

The frontend lives in:

```text
frontend/
```

Important files:

```text
frontend/app/map/page.tsx
frontend/components/MapboxView.tsx
frontend/components/IntelligencePanel.tsx
frontend/components/SearchScenarioBar.tsx
frontend/lib/api/mockClient.ts
frontend/lib/climateOverlaySimulation.ts
```

Despite the name `mockClient.ts`, the frontend API client now calls the FastAPI backend with `fetch()`.

Current frontend features:

- Mapbox map/globe experience.
- Search-driven map navigation.
- City/location markers.
- Climate overlay toggle.
- Heat/flood/outdoor comfort/water stress toggles.
- Regional boundary display.
- Climate surface rendering.
- Right intelligence panel with tabs.
- Scenario year and warming controls.
- Comparison mode.
- Demo tour mode.
- Natural Language Climate Advisor panel.
- Saved scenario UI.
- Timeline/evolution controls.

Important frontend behavior:

```text
User searches location
-> frontend calls backend search API
-> selected location updates app state
-> map flies to coordinates
-> backend boundary/climate/scenario APIs are called
-> intelligence panel updates
```

## 4. Backend Overview

The backend lives in:

```text
backend/
```

Entry point:

```text
backend/app/main.py
```

Main route folder:

```text
backend/app/api/routes/
```

Important route files:

```text
health.py
search.py
spatial.py
region.py
scenario.py
climate.py
data_pipeline.py
environment.py
explain.py
rag.py
recommendations.py
advisor.py
saved_scenarios.py
admin.py
```

FastAPI route files are similar to Spring Boot `@RestController` classes: they expose HTTP endpoints and call service-layer code.

## 5. Backend Endpoints

Important endpoints currently available:

```text
GET  /health
GET  /api/search
GET  /api/search/suggestions
POST /api/spatial/resolve
GET  /api/region-boundary
POST /api/scenario/score
POST /api/scenario/compare
GET  /api/climate/raster-sample
GET  /api/climate/surface
GET  /api/climate/cell-detail
GET  /api/climate/timeline
POST /api/climate/composite-risk
GET  /api/datasets
POST /api/features/build
POST /api/features/harvest
GET  /api/features/cache
GET  /api/features/cache/stats
POST /api/features/cache/export
GET  /api/model/status
POST /api/model/train
GET  /api/environment/context
POST /api/explain
POST /api/advisor/query
POST /api/recommendations
POST /api/scenarios/save
GET  /api/scenarios
GET  /api/scenarios/{id}
DELETE /api/scenarios/{id}
GET  /api/admin/boundaries
GET  /api/admin/boundaries/{id}
```

## 6. Database And PostGIS Foundation

Database files:

```text
backend/app/db/config.py
backend/app/db/session.py
backend/app/db/models.py
```

Current database models include:

```text
AdministrativeBoundary
Place
ClimateDataset
ClimateFeatureCache
SavedScenario
```

The project uses SQLAlchemy. Conceptually:

```text
SQLAlchemy model ~= JPA @Entity
SessionLocal ~= Spring repository/session access
Pydantic schema ~= DTO/request/response object
```

PostGIS is currently run locally through Docker:

```powershell
docker run --name future-cities-postgis `
  -e POSTGRES_USER=postgres `
  -e POSTGRES_PASSWORD=postgres `
  -e POSTGRES_DB=future_cities_ai `
  -p 5432:5432 `
  -d postgis/postgis:16-3.4
```

Backend database connection is configured in:

```text
backend/.env
```

Do not commit `.env`.

## 7. Geocoding And Search

Important files:

```text
backend/app/services/geocoding.py
backend/app/api/routes/search.py
```

Current behavior:

- Uses seeded locality fixes for known tricky places such as Whitefield.
- Uses Mapbox geocoding if configured.
- Falls back to Nominatim/OpenStreetMap.
- Falls back to deterministic simulated location only if needed.
- Supports parent-location disambiguation.
- Supports suggestions endpoint for frontend dropdown/autocomplete.

Example:

```text
Whitefield + Bengaluru
-> resolves to Whitefield, Bengaluru coordinates
-> avoids wrong global Whitefield matches
```

## 8. Boundary System

Important files:

```text
backend/app/services/boundaries.py
backend/app/services/boundary_resolution.py
backend/app/services/online_boundaries.py
backend/app/api/routes/region.py
backend/scripts/download_geoboundaries.py
backend/scripts/import_boundaries.py
backend/scripts/seed_boundaries.py
```

Boundary lookup order:

```text
1. PostGIS/database boundary lookup
2. Local seed GeoJSON fallback
3. Optional online OSM/Nominatim polygon lookup
4. Simulated fallback boundary
```

Imported boundary state:

```text
39771 boundary records imported into database
```

The boundary downloader/importer supports geoBoundaries-style data. The importer reads GeoJSON files, extracts names/aliases/country fields, and inserts administrative boundary records.

Current limitation:

- Boundaries are stored as GeoJSON JSON fields, not native PostGIS geometry columns yet.
- Lookup is name/alias/hierarchy based, not full point-in-polygon spatial search yet.
- Global locality/ward-level polygon coverage is incomplete.

## 9. Spatial Resolution

Important files:

```text
backend/app/services/spatial_resolution.py
backend/app/api/routes/spatial.py
```

`POST /api/spatial/resolve` combines:

```text
geocoding
+ optional Place persistence
+ boundary lookup
+ nearest climate sample
+ confidence/fallback metadata
```

This endpoint is the foundation for:

- POI resolution.
- Locality/city/district fallback.
- Future grid-cell matching.
- Stable `place_id` references.

## 10. Climate Data Pipeline

Important climate data files:

```text
backend/app/services/climate_data/climate_data_broker.py
backend/app/services/climate_data/climate_raster_service.py
backend/app/services/climate_data/climate_surface_service.py
backend/app/services/climate_data/sample_cache.py
backend/app/services/climate_data/providers/base.py
backend/app/services/climate_data/providers/local_worldclim.py
backend/app/services/climate_data/providers/nasa_nex_cog.py
backend/app/services/climate_data/loaders/worldclim_locator.py
backend/app/services/climate_data/processors/geotiff_sampler.py
backend/app/services/climate_data/processors/grid_sampler.py
```

Current provider strategy:

```text
ClimateDataBroker
-> try local WorldClim
-> try NASA NEX remote COG provider
-> fallback to demo grid if allowed
```

The broker is similar to a provider router:

```text
Request: lat/lon/year/scenario/model/variable
-> provider order decides where to sample
-> result is cached
-> caller receives ClimateRasterSample
```

## 11. Downloaded Data

Current local data:

```text
WorldClim CMIP6 + historical: ~15.5 GB
geoBoundaries raw data: ~317 MB
ESA WorldCover MVP city tiles: ~674 MB
```

WorldClim CMIP6 downloaded matrix:

```text
models: MPI-ESM1-2-HR, MIROC6, CNRM-CM6-1
scenarios: ssp245, ssp585
periods: 2021-2040, 2041-2060, 2061-2080, 2081-2100
variables: tmin, tmax, prec
resolution: 2.5m
```

WorldCover downloaded for:

```text
Bengaluru / Whitefield
Mumbai / Pune
Istanbul
Madrid
Manchester
Varanasi
```

Important downloader scripts:

```text
backend/scripts/download_worldclim_cmip6.py
backend/scripts/download_worldclim_baseline.py
backend/scripts/download_worldcover_bbox.py
backend/scripts/download_ghsl.py
backend/scripts/download_geoboundaries.py
backend/scripts/prepare_foundation_data.py
```

## 12. Environmental Data

Important file:

```text
backend/app/services/environmental_data.py
```

Current sources:

- ESA WorldCover land-cover class.
- Copernicus DEM remote elevation COG.

Current features derived:

```text
green_cover_proxy
built_up_proxy
elevation
land_cover category
```

Recent important change:

```text
sample_worldcover()
-> now checks local WorldCover GeoTIFF first
-> falls back to remote ESA URL only if local file is missing and remote is allowed
```

This means downloaded WorldCover tiles are now actually used in ML feature extraction.

## 13. Feature Engineering

Important files:

```text
backend/app/services/feature_engineering.py
backend/app/services/feature_harvesting.py
backend/app/services/feature_cache.py
backend/app/api/routes/data_pipeline.py
```

The feature engineering layer converts climate/geographic/context data into model-ready numbers.

Current feature contract:

```text
FEATURE_SCHEMA_VERSION = climate_features_v1
```

Important ML features:

```text
heat_stress_index
precipitation_anomaly_pct
relative_humidity_pct
vegetation_index
water_stress_index
urban_density_index
coastal_exposure_index
future_time_index
warming_level_c
future_monthly_tmax_c
future_monthly_tmin_c
future_monthly_precipitation_mm
elevation_m
```

Each engineered feature records:

```text
value
unit
source
dataset_key
is_fallback
confidence
```

This is important because the AI layer should know whether it is explaining real sampled evidence or fallback priors.

## 14. Feature Cache

Recent addition:

```text
backend/app/services/feature_cache.py
backend/scripts/export_feature_cache_training_data.py
ClimateFeatureCache model in backend/app/db/models.py
```

Purpose:

```text
User/API requests location scenario
-> backend samples climate/cloud/local data
-> feature vector is stored in PostGIS
-> cached feature vectors can later be exported as ML training rows
```

This avoids storing giant raw datasets locally.

Architecture direction:

```text
Remote/public datasets
-> extract only needed values
-> cache compact feature vector
-> train ML from feature cache
```

New endpoints:

```text
GET  /api/features/cache
GET  /api/features/cache/stats
POST /api/features/cache/export
```

## 15. ML System

Important ML files:

```text
backend/app/services/ml_training.py
backend/app/services/ml_inference.py
backend/app/services/ml_targets.py
backend/scripts/train_climate_model.py
backend/scripts/harvest_training_features.py
backend/scripts/harvest_boundary_training_features.py
```

Current model:

```text
model_version: trained_linear_adjustment_v2
model_type: ridge_regularized_linear_regression
```

Current trained artifact:

```text
backend/data/models/climate_adjustment_model_v1.json
```

Current broader training dataset:

```text
backend/data/models/boundary_training_features_v1.json
```

Latest broad training stats:

```text
boundary samples: 300
training rows: 2400
real_data_row_count: 2400
high_completeness_row_count: 24
```

The model currently predicts adjustment values:

```text
heat_adjustment
flood_adjustment
comfort_adjustment
water_stress_adjustment
livability_adjustment
```

These adjustments are blended into the deterministic climate engine and scenario scoring path.

Important caveat:

The model currently trains on proxy labels generated from expert rules and sampled climate features. It is not yet trained on observed real-world outcome labels such as mortality, hospitalizations, insurance losses, or measured livability outcomes.

## 16. Climate Scoring

Important files:

```text
backend/app/services/climate_engine.py
backend/app/services/simulation.py
backend/app/api/routes/scenario.py
```

Scenario scoring combines:

```text
user scenario input
+ region climate type
+ WorldClim/raster samples
+ engineered features
+ ML adjustment model
+ deterministic fallback formulas
```

User-facing outputs include:

```text
livability_score
heat_risk
flood_risk
outdoor_comfort
green_cover
wet_bulb_anomaly
dominant_risk_driver
score_breakdown
data_evidence
model_inputs_used
```

## 17. Climate Surface And Map Overlay

Important files:

```text
backend/app/services/climate_data/climate_surface_service.py
frontend/components/MapboxView.tsx
frontend/lib/climateOverlaySimulation.ts
```

Current overlay behavior:

- Region boundary is shown after search.
- Boundary remains visible even if climate overlay toggle is off.
- Climate overlay is clipped/painted to the returned boundary.
- Raster/grid evidence is summarized and rendered as smoother surface fill instead of global blobs.

Current limitation:

- True vector-tile/raster-tile rendering is not implemented.
- Surface still has prototype constraints.
- Needs frontend polish and better visual interpolation.

## 18. AI Explanation

Important files:

```text
backend/app/services/ai_explanation.py
backend/app/api/routes/explain.py
```

Current AI explanation behavior:

- Uses backend-computed numbers.
- Must not invent climate scores.
- Template fallback works without an LLM.
- Optional LLM mode is planned/configurable through `OPENAI_API_KEY`.

The AI layer is meant to translate:

```text
scores + features + evidence + constraints
```

into:

```text
human_summary
commute_impact
outdoor_activity_impact
nighttime_recovery
vulnerable_groups_note
confidence_note
```

## 19. RAG System

Important files:

```text
backend/app/services/rag_retrieval.py
backend/app/api/routes/rag.py
backend/scripts/build_climate_knowledge_base.py
```

Current RAG status:

- Keyword/token-based retrieval exists.
- Climate knowledge base/chunk building exists.
- Full vector database is not implemented yet.

Planned RAG direction:

```text
scrape/ingest trusted climate documents
-> chunk text
-> embed chunks
-> store in vector DB or local FAISS/Chroma
-> retrieve relevant passages per user question
-> AI explains using retrieved context + numeric backend facts
```

## 20. Natural Language Climate Advisor

Important files:

```text
backend/app/services/advisor_parser.py
backend/app/services/advisor_engine.py
backend/app/api/routes/advisor.py
frontend/components/IntelligencePanel.tsx
```

Current behavior:

User can ask something like:

```text
I live in Whitefield and have asthma. How bad will summers get by 2050 if warming reaches +2.7C? Should I consider Pune or Manchester instead?
```

Backend parses:

```text
primary location
comparison locations
target year
warming level
season
health constraints
lifestyle constraints
relocation intent
```

Advisor returns:

```text
interpreted_query
extracted_inputs
primary_location_score
recommendation_summary
key_risks
suggested_comparison_locations
fallback_locations
human_explanation
confidence_note
```

Current limitation:

- Parser is deterministic/rule-based.
- LLM parsing can be added later.
- Recommendations are still v1 and use prototype scoring.

## 21. Recommendation Engine

Important files:

```text
backend/app/services/recommendation_engine.py
backend/app/api/routes/recommendations.py
```

Current recommendation system supports:

```text
current location
target year
warming tolerance
heat sensitivity
respiratory sensitivity
flood tolerance
outdoor lifestyle
urban/quieter preference
coastal preference
elderly/family sensitivity
remote work flexibility
```

It returns:

```text
recommended regions
suitability score
dominant future risks
livability trajectory
resilience score
fallback alternatives
explanation summary
```

## 22. Timeline And Climate Evolution

Important files:

```text
backend/app/services/climate_timeline.py
backend/app/api/routes/climate.py
frontend map/timeline controls
```

Current timeline supports:

```text
2025 -> 2100 pathway snapshots
optimistic/moderate/severe concepts
yearly score progression
dominant risk progression
raster summary progression
```

Current limitation:

- Temporal interpolation is deterministic/prototype-level.
- No full CMIP6 time-series animation stack yet.

## 23. Climate Interaction Engine

Important file:

```text
backend/app/services/climate_interaction_engine.py
```

Models interactions such as:

```text
high heat + low vegetation -> worse outdoor comfort
flood + dense urban area -> infrastructure pressure
coastal humidity -> nighttime heat retention
water stress -> lower livability resilience
green cover -> heat buffering
```

Returns:

```text
composite_risk_score
dominant_interaction_chain
resilience_score
infrastructure_pressure
human_exposure_score
cascading_risks
mitigation_factors
```

## 24. Saved Scenarios

Important files:

```text
backend/app/services/saved_scenarios.py
backend/app/api/routes/saved_scenarios.py
SavedScenario model in backend/app/db/models.py
```

Supports:

```text
POST   /api/scenarios/save
GET    /api/scenarios
GET    /api/scenarios/{id}
DELETE /api/scenarios/{id}
```

No authentication yet. Saved scenarios are prototype-local.

## 25. Data Scripts

Important scripts:

```text
download_worldclim_cmip6.py
download_worldclim_baseline.py
download_worldcover_bbox.py
download_ghsl.py
download_geoboundaries.py
import_boundaries.py
seed_boundaries.py
prepare_foundation_data.py
harvest_training_features.py
harvest_boundary_training_features.py
export_feature_cache_training_data.py
train_climate_model.py
build_climate_knowledge_base.py
```

Recommended current training path:

```powershell
cd backend
python scripts/harvest_boundary_training_features.py `
  --limit 300 `
  --per-country 5 `
  --year 2030 `
  --year 2050 `
  --warming 1.7 `
  --warming 2.7 `
  --season Summer `
  --season Monsoon `
  --output data\models\boundary_training_features_v1.json `
  --overwrite

python scripts/train_climate_model.py `
  --training-data data\models\boundary_training_features_v1.json `
  --overwrite
```

## 26. What Is Real vs Prototype

Real:

- FastAPI backend.
- Next.js frontend.
- Mapbox map integration.
- Backend HTTP API calls from frontend.
- Real geocoding path with fallbacks.
- PostGIS/SQLAlchemy database foundation.
- 39k imported boundary records.
- Local WorldClim CMIP6 rasters.
- Local ESA WorldCover tiles for MVP regions.
- Feature engineering contract.
- ML model training/inference path.
- Scenario scoring path.
- Advisor/RAG/explanation skeletons.

Prototype:

- ML labels are proxy labels, not observed outcome labels.
- RAG is not yet vector DB-based.
- AI explanation is mostly template fallback unless LLM configured.
- Boundary lookup is not yet full spatial point-in-polygon.
- Climate overlay is not a production raster/vector-tile renderer.
- GHSL/WorldCover global coverage is not fully integrated.
- User auth is absent.

## 27. How To Run

Backend:

```powershell
cd backend
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Frontend:

```powershell
cd frontend
npm install
npm run dev
```

PostGIS Docker:

```powershell
docker start future-cities-postgis
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

Frontend:

```text
http://localhost:3000/map
```

## 28. Suggested Next Steps

Highest-value next steps:

1. Add a real vector DB path for RAG.
2. Improve AI advisor so explanations explicitly cite retrieved documents plus backend numeric evidence.
3. Add proper feature-cache training workflow:
   ```text
   API usage -> cached feature vectors -> export -> train model
   ```
4. Add GHSL sampler for population/built-up density.
5. Improve boundary matching with actual point-in-polygon using native PostGIS geometry.
6. Polish frontend UX after backend pipelines are stable.
7. Add better model evaluation and documented caveats.

## 29. One-Sentence Current State

Future Cities AI is now a working full-stack GeoAI prototype with real geocoding, imported administrative boundaries, WorldClim climate raster sampling, local land-cover evidence for MVP cities, feature engineering, an explainable ML adjustment model, AI/advisor scaffolding, and a cinematic Mapbox frontend, but it still needs vector RAG, stronger observed-label ML data, and production-grade spatial/raster infrastructure.
