from datetime import datetime

from sqlalchemy import DateTime, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class AdministrativeBoundary(Base):
    __tablename__ = "administrative_boundaries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    aliases: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    country: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    region_type: Mapped[str] = mapped_column(String(80), nullable=False, default="region")
    climate_region_type: Mapped[str] = mapped_column(String(80), nullable=False, default="continental")
    source: Mapped[str] = mapped_column(String(120), nullable=False, default="local_seed_geojson")
    geometry_geojson: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
