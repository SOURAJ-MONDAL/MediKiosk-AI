import os
import sys
import streamlit as st
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.db import init_db
from components.sidebar import render_sidebar
from services.auth_service import AuthService
from utils.auth_session import auto_login_script, clear_persistent_cookie, set_persistent_cookie

init_db()


def bootstrap_seed():
    from database.seed import seed_database
    seed_database()


bootstrap_seed()

st.set_page_config(
    page_title="MediKiosk — AI Health Assistant",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

if "user" not in st.session_state:
    st.session_state.user = None
if "_auth_token" not in st.session_state:
    st.session_state._auth_token = None

pending_cookie = st.session_state.pop("_pending_cookie", None)

if st.session_state.get("user"):
    if pending_cookie:
        set_persistent_cookie(pending_cookie)
else:
    if pending_cookie == "":
        clear_persistent_cookie()
    else:
        auto_token = st.query_params.get("auto_token")
        if auto_token:
            user = AuthService.get_user_by_token(auto_token)
            if user:
                st.session_state.user = user
                st.session_state._auth_token = auto_token
            del st.query_params["auto_token"]
        if not st.session_state.get("user"):
            auto_login_script()

user = st.session_state.user

home = st.Page("app_pages/home.py", title="Home", icon=":material/home:", url_path="home")
login = st.Page("app_pages/login.py", title="Login", icon=":material/login:", url_path="login")
register = st.Page("app_pages/register.py", title="Sign up", icon=":material/person_add:", url_path="register")
ai_assistant = st.Page("app_pages/ai_assistant.py", title="AI Assistant", icon=":material/smart_toy:", url_path="ai")
doctors = st.Page("app_pages/doctors.py", title="Find Doctors", icon=":material/search:", url_path="doctors")
prescriptions = st.Page("app_pages/prescriptions.py", title="Prescriptions & Reviews", icon=":material/medication:", url_path="prescriptions")
documents = st.Page("app_pages/documents.py", title="Documents", icon=":material/folder:", url_path="documents")
profile = st.Page("app_pages/profile.py", title="Profile", icon=":material/person:", url_path="profile")
patient_dashboard = st.Page("app_pages/patient_dashboard.py", title="My Dashboard", icon=":material/dashboard:", url_path="dashboard")
doctor_dashboard = st.Page("app_pages/doctor_dashboard.py", title="Doctor Dashboard", icon=":material/medical_services:", url_path="doctor-dashboard")

if user and user.get("role") == "doctor":
    pages = [home, doctor_dashboard, profile]
elif user:
    pages = [home, patient_dashboard, ai_assistant, doctors, prescriptions, documents, profile]
else:
    pages = [home, login, register]

nav = st.navigation(pages)

render_sidebar()

nav.run()