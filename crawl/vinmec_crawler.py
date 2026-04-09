from __future__ import annotations

import json
import re
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup

from crawl.db import DB_PATH, get_connection, initialize_database
from crawl.monitor import CrawlMonitor


BOOKING_URL = "https://www.vinmec.com/vie/dang-ky-kham/"
API_BASE = "https://api2.vinmec.com/api/v1/auto-booking/vinmec"
RAW_DIR = Path(__file__).resolve().parent / "raw"
DEFAULT_TARGET_FACILITY_TITLE = "BV ĐKQT Vinmec Times City (Hà Nội)"


def slugify(text: str) -> str:
    lowered = text.lower().strip()
    lowered = re.sub(r"[^\w\s-]", "", lowered, flags=re.UNICODE)
    lowered = re.sub(r"\s+", "-", lowered)
    return lowered


def crawl_catalog(
    days_ahead: int = 3,
    timeout: int = 20,
    monitor: CrawlMonitor | None = None,
    target_facility_title: str | None = None,
) -> dict[str, Any]:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
            )
        }
    )

    if monitor:
        monitor.update_stage("Tải trang đăng ký khám", BOOKING_URL)
    booking_page = session.get(BOOKING_URL, timeout=timeout)
    if monitor:
        monitor.increment_requests()
    booking_page.raise_for_status()
    soup = BeautifulSoup(booking_page.text, "lxml")

    if monitor:
        monitor.update_stage("Lấy danh sách cơ sở")
    facilities = _fetch_facilities(session, timeout, monitor)
    if target_facility_title:
        facilities = [
            facility for facility in facilities
            if facility["title"].strip() == target_facility_title.strip()
        ]
        if monitor:
            monitor.log(f"Đã lọc chỉ crawl cơ sở: {target_facility_title}")
    if monitor:
        monitor.set_counts(facility_count=len(facilities))
        monitor.log(f"Đã lấy {len(facilities)} cơ sở")
    if target_facility_title and not facilities:
        raise RuntimeError(f"Không tìm thấy cơ sở mục tiêu: {target_facility_title}")
    specialties: list[dict[str, Any]] = []
    doctors: list[dict[str, Any]] = []
    slots: list[dict[str, Any]] = []

    specialty_seen: set[tuple[str, str]] = set()
    doctor_seen: set[tuple[str, str, str]] = set()
    slot_seen: set[str] = set()

    for facility_index, facility in enumerate(facilities, start=1):
        if monitor:
            monitor.set_context(
                facility=facility["title"],
                specialty="-",
                doctor="-",
                date_value="-",
            )
            monitor.update_stage(
                "Đang xử lý cơ sở",
                f"{facility['title']} ({facility_index}/{len(facilities)})",
            )
        specialty_items = _fetch_json(
            session,
            f"{API_BASE}/doctor-speciality/?vinmec_place_id={facility['id']}",
            timeout,
            monitor,
        )
        if monitor:
            monitor.log(f"{facility['title']}: nhận {len(specialty_items)} chuyên khoa")
        for specialty in specialty_items:
            if monitor:
                monitor.set_context(specialty=specialty.get("title", "-"), doctor="-", date_value="-")
            specialty_key = (str(specialty["id"]), str(facility["id"]))
            if specialty_key not in specialty_seen:
                specialties.append(
                    {
                        "id": str(specialty["id"]),
                        "facility_id": str(facility["id"]),
                        "title": specialty.get("title", ""),
                        "ab_booking_enabled": 1 if specialty.get("ab_booking_enabled", True) else 0,
                    }
                )
                specialty_seen.add(specialty_key)
                if monitor:
                    monitor.set_counts(specialty_count=len(specialties))

            doctor_items = _fetch_json(
                session,
                (
                    f"{API_BASE}/ab-doctor/?ab_doctor_speciality_id={specialty['id']}"
                    f"&vinmec_place_id={facility['id']}"
                ),
                timeout,
                monitor,
            )
            if monitor:
                monitor.log(
                    f"{facility['title']} / {specialty.get('title', '')}: nhận {len(doctor_items)} bác sĩ"
                )
            for doctor in doctor_items:
                if monitor:
                    monitor.set_context(doctor=doctor.get("heading", "-"))
                doctor_key = (str(doctor.get("id")), str(facility["id"]), str(specialty["id"]))
                if doctor_key not in doctor_seen:
                    doctors.append(
                        {
                            "id": str(doctor.get("id")),
                            "facility_id": str(facility["id"]),
                            "specialty_id": str(specialty["id"]),
                            "heading": doctor.get("heading", ""),
                            "subheading": doctor.get("subheading", ""),
                            "vinmec_website_id": str(doctor.get("vinmec_website_id") or ""),
                            "price_json": json.dumps(doctor.get("price"), ensure_ascii=False),
                            "extra_price_json": json.dumps(doctor.get("extra_price"), ensure_ascii=False),
                            "ab_booking_enabled": 1 if doctor.get("ab_booking_enabled", True) else 0,
                        }
                    )
                    doctor_seen.add(doctor_key)
                    if monitor:
                        monitor.set_counts(doctor_count=len(doctors))

                for offset in range(days_ahead):
                    selected_day = date.today() + timedelta(days=offset)
                    if monitor:
                        monitor.set_context(date_value=selected_day.isoformat())
                    slot_items = _fetch_json(
                        session,
                        (
                            f"{API_BASE}/ab-time-slot/?doctor_id={doctor['id']}"
                            f"&doctor_speciality_id={specialty['id']}"
                            f"&vinmec_place_id={facility['id']}"
                            f"&date={selected_day.isoformat()}"
                        ),
                        timeout,
                        monitor,
                        allow_nonfatal=True,
                    )
                    if monitor and slot_items:
                        monitor.log(
                            f"{doctor.get('heading', 'Bác sĩ')} - {selected_day.isoformat()}: {len(slot_items)} slot"
                        )
                    for slot in slot_items:
                        slot_id = str(slot.get("id"))
                        if slot_id in slot_seen:
                            continue
                        slots.append(
                            {
                                "id": slot_id,
                                "doctor_id": str(doctor.get("id")),
                                "specialty_id": str(specialty["id"]),
                                "facility_id": str(facility["id"]),
                                "date": selected_day.isoformat(),
                                "start_time": slot.get("start_time"),
                                "end_time": slot.get("end_time"),
                                "extra_booking": 1 if slot.get("extra_booking", False) else 0,
                            }
                        )
                        slot_seen.add(slot_id)
                        if monitor:
                            monitor.set_counts(slot_count=len(slots))

    raw_payload = {
        "source_url": BOOKING_URL,
        "page_title": soup.title.get_text(" ", strip=True) if soup.title else "",
        "generated_at": datetime.utcnow().isoformat(),
        "facilities": facilities,
        "specialties": specialties,
        "doctors": doctors,
        "slots": slots,
    }
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    snapshot_path = RAW_DIR / f"vinmec_catalog_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    if monitor:
        monitor.update_stage("Ghi snapshot raw", str(snapshot_path))
    snapshot_path.write_text(json.dumps(raw_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    raw_payload["snapshot_path"] = str(snapshot_path)
    return raw_payload


def save_catalog_to_database(payload: dict[str, Any], monitor: CrawlMonitor | None = None) -> None:
    initialize_database()
    connection = get_connection()
    started_at = datetime.utcnow().isoformat()
    try:
        with connection:
            if monitor:
                monitor.update_stage("Xóa dữ liệu cũ trong database")
            connection.execute("DELETE FROM facilities")
            connection.execute("DELETE FROM specialties")
            connection.execute("DELETE FROM doctors")
            connection.execute("DELETE FROM slots")

            if monitor:
                monitor.update_stage("Lưu facilities vào database")
            connection.executemany(
                """
                INSERT INTO facilities (id, slug, title, address, city, latitude, longitude)
                VALUES (:id, :slug, :title, :address, :city, :latitude, :longitude)
                """,
                payload["facilities"],
            )
            if monitor:
                monitor.update_stage("Lưu specialties vào database")
            connection.executemany(
                """
                INSERT INTO specialties (id, facility_id, title, ab_booking_enabled)
                VALUES (:id, :facility_id, :title, :ab_booking_enabled)
                """,
                payload["specialties"],
            )
            if monitor:
                monitor.update_stage("Lưu doctors vào database")
            connection.executemany(
                """
                INSERT INTO doctors (
                    id, facility_id, specialty_id, heading, subheading,
                    vinmec_website_id, price_json, extra_price_json, ab_booking_enabled
                )
                VALUES (
                    :id, :facility_id, :specialty_id, :heading, :subheading,
                    :vinmec_website_id, :price_json, :extra_price_json, :ab_booking_enabled
                )
                """,
                payload["doctors"],
            )
            if monitor:
                monitor.update_stage("Lưu slots vào database")
            connection.executemany(
                """
                INSERT INTO slots (
                    id, doctor_id, specialty_id, facility_id, date,
                    start_time, end_time, extra_booking
                )
                VALUES (
                    :id, :doctor_id, :specialty_id, :facility_id, :date,
                    :start_time, :end_time, :extra_booking
                )
                """,
                payload["slots"],
            )
            if monitor:
                monitor.update_stage("Ghi lịch sử crawl")
            connection.execute(
                """
                INSERT INTO crawl_runs (
                    source_url, started_at, finished_at, status,
                    facility_count, specialty_count, doctor_count, slot_count, note
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    BOOKING_URL,
                    started_at,
                    datetime.utcnow().isoformat(),
                    "success",
                    len(payload["facilities"]),
                    len(payload["specialties"]),
                    len(payload["doctors"]),
                    len(payload["slots"]),
                    payload.get("snapshot_path"),
                ),
            )
    finally:
        connection.close()


def _fetch_facilities(session: requests.Session, timeout: int, monitor: CrawlMonitor | None = None) -> list[dict[str, Any]]:
    items = _fetch_json(session, f"{API_BASE}/vinmec-place/", timeout, monitor)
    return [
        {
            "id": str(item.get("id")),
            "slug": slugify(item.get("title", "")),
            "title": item.get("title", ""),
            "address": item.get("address", ""),
            "city": item.get("province_name") or item.get("city") or "",
            "latitude": item.get("latitude"),
            "longitude": item.get("longitude"),
        }
        for item in items
    ]


def _fetch_json(
    session: requests.Session,
    url: str,
    timeout: int,
    monitor: CrawlMonitor | None = None,
    allow_nonfatal: bool = False,
) -> list[dict[str, Any]]:
    last_error: Exception | None = None
    for attempt in range(1, 4):
        try:
            if monitor:
                monitor.increment_requests()
            response = session.get(url, timeout=timeout)
            response.raise_for_status()
            payload = response.json()
            if isinstance(payload, list):
                return payload
            if isinstance(payload, dict):
                data = payload.get("data", [])
                if isinstance(data, list):
                    return data
                return []
            return []
        except requests.exceptions.RequestException as exc:
            last_error = exc
            if monitor:
                monitor.warning(f"Lỗi request lần {attempt}/3: {exc}")
            if attempt < 3:
                time.sleep(1.2 * attempt)
                continue

    if allow_nonfatal:
        if monitor:
            monitor.warning(f"Bỏ qua endpoint lỗi sau 3 lần thử: {url}")
        return []

    raise last_error if last_error else RuntimeError(f"Không lấy được dữ liệu từ {url}")
