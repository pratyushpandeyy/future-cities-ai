from dataclasses import dataclass
import re

from app.db.models import AdministrativeBoundary
from app.models.schemas import LocationResult


@dataclass(frozen=True)
class BoundaryCandidate:
    level: str
    value: str


def boundary_search_hierarchy(
    location: str,
    location_result: LocationResult,
) -> list[BoundaryCandidate]:
    candidates = [
        BoundaryCandidate("input", location),
        BoundaryCandidate("geocoder_label", location_result.location_name),
        BoundaryCandidate("locality", location_result.locality or ""),
        BoundaryCandidate("district", location_result.district or ""),
        BoundaryCandidate("city", location_result.city or ""),
        BoundaryCandidate("region", location_result.region or ""),
        BoundaryCandidate("country", location_result.country or ""),
    ]

    hierarchy_parts = split_hierarchy_label(location_result.hierarchy_label)
    candidates.extend(
        BoundaryCandidate("hierarchy", hierarchy_part)
        for hierarchy_part in hierarchy_parts
    )

    return dedupe_candidates(candidates)


def match_boundary_candidates(
    boundary: AdministrativeBoundary,
    candidates: list[BoundaryCandidate],
) -> tuple[BoundaryCandidate, str] | None:
    indexed_terms = boundary_index_terms(boundary)

    for candidate in candidates:
        normalized_candidate = normalize_boundary_text(candidate.value)

        if not normalized_candidate:
            continue

        for term_type, raw_term, normalized_term in indexed_terms:
            if normalized_candidate == normalized_term:
                return candidate, f"{candidate.level} exact {term_type} match: {raw_term}"

        for term_type, raw_term, normalized_term in indexed_terms:
            if (
                normalized_candidate in normalized_term
                or normalized_term in normalized_candidate
            ):
                return candidate, f"{candidate.level} fuzzy {term_type} match: {raw_term}"

    return None


def boundary_index_terms(
    boundary: AdministrativeBoundary,
) -> list[tuple[str, str, str]]:
    raw_terms = [
        ("name", boundary.name),
        ("country", boundary.country or ""),
        ("region_type", boundary.region_type),
        ("source", boundary.source),
        *[("alias", alias) for alias in boundary.aliases],
    ]

    indexed_terms = []

    for term_type, raw_term in raw_terms:
        normalized = normalize_boundary_text(raw_term)

        if normalized:
            indexed_terms.append((term_type, raw_term, normalized))

    return indexed_terms


def normalize_boundary_text(value: str) -> str:
    cleaned = value.lower().replace("&", " and ")
    cleaned = re.sub(r"[^a-z0-9]+", " ", cleaned)
    return " ".join(cleaned.split())


def split_hierarchy_label(hierarchy_label: str | None) -> list[str]:
    if not hierarchy_label:
        return []

    return [
        part.strip()
        for part in hierarchy_label.replace(">", "/").split("/")
        if part.strip()
    ]


def dedupe_candidates(candidates: list[BoundaryCandidate]) -> list[BoundaryCandidate]:
    seen = set()
    deduped = []

    for candidate in candidates:
        normalized = normalize_boundary_text(candidate.value)

        if not normalized or normalized in seen:
            continue

        seen.add(normalized)
        deduped.append(candidate)

    return deduped
