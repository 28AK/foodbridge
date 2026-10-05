from datetime import datetime, timedelta, timezone

from app.services.geo import haversine_km
from app.services.matching import ist_day_start, is_non_veg, score_candidate
from app.services.routing import plan_route

NOW = datetime(2026, 10, 2, 12, 0, tzinfo=timezone.utc)
NGO = (26.85, 80.95)  # Lucknow


def test_haversine_known_distance():
    # Hazratganj -> Gomti Nagar is roughly 5.7 km in a straight line
    assert 5 < haversine_km(26.8500, 80.9462, 26.8560, 81.0040) < 6.5


def test_closer_ngo_scores_higher():
    near = score_candidate(2, 100, 100, 20, hours_left=4)
    far = score_candidate(12, 100, 100, 20, hours_left=4)
    assert near["score"] > far["score"]


def test_full_ngo_is_excluded():
    assert score_candidate(2, 0, 50, 20, hours_left=4) is None


def test_unreachable_before_deadline_is_excluded():
    # 14 km takes ~70 min with handling; only 30 min left
    assert score_candidate(14, 100, 100, 20, hours_left=0.5) is None


def test_demand_matters():
    hungry = score_candidate(5, 100, 100, 20, hours_left=4)
    satisfied = score_candidate(5, 100, 0, 20, hours_left=4)
    assert hungry["score"] > satisfied["score"]


def test_is_non_veg_uses_declaration_and_confident_ai():
    veg = {"food_category": "veg", "ai": {"category": {"non_veg": False, "confidence": 0.9}}}
    declared = {"food_category": "non_veg", "ai": None}
    ai_sure = {"food_category": "veg", "ai": {"category": {"non_veg": True, "confidence": 0.8}}}
    ai_unsure = {"food_category": "veg", "ai": {"category": {"non_veg": True, "confidence": 0.3}}}
    assert [is_non_veg(x) for x in (veg, declared, ai_sure, ai_unsure)] == [False, True, True, False]


def test_ist_day_start():
    # 02:00 IST on 3 Oct is still "3 Oct" -> day starts 2 Oct 18:30 UTC
    assert ist_day_start(datetime(2026, 10, 2, 20, 30, tzinfo=timezone.utc)) == \
        datetime(2026, 10, 2, 18, 30, tzinfo=timezone.utc)


def stop(id_, lat, lng, hours):
    return {"id": id_, "lat": lat, "lng": lng, "deadline": NOW + timedelta(hours=hours)}


def test_route_visits_nearest_first_and_returns():
    stops = [stop("far", 26.90, 81.05, 5), stop("near", 26.86, 80.96, 5)]
    plan = plan_route(NGO, stops, NOW)
    assert [s["id"] for s in plan["stops"]] == ["near", "far"]
    assert plan["all_on_time"]
    assert plan["return_km"] > 0
    assert "google.com/maps/dir" in plan["maps_url"]


def test_route_prioritises_urgent_stop():
    # "urgent" is farther but its deadline is about to pass
    stops = [stop("near", 26.86, 80.96, 5), stop("urgent", 26.89, 81.00, 0.4)]
    plan = plan_route(NGO, stops, NOW)
    assert plan["stops"][0]["id"] == "urgent"


def test_empty_route():
    plan = plan_route(NGO, [], NOW)
    assert plan["stops"] == [] and plan["maps_url"] is None and plan["total_km"] == 0
