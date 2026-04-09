from app.models import CopilotRequest, CopilotResponse
from app.services.availability import availability_service
from app.services.triage import triage_service


DISCLAIMER = "AI hỗ trợ điều hướng đặt khám, không thay thế chẩn đoán lâm sàng."


class BookingCopilotService:
    def recommend(self, payload: CopilotRequest) -> CopilotResponse:
        triage = triage_service.analyze(payload.symptom_text)

        if triage.status == "unrelated":
            return CopilotResponse(
                status="unrelated",
                message=(
                    "Tôi chỉ hỗ trợ đặt lịch khám và điều hướng chuyên khoa. "
                    "Bạn vui lòng mô tả triệu chứng, cơ sở muốn khám hoặc thời gian mong muốn."
                ),
                disclaimer=DISCLAIMER,
                confidence=triage.confidence,
            )

        if triage.status == "emergency":
            return CopilotResponse(
                status="emergency",
                message=(
                    "Triệu chứng bạn mô tả có dấu hiệu nguy cấp. "
                    "Bạn cần đến cơ sở cấp cứu gần nhất hoặc liên hệ nhân viên hỗ trợ ngay."
                ),
                disclaimer=DISCLAIMER,
                confidence=triage.confidence,
                fallback_options=[
                    "Dừng quy trình đặt lịch tự động.",
                    "Liên hệ tổng đài Vinmec để được hướng dẫn khẩn.",
                ],
            )

        if triage.status == "follow_up_required":
            return CopilotResponse(
                status="follow_up_required",
                message="Cần thêm thông tin trước khi gợi ý lịch khám an toàn.",
                disclaimer=DISCLAIMER,
                confidence=triage.confidence,
                suggested_department=triage.department,
                follow_up_questions=triage.follow_up_questions,
            )

        recommendations = availability_service.get_ranked_recommendations(
            department_id=triage.department.id,
            facility_id=payload.facility_id,
            preferred_doctor_id=payload.preferred_doctor_id,
            patient_gender=payload.gender,
        )

        fallback_options = []
        if recommendations and not recommendations[0]["available"]:
            fallback_options = [
                "Chọn slot gần nhất của cùng bác sĩ.",
                "Đổi sang bác sĩ khác cùng chuyên khoa.",
                "Đổi sang cơ sở khác của Vinmec.",
                "Để tổng đài viên gọi lại xác nhận lịch.",
            ]

        return CopilotResponse(
            status="recommended",
            message=f"Gợi ý phù hợp nhất hiện tại là {triage.department.name}.",
            disclaimer=DISCLAIMER,
            confidence=triage.confidence,
            suggested_department=triage.department,
            recommended_doctors=recommendations[:5],
            fallback_options=fallback_options,
        )


booking_copilot_service = BookingCopilotService()
