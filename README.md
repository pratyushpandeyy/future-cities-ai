# Future Cities AI

Future Cities AI is organized as a monorepo with a Next.js frontend and a placeholder FastAPI backend.

## Frontend

```bash
cd frontend
npm run dev
```

The frontend runs at `http://localhost:3000` by default.

Create `frontend/.env.local` locally with:

```bash
NEXT_PUBLIC_MAPBOX_TOKEN=your_mapbox_token
```

Do not commit `.env.local`.

## Backend

The backend is prepared for future FastAPI work.

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API will run at `http://127.0.0.1:8000`.

Available mock endpoints:

- `GET /health`
- `GET /api/search?query=istanbul`
- `POST /api/spatial/resolve`
- `GET /api/datasets`
- `GET /api/datasets/{dataset_key}`
- `POST /api/features/build`
- `POST /api/scenario/score`
- `POST /api/scenario/compare`
- `GET /api/region-boundary?location=istanbul`
- `GET /api/climate/raster-sample?lat=19.076&lon=72.8777&layer_type=heat_stress`

For real geocoding, set this in `backend/.env`:

```bash
MAPBOX_GEOCODING_TOKEN=your_mapbox_token
```

If no Mapbox token is configured, the backend tries Nominatim/OpenStreetMap and then falls back to deterministic simulated search.

## Climate Raster v0

The backend includes a first lightweight climate-data ingestion path:

- demo dataset: `backend/data/climate/demo_heat_stress_grid.json`
- loader: `backend/app/services/climate_data/loaders/json_grid_loader.py`
- processor: `backend/app/services/climate_data/processors/grid_sampler.py`
- service: `backend/app/services/climate_data/climate_raster_service.py`

Test a nearest-grid sample:

```text
http://127.0.0.1:8000/api/climate/raster-sample?lat=19.076&lon=72.8777&layer_type=heat_stress
```

The scenario scoring engine samples this grid when available and blends the value into the deterministic heat score. If the raster path is unavailable, formula-based scoring remains the fallback.

## Optional PostgreSQL/PostGIS Boundary Store

The backend can now look up administrative boundaries from PostgreSQL before falling back to local GeoJSON files.

Start a local PostGIS container:

```bash
docker run --name future-cities-postgis -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=future_cities_ai -p 5432:5432 -d postgis/postgis:16-3.4
```

Add this to `backend/.env`:

```bash
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/future_cities_ai
```

Install backend dependencies and seed the boundary table:

```bash
cd backend
pip install -r requirements.txt
python scripts/seed_boundaries.py
```

Then restart the backend:

```bash
uvicorn app.main:app --reload
```

Test boundary lookup:

```text
http://127.0.0.1:8000/api/region-boundary?location=Whitefield
http://127.0.0.1:8000/api/region-boundary?location=Istanbul
http://127.0.0.1:8000/api/region-boundary?location=Paris
```

Expected behavior:

- Seeded places return `boundary_source: "database"` after the DB is seeded.
- Seeded places return `boundary_source: "real_geojson"` if the DB is unavailable but local GeoJSON fallback matches.
- Unknown places return `boundary_source: "simulated_fallback"`.

Inspect database-backed boundaries:

```text
http://127.0.0.1:8000/api/admin/boundaries
http://127.0.0.1:8000/api/admin/boundaries/1
```

Import additional GeoJSON boundary files from sources such as geoBoundaries,
GADM, OSM exports, or Overture-derived GeoJSON:

```powershell
cd backend
python scripts/import_boundaries.py --input data/raw/geoboundaries --provider geoboundaries --region-type administrative_boundary
```

The importer reads every `.geojson`/`.json` file under the input path,
normalizes common name fields such as `shapeName`, `NAME_1`, `NAME_2`,
and `name`, then inserts or updates `administrative_boundaries` rows.
Boundary lookup now tries geocoded names from specific to broad:
locality/POI input -> district -> city -> state/region -> country. If a
locality polygon is missing, the service can still match an imported city,
district, or state polygon before falling back to local seed files or a
simulated bbox.

Resolve a place into one combined spatial context:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/api/spatial/resolve `
  -ContentType "application/json" `
  -Body '{"query":"Whitefield"}'
```

The response includes the geocoded place, persistence status, resolution level,
boundary source, nearest climate grid cell, data source, confidence, and fallback
status.

Build a model-ready feature vector:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/api/features/build `
  -ContentType "application/json" `
  -Body '{"query":"Whitefield","year":2050,"warming_level":2.7,"season":"Summer","time_of_day":"Afternoon"}'
```

Train or inspect the local climate adjustment model:

```powershell
cd backend
python scripts/train_climate_model.py --overwrite
```

```text
http://127.0.0.1:8000/api/model/status
```

The current model artifact is a lightweight linear-regression baseline trained
from harvested feature rows when available, and deterministic expert-rule
profiles otherwise. It is intentionally structured like a real model artifact
so future CMIP6/urban outcome training data can replace the temporary labels
without changing frontend or scenario API contracts.

Harvest compact training features from the same data path used by live scoring:

```powershell
cd backend
python scripts/harvest_training_features.py --overwrite
python scripts/train_climate_model.py --training-data data\models\climate_training_features_v2.json --overwrite
```

You can also do the same through Swagger:

```text
POST /api/features/harvest
POST /api/model/train
GET /api/model/status
```

This is the Option B training path: remote/local climate providers are sampled
into a compact JSON feature table, then the model trains from that table. The
raw global rasters do not need to live inside Git.

