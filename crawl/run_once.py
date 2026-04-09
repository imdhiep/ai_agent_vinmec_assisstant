from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from crawl.db import DB_PATH, initialize_database
from crawl.monitor import CrawlMonitor
from crawl.vinmec_crawler import (
    DEFAULT_TARGET_FACILITY_TITLE,
    crawl_catalog,
)


def main() -> None:
    with CrawlMonitor() as monitor:
        monitor.update_stage("Khởi tạo database", str(DB_PATH))
        monitor.log(f"Cấu hình hiện tại: chỉ crawl cơ sở '{DEFAULT_TARGET_FACILITY_TITLE}'")
        initialize_database()
        payload = crawl_catalog(
            days_ahead=3,
            monitor=monitor,
            target_facility_title=DEFAULT_TARGET_FACILITY_TITLE,
            persist_to_db=True,
        )
        monitor.success("Đã crawl và lưu vào database SQLite thành công.")
        print(f"Database: {DB_PATH}")
        print(f"Số cơ sở: {len(payload['facilities'])}")
        print(f"Số chuyên khoa: {len(payload['specialties'])}")
        print(f"Số bác sĩ: {len(payload['doctors'])}")
        print(f"Số slot: {len(payload['slots'])}")
        print(f"Snapshot raw: {payload['snapshot_path']}")


if __name__ == "__main__":
    main()
