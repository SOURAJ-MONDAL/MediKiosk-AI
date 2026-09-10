import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database.db as db_module
from database.db import init_db
from services.auth_service import AuthService
from utils.security import hash_password, verify_password

TEST_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_medikiosk_auth.db")


def setup_module():
    db_module.DB_PATH = TEST_DB
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    init_db()


def teardown_module():
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)


def test_password_hashing():
    hashed = hash_password("TestPassword123")
    assert hashed != "TestPassword123"
    assert "$" in hashed
    assert verify_password("TestPassword123", hashed)
    assert not verify_password("WrongPassword", hashed)


def test_registration():
    result = AuthService.register("testuser@test.com", "ValidPass123!", "Test", "User", role="patient")
    assert result["success"] is True
    assert result["role"] == "patient"


def test_registration_duplicate_email():
    AuthService.register("dup@test.com", "ValidPass123!", "Test", "User")
    result = AuthService.register("dup@test.com", "ValidPass123!", "Test", "User")
    assert result["success"] is False


def test_invalid_email_registration():
    result = AuthService.register("not-an-email", "ValidPass123!", "Test", "User")
    assert result["success"] is False


def test_weak_password_registration():
    result = AuthService.register("weak@test.com", "weak", "Test", "User")
    assert result["success"] is False


def test_login_success():
    AuthService.register("login@test.com", "ValidPass123!", "Test", "User")
    result = AuthService.login("login@test.com", "ValidPass123!")
    assert result["success"] is True
    assert result["role"] == "patient"


def test_login_invalid_credentials():
    result = AuthService.login("login@test.com", "WrongPass!")
    assert result["success"] is False
    result2 = AuthService.login("nonexistent@test.com", "Whatever123")
    assert result2["success"] is False


def test_role_registration_doctor():
    result = AuthService.register("doc@test.com", "ValidPass123!", "Dr", "Test", role="doctor")
    assert result["success"] is True
    assert result["role"] == "doctor"


def test_phone_10_and_age_validation():
    from utils.validators import validate_phone_10, validate_age
    assert validate_phone_10("9876543210")
    assert not validate_phone_10("123456789")
    assert not validate_phone_10("98765432100")
    assert not validate_phone_10("12345abcde")
    assert not validate_phone_10("")
    assert validate_age(1)
    assert validate_age(99)
    assert not validate_age(0)
    assert not validate_age(100)
    assert not validate_age(-1)


def test_register_doctor_full_profile():
    from services.doctor_service import DoctorService
    doctor_info = {
        "age": 42,
        "specialization": "Cardiology",
        "qualification": "MD (Cardiology)",
        "experience_years": 15,
        "languages": "English, Hindi",
        "bio": "Senior cardiologist with 15 years of experience.",
        "consultation_fee": 400.0,
        "hospitals": ["Apollo Hospital", "City Care Clinic"],
        "chambers": ["12, Green Park, New Delhi"],
        "license_file": b"license-bytes",
        "license_filename": "license.pdf",
        "pass_certificate": b"cert-bytes",
        "pass_certificate_filename": "cert.pdf",
        "profile_image_data": b"photo-bytes",
    }
    result = AuthService.register(
        "dr.full@test.com", "ValidPass123!", "Priya", "Sharma",
        role="doctor", phone="9876543210", doctor_info=doctor_info
    )
    assert result["success"] is True
    user = AuthService.get_user_by_id(result["user_id"])
    assert user["profile_image_data"] == b"photo-bytes"
    assert user["profile_image"].startswith("https://")
    doctor = DoctorService.get_doctor_by_user_id(result["user_id"])
    assert doctor["age"] == 42
    assert doctor["specialization"] == "Cardiology"
    assert doctor["qualification"] == "MD (Cardiology)"
    assert doctor["experience_years"] == 15
    assert doctor["languages"] == "English, Hindi"
    assert doctor["bio"] == "Senior cardiologist with 15 years of experience."
    assert doctor["consultation_fee"] == 400.0
    assert doctor["license_filename"] == "license.pdf"
    assert doctor["license_file"] == b"license-bytes"
    assert doctor["pass_certificate_filename"] == "cert.pdf"
    assert doctor["pass_certificate"] == b"cert-bytes"
    assert doctor["phone"] == "9876543210"
    hospitals = DoctorService.get_doctor_hospitals(doctor["id"])
    assert [h["hospital_name"] for h in hospitals] == ["Apollo Hospital", "City Care Clinic"]
    chambers = DoctorService.get_doctor_chambers(doctor["id"])
    assert [c["address"] for c in chambers] == ["12, Green Park, New Delhi"]


def test_register_doctor_fee_and_schedule_stored():
    from services.doctor_service import DoctorService
    doctor_info = {
        "age": 42,
        "consultation_fee": 350.0,
        "hospitals": ["Apollo Hospital"],
        "chambers": [],
        "schedule": [
            {"day": "Monday", "start": "09:00", "end": "13:00",
             "sitting": "Hospital", "hospital_name": "Apollo Hospital", "chamber_address": None},
            {"day": "Wednesday", "start": "16:00", "end": "20:00",
             "sitting": "Personal chamber", "hospital_name": None, "chamber_address": "12, Green Park, New Delhi"},
        ],
        "license_file": b"x", "license_filename": "l.pdf",
        "pass_certificate": b"y", "pass_certificate_filename": "c.pdf",
    }
    result = AuthService.register("sched@test.com", "ValidPass123!", "Priya", "Sharma",
                                   role="doctor", doctor_info=doctor_info)
    assert result["success"] is True
    doctor = DoctorService.get_doctor_by_user_id(result["user_id"])
    assert doctor["consultation_fee"] == 350.0
    entries = DoctorService.get_doctor_schedule_entries(doctor["id"])
    assert len(entries) == 2
    assert entries[0]["day"] == "Monday"
    assert entries[0]["start_time"] == "09:00"
    assert entries[0]["end_time"] == "13:00"
    assert entries[0]["sitting_type"] == "hospital"
    assert entries[0]["hospital_name"] == "Apollo Hospital"
    assert entries[1]["sitting_type"] == "chamber"
    assert entries[1]["chamber_address"] == "12, Green Park, New Delhi"


