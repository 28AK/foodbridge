"""Spoilage risk score and pickup window.

Combines two signals:
  * time risk   – fraction of the category's safe shelf life already used (0-1)
  * visual risk – CLIP's probability that the photo shows spoiled food (0-1)

risk = 1 - (1 - time) * (1 - visual)
i.e. the chance that *either* signal says the food is going bad, so old food or
spoiled-looking food each push the score up on their own.
"""
from datetime import datetime, timedelta

from app.services.food_catalog import CATEGORIES

VISUAL_SPOILED_FLAG = 0.8     # visual spoilage this confident forces a critical score
MIN_PICKUP_HOURS = 0.5        # less time than this left -> not worth dispatching
QUANTITY_MISMATCH_FACTOR = 3  # declared servings this many times off the AI estimate


def risk_level(score: float) -> str:
    if score < 35:
        return "low"
    if score < 60:
        return "medium"
    if score < 85:
        return "high"
    return "critical"


def assess_freshness(category: str, prepared_at: datetime, spoiled_probability: float,
                     now: datetime) -> dict:
    cat = CATEGORIES[category]
    shelf = cat["shelf_hours"]
    age_hours = max((now - prepared_at).total_seconds() / 3600, 0.0)
    time_ratio = age_hours / shelf

    time_risk = min(time_ratio, 1.0)
    score = (1 - (1 - time_risk) * (1 - spoiled_probability)) * 100

    reasons = [f"Prepared {age_hours:.1f} h ago; {cat['name'].lower()} stay safe for about {shelf} h"]
    if spoiled_probability >= VISUAL_SPOILED_FLAG:
        score = max(score, 85)
        reasons.append(f"Photo looks spoiled ({spoiled_probability:.0%} confidence)")
    if time_ratio >= 1:
        score = 100
        reasons.append("Safe shelf life has passed")

    # Visible spoilage shortens the remaining window
    remaining = max(shelf - age_hours, 0.0) * (1 - 0.5 * spoiled_probability)
    level = risk_level(score)
    safe = level != "critical" and remaining >= MIN_PICKUP_HOURS

    return {
        "risk_score": round(score),
        "risk_level": level,
        "food_age_hours": round(age_hours, 2),
        "shelf_life_hours": shelf,
        "remaining_hours": round(remaining, 2),
        "pickup_deadline": now + timedelta(hours=remaining),
        "safe_to_donate": safe,
        "reasons": reasons,
    }


def quantity_check(declared: int, estimate: dict) -> str | None:
    """Warning text if the donor's servings look far off the AI estimate."""
    low, high = estimate["min_servings"], estimate["max_servings"]
    if declared > high * QUANTITY_MISMATCH_FACTOR:
        return (f"You entered {declared} servings but the photo looks like {estimate['label']} "
                f"(~{low}-{high}). Please double-check the quantity.")
    if declared * QUANTITY_MISMATCH_FACTOR < low:
        return (f"You entered {declared} servings but the photo looks like {estimate['label']} "
                f"(~{low}-{high}). You may be able to donate more.")
    return None
