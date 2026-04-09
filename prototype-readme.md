# Prototype — Vinmec AI Patient Booking Copilot

## Mô tả
Ứng dụng prototype giúp gợi ý chuyên khoa và hỗ trợ đặt lịch khám Vinmec bằng cách:
- nhận triệu chứng từ người dùng,
- đánh giá mức độ phù hợp,
- kiểm tra lịch bác sĩ,
- và đưa ra phương án thay thế khi lịch trống không khả dụng.

Hệ thống tập trung vào trải nghiệm đặt khám thông minh, với luồng đánh giá triệu chứng, ánh xạ chuyên khoa, kiểm tra slot, và trả về khuyến nghị / fallback phù hợp.

## Level: Mock prototype
- Giao diện chính: Streamlit (`streamlit_app.py` + `streamlit_booking_app.py`).
- Dữ liệu demo: JSON mock trong `data/*.json` và fallback catalog từ `Đăng ký khám _ Vinmec.html`.
- Crawl: `crawl/run_once.py` thu thập dữ liệu Vinmec và lưu vào SQLite/JSON.
- AI: OpenAI qua GitHub Models SDK (`app/services/github_models.py`).

## Links
- Prototype:https://github.com/imdhiep/Lab5_C401_A4 chạy local bằng `streamlit run streamlit_app.py`
- Prompt test log: xem file `prototype/prompt-tests.md`
- Video demo: đã demo trên lớp

## Tools
- UI: Streamlit với CSS/asset Vinmec từ `Đăng ký khám _ Vinmec_files/` và `streamlit_assets/overrides.css`.
- AI: OpenAI SDK thông qua GitHub Models (mặc định `openai/gpt-4o`).
- Dữ liệu: JSON mock (`data/facilities.json`, `data/departments.json`, `data/doctors.json`, `data/schedules.json`), plus live crawl `crawl/vinmec_crawler.py` và `app/services/vinmec_live_catalog.py`.
- Storage: mock database đọc JSON (`app/database/mock_db.py`) và crawler/SQLite (`crawl/db.py`, `app/services/catalog_repository.py`).
- Luồng xử lý: triage và logic booking trong `app/services/triage.py`, `app/services/availability.py`, `app/services/copilot.py`, `app/services/knowledge_base.py`.

#

## Phân công
| Thành viên | Phần                                                                                                                      | Output                                                                                                         |
| ---------- | ------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| Quân       | Viết Business Canvas, phân tích rủi ro (Failure Modes), hoàn thiện problem statement, Mini AI spec                        | `spec/spec-final.md` phần 1, 2; nội dung cho `slides.pdf`                                                      |
| Hiệp       | Crawl dữ liệu Vinmec, làm sạch data, tổ chức database/catalog, xây dựng workflow backend và logic lấy bác sĩ/slot         | `demo/data_pipeline/` (code), dữ liệu trong `data/`, mô tả luồng xử lý backend                                 |
| Dương      | Code UI Streamlit, tích hợp chatbot với backend/data, viết system prompt và tối ưu prompt engineering                     | `demo/prompt_logic/` (code), giao diện demo hoàn chỉnh                                                         |
| Đạt        | Xác định 4 luồng User Stories, xây dựng ROI, Metrics, Eval criteria, test case                                            | `prototype/`, `demo/demo-script.md`, `spec/spec-final.md` phần 3, 4, `prototype/`, `prototype/prompt-tests.md` |
| Đức Anh    | Viết phần kết luận/đề xuất triển khai trong spec, thiết kế luồng màn hình và trải nghiệm người dùng end-to-end            | `spec/spec-final.md` phần 5, `demo/demo-script.md`, UI flow/prototype                                          |
| Chung      | Thiết kế prototype tổng thể, test các tình huống prompt, chuẩn bị kịch bản demo và hỗ trợ kiểm thử trải nghiệm người dùng | `docs/vinmec_hackathon_testcases.md`, `docs/vinmec_main_flow.md`                                               |