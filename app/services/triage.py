from dataclasses import dataclass
import unicodedata

from app.models import Department
from app.services.knowledge_base import knowledge_base


RED_FLAG_KEYWORDS = {
    "đau ngực",
    "khó thở",
    "đột quỵ",
    "tê liệt",
    "co giật",
    "ngất",
    "bất tỉnh",
    "chảy máu nhiều",
    "không thở được",
}

BOOKING_RELATED_KEYWORDS = {
    "đặt lịch",
    "khám",
    "bác sĩ",
    "chuyên khoa",
    "giờ khám",
    "slot",
    "lịch trống",
    "cơ sở",
    "bệnh viện",
}


@dataclass
class TriageResult:
    status: str
    confidence: float
    department: Department | None
    reasons: list[str]
    follow_up_questions: list[str]


class TriageService:
    def analyze(self, symptom_text: str) -> TriageResult:
        normalized = self._normalize(symptom_text)

        if not self._is_booking_related(normalized):
            return TriageResult("unrelated", 0.0, None, [], [])

        if any(self._normalize(keyword) in normalized for keyword in RED_FLAG_KEYWORDS):
            return TriageResult(
                "emergency",
                1.0,
                None,
                ["Triệu chứng có dấu hiệu nguy cấp cần được ưu tiên cấp cứu."],
                [],
            )

        matches: list[tuple[Department, int]] = []
        for department in knowledge_base.get_departments():
            score = sum(1 for keyword in department.symptom_keywords if self._normalize(keyword) in normalized)
            score += sum(1 for alias in department.aliases if self._normalize(alias) in normalized)
            if score:
                matches.append((department, score))

        matches.sort(key=lambda item: item[1], reverse=True)
        if not matches:
            return TriageResult(
                "follow_up_required",
                0.42,
                None,
                ["Mô tả hiện tại chưa đủ để ánh xạ an toàn sang chuyên khoa."],
                [
                    "Triệu chứng xuất hiện ở vị trí nào trên cơ thể?",
                    "Bạn ưu tiên khám cho người lớn, trẻ em hay sản phụ?",
                    "Bạn muốn đặt lịch ở cơ sở nào của Vinmec?",
                ],
            )

        best_department, best_score = matches[0]
        confidence = min(0.55 + (best_score * 0.12), 0.95)
        if confidence < 0.70:
            return TriageResult(
                "follow_up_required",
                confidence,
                best_department,
                [f"Tạm thời nghiêng về {best_department.name} nhưng độ tự tin chưa cao."],
                [
                    "Bạn có thể mô tả rõ hơn triệu chứng chính và thời gian xuất hiện không?",
                    "Bạn có ưu tiên khám với bác sĩ nam hay nữ không?",
                    "Bạn muốn khám trong giờ hành chính hay slot gần nhất?",
                ],
            )

        return TriageResult(
            "recommended",
            confidence,
            best_department,
            [f"Triệu chứng phù hợp nhất với {best_department.name}."],
            [],
        )

    def _normalize(self, text: str) -> str:
        lowered = " ".join(text.lower().strip().split())
        normalized = unicodedata.normalize("NFD", lowered)
        normalized = "".join(char for char in normalized if unicodedata.category(char) != "Mn")
        normalized = normalized.replace("đ", "d")
        return normalized

    def _is_booking_related(self, normalized: str) -> bool:
        if any(self._normalize(keyword) in normalized for keyword in BOOKING_RELATED_KEYWORDS):
            return True

        if any(self._normalize(keyword) in normalized for keyword in RED_FLAG_KEYWORDS):
            return True

        for department in knowledge_base.get_departments():
            if any(self._normalize(keyword) in normalized for keyword in department.symptom_keywords):
                return True
            if any(self._normalize(alias) in normalized for alias in department.aliases):
                return True

        return False


triage_service = TriageService()
