from typing import Literal, Optional

from pydantic import BaseModel, Field


class Facility(BaseModel):
    id: str
    name: str
    city: str
    hotline: str
    address: str


class Department(BaseModel):
    id: str
    name: str
    aliases: list[str] = Field(default_factory=list)
    symptom_keywords: list[str] = Field(default_factory=list)


class Doctor(BaseModel):
    id: str
    name: str
    title: str
    department_id: str
    facility_ids: list[str]
    specialties: list[str]
    bio: str
    languages: list[str] = Field(default_factory=list)
    gender_focus: Optional[Literal["male", "female", "all"]] = "all"


class ScheduleSlot(BaseModel):
    id: str
    doctor_id: str
    facility_id: str
    start_at: str
    end_at: str
    status: Literal["available", "held", "booked", "unavailable"]
    consultation_fee: int


class BookingRequest(BaseModel):
    facility_id: str
    department_id: str
    doctor_id: Optional[str] = None
    slot_id: Optional[str] = None
    patient_name: str
    gender: Literal["male", "female", "other"]
    phone: str
    birth_date: str
    email: Optional[str] = None
    symptom_text: str


class CopilotRequest(BaseModel):
    symptom_text: str
    gender: Optional[Literal["male", "female", "other"]] = None
    age: Optional[int] = None
    facility_id: Optional[str] = None
    preferred_date: Optional[str] = None
    preferred_doctor_id: Optional[str] = None


class CopilotResponse(BaseModel):
    status: Literal["recommended", "follow_up_required", "redirect_human", "emergency", "unrelated"]
    message: str
    disclaimer: str
    confidence: float
    suggested_department: Optional[Department] = None
    recommended_doctors: list[dict] = Field(default_factory=list)
    follow_up_questions: list[str] = Field(default_factory=list)
    fallback_options: list[str] = Field(default_factory=list)
