import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database.db as db_module
from database.db import init_db, get_db
from services.prescription_service import PrescriptionService
from services.appointment_service import AppointmentService
from utils.security import hash_password


def setup_module():
    db_module.DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_medikiosk_rx.db")
    if os.path.exists(db_module.DB_PATH):
        os.remove(db_module.DB_PATH)
    init_db()
    seed_data()


def teardown_module():
    if os.path.exists(db_module.DB_PATH):
        os.remove(db_module.DB_PATH)


def seed_data():
    conn = get_db()
    try:
        cursor = conn.execute(
            "INSERT INTO users (email, password_hash, role, first_name, last_name) VALUES (?, ?, 'patient', ?, ?)",
            ("rxpatient@test.com", "hash", "Rx", "Patient"),
        )
        conn.execute("INSERT INTO patients (user_id) VALUES (?)", (cursor.lastrowid,))
        cursor = conn.execute(
            "INSERT INTO users (email, password_hash, role, first_name, last_name) VALUES (?, ?, 'doctor', ?, ?)",
            ("rxdoctor@test.com", "hash", "Rx", "Doctor"),
        )
        cursor = conn.execute(
            "INSERT INTO doctors (user_id, specialization) VALUES (?, 'General Physician')",
            (cursor.lastrowid,),
        )
        conn.execute("INSERT INTO locations (name, type, address, city) VALUES (?, 'clinic', ?, ?)",
                     ("Rx Clinic", "1 Test St", "NYC"))
        conn.commit()
    finally:
        conn.close()


def get_ids():
    conn = get_db()
    patient_id = conn.execute(
        "SELECT p.id FROM patients p JOIN users u ON p.user_id = u.id WHERE u.email = ?",
        ("rxpatient@test.com",),
    ).fetchone()["id"]
    doctor_id = conn.execute(
        "SELECT d.id FROM doctors d JOIN users u ON d.user_id = u.id WHERE u.email = ?",
        ("rxdoctor@test.com",),
    ).fetchone()["id"]
    location_id = conn.execute("SELECT id FROM locations WHERE name = ?", ("Rx Clinic",)).fetchone()["id"]
    conn.close()
    return patient_id, doctor_id, location_id


def test_prescription_creation():
    patient_id, doctor_id, location_id = get_ids()
    apt = AppointmentService.book_appointment(patient_id, doctor_id, location_id, "2026-11-01", "10:00")
    assert apt["success"] is True
    result = PrescriptionService.create_prescription(
        appointment_id=apt["appointment_id"],
        doctor_id=doctor_id,
        patient_id=patient_id,
        medicine_name="Paracetamol",
        dosage="500 mg",
        frequency="Twice daily",
        duration="5 days",
        instructions="After food",
        doctor_notes="For fever",
    )
    assert result["success"] is True
    rx = PrescriptionService.get_patient_prescriptions(patient_id)
    assert len(rx) == 1
    assert rx[0]["medicine_name"] == "Paracetamol"


def test_prescription_requires_doctor():
    patient_id, doctor_id, location_id = get_ids()
    apt = AppointmentService.book_appointment(patient_id, doctor_id, location_id, "2026-11-02", "10:00")
    assert apt["success"] is True
    result = PrescriptionService.create_prescription(
        appointment_id=apt["appointment_id"],
        doctor_id=doctor_id,
        patient_id=patient_id,
        medicine_name="Ibuprofen",
        dosage="400 mg",
    )
    assert result["success"] is True

    from database.db import get_db as dbget
    conn = dbget()
    row = conn.execute("SELECT * FROM prescriptions WHERE id = ?", (result["prescription_id"],)).fetchone()
    conn.close()
    assert row["doctor_id"] == doctor_id
    assert row["patient_id"] == patient_id


def test_ai_suggested_prescription_needs_approval():
    patient_id, doctor_id, location_id = get_ids()
    apt = AppointmentService.book_appointment(patient_id, doctor_id, location_id, "2026-11-03", "10:00")
    assert apt["success"] is True
    result = PrescriptionService.create_prescription(
        appointment_id=apt["appointment_id"],
        doctor_id=doctor_id,
        patient_id=patient_id,
        medicine_name="AI Draft Med",
        is_ai_suggested=1,
    )
    assert result["success"] is True
    rx = PrescriptionService.get_patient_prescriptions(patient_id)
    ai_rx = [r for r in rx if r["medicine_name"] == "AI Draft Med"]
    assert ai_rx
    assert ai_rx[0]["is_ai_suggested"] == 1
    assert ai_rx[0]["is_approved"] == 0
    PrescriptionService.approve_prescription(ai_rx[0]["id"])
    rx2 = PrescriptionService.get_patient_prescriptions(patient_id)
    ai_rx2 = [r for r in rx2 if r["medicine_name"] == "AI Draft Med"]
    assert ai_rx2[0]["is_approved"] == 1