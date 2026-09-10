import os
import sys
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database.db as db_module
from database.db import init_db, get_db

TEST_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_medikiosk.db")


def setup_module():
    db_module.DB_PATH = TEST_DB
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    init_db()


def teardown_module():
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)


def test_database_initialization():
    conn = get_db()
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
    conn.close()
    table_names = {t["name"] for t in tables}
    required = {
        "users", "patients", "doctors", "locations", "doctor_locations",
        "schedules", "blocked_slots", "appointments", "prescriptions",
        "notifications", "documents", "ratings", "ai_consultations", "ai_messages",
    }
    assert required.issubset(table_names)


def test_foreign_keys_enabled():
    conn = get_db()
    result = conn.execute("PRAGMA foreign_keys").fetchone()
    conn.close()
    assert result[0] == 1


def test_unique_email_constraint():
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO users (email, password_hash, role, first_name, last_name) VALUES (?, ?, 'patient', ?, ?)",
            ("test@constraint.com", "hash", "Test", "User"),
        )
        conn.commit()
        try:
            conn.execute(
                "INSERT INTO users (email, password_hash, role, first_name, last_name) VALUES (?, ?, 'patient', ?, ?)",
                ("test@constraint.com", "hash2", "Test", "User2"),
            )
            conn.commit()
            assert False, "Expected IntegrityError for duplicate email"
        except sqlite3.IntegrityError:
            pass
    finally:
        conn.execute("DELETE FROM users WHERE email = ?", ("test@constraint.com",))
        conn.commit()
        conn.close()


def test_rating_constraint():
    conn = get_db()
    try:
        try:
            conn.execute(
                "INSERT INTO ratings (patient_id, doctor_id, rating) VALUES (1, 1, 10)"
            )
            conn.commit()
            assert False, "Expected IntegrityError for rating > 5"
        except sqlite3.IntegrityError:
            pass
    finally:
        conn.close()