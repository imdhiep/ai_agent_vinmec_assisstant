from __future__ import annotations

import json
from datetime import datetime

from crawl.db import DB_PATH, get_connection, initialize_database


class CatalogRepository:
    def __init__(self) -> None:
        initialize_database()

    def database_exists(self) -> bool:
        return DB_PATH.exists()

    def get_status(self) -> dict:
        connection = get_connection()
        try:
            last_run = connection.execute(
                """
                SELECT source_url, finished_at, facility_count, specialty_count, doctor_count, slot_count, note
                FROM crawl_runs
                ORDER BY id DESC
                LIMIT 1
                """
            ).fetchone()
            return dict(last_run) if last_run else {}
        finally:
            connection.close()

    def get_facilities(self) -> list[dict]:
        connection = get_connection()
        try:
            rows = connection.execute(
                "SELECT id, slug, title, address, city, latitude, longitude FROM facilities ORDER BY title"
            ).fetchall()
            return [dict(row) for row in rows]
        finally:
            connection.close()

    def get_specialties_by_facility(self, facility_id: str) -> list[dict]:
        connection = get_connection()
        try:
            rows = connection.execute(
                """
                SELECT id, facility_id, title, ab_booking_enabled
                FROM specialties
                WHERE facility_id = ?
                ORDER BY title
                """,
                (facility_id,),
            ).fetchall()
            return [dict(row) for row in rows]
        finally:
            connection.close()

    def get_doctors(self, facility_id: str, specialty_id: str) -> list[dict]:
        connection = get_connection()
        try:
            rows = connection.execute(
                """
                SELECT id, facility_id, specialty_id, heading, subheading, vinmec_website_id,
                       price_json, extra_price_json, ab_booking_enabled
                FROM doctors
                WHERE facility_id = ? AND specialty_id = ? AND ab_booking_enabled = 1
                ORDER BY heading
                """,
                (facility_id, specialty_id),
            ).fetchall()
            results = []
            for row in rows:
                item = dict(row)
                item["price"] = json.loads(item["price_json"]) if item["price_json"] and item["price_json"] != "null" else None
                item["extra_price"] = json.loads(item["extra_price_json"]) if item["extra_price_json"] and item["extra_price_json"] != "null" else None
                results.append(item)
            return results
        finally:
            connection.close()

    def get_slots(self, facility_id: str, specialty_id: str, doctor_id: str) -> list[dict]:
        connection = get_connection()
        try:
            rows = connection.execute(
                """
                SELECT id, doctor_id, specialty_id, facility_id, date, start_time, end_time, extra_booking
                FROM slots
                WHERE facility_id = ? AND specialty_id = ? AND doctor_id = ?
                ORDER BY start_time
                """,
                (facility_id, specialty_id, doctor_id),
            ).fetchall()
            return [dict(row) for row in rows]
        finally:
            connection.close()

    def save_booking_request(self, payload: dict) -> None:
        connection = get_connection()
        try:
            with connection:
                connection.execute(
                    """
                    INSERT INTO booking_requests (
                        patient_name, phone, birth_date, gender, email,
                        facility_id, specialty_id, doctor_id, slot_id, symptom_text, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        payload["patient_name"],
                        payload["phone"],
                        payload["birth_date"],
                        payload["gender"],
                        payload.get("email"),
                        payload["facility_id"],
                        payload["specialty_id"],
                        payload.get("doctor_id"),
                        payload.get("slot_id"),
                        payload["symptom_text"],
                        datetime.utcnow().isoformat(),
                    ),
                )
        finally:
            connection.close()


catalog_repository = CatalogRepository()
