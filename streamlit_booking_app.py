from __future__ import annotations

import base64
import os
import unicodedata
from datetime import date, datetime
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from app.config import BASE_DIR
from app.services.catalog_repository import catalog_repository
from app.services.github_models import (
    DEFAULT_BASE_URL,
    DEFAULT_MODEL,
    ask_booking_agent,
    build_client,
)


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


@st.cache_data(show_spinner=False)
def read_triage_map() -> list[dict]:
    import json

    return json.loads(TRIAGE_MAP_PATH.read_text(encoding="utf-8"))


def normalize(text: str) -> str:
    lowered = " ".join(text.lower().strip().split())
    normalized = unicodedata.normalize("NFD", lowered)
    normalized = "".join(char for char in normalized if unicodedata.category(char) != "Mn")
    return normalized.replace("đ", "d")


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


def render_shell() -> None:
    logo_b64 = to_base64(ASSET_DIR / "Logo_Vinmec_System_c725c14ffd.png")
    cover_b64 = to_base64(ASSET_DIR / "cover_list_doctor_f60bffe168.jpg")
    phone_b64 = to_base64(ASSET_DIR / "Phone.svg")
    calendar_b64 = to_base64(ASSET_DIR / "calendar(1).svg")
    doctor_b64 = to_base64(ASSET_DIR / "doctor.svg")

    st.markdown(
        f"""
        <div class="vm-topbar">
          <div class="vm-topbar-inner">
            <div class="vm-topbar-brand">
              <img src="data:image/png;base64,{logo_b64}" alt="Vinmec">
              <div>
                <div class="vm-topbar-small">Vinmec Healthcare System</div>
                <div class="vm-topbar-title">Đăng ký khám</div>
              </div>
            </div>
            <div class="vm-topbar-links">
              <span>Gọi tổng đài</span>
              <span>Đặt lịch hẹn</span>
            </div>
          </div>
        </div>
        <div class="vm-breadcrumb">Trang chủ / Đăng ký khám</div>
        <div class="vm-cover-wrap">
          <img class="vm-cover-image" src="data:image/jpeg;base64,{cover_b64}" alt="Đăng ký khám">
          <div class="vm-cover-overlay">
            <div class="vm-cover-title">Đăng ký khám</div>
          </div>
        </div>
        <div class="vm-shortcuts">
          <div class="vm-shortcut">
            <img src="data:image/svg+xml;base64,{phone_b64}" alt="Gọi tổng đài">
            <span>Gọi tổng đài</span>
          </div>
          <div class="vm-shortcut active">
            <img src="data:image/svg+xml;base64,{calendar_b64}" alt="Đặt lịch hẹn">
            <span>Đặt lịch hẹn</span>
          </div>
          <div class="vm-shortcut">
            <img src="data:image/svg+xml;base64,{doctor_b64}" alt="Tìm bác sĩ">
            <span>Tìm bác sĩ</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def sidebar_settings() -> tuple[str | None, str, str]:
    st.sidebar.header("Cấu hình agent")
    st.sidebar.caption("Tùy chọn này chỉ dùng khi bạn muốn bật AI agent qua GitHub Models.")
    token = st.sidebar.text_input(
        "GitHub Models token",
        type="password",
        value=st.secrets.get("GITHUB_MODELS_TOKEN", os.getenv("GITHUB_MODELS_TOKEN", "")),
    )
    base_url = st.sidebar.text_input(
        "Base URL",
        value=st.secrets.get("GITHUB_MODELS_BASE_URL", os.getenv("GITHUB_MODELS_BASE_URL", DEFAULT_BASE_URL)),
    )
    model_name = st.sidebar.text_input(
        "Model",
        value=st.secrets.get("GITHUB_MODELS_MODEL", os.getenv("GITHUB_MODELS_MODEL", DEFAULT_MODEL)),
    )
    st.sidebar.divider()
    st.sidebar.subheader("Database đã crawl")
    status = catalog_repository.get_status()
    if status:
        st.sidebar.write(f"Lần crawl cuối: {status.get('finished_at', '')}")
        st.sidebar.write(f"Cơ sở: {status.get('facility_count', 0)}")
        st.sidebar.write(f"Chuyên khoa: {status.get('specialty_count', 0)}")
        st.sidebar.write(f"Bác sĩ: {status.get('doctor_count', 0)}")
        st.sidebar.write(f"Slot: {status.get('slot_count', 0)}")
    else:
        st.sidebar.warning("Chưa có dữ liệu trong database.")
    st.sidebar.info("Chạy một lần: `python crawl/run_once.py`")
    return token or None, base_url, model_name


def is_booking_related(text: str) -> bool:
    normalized = normalize(text)
    keywords = ["dat lich", "kham", "bac si", "chuyen khoa", "lich", "co so", "vinmec"]
    return any(keyword in normalized for keyword in keywords) or len(normalized.split()) >= 3


def detect_red_flag(text: str) -> bool:
    normalized = normalize(text)
    return any(normalize(keyword) in normalized for keyword in RED_FLAG_KEYWORDS)


def infer_specialty(reason: str, specialties: list[dict]) -> tuple[dict | None, float, list[str]]:
    normalized = normalize(reason)
    if not is_booking_related(reason):
        return None, 0.0, []

    scored_titles: list[tuple[str, int]] = []
    for rule in read_triage_map():
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
    if not best_specialty or confidence < 0.70:
        follow_ups = [
            "Triệu chứng xuất hiện ở vị trí nào trên cơ thể?",
            "Bạn muốn khám cho người lớn, trẻ em hay thai phụ?",
            "Bạn ưu tiên cơ sở nào của Vinmec?",
        ]
    return best_specialty, confidence, follow_ups


def format_doctor_label(doctor: dict) -> str:
    subheading = f" - {doctor['subheading']}" if doctor.get("subheading") else ""
    return f"{doctor.get('heading', 'Bác sĩ')}{subheading}"


def format_slot(slot: dict) -> str:
    start_time = slot.get("start_time") or ""
    if "T" in start_time:
        return datetime.fromisoformat(start_time).strftime("%H:%M - %d/%m/%Y")
    return start_time


def rank_doctors_with_slots(facility_id: str, specialty_id: str) -> list[dict]:
    doctors = catalog_repository.get_doctors(facility_id, specialty_id)
    ranked = []
    for doctor in doctors:
        slots = catalog_repository.get_slots(facility_id, specialty_id, doctor["id"])
        ranked.append(
            {
                **doctor,
                "slots": slots,
                "slot_count": len(slots),
                "first_slot": slots[0] if slots else None,
            }
        )
    ranked.sort(key=lambda item: (-item["slot_count"], item["heading"]))
    return ranked


def render_recommendation(
    reason: str,
    selected_facility: dict,
    specialties: list[dict],
    token: str | None,
    base_url: str,
    model_name: str,
) -> tuple[dict | None, list[dict]]:
    if not reason.strip():
        st.warning("Vui lòng nhập lý do khám hoặc triệu chứng.")
        return None, []
    if not is_booking_related(reason):
        st.info("Tôi chỉ hỗ trợ đặt lịch khám và điều hướng chuyên khoa. Vui lòng mô tả triệu chứng, cơ sở muốn khám hoặc thời gian mong muốn đặt lịch.")
        return None, []
    if detect_red_flag(reason):
        st.markdown(
            '<div class="vm-alert-danger"><strong>Dấu hiệu khẩn cấp:</strong> Triệu chứng bạn mô tả có thể cần cấp cứu. Vui lòng đến cơ sở cấp cứu gần nhất hoặc liên hệ nhân viên hỗ trợ ngay.</div>',
            unsafe_allow_html=True,
        )
        return None, []

    suggested_specialty, confidence, follow_ups = infer_specialty(reason, specialties)
    if not suggested_specialty:
        st.markdown('<div class="vm-alert-warning">Chưa đủ thông tin để điều hướng an toàn.</div>', unsafe_allow_html=True)
        for question in follow_ups:
            st.write(f"- {question}")
        return None, []

    ranked = rank_doctors_with_slots(selected_facility["id"], suggested_specialty["id"])
    if token:
        client = build_client(token, base_url)
        answer = ask_booking_agent(
            client=client,
            user_message=reason,
            catalog_context={
                "co_so": selected_facility,
                "chuyen_khoa": suggested_specialty,
                "bac_si": [{k: v for k, v in item.items() if k != "slots"} for item in ranked[:5]],
            },
            model=model_name,
        )
        if answer:
            st.markdown('<div class="vm-agent-box"><strong>Gợi ý từ agent</strong></div>', unsafe_allow_html=True)
            st.info(answer)

    st.markdown(
        f"""
        <div class="vm-recommend-box">
          <div class="vm-chip">Gợi ý chuyên khoa</div>
          <h3>{suggested_specialty['title']}</h3>
          <p>Độ tin cậy ước tính: <strong>{confidence:.0%}</strong></p>
          <p>AI hỗ trợ điều hướng đặt khám, không thay thế chẩn đoán lâm sàng.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if confidence < 0.70:
        st.markdown('<div class="vm-alert-warning">Cần xác nhận thêm trước khi chốt lịch.</div>', unsafe_allow_html=True)
        for question in follow_ups:
            st.write(f"- {question}")
    return suggested_specialty, ranked


def render_doctors(ranked_doctors: list[dict]) -> None:
    if not ranked_doctors:
        st.markdown('<div class="vm-alert-warning">Chưa có bác sĩ phù hợp trong database cho lựa chọn hiện tại.</div>', unsafe_allow_html=True)
        return
    st.markdown("#### Bác sĩ gợi ý")
    for doctor in ranked_doctors[:4]:
        price = doctor.get("price") or {}
        fee = price.get("local")
        next_slot = format_slot(doctor["first_slot"]) if doctor["first_slot"] else "Tạm hết lịch"
        st.markdown(
            f"""
            <div class="vm-doctor-card">
              <div class="vm-doctor-name">{format_doctor_label(doctor)}</div>
              <div class="vm-doctor-meta">{doctor.get('subheading') or 'Thông tin chuyên môn đang được cập nhật'}</div>
              <div class="vm-doctor-grid">
                <span>Lịch trống: <strong>{doctor['slot_count']}</strong></span>
                <span>Slot gần nhất: <strong>{next_slot}</strong></span>
                <span>Phí khám dự kiến: <strong>{f"{fee:,} VND".replace(",", ".") if fee else "Liên hệ xác nhận"}</strong></span>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def run() -> None:
    st.set_page_config(page_title="Đăng ký khám | Vinmec", page_icon="🏥", layout="wide", initial_sidebar_state="expanded")
    inject_styles()
    render_shell()
    token, base_url, model_name = sidebar_settings()

    facilities = catalog_repository.get_facilities()
    if not facilities:
        st.error("Database hiện chưa có dữ liệu. Hãy chạy `python crawl/run_once.py` trước.")
        return

    left_col, right_col = st.columns([1.55, 1.0], gap="large")

    with left_col:
        st.markdown('<div class="vm-section-title">Nội dung chi tiết đặt hẹn</div>', unsafe_allow_html=True)
        facility_map = {item["title"]: item for item in facilities}
        facility_title = st.selectbox("Bệnh viện/phòng khám Vinmec", list(facility_map.keys()))
        selected_facility = facility_map[facility_title]

        specialties = catalog_repository.get_specialties_by_facility(selected_facility["id"])
        specialty_title_map = {item["title"]: item for item in specialties}

        reason = st.text_area("Lý do khám", placeholder="Triệu chứng của bạn", height=150)

        age_col, gender_col = st.columns(2)
        with age_col:
            st.number_input("Tuổi", min_value=0, max_value=120, value=30, key="age_input")
        with gender_col:
            st.selectbox("Giới tính", ["Nam", "Nữ", "Khác"], key="gender_input")

        if st.button("Phân tích và gợi ý lịch khám", type="primary", use_container_width=True):
            suggested_specialty, ranked_doctors = render_recommendation(
                reason,
                selected_facility,
                specialties,
                token,
                base_url,
                model_name,
            )
            if suggested_specialty:
                st.session_state["suggested_specialty_title"] = suggested_specialty["title"]

        specialty_options = ["Chưa xác định chuyên khoa"] + list(specialty_title_map.keys())
        default_specialty = st.session_state.get("suggested_specialty_title", "Chưa xác định chuyên khoa")
        chosen_specialty_title = st.selectbox(
            "Chuyên khoa",
            specialty_options,
            index=specialty_options.index(default_specialty) if default_specialty in specialty_options else 0,
        )

        selected_specialty = None
        ranked_doctors = []
        if chosen_specialty_title != "Chưa xác định chuyên khoa":
            selected_specialty = specialty_title_map[chosen_specialty_title]
            ranked_doctors = rank_doctors_with_slots(selected_facility["id"], selected_specialty["id"])
            render_doctors(ranked_doctors)

        doctor_option_map = {format_doctor_label(item): item for item in ranked_doctors}
        chosen_doctor_label = st.selectbox("Bác sĩ", ["Chưa chọn bác sĩ"] + list(doctor_option_map.keys()))
        selected_doctor = doctor_option_map.get(chosen_doctor_label)

        doctor_slots = selected_doctor["slots"] if selected_doctor else []
        slot_option_map = {format_slot(item): item for item in doctor_slots}
        chosen_slot_label = st.selectbox(
            "Thời gian khám",
            ["Tự động chọn slot sớm nhất"] + list(slot_option_map.keys()) if doctor_slots else ["Chưa có slot"],
        )

        st.markdown('<div class="vm-section-title second">Thông tin khách hàng</div>', unsafe_allow_html=True)
        patient_name = st.text_input("Họ và tên")
        phone = st.text_input("Số điện thoại")
        birth_date = st.date_input("Ngày tháng năm sinh", value=date(1995, 1, 1))
        email = st.text_input("Email")
        agree = st.checkbox("Tôi đã đọc và đồng ý với Chính sách bảo vệ dữ liệu cá nhân của Vinmec.")
        st.caption("*Lưu ý: Tổng đài viên Vinmec sẽ gọi lại cho quý khách để xác nhận thông tin thời gian dựa theo đăng ký và điều chỉnh nếu cần thiết.")

        if st.button("Gửi thông tin", type="primary", use_container_width=True):
            if not agree:
                st.error("Bạn cần đồng ý chính sách dữ liệu cá nhân trước khi gửi.")
            elif not patient_name or not phone or not reason:
                st.error("Vui lòng nhập đủ họ tên, số điện thoại và lý do khám.")
            elif detect_red_flag(reason):
                st.error("Trường hợp này có dấu hiệu khẩn cấp, không thể tiếp tục đặt lịch tự động.")
            elif not selected_specialty:
                st.error("Vui lòng chọn chuyên khoa trước khi gửi.")
            else:
                selected_slot = slot_option_map.get(chosen_slot_label) if chosen_slot_label in slot_option_map else (doctor_slots[0] if doctor_slots else None)
                catalog_repository.save_booking_request(
                    {
                        "patient_name": patient_name,
                        "phone": phone,
                        "birth_date": birth_date.isoformat(),
                        "gender": st.session_state.get("gender_input", "Khác"),
                        "email": email,
                        "facility_id": selected_facility["id"],
                        "specialty_id": selected_specialty["id"],
                        "doctor_id": selected_doctor["id"] if selected_doctor else None,
                        "slot_id": selected_slot["id"] if selected_slot else None,
                        "symptom_text": reason,
                    }
                )

                if selected_doctor and selected_slot:
                    st.success("Đã tạo yêu cầu đặt lịch thành công.")
                    st.markdown(
                        f"""
                        <div class="vm-confirm-card">
                          <h3>Thông tin xác nhận</h3>
                          <p><strong>Khách hàng:</strong> {patient_name}</p>
                          <p><strong>Cơ sở:</strong> {selected_facility['title']}</p>
                          <p><strong>Chuyên khoa:</strong> {selected_specialty['title']}</p>
                          <p><strong>Bác sĩ:</strong> {format_doctor_label(selected_doctor)}</p>
                          <p><strong>Khung giờ:</strong> {format_slot(selected_slot)}</p>
                          <p><strong>Email:</strong> {email or 'Chưa cung cấp'}</p>
                          <p><strong>Ghi chú:</strong> AI hỗ trợ điều hướng đặt khám, không thay thế chẩn đoán lâm sàng.</p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                else:
                    st.warning("Đã lưu yêu cầu nhưng chưa chốt được bác sĩ hoặc slot cụ thể.")
                    st.write("- Đổi sang bác sĩ khác cùng chuyên khoa.")
                    st.write("- Chọn cơ sở Vinmec khác.")
                    st.write("- Để tổng đài viên gọi lại xác nhận lịch phù hợp.")

    with right_col:
        st.markdown(
            f"""
            <div class="vm-side-card">
              <h3>Thông tin cơ sở</h3>
              <p><strong>{selected_facility['title']}</strong></p>
              <p>{selected_facility.get('address') or 'Địa chỉ đang cập nhật'}</p>
              <p>{selected_facility.get('city') or ''}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            <div class="vm-side-card">
              <h3>Phạm vi hỗ trợ</h3>
              <ul>
                <li>Chỉ hỗ trợ đặt khám, điều hướng chuyên khoa, bác sĩ, cơ sở và giờ khám.</li>
                <li>Không chẩn đoán bệnh và không tư vấn điều trị.</li>
                <li>Nếu bác sĩ hết lịch, hệ thống sẽ đề xuất phương án thay thế.</li>
                <li>Dữ liệu hiện tại được đọc từ database SQLite đã crawl trước đó.</li>
              </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )
        db_status = catalog_repository.get_status()
        st.markdown(
            f"""
            <div class="vm-side-card">
              <h3>Dữ liệu đã crawl</h3>
              <p><strong>Lần cập nhật cuối:</strong> {db_status.get('finished_at', 'Chưa có')}</p>
              <p><strong>Số cơ sở:</strong> {db_status.get('facility_count', 0)}</p>
              <p><strong>Số chuyên khoa:</strong> {db_status.get('specialty_count', 0)}</p>
              <p><strong>Số bác sĩ:</strong> {db_status.get('doctor_count', 0)}</p>
              <p><strong>Số slot:</strong> {db_status.get('slot_count', 0)}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
