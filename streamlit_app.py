from __future__ import annotations

import streamlit as st

from streamlit_booking_app import run as run_streamlit_booking_app

run_streamlit_booking_app()
st.stop()

import base64
import json
import os
import unicodedata
from datetime import datetime
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from app.config import BASE_DIR
from app.services.github_models import (
    DEFAULT_BASE_URL,
    DEFAULT_MODEL,
    ask_booking_agent,
    build_client,
)
from app.services.vinmec_live_catalog import crawl_live_catalog, load_catalog


ASSET_DIR = BASE_DIR / "Đăng ký khám _ Vinmec_files"
TRIAGE_MAP_PATH = BASE_DIR / "data" / "triage_map.json"
RED_FLAG_KEYWORDS = [
    "đau ngực",
    "khó thở",
    "đột quỵ",
    "co giật",
    "ngất",
    "bất tỉnh",
    "chảy máu nhiều",
    "liệt",
]

load_dotenv(BASE_DIR / ".env")


st.set_page_config(
    page_title="Đăng ký khám | Vinmec AI Patient Copilot",
    page_icon="🏥",
    layout="wide",
)


def inject_styles() -> None:
    css_chunks = []
    for name in ["reset.css", "css-shared.css", "non-critical-pc.css", "booking.css"]:
        css_path = ASSET_DIR / name
        if css_path.exists():
            css_chunks.append(css_path.read_text(encoding="utf-8", errors="ignore"))
    override_path = BASE_DIR / "streamlit_assets" / "overrides.css"
    css_chunks.append(override_path.read_text(encoding="utf-8"))
    st.markdown(f"<style>{''.join(css_chunks)}</style>", unsafe_allow_html=True)


def to_base64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("utf-8")


