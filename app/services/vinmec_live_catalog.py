from __future__ import annotations

import json
import re
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup

from app.config import BASE_DIR, DATA_DIR


BOOKING_URL = "https://www.vinmec.com/vie/dang-ky-kham/"
API_BASE = "https://api2.vinmec.com/api/v1/auto-booking/vinmec"
CATALOG_PATH = DATA_DIR / "vinmec_live_catalog.json"
LOCAL_HTML_PATH = BASE_DIR / "Đăng ký khám _ Vinmec.html"


def slugify(text: str) -> str:
    lowered = text.lower().strip()
    lowered = re.sub(r"[^\w\s-]", "", lowered, flags=re.UNICODE)
    lowered = re.sub(r"\s+", "-", lowered)
    return lowered


def load_catalog() -> dict[str, Any]:
    if CATALOG_PATH.exists():
        return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    return build_fallback_catalog_from_local_assets()


def save_catalog(payload: dict[str, Any]) -> None:
    CATALOG_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def build_fallback_catalog_from_local_assets() -> dict[str, Any]:
    html = LOCAL_HTML_PATH.read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(html, "lxml")

    facilities = []
    hospital_select = soup.select_one("#hospital")
    if hospital_select:
        for option in hospital_select.select("option"):
            value = option.get("value", "").strip()
            title = option.get_text(" ", strip=True)
            if not value or "Chọn" in title:
                continue
            facilities.append(
                {
                    "id": value,
                    "slug": slugify(title),
                    "title": title,
                    "source": "local_saved_page",
                }
            )

    return {
        "generated_at": None,
        "source_url": BOOKING_URL,
        "source": "local_saved_page",
        "facilities": facilities,
        "specialties": [],
        "doctors": [],
        "slots": [],
    }


def crawl_live_catalog(days_ahead: int = 3, timeout: int = 20) -> dict[str, Any]:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
            )
        }
    )

    booking_page = session.get(BOOKING_URL, timeout=timeout)
    booking_page.raise_for_status()
    soup = BeautifulSoup(booking_page.text, "lxml")

    facilities = _fetch_facilities(session, timeout)
    specialties = []
    doctors = []
    slots = []

    specialty_seen: set[tuple[str, str]] = set()
    doctor_seen: set[tuple[str, str, str]] = set()
    slot_seen: set[str] = set()

    for facility in facilities:
        specialty_items = _fetch_json(
            session,
            f"{API_BASE}/doctor-speciality/?vinmec_place_id={facility['id']}",
            timeout,
        )
        for specialty in specialty_items:
            specialty_key = (str(facility["id"]), str(specialty["id"]))
            if specialty_key not in specialty_seen:
                specialties.append(
                    {
                        "id": str(specialty["id"]),
                        "facility_id": str(facility["id"]),
                        "title": specialty.get("title", ""),
                        "ab_booking_enabled": specialty.get("ab_booking_enabled", True),
                    }
                )
                specialty_seen.add(specialty_key)

            doctor_items = _fetch_json(
                session,
                (
                    f"{API_BASE}/ab-doctor/?ab_doctor_speciality_id={specialty['id']}"
                    f"&vinmec_place_id={facility['id']}"
                ),
                timeout,
            )
            for doctor in doctor_items:
                doctor_key = (
                    str(doctor.get("id")),
                    str(facility["id"]),
                    str(specialty["id"]),
                )
                if doctor_key not in doctor_seen:
                    doctors.append(
                        {
                            "id": str(doctor.get("id")),
                            "facility_id": str(facility["id"]),
                            "specialty_id": str(specialty["id"]),
                            "heading": doctor.get("heading", ""),
                            "subheading": doctor.get("subheading", ""),
                            "vinmec_website_id": doctor.get("vinmec_website_id"),
                            "price": doctor.get("price"),
                            "extra_price": doctor.get("extra_price"),
                            "ab_booking_enabled": doctor.get("ab_booking_enabled", True),
                        }
                    )
                    doctor_seen.add(doctor_key)

                for offset in range(days_ahead):
                    selected_day = date.today() + timedelta(days=offset)
                    slot_items = _fetch_json(
                        session,
                        (
                            f"{API_BASE}/ab-time-slot/?doctor_id={doctor['id']}"
                            f"&doctor_speciality_id={specialty['id']}"
                            f"&vinmec_place_id={facility['id']}"
                            f"&date={selected_day.isoformat()}"
                        ),
                        timeout,
                    )
                    for slot in slot_items:
                        slot_id = str(slot.get("id"))
                        if slot_id in slot_seen:
                            continue
                        slots.append(
                            {
                                "id": slot_id,
                                "doctor_id": str(doctor.get("id")),
                                "specialty_id": str(specialty.get("id")),
                                "facility_id": str(facility["id"]),
                                "date": selected_day.isoformat(),
                                "start_time": slot.get("start_time"),
                                "end_time": slot.get("end_time"),
                                "extra_booking": slot.get("extra_booking", False),
                            }
                        )
                        slot_seen.add(slot_id)

    payload = {
        "generated_at": date.today().isoformat(),
        "source_url": BOOKING_URL,
        "source": "live_website_and_public_booking_api",
        "page_title": soup.title.get_text(" ", strip=True) if soup.title else "",
        "facilities": facilities,
        "specialties": specialties,
        "doctors": doctors,
        "slots": slots,
    }
    save_catalog(payload)
    return payload


def _fetch_facilities(session: requests.Session, timeout: int) -> list[dict[str, Any]]:
    items = _fetch_json(session, f"{API_BASE}/vinmec-place/", timeout)
    facilities = []
    for item in items:
        facilities.append(
            {
                "id": str(item.get("id")),
                "slug": slugify(item.get("title", "")),
                "title": item.get("title", ""),
                "address": item.get("address", ""),
                "city": item.get("province_name") or item.get("city") or "",
                "latitude": item.get("latitude"),
                "longitude": item.get("longitude"),
            }
        )
    return facilities


def _fetch_json(session: requests.Session, url: str, timeout: int) -> list[dict[str, Any]]:
    response = session.get(url, timeout=timeout)
    response.raise_for_status()
    payload = response.json()
    return payload.get("data", [])
