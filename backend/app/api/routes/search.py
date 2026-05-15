from fastapi import APIRouter

from app.models.schemas import LocationResult
from app.services.geocoding import geocode_location
from app.services.simulation import search_location

router = APIRouter(prefix="/api", tags=["search"])


@router.get("/search", response_model=LocationResult)
def search(query: str) -> LocationResult:
    geocoded_location = geocode_location(query)

    if geocoded_location:
        simulated_location = search_location(query)

        if simulated_location.known:
            return LocationResult(
                location_name=simulated_location.location_name,
                region=geocoded_location.region,
                climate_zone=geocoded_location.climate_zone,
                latitude=geocoded_location.latitude,
                longitude=geocoded_location.longitude,
                locality=geocoded_location.locality,
                district=geocoded_location.district,
                city=geocoded_location.city or simulated_location.location_name,
                country=geocoded_location.country,
                hierarchy_label=geocoded_location.hierarchy_label,
                place_type=geocoded_location.place_type,
                geocoder_provider=geocoded_location.geocoder_provider,
                geocoder_metadata=geocoded_location.geocoder_metadata,
                bbox=geocoded_location.bbox,
                known=True,
                extrapolated=False,
                location_id=geocoded_location.location_id,
            )

        return geocoded_location

    return search_location(query)
