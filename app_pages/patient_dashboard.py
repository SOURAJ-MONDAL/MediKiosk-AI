import streamlit as st
from components.ui import inject_global_styles
from services.patient_service import PatientService
from services.appointment_service import AppointmentService
from services.notification_service import NotificationService
from services.doctor_service import DoctorService
from services.matching_service import MatchingService
from utils.helpers import get_greeting, format_date, format_time
from components.appointment_card import render_appointment_card
from components.notification_card import render_notification_card, render_empty_notifications
from components.doctor_card import render_doctor_card


def require_patient():
    inject_global_styles()
    if "user" not in st.session_state or not st.session_state.user:
        st.info("Please log in to access this page.", icon=":material/lock:")
        if st.button("Go to login", icon=":material/login:"):
            st.switch_page("app_pages/login.py")
        st.stop()
    if st.session_state.user.get("role") != "patient":
        st.error("This page is for patients only.", icon=":material/error:")
        st.stop()


require_patient()

user = st.session_state.user
patient = PatientService.get_patient_by_user_id(user["id"])

if not patient:
    st.error("Patient profile not found.", icon=":material/error:")
    st.stop()

g1 = st.columns([3, 1])
with g1[0]:
    st.markdown(f"""
    <div class="mk-section" style="margin-top: 0.5rem;">
        <div class="mk-eyebrow">Patient dashboard</div>
        <div class="mk-section-title">{get_greeting()}, {user['first_name']} 👋</div>
        <div class="mk-section-sub">Here's your health overview and upcoming appointments.</div>
    </div>
    """, unsafe_allow_html=True)

@st.dialog("Notifications", width="large")
def _show_notifications_dialog():
    notes = NotificationService.get_user_notifications(user["id"])
    if not notes:
        render_empty_notifications()
        return
    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("Mark all as read", icon=":material/done_all:", width="stretch"):
            NotificationService.mark_all_read(user["id"])
            st.rerun()
    with c2:
        if st.button("Close", width="stretch"):
            st.rerun()
    st.divider()
    for n in notes:
        render_notification_card(n)
        cols = st.columns([1, 1])
        with cols[0]:
            if not n.get("is_read"):
                if st.button("Mark as read", key=f"dlg_mark_{n['id']}", icon=":material/check:", width="stretch"):
                    NotificationService.mark_read(n["id"])
                    st.rerun()
            else:
                st.caption("✓ Read")
        with cols[1]:
            st.caption(n.get("created_at", "")[:16])
        st.divider()

unread = NotificationService.get_unread_count(user["id"])
with g1[1]:
    # Clickable card — clicking opens the notifications dialog
    st.markdown('<div style="margin-top: 1.5rem;"></div>', unsafe_allow_html=True)
    if st.button(f"{unread}\nUnread notifications", key="open_notif_dialog", width="stretch", icon=":material/notifications:"):
        _show_notifications_dialog()
    # Keep a subtle card look via caption
    st.caption("Click to read notifications" if unread else "No unread notifications — click to view all")

st.markdown('<div style="height:0.5rem;"></div>', unsafe_allow_html=True)

quick_actions = st.columns(4)
with quick_actions[0]:
    if st.button("AI Assistant", icon=":material/smart_toy:", width="stretch"):
        st.switch_page("app_pages/ai_assistant.py")
with quick_actions[1]:
    if st.button("Find a Doctor", icon=":material/search:", width="stretch"):
        st.switch_page("app_pages/doctors.py")
with quick_actions[2]:
    if st.button("Book appointment", icon=":material/calendar_month:", width="stretch"):
        st.session_state.selected_doctor_id = None
        st.switch_page("app_pages/doctors.py")
with quick_actions[3]:
    if st.button("My Documents", icon=":material/folder:", width="stretch"):
        st.switch_page("app_pages/documents.py")

st.markdown('<div style="height:1.5rem;"></div>', unsafe_allow_html=True)

overview = st.columns(3)
upcoming = AppointmentService.get_upcoming_for_patient(patient["id"])
completed = [a for a in AppointmentService.get_patient_appointments(patient["id"]) if a["status"] == "completed"]
prescription_count = 0
try:
    from services.prescription_service import PrescriptionService
    prescription_count = len(PrescriptionService.get_patient_prescriptions(patient["id"]))
except Exception:
    pass

with overview[0]:
    st.metric("Upcoming appointments", len(upcoming))
with overview[1]:
    st.metric("Completed visits", len(completed))
with overview[2]:
    st.metric("Prescriptions", prescription_count)

st.markdown('<div style="height:1.5rem;"></div>', unsafe_allow_html=True)

upcoming_tab, history_tab, notifications_tab, chats_tab = st.tabs(
    ["Upcoming appointments", "Appointment history", "Notifications", "Past Chats"]
)

