# Future Cities AI Project Walkthrough

This document explains the current full-stack architecture in simple terms. The project is now a monorepo with a Next.js frontend and a FastAPI backend.

## 1. Architecture Overview

Future Cities AI currently has two main apps:

- Frontend: interactive map UI, controls, panels, overlays, demo tour
- Backend: simulated climate intelligence API

Request flow:

```text
User action in frontend
-> React handler in /frontend/app/map/page.tsx
-> frontend API client in /frontend/lib/api/mockClient.ts
-> FastAPI route in /backend/app/api/routes/
-> service logic in /backend/app/services/simulation.py
-> JSON response
-> React state update
-> Mapbox and intelligence panel update
```

The backend is real HTTP, but the data is still simulated.

## 2. Folder Structure

```text
future-cities-ai/
  frontend/
    app/
    components/
    lib/
    public/
    package.json
    .env.local

  backend/
    app/
      main.py
      api/
        routes/
      models/
      services/
      db/
    requirements.txt
    .env.example

  docs/
    PROJECT_VISION.md
    PROJECT_WALKTHROUGH.md

  README.md
```

## 3. Main Frontend Files

`/frontend/app/map/page.tsx`

Main map page. Owns most UI state:

- selected city
- year
- warming level
- season
- comparison mode
- active panel tab
- loading/error state
- demo tour state

`/frontend/lib/api/mockClient.ts`

Frontend API client. This file calls the FastAPI backend with `fetch()`.

Main functions:

- `searchLocation()`
- `getScenarioScore()`
- `compareScenarios()`
- `getRegionBoundary()`
- `getHumanImpactExplanation()`

`/frontend/lib/api/mockData.ts`

Frontend seed data for known cities and UI constants.

`/frontend/components/SearchScenarioBar.tsx`

Search bar, scenario mode controls, warming slider, season selector, demo tour button.

`/frontend/components/MapboxView.tsx`

Mapbox map renderer. Handles:

- city markers
- map fly/focus behavior
- clicked local cell marker
- region boundary layer
- climate overlay layer

`/frontend/components/IntelligencePanel.tsx`

Right-side intelligence panel. Contains tabs:

- Overview
- Impact
- Regional Mapping
- Comparison
- Technical

`/frontend/components/ComparisonScenarioControls.tsx`

Controls for Scenario A and Scenario B in comparison mode.

## 4. Main Backend Files

`/backend/app/main.py`

FastAPI app entry point. Registers routes and CORS.

`/backend/app/api/routes/health.py`

Health endpoint:

```text
GET /health
```

`/backend/app/api/routes/search.py`

Search endpoint:

```text
GET /api/search?query=istanbul
```

`/backend/app/api/routes/scenario.py`

Scenario endpoints:

```text
POST /api/scenario/score
POST /api/scenario/compare
```

`/backend/app/api/routes/region.py`

Region boundary endpoint:

```text
GET /api/region-boundary?location=istanbul
```

`/backend/app/models/schemas.py`

Pydantic request/response models. Similar to DTOs in Spring Boot.

`/backend/app/services/simulation.py`

Mock service layer. Generates deterministic simulated climate data.

## 5. API Contract Summary

### `GET /health`

Returns:

```json
{
  "status": "ok"
}
```

### `GET /api/search?query=istanbul`

Returns:

```json
{
  "location_name": "Istanbul",
  "region": "Marmara region",
  "climate_zone": "Bosphorus maritime transition",
  "latitude": 41.0082,
  "longitude": 28.9784,
  "known": true,
  "extrapolated": false,
  "location_id": "istanbul"
}
```

### `POST /api/scenario/score`

Input:

```json
{
  "location": "Istanbul",
  "year": 2030,
  "warmingLevel": 1.7,
  "season": "Summer",
  "timeOfDay": "Afternoon"
}
```

Returns:

- location metadata
- livability score
- heat risk
- flood risk
- outdoor comfort
- green cover
- wet bulb anomaly
- human-readable summary

### `POST /api/scenario/compare`

Input:

```json
{
  "scenarioA": {
    "location": "Istanbul",
    "year": 2030,
    "warmingLevel": 1.7,
    "season": "Summer",
    "timeOfDay": "Afternoon"
  },
  "scenarioB": {
    "location": "Istanbul",
    "year": 2050,
    "warmingLevel": 2.7,
    "season": "Summer",
    "timeOfDay": "Afternoon"
  }
}
```

Returns:

- heat increase
- flood increase
- comfort decline
- livability decline
- explanation

### `GET /api/region-boundary?location=istanbul`

Returns:

