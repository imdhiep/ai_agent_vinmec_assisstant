from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from crawl.db import DB_PATH
from crawl.vinmec_crawler import crawl_catalog, save_catalog_to_database


def main() -> None:
    payload = crawl_catalog(days_ahead=3)
    save_catalog_to_database(payload)
    print("Đã crawl dữ liệu thật từ website và API public của Vinmec vào SQLite.")
    print(f"Số cơ sở: {len(payload['facilities'])}")
    print(f"Số chuyên khoa: {len(payload['specialties'])}")
    print(f"Số bác sĩ: {len(payload['doctors'])}")
    print(f"Số slot: {len(payload['slots'])}")
    print(f"Database: {DB_PATH}")


if __name__ == "__main__":
    main()
