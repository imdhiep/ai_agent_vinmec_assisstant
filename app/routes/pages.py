from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.config import TEMPLATES_DIR


templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
router = APIRouter(tags=["pages"])


@router.get("/", response_class=HTMLResponse)
def booking_page(request: Request):
    return templates.TemplateResponse(
        "booking.html",
        {
            "request": request,
            "page_title": "Dang ky kham | Vinmec AI Booking Copilot",
        },
    )