- location metadata
- boundary source
- simulated polygon coordinates

## 6. Search Flow

Example: user searches `Istanbul`.

```text
/frontend/components/SearchScenarioBar.tsx
-> handleSubmit()
-> calls onSearch(query)

/frontend/app/map/page.tsx
-> searchRegion(query)
-> calls searchLocation()

/frontend/lib/api/mockClient.ts
-> searchLocation()
-> GET /api/search?query=Istanbul

/backend/app/api/routes/search.py
-> search(query)
-> calls search_location(query)

/backend/app/services/simulation.py
-> search_location()
-> returns LocationResult

/frontend/app/map/page.tsx
-> updates selectedCity, regionalMapping, focusedCityName
```

Result:

- map flies to Istanbul
- region mapping updates
- right panel updates
- region boundary request starts

## 7. Scenario Score Flow

Scenario score is triggered when location/scenario state changes.

```text
/frontend/app/map/page.tsx
-> useEffect(...)
-> calls getScenarioScore()

/frontend/lib/api/mockClient.ts
-> POST /api/scenario/score

/backend/app/api/routes/scenario.py
-> scenario_score(payload)
-> calls score_scenario(payload)

/backend/app/services/simulation.py
-> score_scenario()
-> computes simulated score

/frontend/app/map/page.tsx
-> stores score in scenarioScore state
```

Result:

- livability score updates
- heat/flood/comfort values update
- right panel re-renders

## 8. Comparison Flow

Comparison mode uses Scenario A and Scenario B.

```text
/frontend/app/map/page.tsx
-> scenarioA / scenarioB state
-> calls compareScenarios()

/frontend/lib/api/mockClient.ts
-> POST /api/scenario/compare

/backend/app/api/routes/scenario.py
-> scenario_compare(payload)
-> calls compare_scenarios(payload)

/backend/app/services/simulation.py
-> compare_scenarios()
-> computes Scenario B minus Scenario A deltas

/frontend/app/map/page.tsx
-> stores comparisonMetrics
```

Result:

- Comparison tab shows deltas
- split maps use Scenario A/B controls
- explanation updates

## 9. Region Boundary Flow

After search/select location, frontend requests boundary data.

```text
/frontend/app/map/page.tsx
-> regionalMapping changes
-> calls getRegionBoundary(regionalMapping)

/frontend/lib/api/mockClient.ts
-> GET /api/region-boundary?location=Istanbul

/backend/app/api/routes/region.py
-> get_region_boundary(location)
-> calls region_boundary(location)

/backend/app/services/simulation.py
-> region_boundary()
-> returns simulated polygon

/frontend/app/map/page.tsx
-> stores regionBoundary

/frontend/components/MapboxView.tsx
-> receives regionBoundary
-> draws Mapbox region layer
```

Result:

- simulated regional boundary appears
- climate overlay can render in that region

## 10. Current Mock / Simulated Parts

These are currently simulated:

- geocoding/search
- known city metadata
- unknown location extrapolation
- climate zones
- region boundaries
- scenario scores
- heat/flood/comfort risk
- wet bulb anomaly
- human-readable explanations
- local urban cell risk
- climate overlay surfaces

The HTTP API is real. The intelligence data is fake for now.

## 11. Future Backend Roadmap

Good replacement points:

`/backend/app/services/simulation.py`

Replace `search_location()` with:

- Mapbox Geocoding
- Pelias
- Google Geocoding
- custom gazetteer

Replace `region_boundary()` with:

- PostGIS administrative boundaries
- GeoJSON boundary lookup
- climate grid cell lookup

Replace `score_scenario()` with:

- real climate model data
- raster/grid-cell climate data
- urban heat island model
- flood exposure model
- vegetation/green cover data

Replace comparison/explanation logic with:

- real delta calculations
- ML scoring
- LLM-generated explanations
- personalized risk profiles

Potential future backend folders:

```text
/backend/app/services/geocoding.py
/backend/app/services/postgis_regions.py
/backend/app/services/climate_grid.py
/backend/app/services/risk_scoring.py
/backend/app/services/ai_explanations.py
```

## 12. How To Run Locally

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Backend runs at:

```text
http://127.0.0.1:8000
```

Swagger docs:

```text
http://127.0.0.1:8000/docs
```

### Frontend

Create:

```text
/frontend/.env.local
```

With:

```text
NEXT_PUBLIC_MAPBOX_TOKEN=your_mapbox_token
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

Then run:

```bash
cd frontend
npm run dev
```

Frontend runs at:

```text
http://localhost:3000
```

Open:

```text
http://localhost:3000/map
```
