# Vinmec AI Patient Booking Copilot

Ứng dụng Streamlit hỗ trợ `đặt lịch khám` theo spec `VINMEC AI PATIENT COPILOT`.
Luồng dữ liệu hiện tại là:

`crawl một lần -> lưu vào SQLite -> Streamlit chỉ đọc database`

## Mục tiêu

- Chỉ trả lời về đặt khám.
- Gợi ý chuyên khoa từ triệu chứng.
- Kiểm tra bác sĩ có lịch hay không.
- Nếu bác sĩ hết lịch, đề xuất:
  - slot gần nhất của cùng bác sĩ,
  - bác sĩ khác cùng chuyên khoa,
  - cơ sở khác của Vinmec,
  - hoặc chuyển tổng đài viên hỗ trợ.

## Công nghệ

- Giao diện: Streamlit
- Agent: OpenAI SDK gọi qua GitHub Models
- Dữ liệu: JSON + crawler từ website và API public của Vinmec
- Asset giao diện: tái sử dụng từ thư mục `Đăng ký khám _ Vinmec_files`

## Chạy ứng dụng

1. Cài Python 3.11+
2. Cài thư viện:

```bash
pip install -r requirements.txt
```

3. Chạy:

```bash
streamlit run streamlit_app.py
```

## Chỗ nhập GitHub token

Bạn có thể nhập token ở 1 trong 3 nơi:

1. Sidebar của ứng dụng Streamlit tại ô `GitHub Models token`
2. File `.env`

```env
GITHUB_MODELS_TOKEN=your_token_here
GITHUB_MODELS_BASE_URL=https://models.github.ai/inference
GITHUB_MODELS_MODEL=openai/gpt-4o
```

3. File `.streamlit/secrets.toml`

```toml
GITHUB_MODELS_TOKEN = "your_token_here"
GITHUB_MODELS_BASE_URL = "https://models.github.ai/inference"
GITHUB_MODELS_MODEL = "openai/gpt-4o"
```

## Crawl dữ liệu thật từ Vinmec

Chạy một lần:

```bash
python crawl/run_once.py
```

Hiện tại cấu hình tạm thời chỉ crawl:

- `BV ĐKQT Vinmec Times City (Hà Nội)`

Nếu muốn mở lại nhiều cơ sở sau này, chỉnh hằng số `DEFAULT_TARGET_FACILITY_TITLE` trong [crawl/vinmec_crawler.py](D:\python ky 9\hello\ai_agent_vinmec_assisstant\crawl\vinmec_crawler.py).

Script này sẽ:

- crawl từ `https://www.vinmec.com/vie/dang-ky-kham/`
- gọi các API public liên quan để lấy cơ sở, chuyên khoa, bác sĩ, slot
- lưu snapshot raw vào thư mục `crawl/raw/`
- chuẩn hóa và ghi vào SQLite tại `data/vinmec_catalog.db`
- ghi dần vào database ngay trong lúc crawl, nên nếu lỗi giữa chừng thì phần đã lấy được vẫn còn trong DB

Từ những lần chạy app sau, Streamlit sẽ chỉ đọc dữ liệu từ database này, không crawl realtime nữa.

## Cấu trúc chính

- `streamlit_app.py`: entrypoint giữ nguyên để chạy app
- `streamlit_booking_app.py`: giao diện Streamlit chính theo phong cách Vinmec
- `crawl/run_once.py`: script crawl một lần
- `crawl/vinmec_crawler.py`: logic crawl và ghi SQLite
- `crawl/db.py`: schema và kết nối database
- `app/services/catalog_repository.py`: truy xuất dữ liệu từ SQLite cho app
- `data/triage_map.json`: ánh xạ triệu chứng -> chuyên khoa
- `system prompt.txt`: prompt hệ thống booking-only
- `Đăng ký khám _ Vinmec_files/`: CSS, ảnh, icon, text asset lấy từ giao diện Vinmec
