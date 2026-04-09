from app.database.mock_db import db
from app.models import Department, Doctor, Facility, ScheduleSlot


class KnowledgeBaseService:
    def get_facilities(self) -> list[Facility]:
        return [Facility(**item) for item in db.facilities()]

    def get_departments(self) -> list[Department]:
        return [Department(**item) for item in db.departments()]

    def get_doctors(self) -> list[Doctor]:
        return [Doctor(**item) for item in db.doctors()]

    def get_schedules(self) -> list[ScheduleSlot]:
        return [ScheduleSlot(**item) for item in db.schedules()]

    def get_department_by_id(self, department_id: str) -> Department | None:
        return next((item for item in self.get_departments() if item.id == department_id), None)

    def get_doctor_by_id(self, doctor_id: str) -> Doctor | None:
        return next((item for item in self.get_doctors() if item.id == doctor_id), None)

    def get_facility_by_id(self, facility_id: str) -> Facility | None:
        return next((item for item in self.get_facilities() if item.id == facility_id), None)

    def get_doctors_by_department(self, department_id: str, facility_id: str | None = None) -> list[Doctor]:
        doctors = [doctor for doctor in self.get_doctors() if doctor.department_id == department_id]
        if facility_id:
            doctors = [doctor for doctor in doctors if facility_id in doctor.facility_ids]
        return doctors


knowledge_base = KnowledgeBaseService()