def test_update_profile_image():
    result = AuthService.register("pic@test.com", "ValidPass123!", "Test", "User")
    assert result["success"] is True
    assert AuthService.update_profile_image(result["user_id"], b"new-bytes")
    user = AuthService.get_user_by_id(result["user_id"])
    assert user["profile_image_data"] == b"new-bytes"


def test_delete_user_patient_cascades():
    from services.patient_service import PatientService
    result = AuthService.register("del.patient@test.com", "ValidPass123!", "Del", "Me")
    assert result["success"] is True
    uid = result["user_id"]
    assert PatientService.get_patient_by_user_id(uid) is not None

    assert AuthService.delete_user(uid) is True
    assert AuthService.get_user_by_id(uid) is None
    assert PatientService.get_patient_by_user_id(uid) is None
    assert AuthService.login("del.patient@test.com", "ValidPass123!")["success"] is False
    assert AuthService.delete_user(uid) is False


def test_delete_user_doctor_cascades():
    from services.doctor_service import DoctorService
    from database.db import get_db_context
    doctor_info = {
        "age": 40,
        "consultation_fee": 200.0,
        "hospitals": ["Apollo Hospital"],
        "chambers": ["12, Green Park, New Delhi"],
        "schedule": [
            {"day": "Monday", "start": "09:00", "end": "13:00",
             "sitting": "Hospital", "hospital_name": "Apollo Hospital", "chamber_address": None},
        ],
        "license_file": b"x",
        "license_filename": "license.pdf",
        "pass_certificate": b"y",
        "pass_certificate_filename": "cert.pdf",
    }
    result = AuthService.register("del.doctor@test.com", "ValidPass123!", "Dr", "Del",
                                  role="doctor", doctor_info=doctor_info)
    assert result["success"] is True
    uid = result["user_id"]
    doctor = DoctorService.get_doctor_by_user_id(uid)
    assert doctor is not None
    doctor_id = doctor["id"]
    assert DoctorService.get_doctor_hospitals(doctor_id) != []
    assert DoctorService.get_doctor_chambers(doctor_id) != []
    assert DoctorService.get_doctor_schedule_entries(doctor_id) != []

    assert AuthService.delete_user(uid) is True
    assert DoctorService.get_doctor_by_user_id(uid) is None
    assert DoctorService.get_doctor_schedule_entries(doctor_id) == []
    with get_db_context() as conn:
        hosp = conn.execute("SELECT COUNT(*) AS c FROM doctor_hospitals WHERE doctor_id = ?",
                            (doctor_id,)).fetchone()
        cham = conn.execute("SELECT COUNT(*) AS c FROM doctor_chambers WHERE doctor_id = ?",
                            (doctor_id,)).fetchone()
        sched = conn.execute("SELECT COUNT(*) AS c FROM doctor_schedules WHERE doctor_id = ?",
                             (doctor_id,)).fetchone()
        assert hosp["c"] == 0
        assert cham["c"] == 0
        assert sched["c"] == 0


def test_persistent_token_roundtrip():
    result = AuthService.register("token@test.com", "ValidPass123!", "Token", "User")
    assert result["success"] is True
    uid = result["user_id"]

    token = AuthService.create_persistent_token(uid)
    assert token and len(token) > 20

    user = AuthService.get_user_by_token(token)
    assert user is not None
    assert user["id"] == uid
    assert user["email"] == "token@test.com"

    assert AuthService.get_user_by_token("garbage-token") is None
    assert AuthService.get_user_by_token("") is None
    assert AuthService.get_user_by_token("x" * 300) is None

    assert AuthService.revoke_token(token) is True
    assert AuthService.get_user_by_token(token) is None
    assert AuthService.revoke_token(token) is False


def test_revoke_user_tokens_and_delete_cascade():
    result = AuthService.register("tokendel@test.com", "ValidPass123!", "Token", "Del")
    uid = result["user_id"]
    t1 = AuthService.create_persistent_token(uid)
    t2 = AuthService.create_persistent_token(uid)
    assert AuthService.get_user_by_token(t1) is not None
    assert AuthService.get_user_by_token(t2) is not None

    AuthService.revoke_user_tokens(uid)
    assert AuthService.get_user_by_token(t1) is None
    assert AuthService.get_user_by_token(t2) is None

    t3 = AuthService.create_persistent_token(uid)
    assert AuthService.delete_user(uid) is True
    assert AuthService.get_user_by_token(t3) is None


def test_change_password():
    AuthService.register("changepw@test.com", "ValidPass123!", "Test", "User")
    user = AuthService.get_user_by_id(1)
    result = AuthService.login("changepw@test.com", "ValidPass123!")
    user_id = result["user_id"]
    result = AuthService.change_password(user_id, "ValidPass123!", "NewValid123!")
    assert result["success"] is True
    assert AuthService.login("changepw@test.com", "NewValid123!")["success"] is True
    assert AuthService.login("changepw@test.com", "ValidPass123!")["success"] is False