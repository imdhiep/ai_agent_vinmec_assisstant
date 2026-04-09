from datetime import datetime

from app.models import Doctor, ScheduleSlot
from app.services.knowledge_base import knowledge_base


class AvailabilityService:
    def get_ranked_recommendations(
        self,
        department_id: str,
        facility_id: str | None = None,
        preferred_doctor_id: str | None = None,
        patient_gender: str | None = None,
    ) -> list[dict]:
        doctors = knowledge_base.get_doctors_by_department(department_id, facility_id)
        if patient_gender in {"male", "female"}:
            doctors = [
                doctor for doctor in doctors
                if doctor.gender_focus in {"all", patient_gender}
            ]
        schedules = knowledge_base.get_schedules()
        recommendations: list[dict] = []

        for doctor in doctors:
            doctor_slots = [
                slot for slot in schedules
                if slot.doctor_id == doctor.id and slot.status == "available"
            ]
            doctor_slots.sort(key=lambda slot: slot.start_at)
            next_slot = doctor_slots[0] if doctor_slots else None
            has_availability = next_slot is not None
            match_score = self._match_score(doctor, preferred_doctor_id, has_availability)

            recommendations.append(
                {
                    "doctor_id": doctor.id,
                    "doctor_name": doctor.name,
                    "title": doctor.title,
                    "bio": doctor.bio,
                    "specialties": doctor.specialties,
                    "match_score": match_score,
                    "available": has_availability,
                    "next_slot": next_slot.model_dump() if next_slot else None,
                    "fallback_label": self._fallback_label(doctor, next_slot),
                }
            )

        recommendations.sort(
            key=lambda item: (
                not item["available"],
                -item["match_score"],
                item["next_slot"]["start_at"] if item["next_slot"] else "9999-12-31T00:00:00",
            )
        )
        return recommendations

    def get_slot_by_id(self, slot_id: str) -> ScheduleSlot | None:
        return next((slot for slot in knowledge_base.get_schedules() if slot.id == slot_id), None)

    def _match_score(self, doctor: Doctor, preferred_doctor_id: str | None, has_availability: bool) -> int:
        score = 75
        score += 20 if has_availability else -25
        score += 15 if preferred_doctor_id and doctor.id == preferred_doctor_id else 0
        score += min(len(doctor.specialties) * 2, 10)
        return max(score, 0)

    def _fallback_label(self, doctor: Doctor, next_slot: ScheduleSlot | None) -> str:
        if next_slot:
            dt = datetime.fromisoformat(next_slot.start_at)
            return f"Còn lịch lúc {dt.strftime('%H:%M %d/%m/%Y')}"
        return f"{doctor.name} tạm hết lịch, cần gọi tổng đài hoặc chọn bác sĩ khác."


availability_service = AvailabilityService()
