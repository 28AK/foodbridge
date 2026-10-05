from datetime import datetime, timedelta, timezone

from app.services.freshness import assess_freshness, quantity_check, risk_level

NOW = datetime(2026, 10, 2, 12, 0, tzinfo=timezone.utc)


def hours_ago(h: float) -> datetime:
    return NOW - timedelta(hours=h)


def test_fresh_food_is_low_risk_with_full_window():
    r = assess_freshness("rice", hours_ago(0.5), 0.02, NOW)
    assert r["risk_level"] == "low"
    assert r["safe_to_donate"]
    assert 5 < r["remaining_hours"] < 6
    assert r["pickup_deadline"] > NOW


def test_risk_rises_with_age():
    young = assess_freshness("curry_dal", hours_ago(1), 0.0, NOW)["risk_score"]
    old = assess_freshness("curry_dal", hours_ago(5), 0.0, NOW)["risk_score"]
    assert old > young


def test_past_shelf_life_is_critical_and_unsafe():
    r = assess_freshness("meat_egg_fish", hours_ago(5), 0.0, NOW)  # shelf life 4 h
    assert r["risk_score"] == 100
    assert r["risk_level"] == "critical"
    assert not r["safe_to_donate"]


def test_visibly_spoiled_food_is_rejected_even_when_recent():
    r = assess_freshness("baked", hours_ago(0.2), 0.95, NOW)
    assert r["risk_level"] == "critical"
    assert not r["safe_to_donate"]


def test_spoilage_shortens_window():
    clean = assess_freshness("breads", hours_ago(2), 0.0, NOW)["remaining_hours"]
    doubtful = assess_freshness("breads", hours_ago(2), 0.5, NOW)["remaining_hours"]
    assert doubtful < clean


def test_risk_level_bands():
    assert [risk_level(s) for s in (10, 40, 70, 90)] == ["low", "medium", "high", "critical"]


def test_quantity_check():
    plate = {"label": "1 plate / bowl", "min_servings": 1, "max_servings": 3}
    assert quantity_check(2, plate) is None
    assert "double-check" in quantity_check(50, plate)
    vessels = {"label": "many large vessels", "min_servings": 40, "max_servings": 200}
    assert "donate more" in quantity_check(5, vessels)


def test_old_food_alone_reaches_high_risk():
    # 5 of 6 safe hours used, photo looks fine -> must not be "medium"
    r = assess_freshness("curry_dal", hours_ago(5), 0.02, NOW)
    assert r["risk_level"] == "high"
    assert r["safe_to_donate"]  # still ~1 h left to collect it
