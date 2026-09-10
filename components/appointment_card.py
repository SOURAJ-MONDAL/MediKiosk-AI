import streamlit as st
from utils.helpers import format_date, format_time, get_day_name
from utils.constants import APPOINTMENT_STATUSES


def render_appointment_card(appointment: dict, role: str = "patient"):
    status_key = appointment.get("status", "booked")
    status_info = APPOINTMENT_STATUSES.get(status_key, APPOINTMENT_STATUSES["booked"])
    badge_class = f"mk-badge-{status_info['color']}"

    header_left = ""
    header_right = f"<span class='mk-badge {badge_class}'>{status_key.title()}</span>"

    if role == "patient":
        name = f"Dr. {appointment.get('doctor_first_name', '')} {appointment.get('doctor_last_name', '')}"
        subtitle = appointment.get("specialization", "")
    else:
        name = f"{appointment.get('patient_first_name', '')} {appointment.get('patient_last_name', '')}"
        subtitle = "Patient"

    date_str = appointment.get("appointment_date", "")
    time_str = appointment.get("appointment_time", "")
    try:
        weekday = get_day_name(__import__("datetime").datetime.strptime(date_str, "%Y-%m-%d").weekday())
    except (ValueError, TypeError):
        weekday = ""

    st.markdown(f"""
    <div class="mk-card">
        <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:0.5rem;">
            <div>
                <div class="mk-card-title">{name}</div>
                <div class="mk-card-subtitle">{subtitle}</div>
            </div>
            {header_right}
        </div>
        <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap:0.6rem; margin:0.6rem 0;">
            <div class="mk-info-row">
                <div class="mk-info-icon">📍</div>
                <div><div class="mk-info-label">Location</div><div class="mk-info-value">{appointment.get('location_name', '')}</div></div>
            </div>
            <div class="mk-info-row">
                <div class="mk-info-icon">📅</div>
                <div><div class="mk-info-label">Date</div><div class="mk-info-value">{format_date(date_str)}</div></div>
            </div>
            <div class="mk-info-row">
                <div class="mk-info-icon">🕐</div>
                <div><div class="mk-info-label">Time</div><div class="mk-info-value">{format_time(time_str)}</div></div>
            </div>
        </div>
        {f"<div style='font-size:0.82rem; color:#6b7f94; margin-top:0.2rem;'>Reason: {appointment.get('reason', '')}</div>" if appointment.get("reason") else ""}
    </div>
    """, unsafe_allow_html=True)