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
