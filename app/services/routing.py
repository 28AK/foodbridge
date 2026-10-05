"""Pickup route suggestion for an NGO collecting several donations.

Greedy nearest-neighbour from the NGO, with a deadline guard: if any remaining
pickup is about to miss its deadline, go there first (earliest-deadline-first).
The route ends back at the NGO, where the food is delivered.
"""
from datetime import datetime, timedelta
from urllib.parse import urlencode

from app.services.geo import HANDLING_MINUTES, haversine_km, travel_minutes

URGENT_SLACK_MINUTES = 30


def plan_route(origin: tuple[float, float], stops: list[dict], start: datetime) -> dict:
    """`stops`: dicts with id, lat, lng, deadline (aware datetime) and any extra fields."""
    remaining = list(stops)
    position, clock = origin, start
    ordered, total_km = [], 0.0

    while remaining:
        def arrival(stop):
            km = haversine_km(*position, stop["lat"], stop["lng"])
            return km, clock + timedelta(minutes=travel_minutes(km))

        options = [(stop, *arrival(stop)) for stop in remaining]
        urgent = [o for o in options
                  if (o[0]["deadline"] - o[2]) < timedelta(minutes=URGENT_SLACK_MINUTES)]
        if urgent:
            stop, km, eta = min(urgent, key=lambda o: o[0]["deadline"])
        else:
            stop, km, eta = min(options, key=lambda o: o[1])

        ordered.append({
            **stop,
            "order": len(ordered) + 1,
            "leg_km": round(km, 2),
            "eta": eta,
            "on_time": eta <= stop["deadline"],
        })
        total_km += km
        remaining.remove(stop)
        position, clock = (stop["lat"], stop["lng"]), eta + timedelta(minutes=HANDLING_MINUTES)

    back_km = haversine_km(*position, *origin) if ordered else 0.0
    total_km += back_km
    finish = clock + timedelta(minutes=travel_minutes(back_km))

    return {
        "stops": ordered,
        "total_km": round(total_km, 2),
        "return_km": round(back_km, 2),
        "estimated_finish": finish,
        "all_on_time": all(s["on_time"] for s in ordered),
        "maps_url": google_maps_url(origin, ordered),
    }


def google_maps_url(origin: tuple[float, float], stops: list[dict]) -> str | None:
    """Turn-by-turn directions link (no API key needed): NGO -> pickups -> NGO."""
    if not stops:
        return None
    fmt = lambda lat, lng: f"{lat:.6f},{lng:.6f}"
    params = {
        "api": "1",
        "origin": fmt(*origin),
        "destination": fmt(*origin),
        "waypoints": "|".join(fmt(s["lat"], s["lng"]) for s in stops),
        "travelmode": "driving",
    }
    return "https://www.google.com/maps/dir/?" + urlencode(params)
