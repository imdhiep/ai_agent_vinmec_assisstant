from datetime import datetime

from app.models import BookingRequest
from app.services.availability import availability_service
from app.services.knowledge_base import knowledge_base


class BookingService:
    def create_booking(self, payload: BookingRequest) -> dict:
        doctor = knowledge_base.get_doctor_by_id(payload.doctor_id) if payload.doctor_id else None
        department = knowledge_base.get_department_by_id(payload.department_id)
        facility = knowledge_base.get_facility_by_id(payload.facility_id)

        if not department or not facility:
            return {
                "status": "validation_error",
                "message": "Thông tin cơ sở hoặc chuyên khoa không hợp lệ.",
            }

        if payload.slot_id:
            slot = availability_service.get_slot_by_id(payload.slot_id)
            if not slot or slot.status != "available":
                return {
                    "status": "slot_conflict",
                    "message": "Khung giờ vừa được đặt hoặc không còn khả dụng. Vui lòng chọn slot khác.",
                }
        else:
            ranked = availability_service.get_ranked_recommendations(
                department_id=payload.department_id,
                facility_id=payload.facility_id,
                preferred_doctor_id=payload.doctor_id,
                patient_gender=payload.gender,
            )
            first_available = next((item for item in ranked if item["available"]), None)
            if not first_available:
                return {
                    "status": "needs_confirmation",
                    "message": (
                        "Hiện chưa có bác sĩ trống lịch ngay. "
                        "Vui lòng chọn slot gần nhất hoặc để tổng đài liên hệ xác nhận."
                    ),
                    "alternatives": ranked[:3],
                }
            slot = availability_service.get_slot_by_id(first_available["next_slot"]["id"])
            doctor = knowledge_base.get_doctor_by_id(first_available["doctor_id"])

        return {
            "status": "confirmed",
            "message": "Yêu cầu đặt lịch đã được tạo thành công.",
            "booking": {
                "patient_name": payload.patient_name,
                "facility": facility.name,
                "department": department.name,
                "doctor": doctor.name if doctor else "Sẽ xác nhận sau",
                "start_at": slot.start_at if slot else None,
                "fee": slot.consultation_fee if slot else None,
                "symptom_summary": payload.symptom_text,
                "note": "AI hỗ trợ điều hướng đặt khám, không thay thế chẩn đoán lâm sàng.",
                "created_at": datetime.utcnow().isoformat(),
            },
        }


booking_service = BookingService()
