# Future Cities AI - Data Sources And Storage

Last updated: 2026-06-24

## Storage Architecture

Do not store full NetCDF, GeoTIFF, Zarr, or GeoParquet archives as database rows.

Use:

```text
PostgreSQL + PostGIS
  places and aliases
  points and administrative polygons
  dataset catalog and provenance
  spatial indexes
  precomputed grid-cell summaries
  engineered feature vectors
  scenario/model outputs

Object storage
  NetCDF
  GeoTIFF / Cloud Optimized GeoTIFF
  Zarr
  GeoParquet
  raw downloads and processed tiles
  trained model artifacts
```

The dataset registry stores a `storage_uri`, such as:

```text
s3://future-cities-climate/worldclim/...
r2://future-cities-climate/cmip6/...
file:///D:/future-cities-data/...
```

Loaders should read through the URI. Moving data from local disk to cloud object
storage should not change the feature or ML API.

## Download First

### Automated WorldClim Download

The repository includes:

```text
backend/scripts/download_worldclim_cmip6.py
```

Preview the default matrix:

```powershell
cd backend
python scripts/download_worldclim_cmip6.py --dry-run
```

Download one test file:

```powershell
python scripts/download_worldclim_cmip6.py `
  --models MPI-ESM1-2-HR `
  --scenarios ssp245 `
  --periods 2041-2060 `
  --variables tmax
```

Download the 72-file MVP matrix:

```powershell
python scripts/download_worldclim_cmip6.py --confirm
```

Default matrix:

```text
models: MPI-ESM1-2-HR, MIROC6, CNRM-CM6-1
scenarios: SSP245, SSP585
periods: 2021-2040, 2041-2060, 2061-2080, 2081-2100
variables: tmin, tmax, precipitation
resolution: 2.5 arc-minutes
```

### Automated Historical Baseline And Elevation

```powershell
cd backend
python scripts/download_worldclim_baseline.py --dry-run
python scripts/download_worldclim_baseline.py --confirm --extract
```

Default variables:

```text
tmin
tmax
precipitation
elevation
```

The historical climate baseline is WorldClim 1970-2000. It enables monthly
future-minus-baseline anomaly calculation.

### Automated ESA WorldCover Subsets

WorldCover is downloaded as 3-degree 10m tiles. Only request tiles intersecting
target cities or a supplied bounding box:

```powershell
python scripts/download_worldcover_bbox.py `
  --cities bengaluru mumbai pune manchester istanbul madrid varanasi `
  --confirm
```

### Automated GHSL Urban Foundation

```powershell
python scripts/download_ghsl.py --dry-run
python scripts/download_ghsl.py --confirm-large-download
```

The default products are:

```text
GHS_POP 2020 global population, 100m
GHS_BUILT_S 2020 global built-up surface, 100m
```

Their combined archive size is approximately 6.65 GB. These global products
should later be converted into city/region subsets or Cloud Optimized GeoTIFFs
for repeated access.

### 1. geoBoundaries

Purpose:

- global administrative polygons
- point-in-polygon matching
- city/district/state hierarchy

Use the `gbOpen` release because its API documentation recommends it for most
users and describes it as CC BY 4.0 with attribution.

Start with:

```text
IND ADM0-ADM3
GBR ADM0-ADM3
TUR ADM0-ADM3
ESP ADM0-ADM3
```

Then expand globally.

Official API:

```text
https://www.geoboundaries.org/api.html
```

### 2. Overture Maps By Bounding Box

Purpose:

- POIs
- buildings
- addresses
- local urban form

Do not download the entire global release initially. Overture's Python client can
read cloud-hosted GeoParquet and download only features inside a bounding box.

Start with bounding boxes for:

```text
Bengaluru
Mumbai
Pune
Manchester
Istanbul
Madrid
Varanasi
```

Official quickstart:

```text
https://docs.overturemaps.org/getting-data/
```

Implemented access:

