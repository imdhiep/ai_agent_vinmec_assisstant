from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path


DB_PATH = Path(__file__).resolve().parent.parent / "data" / "vinmec_catalog.db"


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database() -> None:
    connection = get_connection()
    try:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS crawl_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_url TEXT NOT NULL,
                started_at TEXT NOT NULL,
                finished_at TEXT NOT NULL,
                status TEXT NOT NULL,
                facility_count INTEGER NOT NULL DEFAULT 0,
                specialty_count INTEGER NOT NULL DEFAULT 0,
                doctor_count INTEGER NOT NULL DEFAULT 0,
                slot_count INTEGER NOT NULL DEFAULT 0,
                note TEXT
            );

            CREATE TABLE IF NOT EXISTS facilities (
                id TEXT PRIMARY KEY,
                slug TEXT,
                title TEXT NOT NULL,
                address TEXT,
                city TEXT,
                latitude REAL,
                longitude REAL
            );

            CREATE TABLE IF NOT EXISTS specialties (
                id TEXT NOT NULL,
                facility_id TEXT NOT NULL,
                title TEXT NOT NULL,
                ab_booking_enabled INTEGER NOT NULL DEFAULT 1,
                PRIMARY KEY (id, facility_id)
            );

            CREATE TABLE IF NOT EXISTS doctors (
                id TEXT NOT NULL,
                facility_id TEXT NOT NULL,
                specialty_id TEXT NOT NULL,
                heading TEXT NOT NULL,
                subheading TEXT,
                vinmec_website_id TEXT,
                price_json TEXT,
                extra_price_json TEXT,
                ab_booking_enabled INTEGER NOT NULL DEFAULT 1,
                PRIMARY KEY (id, facility_id, specialty_id)
            );

            CREATE TABLE IF NOT EXISTS slots (
                id TEXT PRIMARY KEY,
                doctor_id TEXT NOT NULL,
                specialty_id TEXT NOT NULL,
                facility_id TEXT NOT NULL,
                date TEXT NOT NULL,
                start_time TEXT,
                end_time TEXT,
                extra_booking INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS booking_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_name TEXT NOT NULL,
                phone TEXT NOT NULL,
                birth_date TEXT NOT NULL,
                gender TEXT NOT NULL,
                email TEXT,
                facility_id TEXT NOT NULL,
                specialty_id TEXT NOT NULL,
                doctor_id TEXT,
                slot_id TEXT,
                symptom_text TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )
        connection.commit()
    finally:
        connection.close()


def clear_catalog_tables(connection: sqlite3.Connection) -> None:
    connection.execute("DELETE FROM facilities")
    connection.execute("DELETE FROM specialties")
    connection.execute("DELETE FROM doctors")
    connection.execute("DELETE FROM slots")
    connection.commit()


def begin_crawl_run(source_url: str, note: str | None = None) -> int:
    connection = get_connection()
    started_at = datetime.utcnow().isoformat()
    try:
        cursor = connection.execute(
            """
            INSERT INTO crawl_runs (
                source_url, started_at, finished_at, status,
                facility_count, specialty_count, doctor_count, slot_count, note
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (source_url, started_at, started_at, "running", 0, 0, 0, 0, note),
        )
        connection.commit()
        return int(cursor.lastrowid)
    finally:
        connection.close()


def update_crawl_run(
    run_id: int,
    *,
    status: str | None = None,
    facility_count: int | None = None,
    specialty_count: int | None = None,
    doctor_count: int | None = None,
    slot_count: int | None = None,
    note: str | None = None,
) -> None:
    connection = get_connection()
    try:
        current = connection.execute(
            """
            SELECT status, facility_count, specialty_count, doctor_count, slot_count, note
            FROM crawl_runs
            WHERE id = ?
            """,
            (run_id,),
        ).fetchone()
        if not current:
            return

        connection.execute(
            """
            UPDATE crawl_runs
            SET finished_at = ?,
                status = ?,
                facility_count = ?,
                specialty_count = ?,
                doctor_count = ?,
                slot_count = ?,
                note = ?
            WHERE id = ?
            """,
            (
                datetime.utcnow().isoformat(),
                status or current["status"],
                facility_count if facility_count is not None else current["facility_count"],
                specialty_count if specialty_count is not None else current["specialty_count"],
                doctor_count if doctor_count is not None else current["doctor_count"],
                slot_count if slot_count is not None else current["slot_count"],
                note if note is not None else current["note"],
                run_id,
            ),
        )
        connection.commit()
    finally:
        connection.close()
