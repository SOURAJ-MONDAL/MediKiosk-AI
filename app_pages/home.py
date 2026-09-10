import streamlit as st
from components.ui import inject_global_styles
from components.navbar import render_safety_disclaimer
from services.doctor_service import DoctorService
from services.appointment_service import AppointmentService
from utils.constants import SPECIALTIES
from utils.helpers import get_greeting, format_date, format_time
from datetime import date


def require_login():
    inject_global_styles()
    if "user" not in st.session_state or not st.session_state.user:
        st.info("Please log in to access this page.", icon=":material/lock:")
        if st.button("Go to login", icon=":material/login:"):
            st.session_state.page = "login"
            st.switch_page("app_pages/login.py")
        st.stop()


def _render_doctor_home(user):
    inject_global_styles()
    doctor = DoctorService.get_doctor_by_user_id(user["id"])
    if not doctor:
        st.error("Doctor profile not found.", icon=":material/error:")
        st.stop()

    WEEK_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    today = date.today()
    today_weekday = WEEK_DAYS[today.weekday()]
    today_iso = today.isoformat()

    st.markdown(f"""
    <div class="mk-section" style="margin-top: 0.5rem;">
        <div class="mk-eyebrow">MediKiosk</div>
        <div class="mk-section-title">{get_greeting()}, Dr. {user['first_name']} 👨‍⚕️</div>
        <div class="mk-section-sub">{doctor.get('specialization', '')} · {doctor.get('qualification', '')}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div style="height:1rem;"></div>', unsafe_allow_html=True)

    today_appointments = AppointmentService.get_doctor_appointments(doctor["id"], date_str=today_iso)
    accepted_today = [a for a in today_appointments if a["status"] == "confirmed"]

    def _status_badge(status: str) -> str:
        if status == "confirmed":
            return '<span class="mk-badge mk-badge-green">Accepted</span>'
        if status == "booked":
            return '<span class="mk-badge" style="background:#fff3cd; color:#8a6d1a;">Pending</span>'
        if status == "completed":
            return '<span class="mk-badge mk-badge-green">Completed</span>'
        if status == "cancelled":
            return '<span class="mk-badge" style="background:#fde2e2; color:#a33;">Cancelled</span>'
        if status == "no_show":
            return '<span class="mk-badge" style="background:#e8e8e8; color:#555;">No-show</span>'
        return f'<span class="mk-badge mk-badge-blue">{status.title()}</span>'

    def _appointment_actions(apt: dict):
        if apt["status"] == "booked":
            c1, c2 = st.columns([1, 1])
            with c1:
                if st.button("Accept", key=f"h_accept_{apt['id']}", icon=":material/thumb_up:", width="stretch"):
                    AppointmentService.update_status(apt["id"], "confirmed")
                    st.session_state._doctor_last_action = f"Appointment #{apt['id']} accepted."
                    st.rerun()
            with c2:
                if st.button("Cancel", key=f"h_cancel_today_{apt['id']}", icon=":material/cancel:", width="stretch"):
                    AppointmentService.update_status(apt["id"], "cancelled")
                    st.session_state._doctor_last_action = f"Appointment #{apt['id']} cancelled."
                    st.rerun()
        elif apt["status"] == "confirmed":
            c1, c2 = st.columns([1, 1])
            with c1:
                if st.button("Mark completed", key=f"h_complete_{apt['id']}", icon=":material/task_alt:", width="stretch"):
                    AppointmentService.update_status(apt["id"], "completed")
                    st.session_state._doctor_last_action = f"Appointment #{apt['id']} completed."
                    st.rerun()
            with c2:
                if st.button("Cancel", key=f"h_cancel_conf_{apt['id']}", icon=":material/cancel:", width="stretch"):
                    AppointmentService.update_status(apt["id"], "cancelled")
                    st.session_state._doctor_last_action = f"Appointment #{apt['id']} cancelled."
                    st.rerun()

    st.markdown(f"""
    <div class="mk-section" style="margin-top: 0.5rem;">
        <div class="mk-eyebrow">Today's schedule</div>
        <div class="mk-section-title">📅 {today_weekday}, {format_date(today_iso)}</div>
        <div class="mk-section-sub">{len(today_appointments)} appointment(s) today · {len(accepted_today)} accepted</div>
    </div>
    """, unsafe_allow_html=True)

    schedule_today = [s for s in DoctorService.get_doctor_schedule_entries(doctor["id"])
                      if s["day"] == today_weekday]
    schedule_today.sort(key=lambda s: s["start_time"])

    def _is_in_window(time_str: str, entry: dict) -> bool:
        return entry["start_time"] <= time_str < entry["end_time"]

    def _sitting_label(entry: dict) -> str:
        sitting = (entry.get("sitting_type") or "").lower()
        if sitting == "hospital":
            return f"Hospital · {entry.get('hospital_name') or '—'}"
        return f"Personal chamber · {entry.get('chamber_address') or '—'}"

    if schedule_today:
        for entry in schedule_today:
            window_appts = [a for a in today_appointments if _is_in_window(a["appointment_time"], entry)]
            st.markdown(f"""
            <div class="mk-card">
                <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:0.5rem;">
                    <div>
                        <div class="mk-card-title">🕐 {format_time(entry['start_time'])} – {format_time(entry['end_time'])}</div>
                        <div class="mk-card-subtitle">{_sitting_label(entry)}</div>
                    </div>
                    <span class="mk-badge mk-badge-blue">{len(window_appts)} appointment(s)</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if window_appts:
                for apt in sorted(window_appts, key=lambda a: a["appointment_time"]):
                    st.markdown(f"""
                    <div class="mk-card">
                        <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:0.5rem;">
                            <div>
                                <div class="mk-card-title">{format_time(apt['appointment_time'])} · {apt['patient_first_name']} {apt['patient_last_name']}</div>
                                <div class="mk-card-subtitle">{apt.get('location_name', '')}{f" · {apt.get('reason', '')}" if apt.get('reason') else ""}</div>
                            </div>
                            {_status_badge(apt['status'])}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    _appointment_actions(apt)
                    st.markdown('<div style="height:0.4rem;"></div>', unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="mk-card">
                    <div style="color:#6b7f94; font-size:0.9rem;">No appointments in this block yet.</div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown('<div style="height:0.6rem;"></div>', unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="mk-empty">
            <div class="mk-empty-icon">🗓️</div>
            <div class="mk-empty-title">No schedule set for today</div>
            <div class="mk-empty-text">Your weekly schedule is currently empty. Set your visiting hours at sign-up to show up here.</div>
        </div>
        """, unsafe_allow_html=True)

        if today_appointments:
            st.markdown("##### Appointments today (outside a scheduled block)")
            for apt in sorted(today_appointments, key=lambda a: a["appointment_time"]):
                st.markdown(f"""
                <div class="mk-card">
                    <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:0.5rem;">
                        <div>
                            <div class="mk-card-title">{format_time(apt['appointment_time'])} · {apt['patient_first_name']} {apt['patient_last_name']}</div>
                            <div class="mk-card-subtitle">{apt.get('location_name', '')}</div>
                        </div>
                        {_status_badge(apt['status'])}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                _appointment_actions(apt)
                st.markdown('<div style="height:0.4rem;"></div>', unsafe_allow_html=True)


def render_home():
    inject_global_styles()

    user = st.session_state.get("user")
    if user and user.get("role") == "doctor":
        _render_doctor_home(user)
        return

    if st.session_state.pop("account_deleted", False):
        st.success(
            "Your account has been permanently deleted. We're sorry to see you go.",
            icon=":material/check_circle:",
        )

    st.markdown("""
    <div class="mk-hero">
        <div class="mk-eyebrow">AI-Powered Healthcare Platform</div>
        <h1>Your Intelligent<br>Healthcare Companion</h1>
        <div class="mk-hero-sub">
            MediKiosk helps you understand your health concerns, organize your symptoms,
            discover suitable doctors, and book appointments — all in one place.
            Think of it as your intelligent health assistant that connects you with the care you need.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div style="height:1rem;"></div>', unsafe_allow_html=True)

    is_logged_in = bool(st.session_state.get("user"))
    if is_logged_in:
        left, right = st.columns(2)
        with left:
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Talk to MediKiosk AI", icon=":material/smart_toy:", width="stretch", type="primary"):
                    st.session_state.page = "ai"
                    st.switch_page("app_pages/ai_assistant.py")
            with col2:
                if st.button("Find a Doctor", icon=":material/search:", width="stretch"):
                    st.session_state.page = "doctors"
                    st.switch_page("app_pages/doctors.py")
        with right:
            if st.button("My Dashboard", icon=":material/dashboard:", width="stretch"):
                user = st.session_state.user
                if user.get("role") == "doctor":
                    st.switch_page("app_pages/doctor_dashboard.py")
                else:
                    st.switch_page("app_pages/patient_dashboard.py")
    else:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Sign Up", icon=":material/person_add:", width="stretch", type="primary"):
                st.switch_page("app_pages/register.py")
        with col2:
            if st.button("Sign In", icon=":material/login:", width="stretch", type="primary"):
                st.switch_page("app_pages/login.py")

    st.markdown('<div style="height:2.5rem;"></div>', unsafe_allow_html=True)

    stats = st.columns(4)
    doctors = DoctorService.get_all_doctors()
    specializations = doctors[0].get("specialization") if False else None
    stat_data = [
        ("10+", "Specialties"),
        (f"{len(doctors)}+", "Doctors"),
        ("6+", "Locations"),
        ("24/7", "AI Assistance"),
    ]
    for col, (value, label) in zip(stats, stat_data):
        with col:
            st.markdown(f"""
            <div class="mk-card">
                <div class="mk-stat">
                    <div class="mk-stat-value">{value}</div>
                    <div class="mk-stat-label">{label}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<div style="height:2rem;"></div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="mk-section">
        <div class="mk-section-title">How MediKiosk works</div>
        <div class="mk-section-sub">From symptom to appointment in five intelligent steps.</div>
    </div>
    """, unsafe_allow_html=True)

    steps = [
        ("🗣️", "Describe your symptoms", "Talk to the MediKiosk AI Health Assistant about how you're feeling. It asks smart follow-up questions to understand your situation."),
        ("🧠", "Get a structured health summary", "Our AI organizes your symptoms into a clear summary with urgency guidance and recommended next steps."),
        ("🩺", "Discover the right doctor", "Based on your summary, MediKiosk recommends relevant specialties. Browse, filter, and compare doctors."),
        ("📅", "Book your appointment", "Choose a doctor, location, date, and time. Get instant confirmation with a polished booking flow."),
        ("💊", "Get care and follow-up", "Attend your consultation, receive prescriptions and follow-up guidance, and track your health records."),
    ]
    for icon, title, desc in steps:
        c1, c2 = st.columns([1, 5])
        with c1:
            st.markdown(f'<div style="font-size:1.4rem; text-align:center;">{icon}</div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div style="font-weight:700; color:#1a2a3a;">{title}</div><div style="font-size:0.88rem; color:#6b7f94; line-height:1.55;">{desc}</div>', unsafe_allow_html=True)
        st.markdown('<div style="height:0.4rem;"></div>', unsafe_allow_html=True)

    st.markdown('<div style="height:2rem;"></div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="mk-section">
        <div class="mk-section-title">Everything you need, in one place</div>
    </div>
    """, unsafe_allow_html=True)

    features = [
        ("🤖", "AI Health Assistant", "Describe symptoms conversationally. Get follow-up questions and structured summaries."),
        ("🩺", "Doctor discovery", "Search across 10+ specialties, filter by location and fee, compare ratings."),
        ("📅", "Smart appointments", "Book with real availability, location selection, and instant confirmation."),
        ("🔐", "Secure records", "Your health documents, prescriptions, and history organized in one place."),
        ("⚡", "Doctor dashboard", "Doctors review patients, consult AI summaries, and issue prescriptions."),
        ("⭐", "Ratings & reviews", "Share feedback after consultations to help others choose well."),
    ]

    for i in range(0, len(features), 3):
        row = st.columns(3)
        for col, (icon, title, desc) in zip(row, features[i:i + 3]):
            with col:
                st.markdown(f"""
                <div class="mk-feature">
                    <div class="mk-feature-icon">{icon}</div>
                    <div class="mk-feature-title">{title}</div>
                    <div class="mk-feature-desc">{desc}</div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown('<div style="height:2.5rem;"></div>', unsafe_allow_html=True)

    with st.expander("Medical safety disclaimer", expanded=False, icon=":material/health_and_safety:"):
        st.markdown("""
        MediKiosk provides AI-assisted health information and appointment support.
        It is **not** a substitute for professional medical advice, diagnosis, or treatment.

        - The AI assistant offers general guidance only — it cannot diagnose you.
        - AI recommendations are suggestions, not medical prescriptions.
        - If you believe you're experiencing a medical emergency, contact your local
          emergency services or seek immediate in-person care.
        - Doctor matching is based on symptom patterns and user preference, not a diagnosis.
        """)

    render_safety_disclaimer()

    st.markdown("""
    <div class="mk-footer">
        MediKiosk — AI-assisted healthcare for everyone · Prototype for demonstration purposes
    </div>
    """, unsafe_allow_html=True)


render_home()