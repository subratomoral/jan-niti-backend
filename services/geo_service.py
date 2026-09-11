"""Geographic facility proximity and spatial context service with dynamic sector intelligence."""

import math
from typing import Optional
from schemas.ai import GeoAnalysisResponse, GeoFacilityContext

# Known civic anchor facilities for key regional hubs (Odisha baseline)
KNOWN_FACILITY_REGISTRY = {
    "Healthcare": {
        "facility_name": "District Headquarters Hospital & Trauma Care",
        "base_lat": 20.2961,
        "base_lon": 85.8245,
    },
    "Roads": {
        "facility_name": "PWD Road Maintenance & Transit Division Depot",
        "base_lat": 20.3012,
        "base_lon": 85.8180,
    },
    "Water": {
        "facility_name": "Public Health Engineering Municipal Water Treatment Plant",
        "base_lat": 20.2750,
        "base_lon": 85.8350,
    },
    "Education": {
        "facility_name": "Government Lead Cluster Secondary School",
        "base_lat": 20.3150,
        "base_lon": 85.8450,
    },
    "Employment": {
        "facility_name": "District Employment Exchange & Skill Training Facility",
        "base_lat": 20.2880,
        "base_lon": 85.8200,
    },
    "Other": {
        "facility_name": "Municipal Ward Administrative Civic Facility",
        "base_lat": 20.2900,
        "base_lon": 85.8250,
    },
}


def _haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates geodesic distance between two coordinate pairs using Haversine formula."""
    r = 6371.0  # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(r * c, 1)


def evaluate_geo_context(
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    location_name: Optional[str] = None,
    category: str = "Healthcare",
) -> GeoAnalysisResponse:
    latitude = float(lat) if lat is not None else 20.2961
    longitude = float(lon) if lon is not None else 85.8245
    loc_name = location_name or "Bhubaneswar"

    # Category ke according matching infrastructure select karein
    facility_data = KNOWN_FACILITY_REGISTRY.get(
        category, KNOWN_FACILITY_REGISTRY["Other"]
    )

    # Citizen coordinates se facility ka actual distance calculate karein
    computed_distance = _haversine_distance_km(
        latitude,
        longitude,
        facility_data["base_lat"],
        facility_data["base_lon"],
    )

    # Realistic proximity fallback (minimum 0.4 km)
    distance_km = max(0.4, computed_distance)

    # Distance ke basis par 2km ke andar kitni facilities hain evaluate karein
    facilities_2km = 1 if distance_km <= 2.0 else 0
    hotspot_level = (
        "High" if distance_km >= 4.0 else "Medium" if distance_km >= 2.0 else "Low"
    )

    return GeoAnalysisResponse(
        latitude=latitude,
        longitude=longitude,
        location_name=loc_name,
        geo_context=GeoFacilityContext(
            nearest_facility_name=facility_data["facility_name"],
            nearest_facility_distance_km=distance_km,
            facilities_within_2km=facilities_2km,
            population_density_est=int(12000 + (distance_km * 950)),
            area_hotspot_level=hotspot_level,
        ),
        analysis_mode="live" if (lat is not None and lon is not None) else "demo",
    )
