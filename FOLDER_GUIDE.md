# Hướng dẫn thư mục

## Root

- `streamlit_app.py`: file chạy chính của ứng dụng Streamlit.
- `streamlit_booking_app.py`: giao diện Streamlit mới bám sát trang Vinmec hơn.
- `README.md`: cách chạy, cách nhập token GitHub Models, mô tả kiến trúc.
- `requirements.txt`: danh sách thư viện cần cài.
- `system prompt.txt`: prompt hệ thống để agent chỉ trả lời về đặt khám.
- `.env.example`: mẫu biến môi trường để tự điền token.
- `.streamlit/secrets.toml.example`: mẫu secrets cho Streamlit.

## app/

- `config.py`: cấu hình đường dẫn gốc.
- `models.py`: schema dữ liệu dùng lại từ phần business logic.

## app/services/

- `catalog_repository.py`: đọc dữ liệu từ SQLite và lưu booking request.
- `github_models.py`: tạo OpenAI client với `base_url` của GitHub Models.
- `vinmec_live_catalog.py`: crawl dữ liệu thật từ website và API public của Vinmec.
- `triage.py`, `availability.py`, `booking.py`, `copilot.py`: phần logic cũ có thể tái sử dụng thêm nếu cần mở rộng.

## data/

- `vinmec_catalog.db`: database SQLite sau khi chạy crawl một lần.
- `triage_map.json`: luật ánh xạ triệu chứng sang chuyên khoa.
- `vinmec_live_catalog.json`: file JSON cũ, có thể giữ lại như dữ liệu tham khảo nếu cần.
- `facilities.json`, `departments.json`, `doctors.json`, `schedules.json`: dữ liệu mẫu để fallback.

## crawl/

- `run_once.py`: script chính để crawl một lần rồi ghi vào SQLite.
- `vinmec_crawler.py`: logic crawl từ website và API public của Vinmec.
- `db.py`: schema và helper kết nối SQLite.
- `raw/`: snapshot JSON thô được lưu lại sau mỗi lần crawl.

## streamlit_assets/

- `overrides.css`: CSS bổ sung để Streamlit nhìn gần với giao diện Vinmec hơn.

## scripts/

- `crawl_vinmec_public.py`: script crawl thủ công từ website Vinmec.
- `seed_mock_data.py`: script seed dữ liệu mẫu.

## Đăng ký khám _ Vinmec_files/

- Chứa toàn bộ asset frontend gốc đã tải về từ trang Vinmec.
- Ứng dụng Streamlit tái sử dụng trực tiếp các file CSS, logo, icon và ảnh cover trong thư mục này.
