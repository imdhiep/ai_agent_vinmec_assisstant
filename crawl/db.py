from __future__ import annotations

import sqlite3
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
