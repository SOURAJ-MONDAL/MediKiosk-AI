import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database.db as db_module
from database.db import init_db, get_db
from services.auth_service import AuthService
from services.appointment_service import AppointmentService
from utils.security import hash_password

TEST_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_medikiosk_apt.db")


def setup_module():
    db_module.DB_PATH = TEST_DB
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    init_db()
    seed_test_data()


def teardown_module():
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)


def seed_test_data():
    conn = get_db()
    try:
        cursor = conn.execute(
            "INSERT INTO users (email, password_hash, role, first_name, last_name) VALUES (?, ?, 'patient', ?, ?)",
            ("aptpatient@test.com", hash_password("ValidPass123!"), "Apt", "Patient"),
        )
        conn.execute("INSERT INTO patients (user_id) VALUES (?)", (cursor.lastrowid,))

        cursor = conn.execute(
            "INSERT INTO users (email, password_hash, role, first_name, last_name) VALUES (?, ?, 'doctor', ?, ?)",
            ("aptdoctor@test.com", hash_password("ValidPass123!"), "Apt", "Doctor"),
        )
        cursor = conn.execute(
            "INSERT INTO doctors (user_id, specialization) VALUES (?, ?)",
            (cursor.lastrowid, "General Physician"),
        )

        conn.execute(
            "INSERT INTO locations (name, type, address, city) VALUES (?, 'clinic', ?, ?)",
            ("Test Clinic", "123 Test St", "New York"),
        )
        conn.commit()
    finally:
        conn.close()


def get_ids():
    conn = get_db()
    patient_id = conn.execute(
        "SELECT p.id FROM patients p JOIN users u ON p.user_id = u.id WHERE u.email = ?",
        ("aptpatient@test.com",),
    ).fetchone()["id"]
    doctor_id = conn.execute(
        "SELECT d.id FROM doctors d JOIN users u ON d.user_id = u.id WHERE u.email = ?",
        ("aptdoctor@test.com",),
    ).fetchone()["id"]
    location_id = conn.execute("SELECT id FROM locations WHERE name = ?", ("Test Clinic",)).fetchone()["id"]
    conn.close()
    return patient_id, doctor_id, location_id


def test_valid_booking():
    patient_id, doctor_id, location_id = get_ids()
    result = AppointmentService.book_appointment(
        patient_id, doctor_id, location_id, "2026-10-10", "10:30", "Checkup"
    )
    assert result["success"] is True


def test_duplicate_booking_prevention():
    patient_id, doctor_id, location_id = get_ids()
    r1 = AppointmentService.book_appointment(patient_id, doctor_id, location_id, "2026-10-11", "14:00")
    assert r1["success"] is True
    r2 = AppointmentService.book_appointment(patient_id, doctor_id, location_id, "2026-10-11", "14:00")
    assert r2["success"] is False


def test_cancellation():
    patient_id, doctor_id, location_id = get_ids()
    result = AppointmentService.book_appointment(patient_id, doctor_id, location_id, "2026-10-12", "09:00")
    assert result["success"] is True
    cancel = AppointmentService.cancel_appointment(result["appointment_id"])
    assert cancel["success"] is True
    apt = AppointmentService.get_appointment_by_id(result["appointment_id"])
    assert apt["status"] == "cancelled"


def test_cannot_cancel_twice():
    patient_id, doctor_id, location_id = get_ids()
    result = AppointmentService.book_appointment(patient_id, doctor_id, location_id, "2026-10-13", "11:00")
    assert result["success"] is True
    AppointmentService.cancel_appointment(result["appointment_id"])
    cancel2 = AppointmentService.cancel_appointment(result["appointment_id"])
    assert cancel2["success"] is False


def test_get_patient_appointments():
    patient_id, _, _ = get_ids()
    appts = AppointmentService.get_patient_appointments(patient_id)
    assert len(appts) > 0
    assert all(a["patient_id"] == patient_id for a in appts)