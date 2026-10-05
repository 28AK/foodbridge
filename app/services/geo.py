"""Distance and travel-time helpers."""
import math

EARTH_RADIUS_KM = 6371.0
AVG_CITY_SPEED_KMPH = 20.0   # typical two-wheeler / van speed in Lucknow traffic
ROAD_FACTOR = 1.3            # roads are longer than the straight-line distance
HANDLING_MINUTES = 15        # loading / unloading at each stop


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlmb / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def travel_minutes(distance_km: float) -> float:
    """Estimated driving time for a straight-line distance."""
    return distance_km * ROAD_FACTOR / AVG_CITY_SPEED_KMPH * 60


def lat_lng(point: dict) -> tuple[float, float]:
    """GeoJSON Point -> (lat, lng). GeoJSON stores [lng, lat]."""
    lng, lat = point["coordinates"]
    return lat, lng
