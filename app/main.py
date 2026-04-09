from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import STATIC_DIR
from app.routes.api import router as api_router
from app.routes.pages import router as pages_router


app = FastAPI(title="Vinmec AI Patient Booking Copilot")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

app.include_router(pages_router)
app.include_router(api_router)
