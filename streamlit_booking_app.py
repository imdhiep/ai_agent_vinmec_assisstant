from __future__ import annotations

import base64
import json
import os
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st
from dotenv import load_dotenv

from app.config import BASE_DIR
from app.services.catalog_repository import catalog_repository
from app.services.github_models import DEFAULT_BASE_URL, DEFAULT_MODEL, build_client


ASSET_DIR = BASE_DIR / "Đăng ký khám _ Vinmec_files"
TRIAGE_MAP_PATH = BASE_DIR / "data" / "triage_map.json"
SYSTEM_PROMPT_PATH = BASE_DIR / "system prompt.txt"
DOCTOR_PRIORITY_LABELS = ["Top priority", "Alternative", "Backup"]
EMERGENCY_KEYWORDS = [
    "duoi nuoc",
    "ngung tho",
    "kho tho",
    "dau nguc",
    "bat tinh",
    "ngat",
    "co giat",
    "dot quy",
    "chay mau nhieu",
    "khong tho duoc",
]
INJURY_NEEDS_CLARIFICATION = [
    "nga xe",
    "truot chan",
    "te nga",
    "tai nan",
    "va dap",
    "chan thuong",
]
SPECIALTY_HINTS = {
    "Mắt": ["dau mat", "mo mat", "do mat", "cay mat", "ngua mat", "nhuc mat", "nhin mo"],
    "Tai - Mũi - Họng": ["dau hong", "viem hong", "nghet mui", "so mui", "dau tai", "u tai"],
    "Da liễu": ["noi man", "man ngua", "ngua da", "di ung da", "phat ban", "noi mun"],
    "Nội Tiêu hoá": ["dau bung", "buon non", "tieu chay", "tao bon", "day bung", "o chua"],
    "Nội Thận - Tiết niệu": ["tieu buot", "tieu rat", "dau hong lung", "tieu dem"],
    "Sản phụ khoa": ["ra huyet", "kinh nguyet", "mang thai", "dau bung duoi", "phu khoa"],
    "Nam khoa": ["sinh ly nam", "duong vat", "tinh hoan"],
    "Hô hấp": ["ho", "viem phoi", "dau tuc nguc khi tho"],
    "Nội thần kinh": ["dau dau", "chong mat", "te tay", "mat ngu", "run tay"],
    "Răng - Hàm - Mặt": ["dau rang", "sung loi", "sau rang", "nhuc rang"],
}

load_dotenv(BASE_DIR / ".env")


@st.cache_data(show_spinner=False)
def read_triage_map() -> list[dict[str, Any]]:
    return json.loads(TRIAGE_MAP_PATH.read_text(encoding="utf-8"))


@st.cache_data(show_spinner=False)
def get_asset_b64(filename: str) -> str:
    return base64.b64encode((ASSET_DIR / filename).read_bytes()).decode("utf-8")


def get_secret(name: str, default: str = "") -> str:
    try:
        return st.secrets.get(name, default)
    except Exception:
        return default


def normalize(text: str) -> str:
    lowered = " ".join(text.lower().strip().split())
    normalized = unicodedata.normalize("NFD", lowered)
    normalized = "".join(char for char in normalized if unicodedata.category(char) != "Mn")
    return normalized.replace("đ", "d")


def normalize(text: str) -> str:
    lowered = " ".join(text.lower().strip().split())
    normalized = unicodedata.normalize("NFD", lowered)
    normalized = "".join(char for char in normalized if unicodedata.category(char) != "Mn")
    normalized = normalized.replace("đ", "d")
    normalized = normalized.replace("Ä‘", "d")
    return normalized


def get_runtime_config() -> tuple[str | None, str, str]:
    token = get_secret("GITHUB_MODELS_TOKEN", os.getenv("GITHUB_MODELS_TOKEN", ""))
    base_url = get_secret("GITHUB_MODELS_BASE_URL", os.getenv("GITHUB_MODELS_BASE_URL", DEFAULT_BASE_URL))
    model_name = get_secret("GITHUB_MODELS_MODEL", os.getenv("GITHUB_MODELS_MODEL", DEFAULT_MODEL))
    return token or None, base_url, model_name


def detect_emergency(normalized: str) -> bool:
    return any(keyword in normalized for keyword in EMERGENCY_KEYWORDS)


def needs_injury_follow_up(normalized: str) -> bool:
    return any(keyword in normalized for keyword in INJURY_NEEDS_CLARIFICATION)


def infer_urgency_level(normalized: str) -> str:
    if detect_emergency(normalized):
        return "critical"
    if any(keyword in normalized for keyword in ["sot cao", "non nhieu", "dau du doi", "kho chiu tang dan"]):
        return "high"
    if any(keyword in normalized for keyword in ["dau", "sung", "rat", "ngua", "ho", "met moi keo dai"]):
        return "medium"
    return "low"


