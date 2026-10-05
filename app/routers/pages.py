"""HTML pages. Access control happens in the API; pages are static shells."""
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from app.config import get_settings

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory=get_settings().frontend_dir / "templates")


def render(request: Request, template: str):
    return templates.TemplateResponse(request, template)


@router.get("/")
async def index(request: Request):
    return render(request, "index.html")


@router.get("/login")
async def login_page(request: Request):
    return render(request, "login.html")


@router.get("/register")
async def register_page(request: Request):
    return render(request, "register.html")


@router.get("/donor")
async def donor_page(request: Request):
    return render(request, "donor.html")


@router.get("/ngo")
async def ngo_page(request: Request):
    return render(request, "ngo.html")


@router.get("/admin")
async def admin_page(request: Request):
    return render(request, "admin.html")