See `docs/DATA_SOURCES_AND_STORAGE.md` for the dataset download order and cloud
storage architecture.

## WorldClim CMIP6 Downloader

Preview the default 72-file MVP matrix without downloading:

```powershell
cd backend
python scripts/download_worldclim_cmip6.py --dry-run
```

Download one test GeoTIFF:

```powershell
python scripts/download_worldclim_cmip6.py `
  --models MPI-ESM1-2-HR `
  --scenarios ssp245 `
  --periods 2041-2060 `
  --variables tmax
```

Download the default matrix of three GCMs, SSP245/SSP585, four future periods,
and tmin/tmax/prec:

```powershell
python scripts/download_worldclim_cmip6.py --confirm
```

The downloader skips completed files, resumes `.part` files when the server
supports range requests, retries failures, and writes:

```text
backend/data/raw/worldclim/cmip6/download_manifest.json
```

The raw download directory is ignored by Git.

## Foundation Dataset Downloaders

All commands below are resumable. Completed files are skipped and active files
use a `.part` suffix.

### WorldClim Historical Baseline And Elevation

Preview:

```powershell
cd backend
python scripts/download_worldclim_baseline.py --dry-run
```

Download and extract historical `tmin`, `tmax`, precipitation, and elevation:

```powershell
python scripts/download_worldclim_baseline.py --confirm --extract
```

These files support future-minus-historical anomaly calculation and elevation
features.

### ESA WorldCover For MVP Cities

Preview the required 3-degree tiles:

```powershell
python scripts/download_worldcover_bbox.py `
  --cities bengaluru mumbai pune manchester istanbul madrid varanasi `
  --dry-run
```

Download only those tiles:

```powershell
python scripts/download_worldcover_bbox.py `
  --cities bengaluru mumbai pune manchester istanbul madrid varanasi `
  --confirm
```

Use `--bbox WEST SOUTH EAST NORTH` instead of `--cities` for another area.
The script never downloads the entire global WorldCover archive by default.

### GHSL Population And Built Surface

Preview:

```powershell
python scripts/download_ghsl.py --dry-run
```

Download the 2020 global 100m population and built-surface products:

```powershell
python scripts/download_ghsl.py --confirm-large-download
```

The two GHSL archives total approximately 6.65 GB. Download only one with:

```powershell
python scripts/download_ghsl.py `
  --products built_surface `
  --confirm-large-download
```

Sample a completed WorldClim GeoTIFF through FastAPI:

```text
GET http://127.0.0.1:8000/api/climate/raster-sample?lat=41.0082&lon=28.9784&layer_type=tmax&year=2050&scenario=ssp245&month=7&source=worldclim
```

The response includes the sampled value, model, scenario, 20-year period,
month, units, raster cell identifier, and source file. Incomplete `.tif.part`
files are not sampled.

## Remote Climate Data Broker

The backend now checks climate providers in this default order:

```text
local WorldClim GeoTIFF
-> public NASA NEX-GDDP-CMIP6 monthly COG
-> demo fallback where allowed
```

Configure the provider order in `backend/.env`:

```text
CLIMATE_DATA_PROVIDER_ORDER=local_worldclim,nasa_nex_cog
```

Inspect active providers and cache state:

```text
GET http://127.0.0.1:8000/api/climate/providers
```

Force a remote NASA sample:

```text
GET http://127.0.0.1:8000/api/climate/raster-sample?lat=41.0082&lon=28.9784&layer_type=tmax&year=2050&scenario=ssp245&month=7&source=nasa
```

The first request reads a remote Cloud Optimized GeoTIFF. Repeated requests use
the ignored local cache under `backend/data/cache/climate_samples/`.

Extended NASA variables are supported:

```text
temperature
tmax
tmin
precipitation
relative humidity
specific humidity
wind speed
solar radiation
longwave radiation
```

Enable the slower extended feature set explicitly:

```env
EXTENDED_CLIMATE_FEATURES_ENABLED=true
```

## Remote Environmental Context

Sample Copernicus DEM elevation and ESA WorldCover land cover:

```text
GET http://127.0.0.1:8000/api/environment/context?lat=41.0082&lon=28.9784
```

These remote sources are opt-in for automatic scenario feature generation:

```env
REMOTE_ENVIRONMENTAL_FEATURES_ENABLED=true
```

Query Overture buildings and POIs around a point:

```env
OVERTURE_ENABLED=true
```

```text
GET http://127.0.0.1:8000/api/environment/urban-context?lat=12.9716&lon=77.5946&radius_degrees=0.005
```

Overture is an external experimental client. Upstream errors are returned as
`available=false` rather than crashing scenario scoring.

Download a bbox subset from Overture cloud GeoParquet:

```powershell
python scripts/download_overture_bbox.py `
  --bbox 77.2 12.7 77.9 13.2 `
  --types building place `
  --confirm
```

After adding database models, rerun `python scripts/seed_boundaries.py`; its
`Base.metadata.create_all()` call creates missing tables in the configured
database.

Useful verification flow:

1. Start PostGIS.
2. Run `python scripts/seed_boundaries.py`.
3. Open `/api/admin/boundaries` and confirm the seed records exist.
4. Open `/api/region-boundary?location=Bangalore`, `/api/region-boundary?location=Whitefield`, and `/api/region-boundary?location=Istanbul`.
5. Confirm each seeded lookup includes `boundary_source: "database"`, `boundary_name`, `boundary_match_reason`, `climate_region_type`, and `db_boundary_id`.
