"""Registration and login for donors, NGOs and admins."""
from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.deps import get_current_user
from app.core.security import create_access_token
from app.core.utils import public_user
from app.schemas import RegisterIn
from app.services import accounts

router = APIRouter(prefix="/api/auth", tags=["auth"])


def token_response(user: dict) -> dict:
    return {
        "access_token": create_access_token(str(user["_id"]), user["role"]),
        "token_type": "bearer",
        "user": public_user(user),
    }


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(data: RegisterIn):
    return token_response(await accounts.register(data))


@router.post("/login")
async def login(form: OAuth2PasswordRequestForm = Depends()):
    """Log in with email (sent as `username`) and password."""
    return token_response(await accounts.authenticate(form.username, form.password))


@router.get("/me")
async def me(user: dict = Depends(get_current_user)):
    return public_user(user)
