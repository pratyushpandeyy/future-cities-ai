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

Useful verification flow:

1. Start PostGIS.
2. Run `python scripts/seed_boundaries.py`.
3. Open `/api/admin/boundaries` and confirm the seed records exist.
4. Open `/api/region-boundary?location=Bangalore`, `/api/region-boundary?location=Whitefield`, and `/api/region-boundary?location=Istanbul`.
5. Confirm each seeded lookup includes `boundary_source: "database"`, `boundary_name`, `boundary_match_reason`, `climate_region_type`, and `db_boundary_id`.
