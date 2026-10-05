"""Request/response schemas."""
import re
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

DonorType = Literal["household", "restaurant", "hotel", "caterer", "event"]
OrgType = Literal["ngo", "shelter", "community_kitchen"]
FoodCategory = Literal["veg", "non_veg"]

# Pickup lifecycle (synopsis §7.5): Listed -> Matched -> Picked Up -> Delivered
# "rejected" = AI judged the food unsafe at submission time
LISTING_STATUSES = ("listed", "matched", "picked_up", "delivered", "expired", "cancelled", "rejected")

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: str
    password: str = Field(min_length=6, max_length=72)  # bcrypt limit
    phone: str = Field(min_length=10, max_length=15)
    role: Literal["donor", "ngo"]

    # Donor-only
    donor_type: DonorType | None = None

    # NGO-only
    org_type: OrgType | None = None
    address: str | None = Field(None, max_length=200)
    lat: float | None = Field(None, ge=-90, le=90)
    lng: float | None = Field(None, ge=-180, le=180)
    capacity_meals: int | None = Field(None, ge=1, le=10_000)
    veg_only: bool = False

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        v = v.strip().lower()
        if not EMAIL_RE.match(v):
            raise ValueError("Enter a valid email address")
        return v

    @model_validator(mode="after")
    def check_role_fields(self):
        if self.role == "donor" and self.donor_type is None:
            self.donor_type = "household"
        if self.role == "ngo":
            missing = [f for f in ("org_type", "address", "lat", "lng", "capacity_meals")
                       if getattr(self, f) in (None, "")]
            if missing:
                raise ValueError(f"NGO registration needs: {', '.join(missing)}")
        return self
