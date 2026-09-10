import streamlit as st
from components.ui import inject_global_styles
from services.patient_service import PatientService
from services.appointment_service import AppointmentService
from services.prescription_service import PrescriptionService
from services.matching_service import MatchingService
from utils.helpers import format_date, format_time


def require_patient():
    inject_global_styles()
    if "user" not in st.session_state or not st.session_state.user:
        st.info("Please log in to view prescriptions.", icon=":material/lock:")
        if st.button("Go to login", icon=":material/login:"):
            st.switch_page("app_pages/login.py")
        st.stop()
    if st.session_state.user.get("role") != "patient":
        st.error("This page is for patients.", icon=":material/error:")
        st.stop()


require_patient()

user = st.session_state.user
patient = PatientService.get_patient_by_user_id(user["id"])

if not patient:
    st.error("Patient profile not found.", icon=":material/error:")
    st.stop()

st.markdown("""
<div class="mk-section" style="margin-top: 0.5rem;">
    <div class="mk-eyebrow">Your records</div>
    <div class="mk-section-title">Prescriptions</div>
    <div class="mk-section-sub">Medications and instructions from your consultations.</div>
</div>
""", unsafe_allow_html=True)

prescriptions = PrescriptionService.get_patient_prescriptions(patient["id"])

if not prescriptions:
    st.markdown("""
    <div class="mk-empty">
        <div class="mk-empty-icon">💊</div>
        <div class="mk-empty-title">No prescriptions yet</div>
        <div class="mk-empty-text">Prescriptions from your doctor consultations will appear here.</div>
    </div>
    """, unsafe_allow_html=True)
else:
    completed_appointments = {a["id"]: a for a in AppointmentService.get_patient_appointments(patient["id"])}

    for rx in prescriptions:
        apt = completed_appointments.get(rx["appointment_id"], {})
        st.markdown(f"""
        <div class="mk-card">
            <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:0.5rem;">
                <div>
                    <div class="mk-card-title">{rx['medicine_name']}</div>
                    <div class="mk-card-subtitle">
                        Dr. {rx.get('doctor_first_name', '')} {rx.get('doctor_last_name', '')} · {rx.get('specialization', '')}
                    </div>
                </div>
                <span class="mk-badge {('mk-badge-green' if rx['is_approved'] else 'mk-badge-orange')}">
                    {'Approved' if rx['is_approved'] else ('Chatbot generated' if rx['is_ai_suggested'] else 'Pending')}
                </span>
            </div>
            <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap:0.6rem; margin:0.75rem 0;">
                <div class="mk-info-row">
                    <div class="mk-info-label">Dosage</div>
                    <div class="mk-info-value">{rx.get('dosage', '—')}</div>
                </div>
                <div class="mk-info-row">
                    <div class="mk-info-label">Frequency</div>
                    <div class="mk-info-value">{rx.get('frequency', '—')}</div>
                </div>
                <div class="mk-info-row">
                    <div class="mk-info-label">Duration</div>
                    <div class="mk-info-value">{rx.get('duration', '—')}</div>
                </div>
            </div>
            {f"<div style='font-size:0.88rem; color:#374151;'><strong>Instructions:</strong> {rx['instructions']}</div>" if rx.get('instructions') else ""}
            {f"<div style='font-size:0.88rem; color:#374151; margin-top:0.3rem;'><strong>Notes:</strong> {rx['doctor_notes']}</div>" if rx.get('doctor_notes') else ""}
            <div style="margin-top:0.6rem;">
                <span class="mk-badge mk-badge-gray mk-badge-sm">Issued {format_date(rx.get('appointment_date', ''))}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown('<div style="height:2rem;"></div>', unsafe_allow_html=True)
st.markdown("""
<div class="mk-section">
    <div class="mk-section-title">Rate your doctor</div>
    <div class="mk-section-sub">Share feedback to help other patients choose well.</div>
</div>
""", unsafe_allow_html=True)

completed = [a for a in AppointmentService.get_patient_appointments(patient["id"]) if a["status"] == "completed"]
if not completed:
    st.caption("Complete a consultation to leave a rating.")
else:
    options = [f"Dr. {a['doctor_first_name']} {a['doctor_last_name']} ({a['appointment_date']})" for a in completed]
    selection = st.selectbox("Select a completed appointment", options, key="rate_select")
    idx = options.index(selection)
    apt = completed[idx]

    rating = st.slider("Rating", 1, 5, 5, key="rate_value", help="1 = poor, 5 = excellent")
    stars = "★" * rating
    st.markdown(f"<span style='color:#f59e0b; font-size:1.2rem;'>{stars}</span>", unsafe_allow_html=True)
    review = st.text_area("Your review (optional)", key="rate_review", placeholder="How was your experience?")
    if st.button("Submit rating", icon=":material/star:", type="primary"):
        result = MatchingService.submit_rating(
            patient_id=patient["id"],
            doctor_id=apt["doctor_id"],
            rating=rating,
            review=review,
            appointment_id=apt["id"],
        )
        if result["success"]:
            st.success("Thank you for your feedback!", icon=":material/check_circle:")
            st.rerun()
        else:
            st.info(result["error"], icon=":material/info:")