def inject_styles() -> None:
    css_chunks: list[str] = []
    for name in ["reset.css", "css-shared.css", "non-critical-pc.css", "booking.css"]:
        css_path = ASSET_DIR / name
        if css_path.exists():
            css_chunks.append(css_path.read_text(encoding="utf-8", errors="ignore"))

    css_chunks.append(
        """
        .main .block-container {
          max-width: 1120px;
          padding-top: 0.75rem;
          padding-bottom: 2rem;
        }
        [data-testid="stAppViewContainer"] {
          background: linear-gradient(180deg, #f4f8fc 0%, #fbfdff 100%);
        }
        [data-testid="stSidebar"] {
          display: none;
        }
        .vm-topbar {
          background: #ffffff;
          border: 1px solid #dfe7ee;
          border-radius: 22px;
          box-shadow: 0 16px 40px rgba(8, 60, 92, 0.08);
          padding: 18px 22px;
          margin-bottom: 18px;
        }
        .vm-topbar-inner {
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 14px;
        }
        .vm-topbar-brand {
          display: flex;
          align-items: center;
          gap: 16px;
        }
        .vm-topbar-brand img {
          width: 76px;
        }
        .vm-topbar-small {
          color: #0a7fbe;
          text-transform: uppercase;
          letter-spacing: 0.08em;
          font-size: 12px;
          font-weight: 700;
          margin-bottom: 4px;
        }
        .vm-topbar-title {
          color: #173c54;
          font-size: 28px;
          font-weight: 800;
        }
        .vm-topbar-links {
          display: flex;
          gap: 10px;
          flex-wrap: wrap;
        }
        .vm-topbar-links span {
          display: inline-flex;
          align-items: center;
          padding: 8px 14px;
          border-radius: 999px;
          background: #eef8ff;
          border: 1px solid #d7e8f4;
          color: #0a568c;
          font-weight: 700;
          font-size: 13px;
        }
        .vm-chat-wrap {
          background: #ffffff;
          border: 1px solid #dbe6ee;
          border-radius: 24px;
          padding: 18px;
          box-shadow: 0 16px 40px rgba(8, 60, 92, 0.08);
        }
        .vm-pill-row {
          display: flex;
          gap: 10px;
          align-items: center;
          flex-wrap: wrap;
          margin-bottom: 10px;
        }
        .vm-pill {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          border-radius: 999px;
          padding: 7px 14px;
          border: 1px solid #cfe3ee;
          background: #f8fcff;
          color: #0b5187;
          font-weight: 700;
          font-size: 13px;
        }
        .vm-analysis-card {
          background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
          border: 1px solid #d9e7ef;
          border-radius: 18px;
          padding: 18px;
          margin-top: 8px;
          margin-bottom: 8px;
        }
        .vm-analysis-title {
          font-size: 22px;
          font-weight: 800;
          color: #13384b;
          margin: 0 0 8px 0;
        }
        .vm-analysis-text {
          color: #355567;
          line-height: 1.7;
          margin-bottom: 10px;
        }
        .vm-disclaimer {
          border-left: 4px solid #4db79f;
          background: #eefbf7;
          border-radius: 10px;
          padding: 12px 14px;
          color: #194c45;
          font-size: 14px;
          margin-top: 10px;
        }
        .vm-ask-box {
          background: #fff8e8;
          border-left: 4px solid #e6a700;
          border-radius: 12px;
          padding: 14px 16px;
          margin-top: 8px;
          color: #6c4b00;
        }
        .vm-danger-box {
          background: #fff1f2;
          border-left: 4px solid #d92d20;
          border-radius: 12px;
          padding: 14px 16px;
          margin-top: 8px;
          color: #6d1f1c;
        }
        .vm-section-head {
          font-size: 18px;
          font-weight: 800;
          color: #173c54;
          margin: 16px 0 10px;
        }
        .vm-doctor-grid {
          display: grid;
          grid-template-columns: repeat(3, minmax(0, 1fr));
          gap: 14px;
          margin-top: 10px;
        }
        .vm-doctor-card {
          background: #ffffff;
          border: 1px solid #dce7ef;
          border-radius: 20px;
          padding: 16px;
          box-shadow: 0 10px 24px rgba(7, 58, 90, 0.06);
        }
        .vm-doctor-card.primary {
          border-color: #72d8c4;
          box-shadow: 0 14px 28px rgba(36, 183, 148, 0.12);
        }
        .vm-doctor-topline {
          display: flex;
          justify-content: space-between;
          gap: 10px;
          align-items: center;
          margin-bottom: 12px;
        }
        .vm-priority {
          color: #0a8f74;
          font-weight: 800;
          text-transform: uppercase;
          font-size: 12px;
          letter-spacing: 0.06em;
        }
        .vm-score {
          color: #0b5db1;
          border: 1px solid #b9d8f7;
          background: #f3f8fe;
          border-radius: 999px;
          padding: 5px 10px;
          font-weight: 700;
          font-size: 12px;
          white-space: nowrap;
        }
        .vm-doctor-name {
          color: #173c54;
          font-size: 21px;
          font-weight: 800;
          line-height: 1.2;
          margin: 0 0 6px 0;
        }
        .vm-doctor-meta {
          color: #637b89;
          margin-bottom: 10px;
          font-size: 14px;
        }
        .vm-doctor-list {
          display: grid;
          gap: 8px;
          color: #21485e;
          font-size: 14px;
        }
        .vm-chat-input-note {
          color: #69808f;
          font-size: 13px;
          text-align: center;
          margin-top: 8px;
        }
        .vm-side-card {
          background: #ffffff;
          border: 1px solid #dce7ef;
          border-radius: 20px;
          padding: 18px;
          box-shadow: 0 12px 28px rgba(7, 58, 90, 0.06);
          margin-bottom: 14px;
        }
        .vm-side-head {
          display: flex;
          align-items: center;
          gap: 10px;
          color: #173c54;
          font-size: 17px;
          font-weight: 800;
          margin-bottom: 12px;
        }
        .vm-side-head img {
          width: 18px;
          height: 18px;
        }
        .vm-side-text {
          color: #5f7584;
          line-height: 1.6;
          font-size: 14px;
        }
        .vm-facility-item {
          border: 1px solid #dbe7ef;
          border-radius: 16px;
          padding: 12px;
          margin-top: 10px;
          background: #fbfdff;
        }
        .vm-facility-item.active {
          border-color: #79d6c2;
          background: #f3fbf8;
        }
        .vm-facility-name {
          color: #173c54;
          font-weight: 800;
          margin-bottom: 4px;
        }
        .vm-support-list {
          display: grid;
          gap: 10px;
        }
        .vm-support-row {
          display: flex;
          gap: 10px;
          align-items: flex-start;
          color: #365568;
          font-size: 14px;
          line-height: 1.55;
        }
        .vm-support-row img {
          width: 18px;
          height: 18px;
          margin-top: 1px;
        }
        @media (max-width: 900px) {
          .vm-doctor-grid {
            grid-template-columns: 1fr;
          }
          .vm-topbar-inner {
            flex-direction: column;
            align-items: flex-start;
          }
        }
        """
    )
    st.markdown(f"<style>{''.join(css_chunks)}</style>", unsafe_allow_html=True)


