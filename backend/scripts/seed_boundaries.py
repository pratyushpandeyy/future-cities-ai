import json
import sys
from pathlib import Path

from sqlalchemy import text


BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(BACKEND_ROOT))

from app.db.models import AdministrativeBoundary  # noqa: E402
from app.db.session import Base, SessionLocal, engine, is_database_configured  # noqa: E402
from app.services.dataset_registry import sync_builtin_datasets  # noqa: E402


BOUNDARY_DIR = BACKEND_ROOT / "data" / "boundaries"

BOUNDARY_SEEDS = {
    "bangalore_urban.geojson": {
        "name": "Bengaluru Urban / Bangalore",
        "aliases": ["bangalore", "bengaluru", "bengaluru urban", "bangalore urban", "whitefield", "koramangala"],
        "country": "India",
        "region_type": "urban_district",
        "climate_region_type": "highland",
    },
    "karnataka.geojson": {
        "name": "Karnataka",
        "aliases": ["karnataka", "bangalore", "bengaluru"],
        "country": "India",
        "region_type": "state",
        "climate_region_type": "highland",
    },
    "maharashtra.geojson": {
        "name": "Maharashtra",
        "aliases": ["maharashtra", "mumbai", "bandra"],
        "country": "India",
        "region_type": "state",
        "climate_region_type": "tropical_humid",
    },
    "greater_manchester.geojson": {
        "name": "Greater Manchester",
        "aliases": ["greater manchester", "manchester", "north west england"],
        "country": "United Kingdom",
        "region_type": "metropolitan_county",
        "climate_region_type": "temperate_oceanic",
    },
    "marmara_istanbul.geojson": {
        "name": "Marmara / Istanbul Region",
        "aliases": ["istanbul", "marmara", "kadikoy", "kadiköy"],
        "country": "Turkey",
        "region_type": "regional_corridor",
        "climate_region_type": "mediterranean",
    },
    "community_of_madrid.geojson": {
        "name": "Community of Madrid",
        "aliases": ["madrid", "community of madrid", "central spain"],
        "country": "Spain",
        "region_type": "autonomous_community",
        "climate_region_type": "mediterranean",
    },
}


def main() -> None:
    if not is_database_configured() or engine is None or SessionLocal is None:
        raise RuntimeError("DATABASE_URL is not configured. Add it to backend/.env first.")

    with engine.begin() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))

    Base.metadata.create_all(bind=engine)

    with SessionLocal() as session:
        for filename, metadata in BOUNDARY_SEEDS.items():
            boundary_path = BOUNDARY_DIR / filename

            with boundary_path.open("r", encoding="utf-8") as file:
                geojson = json.load(file)

            existing = (
                session.query(AdministrativeBoundary)
                .filter(AdministrativeBoundary.name == metadata["name"])
                .one_or_none()
            )

            if existing:
                existing.aliases = metadata["aliases"]
                existing.country = metadata["country"]
                existing.region_type = metadata["region_type"]
                existing.climate_region_type = metadata["climate_region_type"]
                existing.source = f"seed:{filename}"
                existing.geometry_geojson = geojson
            else:
                session.add(
                    AdministrativeBoundary(
                        name=metadata["name"],
                        aliases=metadata["aliases"],
                        country=metadata["country"],
                        region_type=metadata["region_type"],
                        climate_region_type=metadata["climate_region_type"],
                        source=f"seed:{filename}",
                        geometry_geojson=geojson,
                    ),
                )

        session.commit()

    print(f"Seeded {len(BOUNDARY_SEEDS)} administrative boundaries.")
    print(f"Synced {sync_builtin_datasets()} climate dataset records.")


if __name__ == "__main__":
    main()
