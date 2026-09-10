import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from streamlit.testing.v1 import AppTest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "medikiosk.db")
TEST_APPTEST_DB = os.path.join(ROOT, "medikiosk_apptest.db")


def seed_app_db():
    if TEST_APPTEST_DB is not os.path.abspath(os.path.join(ROOT, "test_apptest_smoke.db")):
        pass
    import database.db as db_module
    db_module.DB_PATH = TEST_APPTEST_DB
    if os.path.exists(TEST_APPTEST_DB):
        os.remove(TEST_APPTEST_DB)
    from database.db import init_db
    init_db()
    from database.seed import seed_database
    seed_database()
    return TEST_APPTEST_DB


def test_app_boot():
    db_path = seed_app_db()
    import database.db as db_module
    db_module.DB_PATH = db_path

    at = AppTest.from_file(os.path.join(ROOT, "app.py"), default_timeout=20)
    at.session_state["user"] = None
    at.run()
    assert not at.exception
    assert len(at.error) == 0


def test_home_page_out_of_auth():
    db_path = seed_app_db()
    import database.db as db_module
    db_module.DB_PATH = db_path

    at = AppTest.from_file(os.path.join(ROOT, "app.py"), default_timeout=20)
    at.session_state["user"] = None
    at.run()
    assert not at.exception


def test_patient_page_guards_unauthenticated():
    db_path = seed_app_db()
    import database.db as db_module
    db_module.DB_PATH = db_path

    at = AppTest.from_file(os.path.join(ROOT, "app_pages", "patient_dashboard.py"), default_timeout=20)
    at.session_state["user"] = None
    at.run()
    assert not at.exception
    assert any("log in" in str(info.value).lower() for info in at.info)


def test_login_page_runs():
    db_path = seed_app_db()
    import database.db as db_module
    db_module.DB_PATH = db_path

    at = AppTest.from_file(os.path.join(ROOT, "app_pages", "login.py"), default_timeout=20)
    at.session_state["user"] = None
    at.run()
    assert not at.exception


def test_doctor_page_guards_unauthenticated():
    db_path = seed_app_db()
    import database.db as db_module
    db_module.DB_PATH = db_path

    at = AppTest.from_file(os.path.join(ROOT, "app_pages", "doctor_dashboard.py"), default_timeout=20)
    at.session_state["user"] = None
    at.run()
    assert not at.exception


def build_user(email, password):
    from services.auth_service import AuthService
    result = AuthService.login(email, password)
    assert result["success"] is True
    user = AuthService.get_user_by_id(result["user_id"])
    return {
        "id": user["id"],
        "email": user["email"],
        "role": user["role"],
        "first_name": user["first_name"],
        "last_name": user["last_name"],
        "full_name": f"{user['first_name']} {user['last_name']}",
    }


def get_patient_user():
    return build_user("john.smith@example.com", "Patient123!")


def get_doctor_user():
    return build_user("james.wilson@medikiosk.com", "Doctor123!")


def test_patient_dashboard_authenticated():
    db_path = seed_app_db()
    import database.db as db_module
    db_module.DB_PATH = db_path
    user = get_patient_user()

    at = AppTest.from_file(os.path.join(ROOT, "app_pages", "patient_dashboard.py"), default_timeout=20)
    at.session_state["user"] = user
    at.run()
    assert not at.exception
    assert not any(str(e.value).lower().startswith("traceback") for e in at.error)


def test_doctor_dashboard_authenticated():
    db_path = seed_app_db()
    import database.db as db_module
    db_module.DB_PATH = db_path
    user = get_doctor_user()

    at = AppTest.from_file(os.path.join(ROOT, "app_pages", "doctor_dashboard.py"), default_timeout=20)
    at.session_state["user"] = user
    at.run()
    assert not at.exception


def test_ai_assistant_authenticated():
    db_path = seed_app_db()
    import database.db as db_module
    db_module.DB_PATH = db_path
    user = get_patient_user()

    at = AppTest.from_file(os.path.join(ROOT, "app_pages", "ai_assistant.py"), default_timeout=20)
    at.session_state["user"] = user
    at.run()
    assert not at.exception


def test_doctors_page_authenticated():
    db_path = seed_app_db()
    import database.db as db_module
    db_module.DB_PATH = db_path
    user = get_patient_user()

    at = AppTest.from_file(os.path.join(ROOT, "app_pages", "doctors.py"), default_timeout=20)
    at.session_state["user"] = user
    at.run()
    assert not at.exception