```text
backend/app/services/overture_context.py
backend/scripts/download_overture_bbox.py
```

The live service is opt-in because external release/STAC availability can be
slow or fail independently of this application.

### Remote Terrain And Land Cover

Implemented:

```text
Copernicus DEM GLO-30 remote COG point sampling
ESA WorldCover 2021 remote COG point sampling
```

Endpoint:

```text
GET /api/environment/context?lat=...&lon=...
```

These provide real elevation and point land-cover classes without requiring a
global local archive.

### 3. WorldClim CMIP6 For MVP Projections

Purpose:

- future minimum temperature
- future maximum temperature
- future precipitation

WorldClim provides downscaled, bias-corrected CMIP6 monthly climatologies.

Recommended initial subset:

```text
resolution: 2.5 minutes, or 10 minutes if bandwidth/storage is limited
variables: tmin, tmax, precipitation
scenarios: SSP2-4.5 and SSP5-8.5
periods: 2041-2060 and 2061-2080
models: start with one model, then use a 3-model ensemble
```

Official source:

```text
https://www.worldclim.org/data/cmip6/cmip6climate.html
```

### 4. ERA5-Land Baseline By Region And Variable

Purpose:

- historical baseline
- temperature
- dewpoint/humidity
- precipitation
- soil moisture
- radiation

Do not download global hourly ERA5-Land from 1950 onward.

Start with:

```text
target-city bounding boxes
1991-2020 baseline period
monthly aggregates
2m temperature
2m dewpoint temperature
total precipitation
soil water
surface solar radiation
```

Official source:

```text
https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land
```

### 5. GHSL Urban Form

Purpose:

- built-up surface
- settlement classification
- population/urban density
- urban-development history

Download tiles intersecting the MVP cities before attempting global ingestion.

Official source:

```text
https://human-settlement.emergency.copernicus.eu/download.php
```

### 6. WorldPop

Purpose:

- population counts
- population density
- future population products
- degree of urbanisation

Use as a supplement to GHSL.

Official catalog:

```text
https://www.worldpop.org/datacatalog/
```

## Do Not Download Full NEX-GDDP-CMIP6 Yet

NASA reports that the complete NEX-GDDP-CMIP6 collection is approximately
38 TB, at 0.25-degree daily resolution.

Use its THREDDS spatial subsetting service or public AWS bucket to retrieve only:

```text
selected model
selected SSP
selected variable
selected years
selected bounding box
```

Variables to prioritize:

```text
tasmax
tasmin
pr
hurs or humidity variable where available
```

Official source and subsetting instructions:

```text
https://www.nccs.nasa.gov/data-collections/nex-gddp-cmip6/
```

## Cloud Hosting

Cloud hosting is not mandatory during local development.

Local development can use:

```text
local Postgres/PostGIS container
local D:/future-cities-data directory
dataset registry storage_uri values pointing to local files
```

For a deployed MVP:

```text
Managed PostgreSQL/PostGIS
  Supabase, Neon, AWS RDS, Railway, or another PostGIS-capable provider

Object storage
  Cloudflare R2, Amazon S3, Backblaze B2, or similar

FastAPI
  reads metadata from Postgres
  reads only needed raster windows/objects from object storage
```

Cloudflare R2 currently advertises:

```text
10 GB-month free tier
$0.015 per GB-month for standard storage
free direct egress
```

AWS S3 is usage-based and charges separately for storage, requests, retrieval,
and data transfer depending on storage class and region.

For interviews, keep raw global source data external when possible, store only
the required subsets, and precompute compact feature summaries.

## Cost-Control Strategy

1. Query public cloud datasets directly when permitted.
2. Download only target bounding boxes, variables, years, and scenarios.
3. Convert repeated-access rasters to Cloud Optimized GeoTIFF or Zarr.
4. Precompute seasonal/annual statistics instead of serving daily files.
5. Keep cold raw files in cheaper object-storage tiers.
6. Cache derived location features in Postgres.
7. Never send giant source files to the frontend.
