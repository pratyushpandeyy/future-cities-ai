# Sprint Log

This log records the multi-day local sprint that was later split into logical
Git commits. Commit timestamps show when the work was cleaned up and committed;
the notes below preserve the actual development narrative.

## Sprint Themes

- Moved the project from simulated frontend-only climate scoring toward a
  backend-driven GeoAI platform.
- Added real geocoding, boundary lookup, spatial resolution, and database
  scaffolding.
- Added climate raster sampling from local WorldClim CMIP6 files and remote
  climate/environmental sources.
- Added feature engineering and a deterministic ML-style scoring baseline.
- Added frontend technical evidence so the UI can show which data source powered
  a score.

## Work Areas

### Spatial Resolution And Boundaries

- Added database models for persisted places and administrative boundaries.
- Added spatial resolution flow from query to geocoded place, boundary match,
  climate region type, and nearest climate sample.
- Kept fallbacks to local GeoJSON and simulated boundaries.

### Climate Raster Sampling

- Added local WorldClim CMIP6 file location and GeoTIFF point sampling.
- Added a provider/broker abstraction so the backend can try local rasters,
  remote rasters, cache, and demo fallback in order.
- Added persistent climate sample caching.

### Data And Feature Engineering

- Added dataset registry endpoints to expose available climate and geospatial
  datasets.
- Added feature vector construction that blends raster samples, scenario inputs,
  region context, and fallback features.
- Added deterministic ML-style inference that adjusts heat, flood, comfort,
  water stress, and livability scores.

### Environmental Context And Download Scripts

- Added optional Copernicus DEM, ESA WorldCover, and Overture context helpers.
- Added downloader scripts for WorldClim future/baseline data, WorldCover,
  GHSL, and Overture extracts.
- Documented data source and storage strategy.

### Frontend Evidence And Inspectability

- Added score data evidence metadata to the backend response.
- Added frontend Technical-tab display for source, confidence, variable,
  sampled value, model, period, cache status, and fallback warnings.