def run() -> None:
    st.set_page_config(
        page_title="Đăng ký khám | Vinmec",
        page_icon="🏥",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    inject_styles()

    token, base_url, model_name = sidebar_settings()
    facilities = catalog_repository.get_facilities()
    if not facilities:
        st.error("Database hiện chưa có dữ liệu. Hãy chạy `python crawl/run_once.py` trước.")
        return

    facility_titles = [item["title"] for item in facilities]
    facility_map = {item["title"]: item for item in facilities}
    selected_facility_title = st.session_state.get("selected_facility_title", facility_titles[0])
    if selected_facility_title not in facility_map:
        selected_facility_title = facility_titles[0]
    selected_facility = facility_map[selected_facility_title]
    specialties = catalog_repository.get_specialties_by_facility(selected_facility["id"])

    render_header(selected_facility_title)
    ensure_session()

    left_col, right_col = st.columns([2.3, 1], gap="large")

    with left_col:
        st.markdown(
            f"""
            <div class="vm-chat-wrap">
              <div class="vm-pill-row">
                <div class="vm-pill">Chatbot đặt khám</div>
                <div class="vm-pill">{selected_facility_title}</div>
                <div class="vm-pill">{len(specialties)} chuyên khoa khả dụng</div>
              </div>
              <div class="vm-analysis-text" style="margin-bottom:0;">
                Bạn có thể mô tả triệu chứng, thời gian xuất hiện hoặc nhu cầu đặt khám. Nếu thông tin đủ rõ, AI sẽ đề xuất chuyên khoa ngay; nếu chưa đủ rõ hoặc có yếu tố chấn thương, AI sẽ hỏi thêm ngắn gọn để tránh gợi ý sai.
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        for message in st.session_state.chat_messages:
            render_message(message)

    with right_col:
        chosen_title = st.selectbox(
            "Cơ sở Vinmec",
            options=facility_titles,
            index=facility_titles.index(selected_facility_title),
        )
        if chosen_title != selected_facility_title:
            st.session_state.selected_facility_title = chosen_title
            st.rerun()
        render_right_panel(facilities, facility_map[chosen_title])

    prompt = st.chat_input("Nhập triệu chứng hoặc nhu cầu đặt khám của bạn...")
    if prompt:
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        st.rerun()

    if st.session_state.chat_messages and st.session_state.chat_messages[-1]["role"] == "user":
        latest_prompt = st.session_state.chat_messages[-1]["content"]
        selected_facility_title = st.session_state.get("selected_facility_title", chosen_title)
        selected_facility = facility_map[selected_facility_title]
        specialties = catalog_repository.get_specialties_by_facility(selected_facility["id"])
        with left_col:
            with st.chat_message("assistant"):
                with st.spinner("AI đang phân tích triệu chứng và đối chiếu chuyên khoa phù hợp..."):
                    triage = ask_triage_agent(
                        token=token,
                        base_url=base_url,
                        model_name=model_name,
                        user_message=latest_prompt,
                        selected_facility=selected_facility,
                        specialties=specialties,
                    )
                    assistant_message = build_assistant_message(triage, selected_facility, specialties)
                    render_analysis_payload(assistant_message)
        st.session_state.chat_messages.append(assistant_message)
        st.rerun()

    st.markdown(
        '<div class="vm-chat-input-note">AI Copilot có thể mắc lỗi. Vui lòng xác nhận thông tin quan trọng trước khi đặt khám.</div>',
        unsafe_allow_html=True,
    )


def to_base64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("utf-8")


def render_header(facility_title: str) -> None:
    logo_b64 = to_base64(ASSET_DIR / "Logo_Vinmec_System_c725c14ffd.png")
    st.markdown(
        f"""
        <div class="vm-topbar">
          <div class="vm-topbar-inner">
            <div class="vm-topbar-brand">
              <img src="data:image/png;base64,{logo_b64}" alt="Vinmec">
              <div>
                <div class="vm-topbar-small">Vinmec AI Patient Copilot</div>
                <div class="vm-topbar-title">Khung chat điều hướng đặt khám</div>
              </div>
            </div>
            <div class="vm-topbar-links">
              <span>{facility_title}</span>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def sidebar_settings_legacy() -> tuple[str | None, str, str]:
    st.sidebar.header("Cấu hình AI")
    token = st.sidebar.text_input(
        "GitHub Models token",
        type="password",
        value=get_secret("GITHUB_MODELS_TOKEN", os.getenv("GITHUB_MODELS_TOKEN", "")),
    )
    base_url = st.sidebar.text_input(
        "Base URL",
        value=get_secret("GITHUB_MODELS_BASE_URL", os.getenv("GITHUB_MODELS_BASE_URL", DEFAULT_BASE_URL)),
    )
    model_name = st.sidebar.text_input(
        "Model",
        value=get_secret("GITHUB_MODELS_MODEL", os.getenv("GITHUB_MODELS_MODEL", DEFAULT_MODEL)),
    )
    st.sidebar.divider()
    st.sidebar.subheader("Dữ liệu đã crawl")
    status = catalog_repository.get_status()
    if status:
        st.sidebar.write(f"Lần cập nhật cuối: {status.get('finished_at', '')}")
        st.sidebar.write(f"Cơ sở: {status.get('facility_count', 0)}")
        st.sidebar.write(f"Chuyên khoa: {status.get('specialty_count', 0)}")
        st.sidebar.write(f"Bác sĩ: {status.get('doctor_count', 0)}")
        st.sidebar.write(f"Slot: {status.get('slot_count', 0)}")
    else:
        st.sidebar.warning("Chưa có dữ liệu trong database.")
    st.sidebar.info("Chạy `python crawl/run_once.py` để làm mới dữ liệu.")
    return token or None, base_url, model_name


def sidebar_settings() -> tuple[str | None, str, str]:
    return get_runtime_config()


def load_system_prompt() -> str:
    return SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")


def extract_json_block(content: str) -> dict[str, Any] | None:
    raw = content.strip()
    if raw.startswith("```"):
        raw = raw.split("```", 1)[1]
        raw = raw.replace("json", "", 1).strip()
        raw = raw.rsplit("```", 1)[0].strip()
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        return None


def match_specialty_title(candidate: str | None, specialties: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not candidate:
        return None

    normalized_candidate = normalize(candidate)
    for specialty in specialties:
        if normalize(specialty["title"]) == normalized_candidate:
            return specialty

    for specialty in specialties:
        title = normalize(specialty["title"])
        if normalized_candidate in title or title in normalized_candidate:
            return specialty
    return None


def fallback_triage(user_message: str, specialties: list[dict[str, Any]]) -> dict[str, Any]:
    normalized = normalize(user_message)
    scored_titles: list[tuple[str, int]] = []
    matched_keywords: list[str] = []

    for rule in read_triage_map():
        matched = [keyword for keyword in rule["symptom_keywords"] if normalize(keyword) in normalized]
        if matched:
            matched_keywords.extend(matched)
            for title in rule["specialty_keywords"]:
                scored_titles.append((normalize(title), len(matched)))

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

    if not best_specialty:
        return {
            "status": "ask_follow_up",
            "confidence": 0.35,
            "assistant_message": (
                "Mô tả hiện tại chưa đủ rõ để mình điều hướng đúng chuyên khoa. "
                "Bạn mô tả rõ hơn vị trí đau, thời gian xuất hiện và triệu chứng đi kèm nhé."
            ),
            "recommended_department_title": None,
            "reasoning": "",
            "follow_up_questions": [
                "Triệu chứng xuất hiện ở vị trí nào trên cơ thể?",
                "Tình trạng này bắt đầu từ khi nào và kéo dài bao lâu rồi?",
                "Ngoài triệu chứng chính, bạn còn có sốt, buồn nôn, ho hay khó thở không?",
            ],
        }

    confidence = min(0.6 + best_score * 0.1, 0.9)
    return {
        "status": "recommend",
        "confidence": confidence,
        "assistant_message": f"Mình tạm thời đề xuất chuyên khoa {best_specialty['title']} dựa trên mô tả bạn cung cấp.",
        "recommended_department_title": best_specialty["title"],
        "reasoning": (
            f"Các dấu hiệu như {', '.join(list(dict.fromkeys(matched_keywords))[:3]) or 'triệu chứng bạn mô tả'} "
            f"đang nghiêng về chuyên khoa {best_specialty['title']}."
        ),
        "follow_up_questions": [],
    }


def ask_triage_agent(
    token: str | None,
    base_url: str,
    model_name: str,
    user_message: str,
    selected_facility: dict[str, Any],
    specialties: list[dict[str, Any]],
) -> dict[str, Any]:
    if not token:
        return fallback_triage(user_message, specialties)

    client = build_client(token, base_url)
    if client is None:
        return fallback_triage(user_message, specialties)

    department_titles = [item["title"] for item in specialties]
    system_prompt = load_system_prompt()
    response = client.chat.completions.create(
        model=model_name,
        temperature=0.1,
        messages=[
            {
                "role": "system",
                "content": system_prompt
                + "\n\nBạn phải trả về JSON hợp lệ duy nhất theo schema sau:"
                + '\n{"status":"recommend|ask_follow_up|emergency|out_of_scope","confidence":0.0,"assistant_message":"...","recommended_department_title":"... hoặc null","reasoning":"...","follow_up_questions":["..."]}'
                + "\nNếu đề xuất chuyên khoa, recommended_department_title phải là một trong các chuyên khoa trong danh sách được cung cấp."
                + "\nNếu thông tin còn đủ để định hướng sơ bộ, vẫn có thể đề xuất một chuyên khoa gần nhất thay vì hỏi thêm quá sớm."
                + "\nVí dụ các mô tả như 'đau mắt', 'đau bụng', 'tiểu buốt', 'đau họng' thường đã đủ để đề xuất chuyên khoa sơ bộ."
                + "\nChỉ chuyển sang ask_follow_up khi thông tin quá mơ hồ, quá rộng, hoặc chưa đủ an toàn để định hướng."
            },
            {
                "role": "user",
                "content": (
                    f"Cơ sở Vinmec đang chọn: {selected_facility['title']}\n"
                    f"Danh sách chuyên khoa hợp lệ: {json.dumps(department_titles, ensure_ascii=False)}\n"
                    f"Triệu chứng người dùng: {user_message}"
                ),
            },
        ],
    )
    content = response.choices[0].message.content if response.choices else ""
    parsed = extract_json_block(content or "")
    if not parsed:
        return fallback_triage(user_message, specialties)

    parsed["status"] = str(parsed.get("status", "ask_follow_up"))
    parsed["confidence"] = float(parsed.get("confidence", 0.5))
    parsed["assistant_message"] = str(parsed.get("assistant_message", "")).strip()
    parsed["reasoning"] = str(parsed.get("reasoning", "")).strip()
    parsed["recommended_department_title"] = parsed.get("recommended_department_title")
    parsed["follow_up_questions"] = [
        str(item).strip()
        for item in parsed.get("follow_up_questions", [])
        if str(item).strip()
    ][:3]
    return parsed


def rank_doctors_with_slots(facility_id: str, specialty_id: str) -> list[dict[str, Any]]:
    doctors = catalog_repository.get_doctors(facility_id, specialty_id)
    ranked: list[dict[str, Any]] = []
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

    ranked.sort(
        key=lambda item: (
            item["first_slot"] is None,
            item["first_slot"]["start_time"] if item["first_slot"] else "9999-12-31T00:00:00",
            -item["slot_count"],
            item["heading"],
        )
    )
    return ranked


def format_slot(slot: dict[str, Any] | None) -> str:
    if not slot:
        return "Tạm hết lịch"
    start_time = slot.get("start_time") or ""
    if "T" in start_time:
        return datetime.fromisoformat(start_time).strftime("%H:%M - %d/%m/%Y")
    return start_time


def format_doctor_label(doctor: dict[str, Any]) -> str:
    return doctor.get("heading", "Bác sĩ")


def compute_doctor_match_score(doctor: dict[str, Any], index: int) -> int:
    score = 90
    if doctor.get("first_slot"):
        score += 4
    score += min(doctor.get("slot_count", 0), 3) * 2
    score -= index * 5
    return max(82, min(score, 98))


def build_doctor_reason(doctor: dict[str, Any]) -> str:
    if doctor.get("first_slot"):
        return f"Còn lịch gần nhất vào {format_slot(doctor['first_slot'])}."
    return "Hiện chưa có slot ngay, phù hợp làm phương án thay thế."


def initial_messages() -> list[dict[str, Any]]:
    return [
        {
            "role": "assistant",
            "kind": "greeting",
            "content": (
                "Xin chào. Tôi là trợ lý AI của Vinmec. "
                "Tôi sẽ giúp bạn phân tích triệu chứng và gợi ý chuyên khoa, bác sĩ phù hợp để đặt khám. "
                "Bạn đang gặp vấn đề sức khỏe gì?"
            ),
        }
    ]


def render_analysis_payload(message: dict[str, Any]) -> None:
    status = message["status"]
    if status == "recommend":
        st.markdown(
            f"""
            <div class="vm-analysis-card">
              <div class="vm-pill-row">
                <div class="vm-pill">AI Analysis</div>
                <div class="vm-pill">Confidence Score: {message['confidence']:.0%}</div>
              </div>
              <div class="vm-analysis-title">{message['department_title']}</div>
              <div class="vm-analysis-text">{message['assistant_message']}</div>
              <div class="vm-analysis-text">{message['reasoning']}</div>
              <div class="vm-disclaimer">AI hỗ trợ điều hướng đặt khám, không thay thế chẩn đoán lâm sàng.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        doctors = message.get("doctors", [])
        if doctors:
            st.markdown('<div class="vm-section-head">Available Specialists Matching Your Case</div>', unsafe_allow_html=True)
            st.markdown('<div class="vm-doctor-grid">', unsafe_allow_html=True)
            for index, doctor in enumerate(doctors):
                priority = DOCTOR_PRIORITY_LABELS[min(index, len(DOCTOR_PRIORITY_LABELS) - 1)]
                score = compute_doctor_match_score(doctor, index)
                fee = (doctor.get("price") or {}).get("local")
                primary_class = "primary" if index == 0 else ""
                st.markdown(
                    f"""
                    <div class="vm-doctor-card {primary_class}">
                      <div class="vm-doctor-topline">
                        <div class="vm-priority">{priority}</div>
                        <div class="vm-score">Match Score: {score}%</div>
                      </div>
                      <div class="vm-doctor-name">{format_doctor_label(doctor)}</div>
                      <div class="vm-doctor-meta">{doctor.get('subheading') or message['department_title']}</div>
                      <div class="vm-doctor-list">
                        <span>Slot gần nhất: <strong>{format_slot(doctor.get('first_slot'))}</strong></span>
                        <span>Số lịch khả dụng: <strong>{doctor.get('slot_count', 0)}</strong></span>
                        <span>Phí khám dự kiến: <strong>{f"{fee:,} VND".replace(",", ".") if fee else "Liên hệ xác nhận"}</strong></span>
                        <span>Lý do đề xuất: <strong>{build_doctor_reason(doctor)}</strong></span>
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            st.markdown("</div>", unsafe_allow_html=True)
    elif status == "ask_follow_up":
        st.markdown(
            f"""
            <div class="vm-ask-box">
              <strong>Cần làm rõ thêm</strong><br>
              {message['assistant_message']}
            </div>
            """,
            unsafe_allow_html=True,
        )
        for question in message.get("follow_up_questions", []):
            st.write(f"- {question}")
    elif status == "emergency":
        st.markdown(
            f"""
            <div class="vm-danger-box">
              <strong>Dấu hiệu cần ưu tiên cấp cứu</strong><br>
              {message['assistant_message']}
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(message["assistant_message"])


def render_message(message: dict[str, Any]) -> None:
    with st.chat_message(message["role"]):
        if message["role"] == "assistant" and message.get("kind") == "analysis":
            render_analysis_payload(message)
        else:
            st.markdown(message["content"])


def build_assistant_message(
    triage: dict[str, Any],
    selected_facility: dict[str, Any],
    specialties: list[dict[str, Any]],
) -> dict[str, Any]:
    status = triage.get("status", "ask_follow_up")

    if status in {"out_of_scope", "unrelated"}:
        return {
            "role": "assistant",
            "kind": "analysis",
            "status": "out_of_scope",
            "assistant_message": triage.get(
                "assistant_message",
                "Tôi chỉ hỗ trợ điều hướng đặt khám tại Vinmec. Bạn vui lòng mô tả triệu chứng hoặc thời gian muốn khám.",
            ),
        }

    if status == "emergency":
        return {
            "role": "assistant",
            "kind": "analysis",
            "status": "emergency",
            "assistant_message": triage.get(
                "assistant_message",
                "Triệu chứng bạn mô tả có dấu hiệu nguy cấp. Vui lòng đến cấp cứu hoặc liên hệ nhân viên hỗ trợ ngay.",
            ),
        }

    matched_specialty = match_specialty_title(triage.get("recommended_department_title"), specialties)
    if status == "recommend" and matched_specialty:
        ranked_doctors = rank_doctors_with_slots(selected_facility["id"], matched_specialty["id"])[:3]
        return {
            "role": "assistant",
            "kind": "analysis",
            "status": "recommend",
            "confidence": float(triage.get("confidence", 0.7)),
            "department_title": matched_specialty["title"],
            "assistant_message": triage.get("assistant_message", ""),
            "reasoning": triage.get("reasoning", ""),
            "facility_title": selected_facility["title"],
            "doctors": ranked_doctors,
        }

    return {
        "role": "assistant",
        "kind": "analysis",
        "status": "ask_follow_up",
        "assistant_message": triage.get(
            "assistant_message",
            "Thông tin hiện tại còn mơ hồ nên mình cần hỏi thêm trước khi đề xuất chuyên khoa phù hợp.",
        ),
        "follow_up_questions": triage.get("follow_up_questions", []),
    }


def fallback_triage(user_message: str, specialties: list[dict[str, Any]]) -> dict[str, Any]:
    normalized = normalize(user_message)
    urgency_level = infer_urgency_level(normalized)

    if detect_emergency(normalized):
        return {
            "status": "emergency",
            "confidence": 0.99,
            "assistant_message": (
                "Mô tả của bạn có dấu hiệu cần ưu tiên cấp cứu ngay. "
                "Vui lòng gọi 115, đến khoa cấp cứu gần nhất, hoặc liên hệ nhân viên hỗ trợ Vinmec ngay lúc này."
            ),
            "recommended_department_title": None,
            "reasoning": "Đây là tình huống khẩn cấp nên không phù hợp để tiếp tục luồng đặt khám thông thường.",
            "follow_up_questions": [],
            "urgency_level": "critical",
        }

    if needs_injury_follow_up(normalized):
        return {
            "status": "ask_follow_up",
            "confidence": 0.45,
            "assistant_message": (
                "Mình cần hỏi rõ thêm về tình huống chấn thương trước khi gợi ý chuyên khoa phù hợp cho bạn."
            ),
            "recommended_department_title": None,
            "reasoning": "",
            "follow_up_questions": [
                "Bạn bị ngã ở đâu, và bộ phận nào đang đau nhiều nhất?",
                "Sau khi ngã bạn có khó cử động, sưng nề, tê yếu hay chảy máu không?",
                "Sự việc vừa xảy ra hay đã kéo dài từ trước đó?",
            ],
            "urgency_level": "high",
        }

    scored_titles: list[tuple[str, int]] = []
    matched_keywords: list[str] = []

    for rule in read_triage_map():
        matched = [keyword for keyword in rule["symptom_keywords"] if normalize(keyword) in normalized]
        if matched:
            matched_keywords.extend(matched)
            for title in rule["specialty_keywords"]:
                scored_titles.append((normalize(title), len(matched)))

    for title_hint, keywords in SPECIALTY_HINTS.items():
        hint_matches = [keyword for keyword in keywords if keyword in normalized]
        if hint_matches:
            matched_keywords.extend(hint_matches)
            scored_titles.append((normalize(title_hint), len(hint_matches) + 1))

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

    if not best_specialty:
        return {
            "status": "ask_follow_up",
            "confidence": 0.35,
            "assistant_message": (
                "Mô tả hiện tại chưa đủ rõ để mình điều hướng đúng chuyên khoa. "
                "Bạn mô tả giúp mình vị trí triệu chứng, thời gian xuất hiện và dấu hiệu đi kèm nhé."
            ),
            "recommended_department_title": None,
            "reasoning": "",
            "follow_up_questions": [
                "Triệu chứng xuất hiện ở vị trí nào trên cơ thể?",
                "Tình trạng này bắt đầu từ khi nào và kéo dài bao lâu rồi?",
                "Ngoài triệu chứng chính, bạn có sốt, buồn nôn, ho, khó thở hay sưng nề gì không?",
            ],
            "urgency_level": urgency_level,
        }

    confidence = min(0.62 + best_score * 0.08, 0.92)
    unique_matches = ", ".join(list(dict.fromkeys(matched_keywords))[:3]) or "triệu chứng bạn mô tả"
    return {
        "status": "recommend",
        "confidence": confidence,
        "assistant_message": f"Dựa trên mô tả hiện tại, mình tạm thời đề xuất chuyên khoa {best_specialty['title']} để bạn đặt khám đúng hướng hơn.",
        "recommended_department_title": best_specialty["title"],
        "reasoning": f"Các dấu hiệu như {unique_matches} đang nghiêng về chuyên khoa {best_specialty['title']}.",
        "follow_up_questions": [],
        "urgency_level": urgency_level,
    }


def ask_triage_agent(
    token: str | None,
    base_url: str,
    model_name: str,
    user_message: str,
    selected_facility: dict[str, Any],
    specialties: list[dict[str, Any]],
) -> dict[str, Any]:
    if not token:
        return fallback_triage(user_message, specialties)

    client = build_client(token, base_url)
    if client is None:
        return fallback_triage(user_message, specialties)

    department_titles = [item["title"] for item in specialties]
    system_prompt = load_system_prompt()
    response = client.chat.completions.create(
        model=model_name,
        temperature=0.15,
        messages=[
            {
                "role": "system",
                "content": system_prompt
                + "\n\nBạn phải trả về JSON hợp lệ duy nhất theo schema sau:"
                + '\n{"status":"recommend|ask_follow_up|emergency|out_of_scope","confidence":0.0,"assistant_message":"...","recommended_department_title":"... hoặc null","reasoning":"...","follow_up_questions":["..."],"urgency_level":"low|medium|high|critical"}'
                + "\nNếu đề xuất chuyên khoa, recommended_department_title phải là một trong các chuyên khoa trong danh sách được cung cấp."
                + "\nNếu mô tả như đau mắt, đau bụng, đau họng, tiểu buốt, đau tai hoặc nổi mẩn ngứa thì thường đã đủ để định hướng sơ bộ."
                + "\nNếu là ngã xe, trượt chân, té ngã, va đập thì hỏi thêm về vị trí đau, mức độ sưng nề, hạn chế vận động và chảy máu trước khi chốt."
                + "\nNếu là đuối nước, ngưng thở, co giật, đau ngực dữ dội, khó thở nặng hoặc bất tỉnh thì phải trả về emergency."
                + "\nGiọng điệu thân thiện, tự nhiên, ngắn gọn và an toàn."
            },
            {
                "role": "user",
                "content": (
                    f"Cơ sở Vinmec đang chọn: {selected_facility['title']}\n"
                    f"Danh sách chuyên khoa hợp lệ: {json.dumps(department_titles, ensure_ascii=False)}\n"
                    f"Triệu chứng người dùng: {user_message}"
                ),
            },
        ],
    )
    content = response.choices[0].message.content if response.choices else ""
    parsed = extract_json_block(content or "")
    if not parsed:
        return fallback_triage(user_message, specialties)

    parsed["status"] = str(parsed.get("status", "ask_follow_up"))
    parsed["confidence"] = float(parsed.get("confidence", 0.5))
    parsed["assistant_message"] = str(parsed.get("assistant_message", "")).strip()
    parsed["reasoning"] = str(parsed.get("reasoning", "")).strip()
    parsed["recommended_department_title"] = parsed.get("recommended_department_title")
    parsed["urgency_level"] = str(parsed.get("urgency_level", "medium")).strip().lower() or "medium"
    parsed["follow_up_questions"] = [
        str(item).strip()
        for item in parsed.get("follow_up_questions", [])
        if str(item).strip()
    ][:3]
    return parsed


def expertise_score(doctor: dict[str, Any]) -> int:
    heading = normalize(doctor.get("heading", ""))
    score = 68
    if "thay thuoc uu tu" in heading:
        score += 12
    if "tien si" in heading:
        score += 10
    if "pho giao su" in heading or "giao su" in heading:
        score += 10
    if "chuyen khoa ii" in heading or "bsckii" in heading:
        score += 8
    if "thac si" in heading:
        score += 6
    return min(score, 95)


def schedule_score(doctor: dict[str, Any]) -> int:
    first_slot = doctor.get("first_slot")
    slot_count = int(doctor.get("slot_count", 0))
    if not first_slot:
        return 20
    try:
        delta_hours = max((datetime.fromisoformat(first_slot["start_time"]) - datetime.now()).total_seconds() / 3600, 0)
    except Exception:
        delta_hours = 72

    if delta_hours <= 6:
        base = 95
    elif delta_hours <= 24:
        base = 88
    elif delta_hours <= 72:
        base = 78
    else:
        base = 68
    return min(98, base + min(slot_count, 4))


def urgency_fit_score(doctor: dict[str, Any], urgency_level: str) -> int:
    slot = doctor.get("first_slot")
    if urgency_level == "critical":
        return 100 if slot else 20
    if urgency_level == "high":
        return 96 if slot else 35
    if urgency_level == "medium":
        return 88 if slot else 55
    return 78 if slot else 64


def cost_score(doctor: dict[str, Any]) -> int:
    local_price = ((doctor.get("price") or {}).get("local"))
    if not local_price:
        return 70
    if local_price <= 300000:
        return 92
    if local_price <= 500000:
        return 85
    if local_price <= 800000:
        return 76
    return 68


def compute_doctor_match_score(doctor: dict[str, Any], urgency_level: str, index: int) -> int:
    score = (
        schedule_score(doctor) * 0.35
        + urgency_fit_score(doctor, urgency_level) * 0.30
        + expertise_score(doctor) * 0.25
        + cost_score(doctor) * 0.10
    )
    score -= index * 1.5
    return max(75, min(int(round(score)), 99))


def build_doctor_reason(doctor: dict[str, Any], urgency_level: str) -> str:
    reasons: list[str] = []
    heading = doctor.get("heading") or ""
    if heading:
        reasons.append(f"phù hợp về chuyên môn với hồ sơ bác sĩ {heading}")
    if doctor.get("slot_count", 0) >= 3:
        reasons.append("có nhiều khung giờ khả dụng để dễ sắp lịch")
    elif doctor.get("first_slot"):
        reasons.append("có lịch khám sớm để bạn chủ động thời gian")
    if urgency_level in {"high", "critical"} and doctor.get("first_slot"):
        reasons.append("ưu tiên tốt cho nhu cầu cần khám sớm")
    return "; ".join(reasons[:2]) or "phù hợp để cân nhắc trong danh sách bác sĩ hiện có"


def rank_doctors_with_slots(facility_id: str, specialty_id: str, urgency_level: str) -> list[dict[str, Any]]:
    doctors = catalog_repository.get_doctors(facility_id, specialty_id)
    ranked: list[dict[str, Any]] = []
    for doctor in doctors:
        slots = catalog_repository.get_slots(facility_id, specialty_id, doctor["id"])
        enriched = {
            **doctor,
            "slots": slots,
            "slot_count": len(slots),
            "first_slot": slots[0] if slots else None,
        }
        enriched["match_score"] = compute_doctor_match_score(enriched, urgency_level, 0)
        ranked.append(enriched)

    ranked.sort(
        key=lambda item: (
            -item["match_score"],
            item["first_slot"] is None,
            item["first_slot"]["start_time"] if item["first_slot"] else "9999-12-31T00:00:00",
            item["heading"],
        )
    )
    for index, doctor in enumerate(ranked):
        doctor["match_score"] = compute_doctor_match_score(doctor, urgency_level, index)
    return ranked


def build_assistant_message(
    triage: dict[str, Any],
    selected_facility: dict[str, Any],
    specialties: list[dict[str, Any]],
) -> dict[str, Any]:
    status = triage.get("status", "ask_follow_up")
    urgency_level = str(triage.get("urgency_level", "medium"))

    if status in {"out_of_scope", "unrelated"}:
        return {
            "role": "assistant",
            "kind": "analysis",
            "status": "out_of_scope",
            "assistant_message": triage.get(
                "assistant_message",
                "Mình chỉ hỗ trợ điều hướng đặt khám tại Vinmec. Bạn có thể cho mình biết triệu chứng, cơ sở muốn khám hoặc thời gian mong muốn nhé.",
            ),
        }

    if status == "emergency":
        return {
            "role": "assistant",
            "kind": "analysis",
            "status": "emergency",
            "assistant_message": triage.get(
                "assistant_message",
                "Triệu chứng bạn mô tả có dấu hiệu nguy cấp. Vui lòng đến cấp cứu hoặc liên hệ nhân viên hỗ trợ ngay.",
            ),
            "reasoning": triage.get("reasoning", ""),
        }

    matched_specialty = match_specialty_title(triage.get("recommended_department_title"), specialties)
    if status == "recommend" and matched_specialty:
        ranked_doctors = rank_doctors_with_slots(selected_facility["id"], matched_specialty["id"], urgency_level)[:3]
        return {
            "role": "assistant",
            "kind": "analysis",
            "status": "recommend",
            "confidence": float(triage.get("confidence", 0.7)),
            "department_title": matched_specialty["title"],
            "assistant_message": triage.get("assistant_message", ""),
            "reasoning": triage.get("reasoning", ""),
            "facility_title": selected_facility["title"],
            "urgency_level": urgency_level,
            "doctors": ranked_doctors,
        }

    return {
        "role": "assistant",
        "kind": "analysis",
        "status": "ask_follow_up",
        "assistant_message": triage.get(
            "assistant_message",
            "Thông tin hiện tại còn mơ hồ nên mình cần hỏi thêm trước khi đề xuất chuyên khoa phù hợp.",
        ),
        "follow_up_questions": triage.get("follow_up_questions", []),
        "urgency_level": urgency_level,
    }


def render_analysis_payload(message: dict[str, Any]) -> None:
    doctor_icon = get_asset_b64("doctor.svg")
    calendar_icon = get_asset_b64("calendar.svg")
    check_icon = get_asset_b64("Check_info.svg")
    status = message["status"]
    if status == "recommend":
        st.markdown(
            f"""
            <div class="vm-analysis-card">
              <div class="vm-pill-row">
                <div class="vm-pill"><img src="data:image/svg+xml;base64,{check_icon}" alt=""> AI Analysis</div>
                <div class="vm-pill">Confidence Score: {message['confidence']:.0%}</div>
                <div class="vm-pill">{message.get('facility_title', '')}</div>
              </div>
              <div class="vm-analysis-title">Chuyên khoa đề xuất: {message['department_title']}</div>
              <div class="vm-analysis-text">{message['assistant_message']}</div>
              <div class="vm-analysis-text">{message['reasoning']}</div>
              <div class="vm-disclaimer">AI hỗ trợ điều hướng đặt khám, không thay thế chẩn đoán lâm sàng.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        doctors = message.get("doctors", [])
        if doctors:
            st.markdown(
                f'<div class="vm-section-head"><img src="data:image/svg+xml;base64,{doctor_icon}" alt="" style="width:18px;height:18px;vertical-align:-3px;margin-right:8px;">Bác sĩ đang khả dụng cho trường hợp của bạn</div>',
                unsafe_allow_html=True,
            )
            st.markdown('<div class="vm-doctor-grid">', unsafe_allow_html=True)
            for index, doctor in enumerate(doctors):
                priority = DOCTOR_PRIORITY_LABELS[min(index, len(DOCTOR_PRIORITY_LABELS) - 1)]
                fee = (doctor.get("price") or {}).get("local")
                primary_class = "primary" if index == 0 else ""
                st.markdown(
                    f"""
                    <div class="vm-doctor-card {primary_class}">
                      <div class="vm-doctor-topline">
                        <div class="vm-priority">{priority}</div>
                        <div class="vm-score">Match Score: {doctor['match_score']}%</div>
                      </div>
                      <div class="vm-doctor-name">{format_doctor_label(doctor)}</div>
                      <div class="vm-doctor-meta">{doctor.get('subheading') or message['department_title']}</div>
                      <div class="vm-doctor-list">
                        <span><img src="data:image/svg+xml;base64,{calendar_icon}" alt="" style="width:14px;height:14px;vertical-align:-2px;margin-right:6px;">Slot gần nhất: <strong>{format_slot(doctor.get('first_slot'))}</strong></span>
                        <span>Số lịch khả dụng: <strong>{doctor.get('slot_count', 0)}</strong></span>
                        <span>Phí khám dự kiến: <strong>{f"{fee:,} VND".replace(",", ".") if fee else "Liên hệ xác nhận"}</strong></span>
                        <span>Lý do đề xuất: <strong>{build_doctor_reason(doctor, message.get('urgency_level', 'medium'))}</strong></span>
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            st.markdown("</div>", unsafe_allow_html=True)
    elif status == "ask_follow_up":
        st.markdown(
            f"""
            <div class="vm-ask-box">
              <strong>Cần làm rõ thêm</strong><br>
              {message['assistant_message']}
            </div>
            """,
            unsafe_allow_html=True,
        )
        for question in message.get("follow_up_questions", []):
            st.write(f"- {question}")
    elif status == "emergency":
        st.markdown(
            f"""
            <div class="vm-danger-box">
              <strong>Dấu hiệu cần ưu tiên cấp cứu</strong><br>
              {message['assistant_message']}
            </div>
            """,
            unsafe_allow_html=True,
        )
        if message.get("reasoning"):
            st.caption(message["reasoning"])
    else:
        st.markdown(message["assistant_message"])


def render_right_panel(facilities: list[dict[str, Any]], selected_facility: dict[str, Any]) -> None:
    phone_icon = get_asset_b64("Phone.svg")
    service_icon = get_asset_b64("Service.svg")
    customer_icon = get_asset_b64("Customer.svg")
    check_icon = get_asset_b64("Check_info.svg")
    reload_icon = get_asset_b64("Reload.svg")
    status = catalog_repository.get_status()

    st.markdown(
        f"""
        <div class="vm-side-card">
          <div class="vm-side-head"><img src="data:image/svg+xml;base64,{service_icon}" alt="">Phạm vi hỗ trợ</div>
          <div class="vm-support-list">
            <div class="vm-support-row"><img src="data:image/svg+xml;base64,{check_icon}" alt="">Tiếp nhận triệu chứng cơ bản để gợi ý chuyên khoa phù hợp.</div>
            <div class="vm-support-row"><img src="data:image/svg+xml;base64,{check_icon}" alt="">Đề xuất bác sĩ còn lịch theo mức độ phù hợp, tính khẩn cấp và thời gian trống.</div>
            <div class="vm-support-row"><img src="data:image/svg+xml;base64,{check_icon}" alt="">Không thay thế chẩn đoán, không kê đơn và không xử lý cấp cứu thay bác sĩ.</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="vm-side-card">
          <div class="vm-side-head"><img src="data:image/svg+xml;base64,{customer_icon}" alt="">Cơ sở khả dụng</div>
          <div class="vm-side-text">Bạn đang xem dữ liệu đặt khám theo cơ sở Vinmec hiện có trong catalog.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    for facility in facilities:
        active_class = "active" if facility["id"] == selected_facility["id"] else ""
        address = facility.get("address") or facility.get("city") or "Đang cập nhật địa chỉ"
        st.markdown(
            f"""
            <div class="vm-facility-item {active_class}">
              <div class="vm-facility-name">{facility['title']}</div>
              <div class="vm-side-text">{address}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if status:
        st.markdown(
            f"""
            <div class="vm-side-card">
              <div class="vm-side-head"><img src="data:image/svg+xml;base64,{reload_icon}" alt="">Dữ liệu khả dụng</div>
              <div class="vm-side-text">
                Lần cập nhật gần nhất: {status.get('finished_at', 'N/A')}<br>
                Cơ sở: {status.get('facility_count', 0)}<br>
                Chuyên khoa: {status.get('specialty_count', 0)}<br>
                Bác sĩ: {status.get('doctor_count', 0)}<br>
                Slot: {status.get('slot_count', 0)}
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        f"""
        <div class="vm-side-card">
          <div class="vm-side-head"><img src="data:image/svg+xml;base64,{phone_icon}" alt="">Khi cần người thật hỗ trợ</div>
          <div class="vm-side-text">
            Nếu triệu chứng phức tạp, bạn cần hỗ trợ gấp hoặc muốn xác nhận lại thông tin, hãy chuyển sang tư vấn viên hoặc khoa cấp cứu khi cần.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def initial_messages() -> list[dict[str, Any]]:
    return [
        {
            "role": "assistant",
            "kind": "greeting",
            "content": (
                "Xin chào, mình là trợ lý đặt khám của Vinmec. "
                "Bạn cứ mô tả triệu chứng hoặc nhu cầu khám, mình sẽ giúp gợi ý chuyên khoa và bác sĩ phù hợp trong phạm vi hỗ trợ đặt khám."
            ),
        }
    ]


def ensure_session() -> None:
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = initial_messages()


def run_legacy() -> None:
    st.set_page_config(
        page_title="Đăng ký khám | Vinmec",
        page_icon="🏥",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_styles()

    token, base_url, model_name = sidebar_settings()
    facilities = catalog_repository.get_facilities()
    if not facilities:
        st.error("Database hiện chưa có dữ liệu. Hãy chạy `python crawl/run_once.py` trước.")
        return

    facility_map = {item["title"]: item for item in facilities}
    selected_facility_title = st.sidebar.selectbox("Cơ sở Vinmec", list(facility_map.keys()))
    selected_facility = facility_map[selected_facility_title]
    specialties = catalog_repository.get_specialties_by_facility(selected_facility["id"])

    render_header(selected_facility_title)
    ensure_session()

    st.markdown(
        f"""
        <div class="vm-chat-wrap">
          <div class="vm-pill-row">
            <div class="vm-pill">Chatbot đặt khám</div>
            <div class="vm-pill">{selected_facility_title}</div>
            <div class="vm-pill">{len(specialties)} chuyên khoa khả dụng</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    for message in st.session_state.chat_messages:
        render_message(message)

    prompt = st.chat_input("Nhập triệu chứng hoặc nhu cầu đặt khám của bạn...")
    if prompt:
        user_message = {"role": "user", "content": prompt}
        st.session_state.chat_messages.append(user_message)
        render_message(user_message)

        with st.chat_message("assistant"):
            with st.spinner("AI đang phân tích triệu chứng và đối chiếu chuyên khoa phù hợp..."):
                triage = ask_triage_agent(
                    token=token,
                    base_url=base_url,
                    model_name=model_name,
                    user_message=prompt,
                    selected_facility=selected_facility,
                    specialties=specialties,
                )
                assistant_message = build_assistant_message(triage, selected_facility, specialties)
                render_analysis_payload(assistant_message)
        st.session_state.chat_messages.append(assistant_message)

    st.markdown(
        '<div class="vm-chat-input-note">AI Copilot có thể mắc lỗi. Vui lòng xác nhận thông tin quan trọng trước khi đặt khám.</div>',
        unsafe_allow_html=True,
    )
