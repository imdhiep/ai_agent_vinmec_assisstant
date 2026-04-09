from fastapi import APIRouter

from app.models import BookingRequest, CopilotRequest
from app.services.booking import booking_service
from app.services.copilot import booking_copilot_service
from app.services.knowledge_base import knowledge_base


router = APIRouter(prefix="/api", tags=["api"])


@router.get("/bootstrap")
def bootstrap() -> dict:
    return {
        "facilities": [item.model_dump() for item in knowledge_base.get_facilities()],
        "departments": [item.model_dump() for item in knowledge_base.get_departments()],
        "doctors": [item.model_dump() for item in knowledge_base.get_doctors()],
    }


@router.post("/copilot/recommend")
def recommend(payload: CopilotRequest) -> dict:
    return booking_copilot_service.recommend(payload).model_dump()


@router.post("/booking/create")
def create_booking(payload: BookingRequest) -> dict:
    return booking_service.create_booking(payload)
