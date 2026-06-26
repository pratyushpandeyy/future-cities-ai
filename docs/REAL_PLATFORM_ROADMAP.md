# Future Cities AI - Real Platform Roadmap

This roadmap assumes the target is a real high-granularity climate intelligence platform, not a throwaway demo.

## Product Target

Users should be able to enter:

- any place, POI, neighborhood, city, or region
- a future year
- a warming scenario/pathway
- personal constraints such as asthma, heat sensitivity, elderly family, walking commute, remote work, flood risk aversion, budget, and lifestyle preference

The system should return:

- future livability scores
- heat survivability
- flood exposure
- outdoor comfort
- resilience
- migration/relocation suitability
- explanations
- warnings
- tradeoffs
- fallback regions
- visual map comparisons and timelines

## Target Data Architecture

Production direction:

```text
PostgreSQL + PostGIS
  places
  place_aliases
  admin_boundaries
  locality_boundaries
  climate_grid_cells
  climate_dataset_registry
  climate_samples
  engineered_features
  scenario_runs
  saved_scenarios
  saved_comparisons
```

Raster/object storage direction:

```text
local dev files first
-> cloud object storage later
-> raster/vector tile service later
```

## Target Data Sources

Potential future sources:

- Mapbox Geocoding, Nominatim, GeoNames, Overture Maps, OpenStreetMap
- GADM, geoBoundaries, Natural Earth, OSM boundaries
- CMIP6 / NASA NEX-GDDP-CMIP6 / Copernicus / WorldClim / CHELSA
- ERA5 historical climate baseline
- flood hazard datasets from Fathom/JRC/local open data where available
- MODIS/Landsat/Sentinel vegetation and land surface temperature proxies
- GHSL / WorldPop / OSM built-up and population density
- elevation/SRTM/DEM
- coastal distance and sea-level exposure layers

## Granularity Strategy

Do not depend only on administrative boundaries.

For each user query, resolve multiple spatial identities:

```text
input text
-> geocoded point
-> POI or neighborhood metadata
-> nearest locality boundary if available
-> city/admin boundary
-> nearest climate grid cells
-> optional custom buffer around point
```

Resolution level should be explicit:

```text
poi
locality
neighborhood
ward
city
admin_region
climate_grid_cell
fallback_buffer
```

This enables comparisons such as:

- Whitefield vs Koramangala
- Bandra vs Powai
- Kadikoy vs Besiktas
- Chelsea vs Brooklyn
- areas inside Varanasi

## Backend Layers

Target backend layers:

```text
api/routes
  thin FastAPI route handlers

services/geocoding
  place search and metadata

services/spatial_resolution
  POI -> boundary/grid/buffer mapping

services/climate_data
  raster loading, sampling, dataset registry

services/feature_engineering
  converts raw geospatial/climate data to model features

services/ml_inference
  model interface for future quantitative predictions

services/ai_explanation
  converts computed facts into human reasoning

services/recommendation
  ranks candidate regions and fallbacks
```

## ML Layer Target

The ML layer should eventually receive a feature vector like:

```text
location_id
year
warming_level
season
climate_region_type
heat_anomaly
wet_bulb_proxy
flood_exposure
humidity
vegetation_index
water_stress
urban_density
population_density
coastal_exposure
elevation
user_constraints
```

It should return:

```text
livability_score
heat_survivability
flood_exposure_score
outdoor_comfort
resilience
migration_suitability
dominant_risk_driver
confidence
```

For v1, the model can be deterministic or sklearn-based, as long as the interface is production-shaped.

## AI Layer Boundary

AI should not invent climate numbers.

AI can:

- explain computed scores
- translate scientific terms to plain language
- interpret user constraints
- summarize tradeoffs
- write recommendation narratives
- compare options

AI should receive computed facts from backend services and produce human-readable reasoning.

## 1 Hour Per Day Working Rhythm

Each session should follow this pattern:

```text
10 min - recap one file/flow
35 min - build one small scoped thing
10 min - test manually
5 min  - update learning log
```

Avoid giant feature prompts. Prefer one service, one endpoint, one UI section, or one bug per session.

## 25-Day Near-Term Goal

With 1 hour/day, 25 days should not try to finish the whole platform. The target should be:

```text
credible real-platform foundation
+ one polished end-to-end user story
+ clear docs that explain what is real and what remains future work
```

Recommended 25-day sequence:

1. Current state docs and learning log
2. Search/geocoding flow walkthrough and cleanup
3. Boundary flow walkthrough and cleanup
4. Database model review and POI model plan
5. Add place/POI table model
6. Add spatial resolution service skeleton
7. Add resolution-level response fields
8. Climate grid/raster flow walkthrough
9. Add nearest-cell distance/debug metadata
10. Add feature engineering service skeleton
11. Add feature vector endpoint
12. Climate engine walkthrough
13. Add ML inference interface skeleton
14. Wire scenario score through feature/inference layer
15. Advisor flow walkthrough
16. Improve advisor parser constraints
17. Improve recommendation explanations
18. Compare two neighborhoods/POIs flow
19. Map overlay polish
20. Timeline polish
21. UI/UX cleanup
22. Error/loading state cleanup
23. Demo script and README update
24. Full manual test pass
25. Buffer and final stabilization

## Longer Realistic Timeline At 1 Hour Per Day

Rough estimate:

- 1 month: solid architecture foundation and polished prototype path
- 2-3 months: real POI/place database, better PostGIS spatial matching, reliable comparisons
- 4-6 months: real climate dataset ingestion and feature engineering for selected regions
- 6-9 months: first meaningful ML scoring model and validation workflow
- 9-12+ months: broader geographic coverage, better datasets, production-quality UX, deployment, caching, auth, and evaluation

This project is feasible, but it is a serious platform. The key is to build it in layers without losing the mental model.

