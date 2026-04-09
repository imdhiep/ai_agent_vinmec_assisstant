from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
RAW_PATH = ROOT / "data" / "raw" / "vinmec_public_snapshot.json"


def main() -> None:
    with RAW_PATH.open("r", encoding="utf-8") as file:
        snapshot = json.load(file)

    print("Dữ liệu mẫu hiện dùng các file JSON đã chuẩn hóa cho cơ sở, chuyên khoa, bác sĩ và lịch khám.")
    print("Bạn có thể mở rộng script này để biến snapshot crawl live thành database có cấu trúc.")
    print(f"Nguồn snapshot: {snapshot['source_url']}")
    print(f"Số cơ sở public phát hiện được: {len(snapshot['facilities_seen'])}")


if __name__ == "__main__":
    main()