def test_doctors_page_booking_wizard():
    db_path = seed_app_db()
    import database.db as db_module
    db_module.DB_PATH = db_path
    user = get_patient_user()

    at = AppTest.from_file(os.path.join(ROOT, "app_pages", "doctors.py"), default_timeout=20)
    at.session_state["user"] = user
    at.session_state["booking_doctor_id"] = 1
    at.session_state["booking_step"] = 2
    at.run()
    assert not at.exception


def test_profile_page_authenticated():
    db_path = seed_app_db()
    import database.db as db_module
    db_module.DB_PATH = db_path
    user = get_patient_user()

    at = AppTest.from_file(os.path.join(ROOT, "app_pages", "profile.py"), default_timeout=20)
    at.session_state["user"] = user
    at.run()
    assert not at.exception
    assert any(b.key == "profile_delete_account" for b in at.button)


def test_prescriptions_page_authenticated():
    db_path = seed_app_db()
    import database.db as db_module
    db_module.DB_PATH = db_path
    user = get_patient_user()

    at = AppTest.from_file(os.path.join(ROOT, "app_pages", "prescriptions.py"), default_timeout=20)
    at.session_state["user"] = user
    at.run()
    assert not at.exception


def test_documents_page_authenticated():
    db_path = seed_app_db()
    import database.db as db_module
    db_module.DB_PATH = db_path
    user = get_patient_user()

    at = AppTest.from_file(os.path.join(ROOT, "app_pages", "documents.py"), default_timeout=20)
    at.session_state["user"] = user
    at.run()
    assert not at.exception


def test_register_page_runs():
    db_path = seed_app_db()
    import database.db as db_module
    db_module.DB_PATH = db_path

    at = AppTest.from_file(os.path.join(ROOT, "app_pages", "register.py"), default_timeout=20)
    at.session_state["user"] = None
    at.run()
    assert not at.exception


def test_register_doctor_flow_runs():
    db_path = seed_app_db()
    import database.db as db_module
    db_module.DB_PATH = db_path

    at = AppTest.from_file(os.path.join(ROOT, "app_pages", "register.py"), default_timeout=20)
    at.session_state["user"] = None
    at.run()
    assert not at.exception

    at.segmented_control[0].set_value("Doctor")
    at.run()
    assert not at.exception

    [ni for ni in at.number_input if ni.key == "reg_hosp_count"][0].set_value(2)
    at.run()
    assert not at.exception

    [ni for ni in at.number_input if ni.key == "reg_chamber_count"][0].set_value(2)
    at.run()
    assert not at.exception

    assert any(ni.key == "reg_fee" for ni in at.number_input)
    assert any(sb.key == "reg_specialization" for sb in at.selectbox)
    assert any(ti.key == "reg_qualification" for ti in at.text_input)
    assert any(ni.key == "reg_experience" for ni in at.number_input)
    assert any(ti.key == "reg_languages" for ti in at.text_input)
    assert any(ta.key == "reg_bio" for ta in at.text_area)
    assert any(sb.key == "reg_sched_day_0" for sb in at.selectbox)
    assert any(sb.key == "reg_sched_start_0" for sb in at.selectbox)
    assert any(sb.key == "reg_sched_end_0" for sb in at.selectbox)
    assert any(sb.key == "reg_sched_place_0" for sb in at.selectbox)


def test_register_doctor_phone_age_sanitized():
    db_path = seed_app_db()
    import database.db as db_module
    db_module.DB_PATH = db_path

    at = AppTest.from_file(os.path.join(ROOT, "app_pages", "register.py"), default_timeout=20)
    at.session_state["user"] = None
    at.run()
    at.segmented_control[0].set_value("Doctor")
    at.run()
    assert not at.exception

    [ti for ti in at.text_input if ti.key == "reg_phone"][0].set_value("9876a")
    [ti for ti in at.text_input if ti.key == "reg_age"][0].set_value("12e")
    at.run()
    assert not at.exception
    assert at.session_state["reg_phone"] == "9876"
    assert at.session_state["reg_age"] == "12"

    [ti for ti in at.text_input if ti.key == "reg_phone"][0].set_value("987654321012345")
    at.run()
    assert not at.exception
    assert at.session_state["reg_phone"] == "9876543210"