with upcoming_tab:
    if upcoming:
        for apt in upcoming:
            render_appointment_card(apt, role="patient")
            st.markdown('<div style="height:0.5rem;"></div>', unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="mk-empty">
            <div class="mk-empty-icon">📅</div>
            <div class="mk-empty-title">No upcoming appointments</div>
            <div class="mk-empty-text">Book a consultation with a doctor to get started.</div>
        </div>
        """, unsafe_allow_html=True)

with history_tab:
    history = AppointmentService.get_patient_appointments(patient["id"])
    if history:
        for apt in history:
            render_appointment_card(apt, role="patient")
            # For completed (done) appointments, show doctor-provided prescriptions
            if apt.get("status") == "completed":
                try:
                    from services.prescription_service import PrescriptionService
                    rxs = PrescriptionService.get_appointment_prescriptions(apt["id"])
                    if rxs:
                        with st.expander(f"Prescriptions for {apt.get('appointment_date','')} — {len(rxs)}", expanded=False):
                            for rx in rxs:
                                badge = "Chatbot generated" if rx.get("is_ai_suggested") else ("Approved" if rx.get("is_approved") else "Pending")
                                badge_cls = "mk-badge-orange" if rx.get("is_ai_suggested") else ("mk-badge-green" if rx.get("is_approved") else "mk-badge-orange")
                                st.markdown(f"""
                                <div class="mk-card" style="padding:0.6rem 0.8rem; margin-bottom:0.4rem;">
                                    <div style="display:flex; justify-content:space-between; align-items:center;">
                                        <div style="font-weight:600;">{rx.get('medicine_name','')}</div>
                                        <span class="mk-badge {badge_cls} mk-badge-sm">{badge}</span>
                                    </div>
                                    <div style="font-size:0.82rem; color:#6b7f94;">{rx.get('dosage','')} · {rx.get('frequency','')} · {rx.get('duration','')}</div>
                                    {f"<div style='font-size:0.82rem; margin-top:0.2rem;'><b>Instructions:</b> {rx.get('instructions','')}</div>" if rx.get('instructions') else ""}
                                    {f"<div style='font-size:0.82rem; color:#374151;'><b>Notes:</b> {rx.get('doctor_notes','')}</div>" if rx.get('doctor_notes') else ""}
                                </div>
                                """, unsafe_allow_html=True)
                    else:
                        st.caption("No prescriptions for this visit yet.")
                except Exception:
                    pass
            st.markdown('<div style="height:0.4rem;"></div>', unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="mk-empty">
            <div class="mk-empty-icon">🗂️</div>
            <div class="mk-empty-title">No appointment history yet</div>
        </div>
        """, unsafe_allow_html=True)

with notifications_tab:
    notifications = NotificationService.get_user_notifications(user["id"])
    if notifications:
        if st.button("Mark all as read", icon=":material/done_all:"):
            NotificationService.mark_all_read(user["id"])
            st.rerun()
        st.markdown('<div style="height:0.5rem;"></div>', unsafe_allow_html=True)
        for n in notifications:
            render_notification_card(n)
            if st.button("Mark as read", key=f"mark_{n['id']}", icon=":material/check:"):
                NotificationService.mark_read(n["id"])
                st.rerun()
    else:
        render_empty_notifications()

with chats_tab:
    st.markdown("### Past AI Chats")
    st.caption("Your previous conversations with the AI assistant. Expand to view chat and summary.")
    try:
        from services.ai_service import get_ai_service
        ai_svc = get_ai_service()
        past = ai_svc.get_patient_consultations(patient["id"], limit=20)
    except Exception:
        past = []
    # Also show current unsaved session if any
    if st.session_state.get("chat_history") and not any(len(p.get("messages",[])) == len(st.session_state.chat_history) for p in past):
        with st.expander("Current session (unsaved) — " + (st.session_state.get("chat_history", [{}])[0].get("content","")[:40] if st.session_state.get("chat_history") else "new"), expanded=False):
            for m in st.session_state.get("chat_history", []):
                with st.chat_message(m.get("role","user")):
                    st.markdown(m.get("content",""))
            if st.session_state.get("ai_summary"):
                st.json(st.session_state.ai_summary)
    if not past:
        st.info("No past chats yet. Start a conversation in AI Assistant and save it.", icon=":material/chat:")
    else:
        for c in past:
            title = (c.get("symptoms") or "Chat")[:50]
            when = c.get("created_at","")[:16]
            with st.expander(f"{when} — {title} ({c.get('urgency','')})", expanded=False):
                # summary
                if c.get("parsed_summary"):
                    st.markdown("**Summary:**")
                    st.json(c["parsed_summary"])
                # messages
                st.markdown("**Chat:**")
                for m in c.get("messages", []):
                    with st.chat_message(m.get("role","user")):
                        st.markdown(m.get("content",""))
                st.caption(f"Specialties: {c.get('suggested_specialties','')} | Urgency: {c.get('urgency','')}")

st.markdown('<div style="height:1.5rem;"></div>', unsafe_allow_html=True)

st.markdown("""
<div class="mk-section">
    <div class="mk-section-title">Recommended doctors</div>
    <div class="mk-section-sub">Top-rated doctors based on your health profile.</div>
</div>
""", unsafe_allow_html=True)

recommended = MatchingService.get_top_rated_doctors(limit=3)
if recommended:
    cols = st.columns(3)
    for i, doc in enumerate(recommended):
        with cols[i % 3]:
            render_doctor_card(doc, key_prefix=f"rec_{i}")
else:
    st.info("No recommendations available yet. Explore doctors to find the right match.")