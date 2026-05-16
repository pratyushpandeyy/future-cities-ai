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

For real geocoding, set this in `backend/.env`:

```bash
MAPBOX_GEOCODING_TOKEN=your_mapbox_token
```

If no Mapbox token is configured, the backend tries Nominatim/OpenStreetMap and then falls back to deterministic simulated search.

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

- Seeded places return `boundary_source: "real_geojson"` from the database or local GeoJSON fallback.
- Unknown places return `boundary_source: "simulated_fallback"`.