def render_header() -> None:
    logo_b64 = to_base64(ASSET_DIR / "Logo_Vinmec_System_c725c14ffd.png")
    cover_b64 = to_base64(ASSET_DIR / "cover_list_doctor_f60bffe168.jpg")
    phone_b64 = to_base64(ASSET_DIR / "Phone.svg")
    calendar_b64 = to_base64(ASSET_DIR / "calendar.svg")
    doctor_b64 = to_base64(ASSET_DIR / "doctor.svg")

    st.markdown(
        f"""
        <div class="vm-header">
          <div class="vm-header-left">
            <img class="vm-logo" src="data:image/png;base64,{logo_b64}" alt="Vinmec">
            <div>
              <p class="vm-eyebrow">Vinmec AI Patient Copilot</p>
              <h1 class="vm-title">Đăng ký khám thông minh bằng Streamlit</h1>
              <div class="vm-subtitle">
                Chỉ hỗ trợ đặt khám, gợi ý chuyên khoa, kiểm tra bác sĩ còn lịch và phương án thay thế nếu hết chỗ.
              </div>
            </div>
          </div>
        </div>
        <div class="vm-cover">
          <img src="data:image/jpeg;base64,{cover_b64}" alt="Đăng ký khám Vinmec">
        </div>
        <div class="vm-action-row">
          <div class="vm-action">
            <img src="data:image/svg+xml;base64,{phone_b64}" alt="Gọi tổng đài">
            <span>Gọi tổng đài</span>
          </div>
          <div class="vm-action">
            <img src="data:image/svg+xml;base64,{calendar_b64}" alt="Đặt lịch">
            <span>Đặt lịch hẹn</span>
          </div>
          <div class="vm-action">
            <img src="data:image/svg+xml;base64,{doctor_b64}" alt="Tìm bác sĩ">
            <span>Tìm bác sĩ</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(show_spinner=False)
def read_triage_map() -> list[dict]:
    return json.loads(TRIAGE_MAP_PATH.read_text(encoding="utf-8"))


def normalize(text: str) -> str:
    lowered = " ".join(text.lower().strip().split())
    normalized = unicodedata.normalize("NFD", lowered)
    normalized = "".join(char for char in normalized if unicodedata.category(char) != "Mn")
    normalized = normalized.replace("đ", "d")
    return normalized


def is_booking_related(text: str) -> bool:
    normalized = normalize(text)
    booking_words = ["đặt lịch", "khám", "bác sĩ", "chuyên khoa", "lịch trống", "cơ sở", "vinmec"]
    return any(word in normalized for word in booking_words) or len(normalized.split()) >= 3


def detect_red_flag(text: str) -> bool:
    normalized = normalize(text)
    return any(normalize(keyword) in normalized for keyword in RED_FLAG_KEYWORDS)


def infer_specialty(reason: str, specialties: list[dict]) -> tuple[dict | None, float, list[str]]:
    normalized = normalize(reason)
    if not is_booking_related(normalized):
        return None, 0.0, []

    triage_map = read_triage_map()
    scored_titles: list[tuple[str, int]] = []
    for rule in triage_map:
        score = sum(1 for keyword in rule["symptom_keywords"] if normalize(keyword) in normalized)
        if score:
            for title in rule["specialty_keywords"]:
                scored_titles.append((normalize(title), score))

    best_specialty = None
    best_score = 0
    for specialty in specialties:
        title = normalize(specialty["title"])
        score = 0
        for expected_title, title_score in scored_titles:
            if expected_title in title or title in expected_title:
                score += title_score
        if score > best_score:
            best_score = score
            best_specialty = specialty

    confidence = min(0.55 + best_score * 0.15, 0.95) if best_score else 0.35
    follow_ups = []
    if not best_specialty or confidence < 0.7:
        follow_ups = [
            "Triệu chứng xuất hiện ở vị trí nào trên cơ thể?",
            "Bạn muốn khám cho người lớn, trẻ em hay thai phụ?",
            "Bạn ưu tiên cơ sở nào của Vinmec?",
        ]
    return best_specialty, confidence, follow_ups


def build_catalog_indexes(catalog: dict) -> tuple[list[dict], list[dict], list[dict], list[dict]]:
    return (
        catalog.get("facilities", []),
        catalog.get("specialties", []),
        catalog.get("doctors", []),
        catalog.get("slots", []),
    )


def build_mock_catalog_from_json_files() -> dict:
    data_dir = BASE_DIR / "data"
    facilities = json.loads((data_dir / "facilities.json").read_text(encoding="utf-8"))
    departments = json.loads((data_dir / "departments.json").read_text(encoding="utf-8"))
    doctors = json.loads((data_dir / "doctors.json").read_text(encoding="utf-8"))
    schedules = json.loads((data_dir / "schedules.json").read_text(encoding="utf-8"))

    catalog_facilities = [
        {
            "id": item["id"],
            "title": item["name"],
            "city": item.get("city", ""),
            "address": item.get("address", ""),
        }
        for item in facilities
    ]

    catalog_specialties = []
    for facility in facilities:
        for department in departments:
            catalog_specialties.append(
                {
                    "id": f"{facility['id']}::{department['id']}",
                    "facility_id": facility["id"],
                    "department_id": department["id"],
                    "title": department["name"],
                    "ab_booking_enabled": True,
                }
            )

    catalog_doctors = []
    for doctor in doctors:
        for facility_id in doctor["facility_ids"]:
            specialty_id = f"{facility_id}::{doctor['department_id']}"
            catalog_doctors.append(
                {
                    "id": doctor["id"],
                    "facility_id": facility_id,
                    "specialty_id": specialty_id,
                    "heading": f"{doctor['title']} {doctor['name']}",
                    "subheading": ", ".join(doctor.get("specialties", [])[:2]),
                    "vinmec_website_id": doctor["id"],
                    "price": {"local": 450000, "foreigner": 650000},
                    "extra_price": {"local": 550000, "foreigner": 750000},
                    "ab_booking_enabled": True,
                }
            )

    catalog_slots = [
        {
            "id": item["id"],
            "doctor_id": item["doctor_id"],
            "specialty_id": f"{item['facility_id']}::{next((doctor['department_id'] for doctor in doctors if doctor['id'] == item['doctor_id']), '')}",
            "facility_id": item["facility_id"],
            "date": item["start_at"].split("T")[0],
            "start_time": item["start_at"],
            "end_time": item["end_at"],
            "extra_booking": False,
        }
        for item in schedules
        if item["status"] == "available"
    ]

    return {
        "generated_at": "mock",
        "source_url": "mock_json_files",
        "source": "mock_json_files",
        "facilities": catalog_facilities,
        "specialties": catalog_specialties,
        "doctors": catalog_doctors,
        "slots": catalog_slots,
    }


def get_specialties_by_facility(specialties: list[dict], facility_id: str) -> list[dict]:
    return [item for item in specialties if str(item.get("facility_id")) == str(facility_id)]


def get_doctors_by_filters(doctors: list[dict], facility_id: str, specialty_id: str) -> list[dict]:
    return [
        item for item in doctors
        if str(item.get("facility_id")) == str(facility_id)
        and str(item.get("specialty_id")) == str(specialty_id)
        and item.get("ab_booking_enabled", True)
    ]


def get_slots_by_doctor(slots: list[dict], facility_id: str, specialty_id: str, doctor_id: str) -> list[dict]:
    filtered = [
        item for item in slots
        if str(item.get("facility_id")) == str(facility_id)
        and str(item.get("specialty_id")) == str(specialty_id)
        and str(item.get("doctor_id")) == str(doctor_id)
    ]
    filtered.sort(key=lambda item: item.get("start_time") or "")
    return filtered


def format_doctor_label(doctor: dict) -> str:
    sub = f" - {doctor['subheading']}" if doctor.get("subheading") else ""
    return f"{doctor.get('heading', 'Bác sĩ')}{sub}"


def format_slot(slot: dict) -> str:
    start_time = slot.get("start_time") or ""
    if "T" in start_time:
        dt = datetime.fromisoformat(start_time)
        return dt.strftime("%H:%M - %d/%m/%Y")
    return start_time


def build_fallbacks(doctors: list[dict], slots: list[dict], facility_id: str, specialty_id: str, doctor_id: str) -> list[str]:
    options = []
    for doctor in doctors:
        doctor_slots = get_slots_by_doctor(slots, facility_id, specialty_id, str(doctor["id"]))
        if doctor_slots:
            options.append(f"{format_doctor_label(doctor)} còn lịch lúc {format_slot(doctor_slots[0])}.")
    if not options:
        options = [
            "Đổi sang bác sĩ khác cùng chuyên khoa tại cơ sở này.",
            "Đổi sang cơ sở Vinmec khác.",
            "Để tổng đài viên Vinmec gọi lại xác nhận lịch phù hợp.",
        ]
    return options[:4]


def render_agent_answer(
    reason: str,
    facility: dict | None,
    specialties: list[dict],
    doctors: list[dict],
    slots: list[dict],
    github_token: str | None,
    base_url: str,
    model_name: str,
) -> tuple[dict | None, list[dict], list[dict]]:
    if not reason.strip():
        st.warning("Vui lòng nhập triệu chứng hoặc lý do khám trước khi phân tích.")
        return None, [], []

    if not is_booking_related(reason):
        st.info("Tôi chỉ hỗ trợ đặt lịch khám và điều hướng chuyên khoa. Vui lòng mô tả triệu chứng, cơ sở muốn khám hoặc thời gian mong muốn.")
        return None, [], []

    if detect_red_flag(reason):
        st.markdown(
            '<div class="vm-danger"><strong>Dấu hiệu khẩn cấp:</strong> Triệu chứng bạn mô tả có thể là tình huống cấp cứu. Vui lòng đến cơ sở cấp cứu gần nhất hoặc liên hệ nhân viên hỗ trợ ngay. Luồng đặt lịch tự động sẽ tạm dừng.</div>',
            unsafe_allow_html=True,
        )
        return None, [], []

    selected_specialty, confidence, follow_ups = infer_specialty(reason, specialties)
    if selected_specialty is None:
        st.markdown(
            '<div class="vm-warning"><strong>Chưa đủ thông tin để điều hướng an toàn.</strong></div>',
            unsafe_allow_html=True,
        )
        for question in follow_ups:
            st.write(f"- {question}")
        return None, [], []

    filtered_doctors = get_doctors_by_filters(
        doctors,
        str(facility["id"]) if facility else "",
        str(selected_specialty["id"]),
    )
    ranked_doctors = sorted(
        filtered_doctors,
        key=lambda item: len(get_slots_by_doctor(slots, str(facility["id"]), str(selected_specialty["id"]), str(item["id"]))),
        reverse=True,
    )

    if github_token:
        client = build_client(github_token, base_url)
        model_answer = ask_booking_agent(
            client=client,
            user_message=reason,
            catalog_context={
                "cơ_sở": facility,
                "chuyên_khoa_đề_xuất": selected_specialty,
                "bác_sĩ_gợi_ý": ranked_doctors[:5],
            },
            model=model_name,
        )
        if model_answer:
            st.markdown("### Gợi ý từ agent")
            st.info(model_answer)

    st.markdown(
        f"""
        <div class="vm-card">
          <div class="vm-pill">Điều hướng đặt khám</div>
          <h4>Chuyên khoa phù hợp nhất: {selected_specialty['title']}</h4>
          <p class="vm-muted">Độ tin cậy ước tính: {confidence:.0%}</p>
          <div class="vm-highlight">AI hỗ trợ điều hướng đặt khám, không thay thế chẩn đoán lâm sàng.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if confidence < 0.7:
        st.markdown('<div class="vm-warning"><strong>Cần xác nhận thêm trước khi chốt lịch.</strong></div>', unsafe_allow_html=True)
        for question in follow_ups:
            st.write(f"- {question}")

    return selected_specialty, ranked_doctors, follow_ups


def sidebar_settings() -> tuple[str | None, str, str]:
    st.sidebar.header("Cấu hình agent")
    st.sidebar.caption("Bạn có thể dán GitHub Models token tại đây hoặc lưu vào `.env` / `.streamlit/secrets.toml`.")
    env_token = os.getenv("GITHUB_MODELS_TOKEN")
    secret_token = st.secrets.get("GITHUB_MODELS_TOKEN") if hasattr(st, "secrets") else None
    token = st.sidebar.text_input(
        "GitHub Models token",
        type="password",
        value=secret_token or env_token or "",
        help="Token GitHub Personal Access Token dùng để gọi model qua GitHub Models.",
    )
    base_url = st.sidebar.text_input(
        "Base URL",
        value=os.getenv("GITHUB_MODELS_BASE_URL", DEFAULT_BASE_URL),
    )
    model_name = st.sidebar.text_input(
        "Model",
        value=os.getenv("GITHUB_MODELS_MODEL", DEFAULT_MODEL),
    )
    st.sidebar.markdown(
        """
        Chỗ bạn tự nhập API:
        - Sidebar `GitHub Models token`
        - Hoặc file `.env` với biến `GITHUB_MODELS_TOKEN`
        - Hoặc file `.streamlit/secrets.toml`
        """
    )
    st.sidebar.caption("Khuyến nghị dùng GitHub Personal Access Token có quyền truy cập GitHub Models.")
    return token or None, base_url, model_name


def main() -> None:
    inject_styles()
    render_header()
    token, base_url, model_name = sidebar_settings()

    with st.sidebar:
        st.subheader("Dữ liệu Vinmec")
        st.caption("Ứng dụng ưu tiên đọc dữ liệu crawl thật từ website và API public của Vinmec.")
        if st.button("Làm mới dữ liệu từ website", use_container_width=True):
            with st.spinner("Đang crawl dữ liệu từ Vinmec..."):
                try:
                    crawl_live_catalog(days_ahead=3)
                    st.success("Đã cập nhật dữ liệu crawl từ website Vinmec.")
                except Exception as exc:
                    st.error(f"Không crawl được dữ liệu live: {exc}")

    catalog = load_catalog()
    if not catalog.get("specialties"):
        catalog = build_mock_catalog_from_json_files()
    facilities, specialties, doctors, slots = build_catalog_indexes(catalog)

    if not facilities:
        st.error("Chưa có dữ liệu cơ sở khám. Hãy chạy crawler hoặc kiểm tra file dữ liệu.")
        return

    col_left, col_right = st.columns([1.6, 1.0], gap="large")

    with col_left:
        st.markdown('<div class="vm-card"><h3>Nội dung chi tiết đặt hẹn</h3></div>', unsafe_allow_html=True)

        facility_map = {item["title"]: item for item in facilities}
        facility_title = st.selectbox("Bệnh viện/phòng khám Vinmec", list(facility_map.keys()))
        selected_facility = facility_map[facility_title]

        facility_specialties = get_specialties_by_facility(specialties, str(selected_facility["id"]))
        specialty_titles = ["Chưa xác định chuyên khoa"] + [item["title"] for item in facility_specialties]

        reason = st.text_area(
            "Triệu chứng / lý do khám",
            placeholder="Ví dụ: Tôi muốn đặt lịch khám vì đau bụng, buồn nôn và muốn khám sớm tại Hà Nội.",
            height=140,
        )

        age_col, gender_col = st.columns(2)
        with age_col:
            age = st.number_input("Tuổi", min_value=0, max_value=120, value=30)
        with gender_col:
            gender = st.selectbox("Giới tính", ["Nam", "Nữ", "Khác"])

        selected_specialty = None
        ranked_doctors = []
        if st.button("Phân tích và gợi ý lịch khám", type="primary", use_container_width=True):
            selected_specialty, ranked_doctors, _ = render_agent_answer(
                reason=reason,
                facility=selected_facility,
                specialties=facility_specialties,
                doctors=doctors,
                slots=slots,
                github_token=token,
                base_url=base_url,
                model_name=model_name,
            )
            if selected_specialty:
                st.session_state["specialty_title"] = selected_specialty["title"]
                st.session_state["doctor_options"] = [format_doctor_label(item) for item in ranked_doctors]
                st.session_state["recommended_specialty_id"] = selected_specialty["id"]

        default_specialty_title = st.session_state.get("specialty_title", specialty_titles[0])
        specialty_title = st.selectbox(
            "Chuyên khoa",
            specialty_titles,
            index=specialty_titles.index(default_specialty_title) if default_specialty_title in specialty_titles else 0,
        )

        if specialty_title != "Chưa xác định chuyên khoa":
            selected_specialty = next(item for item in facility_specialties if item["title"] == specialty_title)
            ranked_doctors = get_doctors_by_filters(doctors, str(selected_facility["id"]), str(selected_specialty["id"]))
        else:
            ranked_doctors = []

        doctor_label_map = {format_doctor_label(item): item for item in ranked_doctors}
        chosen_doctor_label = st.selectbox(
            "Bác sĩ",
            ["Chưa chọn bác sĩ"] + list(doctor_label_map.keys()),
        )
        chosen_doctor = doctor_label_map.get(chosen_doctor_label)

        slot_choices = []
        slot_map = {}
        if chosen_doctor and selected_specialty:
            available_slots = get_slots_by_doctor(
                slots,
                str(selected_facility["id"]),
                str(selected_specialty["id"]),
                str(chosen_doctor["id"]),
            )
            slot_choices = ["Tự động chọn slot sớm nhất"] + [format_slot(item) for item in available_slots]
            slot_map = {format_slot(item): item for item in available_slots}
        else:
            available_slots = []

        chosen_slot_label = st.selectbox("Thời gian khám", slot_choices if slot_choices else ["Chưa có slot"])

        st.markdown('<div class="vm-card"><h3>Thông tin khách hàng</h3></div>', unsafe_allow_html=True)
        patient_name = st.text_input("Họ và tên")
        phone = st.text_input("Số điện thoại")
        birth_date = st.date_input("Ngày tháng năm sinh")
        email = st.text_input("Email")
        agree = st.checkbox("Tôi đã đọc và đồng ý với chính sách bảo vệ dữ liệu cá nhân của Vinmec.")

        if st.button("Gửi thông tin đặt lịch", type="primary", use_container_width=True):
            if not agree:
                st.error("Bạn cần đồng ý chính sách dữ liệu cá nhân trước khi gửi.")
            elif not patient_name or not phone or not reason:
                st.error("Vui lòng nhập đủ họ tên, số điện thoại và lý do khám.")
            elif detect_red_flag(reason):
                st.error("Yêu cầu này có dấu hiệu khẩn cấp, không thể tiếp tục luồng đặt lịch tự động.")
            elif specialty_title == "Chưa xác định chuyên khoa":
                st.error("Vui lòng chọn hoặc phân tích để xác định chuyên khoa.")
            else:
                if chosen_doctor is None:
                    fallback_messages = build_fallbacks(
                        ranked_doctors,
                        slots,
                        str(selected_facility["id"]),
                        str(selected_specialty["id"]),
                        "",
                    )
                    st.warning("Bạn chưa chọn bác sĩ cụ thể. Hệ thống đề xuất các phương án gần nhất:")
                    for item in fallback_messages:
                        st.write(f"- {item}")
                else:
                    if available_slots:
                        chosen_slot = slot_map.get(chosen_slot_label) if chosen_slot_label in slot_map else available_slots[0]
                        st.success("Đã tạo yêu cầu đặt lịch thành công.")
                        st.markdown(
                            f"""
                            <div class="vm-card">
                              <h4>Thông tin xác nhận</h4>
                              <p><strong>Khách hàng:</strong> {patient_name}</p>
                              <p><strong>Cơ sở:</strong> {selected_facility['title']}</p>
                              <p><strong>Chuyên khoa:</strong> {selected_specialty['title']}</p>
                              <p><strong>Bác sĩ:</strong> {format_doctor_label(chosen_doctor)}</p>
                              <p><strong>Khung giờ:</strong> {format_slot(chosen_slot)}</p>
                              <p><strong>Ngày sinh:</strong> {birth_date.strftime('%d/%m/%Y')}</p>
                              <p><strong>Giới tính:</strong> {gender}</p>
                              <p><strong>Email:</strong> {email or 'Chưa cung cấp'}</p>
                              <div class="vm-highlight">AI hỗ trợ điều hướng đặt khám, không thay thế chẩn đoán lâm sàng.</div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                    else:
                        st.warning("Bác sĩ bạn chọn hiện chưa có slot trống.")
                        for item in build_fallbacks(
                            ranked_doctors,
                            slots,
                            str(selected_facility["id"]),
                            str(selected_specialty["id"]),
                            str(chosen_doctor["id"]),
                        ):
                            st.write(f"- {item}")

    with col_right:
        st.markdown(
            f"""
            <div class="vm-card">
              <h3>Phạm vi trả lời</h3>
              <ul>
                <li>Chỉ hỗ trợ đặt khám, điều hướng chuyên khoa, bác sĩ, cơ sở và giờ khám.</li>
                <li>Không chẩn đoán bệnh, không kê đơn, không tư vấn điều trị.</li>
                <li>Nếu bác sĩ hết lịch, hệ thống sẽ gợi ý slot gần nhất hoặc bác sĩ khác.</li>
                <li>Dữ liệu hiện tại lấy từ website và API public của Vinmec khi bạn bấm crawl.</li>
              </ul>
            </div>
            <div class="vm-card">
              <h3>Tình trạng dữ liệu</h3>
              <p><strong>Nguồn:</strong> {catalog.get('source', 'Không rõ')}</p>
              <p><strong>URL:</strong> {catalog.get('source_url', '')}</p>
              <p><strong>Ngày cập nhật:</strong> {catalog.get('generated_at') or 'Chưa crawl live'}</p>
              <p><strong>Số cơ sở:</strong> {len(facilities)}</p>
              <p><strong>Số chuyên khoa:</strong> {len(specialties)}</p>
              <p><strong>Số bác sĩ:</strong> {len(doctors)}</p>
              <p><strong>Số slot:</strong> {len(slots)}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


if __name__ == "__main__":
    main()
