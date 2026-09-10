import streamlit as st
from components.ui import inject_global_styles
from services.doctor_service import DoctorService
from services.appointment_service import AppointmentService
from services.notification_service import NotificationService
from services.patient_service import PatientService
from utils.helpers import get_greeting, format_date, format_time
from components.appointment_card import render_appointment_card
from datetime import date


def require_doctor():
    inject_global_styles()
    if "user" not in st.session_state or not st.session_state.user:
        st.info("Please log in to access this page.", icon=":material/lock:")
        if st.button("Go to login", icon=":material/login:"):
            st.switch_page("app_pages/login.py")
        st.stop()
    if st.session_state.user.get("role") != "doctor":
        st.error("This page is for doctors only.", icon=":material/error:")
        st.stop()


require_doctor()

user = st.session_state.user
doctor = DoctorService.get_doctor_by_user_id(user["id"])

if not doctor:
    st.error("Doctor profile not found.", icon=":material/error:")
    st.stop()

WEEK_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

st.markdown(f"""
<div class="mk-section" style="margin-top: 0.5rem;">
    <div class="mk-eyebrow">Doctor dashboard</div>
    <div class="mk-section-title">{get_greeting()}, Dr. {user['first_name']} 👨‍⚕️</div>
    <div class="mk-section-sub">{doctor.get('specialization', '')} · {doctor.get('qualification', '')}</div>
</div>
""", unsafe_allow_html=True)

@st.dialog("Notifications", width="large")
def _show_doctor_notif_dialog():
    from components.notification_card import render_notification_card, render_empty_notifications
    notes = NotificationService.get_user_notifications(user["id"])
    if not notes:
        render_empty_notifications()
        return
    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("Mark all as read", icon=":material/done_all:", width="stretch", key="doc_mark_all"):
            NotificationService.mark_all_read(user["id"])
            st.rerun()
    with c2:
        if st.button("Close", width="stretch", key="doc_close"):
            st.rerun()
    st.divider()
    for n in notes:
        render_notification_card(n)
        cols = st.columns([1, 1])
        with cols[0]:
            if not n.get("is_read"):
                if st.button("Mark as read", key=f"doc_dlg_mark_{n['id']}", icon=":material/check:", width="stretch"):
                    NotificationService.mark_read(n["id"])
                    st.rerun()
            else:
                st.caption("✓ Read")
        with cols[1]:
            st.caption(n.get("created_at", "")[:16])
        st.divider()

unread = NotificationService.get_unread_count(user["id"])
if st.button(f"{unread} unread notifications", key="doc_open_notif", icon=":material/notifications:", width="stretch"):
    _show_doctor_notif_dialog()

st.markdown('<div style="height:1rem;"></div>', unsafe_allow_html=True)

today_appointments = AppointmentService.get_doctor_appointments(doctor["id"], date_str=date.today().isoformat())
upcoming = AppointmentService.get_upcoming_for_doctor(doctor["id"])
all_appts = AppointmentService.get_doctor_appointments(doctor["id"])
completed = [a for a in all_appts if a["status"] == "completed"]

stats = st.columns(4)
with stats[0]:
    st.metric("Today's appointments", len(today_appointments))
with stats[1]:
    st.metric("Upcoming", len(upcoming))
with stats[2]:
    st.metric("Total", len(all_appts))
with stats[3]:
    st.metric("Completed", len(completed))

st.markdown('<div style="height:1.5rem;"></div>', unsafe_allow_html=True)

if st.session_state.get("_doctor_last_action"):
    st.success(st.session_state["_doctor_last_action"])
    st.session_state["_doctor_last_action"] = None

tabs = st.tabs(["Today", "Upcoming", "Patient list", "My locations", "Quick prescription"])

with tabs[0]:
    if today_appointments:
        for apt in today_appointments:
            render_appointment_card(apt, role="doctor")
            # Show summarized version + forwarded past chats (as requested)
            _has_chat = bool(apt.get("ai_chat_history"))
            _has_summary = bool(apt.get("ai_summary"))
            if _has_chat or _has_summary:
                with st.expander("View summary sent by patient", expanded=False):
                    if _has_summary:
                        try:
                            import json as _json
                            _sum = _json.loads(apt["ai_summary"]) if isinstance(apt["ai_summary"], str) else apt["ai_summary"]
                            if isinstance(_sum, dict):
                                _sym = ", ".join(_sum.get("symptoms", [])) if _sum.get("symptoms") else ""
                                st.markdown(f"**Symptoms:** {_sym or 'Not specified'}")
                                st.markdown(f"**Duration:** {_sum.get('duration','Not specified')}")
                                st.markdown(f"**Severity:** {(_sum.get('severity','') or 'Not specified').title()}")
                                if _sum.get("affected_area") and _sum["affected_area"].lower() not in ("not specified",""):
                                    st.markdown(f"**Affected area:** {_sum['affected_area']}")
                                if _sum.get("associated_symptoms"):
                                    st.markdown(f"**Associated symptoms:** {', '.join(_sum['associated_symptoms'])}")
                                st.markdown(f"**Urgency:** {(_sum.get('urgency','') or 'moderate').title()}")
                                if _sum.get("suggested_specialties"):
                                    st.markdown(f"**Suggested specialties:** {', '.join(_sum['suggested_specialties'])}")
                                if _sum.get("suggested_medicines"):
                                    _meds = _sum["suggested_medicines"]
                                    _med_names = ", ".join(m.get("name","") if isinstance(m, dict) else str(m) for m in _meds)
                                    st.markdown(f"**Suggested medicines (info only):** {_med_names}")
                                if _sum.get("safety_notes"):
                                    st.caption(f"ℹ️ {_sum['safety_notes']}")
                            else:
                                st.markdown(str(_sum))
                        except Exception:
                            st.markdown(apt["ai_summary"])
                    # Also show what patient said + forwarded past chats if any
                    if _has_chat:
                        try:
                            import json as _json
                            _chat = _json.loads(apt["ai_chat_history"]) if isinstance(apt["ai_chat_history"], str) else apt["ai_chat_history"]
                            # Detect forwarded past chats marker
                            _has_forwarded = any("[Forwarded past chat" in m.get("content","") for m in _chat)
                            if _has_forwarded:
                                st.markdown("**Forwarded past chats:**")
                                for m in _chat:
                                    if "[Forwarded past chat" in m.get("content",""):
                                        st.markdown(f"---\n*{m['content']}*")
                                    elif m.get("role") == "user":
                                        st.markdown(f"**Patient:** {m.get('content','')}")
                                    else:
                                        st.markdown(f"*{m.get('role','').title()}:* {m.get('content','')}")
                            else:
                                # fallback: just show user messages as before
                                _user_only = [m for m in _chat if m.get("role") == "user"]
                                if _user_only:
                                    st.markdown("**What patient said:**")
                                    for m in _user_only:
                                        st.markdown(f"- {m.get('content','')}")
                        except Exception:
                            st.markdown(apt["ai_chat_history"])
            c1, c2, c3 = st.columns(3)
            with c1:
                if apt["status"] == "booked":
                    if st.button("Start consultation", key=f"start_{apt['id']}", icon=":material/play_arrow:", width="stretch"):
                        AppointmentService.update_status(apt["id"], "confirmed")
                        st.session_state._doctor_last_action = f"Appointment #{apt['id']} confirmed."
                        st.rerun()
            with c2:
                if apt["status"] in ("booked", "confirmed"):
                    if st.button("Mark completed", key=f"complete_{apt['id']}", icon=":material/task_alt:", width="stretch"):
                        AppointmentService.update_status(apt["id"], "completed")
                        st.session_state._doctor_last_action = f"Appointment #{apt['id']} completed."
                        st.rerun()
            with c3:
                if apt["status"] in ("booked", "confirmed"):
                    if st.button("Cancel", key=f"cancel_{apt['id']}", icon=":material/cancel:", width="stretch"):
                        AppointmentService.update_status(apt["id"], "cancelled")
                        st.session_state._doctor_last_action = f"Appointment #{apt['id']} cancelled."
                        st.rerun()
            st.markdown('<div style="height:0.5rem;"></div>', unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="mk-empty">
            <div class="mk-empty-icon">📋</div>
            <div class="mk-empty-title">No appointments today</div>
            <div class="mk-empty-text">Enjoy your day off or check your schedule.</div>
        </div>
        """, unsafe_allow_html=True)

with tabs[1]:
    if upcoming:
        for apt in upcoming:
            render_appointment_card(apt, role="doctor")
            _has_chat_u = bool(apt.get("ai_chat_history"))
            _has_summary_u = bool(apt.get("ai_summary"))
            if _has_chat_u or _has_summary_u:
                with st.expander("View summary sent by patient", expanded=False):
                    if _has_summary_u:
                        try:
                            import json as _json
                            _sum = _json.loads(apt["ai_summary"]) if isinstance(apt["ai_summary"], str) else apt["ai_summary"]
                            if isinstance(_sum, dict):
                                _sym = ", ".join(_sum.get("symptoms", [])) if _sum.get("symptoms") else ""
                                st.markdown(f"**Symptoms:** {_sym or 'Not specified'}")
                                st.markdown(f"**Duration:** {_sum.get('duration','Not specified')}")
                                st.markdown(f"**Severity:** {(_sum.get('severity','') or 'Not specified').title()}")
                                if _sum.get("suggested_specialties"):
                                    st.markdown(f"**Suggested specialties:** {', '.join(_sum['suggested_specialties'])}")
                                if _sum.get("suggested_medicines"):
                                    _meds = _sum["suggested_medicines"]
                                    _med_names = ", ".join(m.get("name","") if isinstance(m, dict) else str(m) for m in _meds)
                                    st.markdown(f"**Suggested medicines (info only):** {_med_names}")
                            else:
                                st.markdown(str(_sum))
                        except Exception:
                            st.markdown(apt["ai_summary"])
                    if _has_chat_u:
                        try:
                            import json as _json
                            _chat = _json.loads(apt["ai_chat_history"]) if isinstance(apt["ai_chat_history"], str) else apt["ai_chat_history"]
                            _has_forwarded = any("[Forwarded past chat" in m.get("content","") for m in _chat)
                            if _has_forwarded:
                                st.markdown("**Forwarded past chats:**")
                            for m in _chat:
                                if "[Forwarded past chat" in m.get("content",""):
                                    st.markdown(f"---\n*{m['content']}*")
                                elif m.get("role") == "user":
                                    st.markdown(f"**Patient:** {m.get('content','')}")
                        except Exception:
                            st.markdown(apt["ai_chat_history"])
            st.markdown('<div style="height:0.5rem;"></div>', unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="mk-empty">
            <div class="mk-empty-icon">🗓️</div>
            <div class="mk-empty-title">No upcoming appointments</div>
        </div>
        """, unsafe_allow_html=True)

with tabs[2]:
    patients = []
    for apt in all_appts:
        if apt["patient_db_id"] not in [p.get("patient_db_id") for p in patients]:
            patients.append(apt)

    if patients:
        for apt in patients:
            st.markdown(f"""
            <div class="mk-card">
                <div class="mk-card-title">{apt['patient_first_name']} {apt['patient_last_name']}</div>
                <div class="mk-card-subtitle">{apt.get('patient_email', '')} · {apt.get('patient_phone', '')}</div>
                <div style="font-size:0.85rem; color:#6b7f94;">Last visit: {format_date(apt.get('appointment_date', ''))}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="mk-empty">
            <div class="mk-empty-icon">👥</div>
            <div class="mk-empty-title">No patients yet</div>
            <div class="mk-empty-text">Patients will appear here after booking appointments.</div>
        </div>
        """, unsafe_allow_html=True)

with tabs[3]:
    st.markdown("### My schedule")
    schedules = DoctorService.get_doctor_schedule(doctor["id"])
    if schedules:
        st.dataframe(schedules, hide_index=True)
    else:
        st.info("No schedules configured.", icon=":material/info:")

    st.markdown('<div style="height:1rem;"></div>', unsafe_allow_html=True)
    st.markdown("### My locations")
    locations = DoctorService.get_doctor_locations(doctor["id"])
    if locations:
        for loc in locations:
            st.markdown(f"""
            <div class="mk-card">
                <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:0.5rem;">
                    <div>
                        <div class="mk-card-title">{loc['name']}</div>
                        <div class="mk-card-subtitle">{loc['type'].title()} · {loc['city']}, {loc.get('state', '')}</div>
                    </div>
                    <span class="mk-badge mk-badge-green">Active</span>
                </div>
                <div style="font-size:0.85rem; color:#6b7f94;">{loc['address']}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("You haven't added any locations yet.", icon=":material/info:")

with tabs[4]:
    st.markdown("### Create a quick prescription")
    st.caption("For any patient, using a recent appointment.")
    completed_appts = [a for a in all_appts if a["status"] == "completed"]
    if not completed_appts:
        st.info("No completed appointments available for prescriptions.", icon=":material/info:")
    else:
        selected_label = [f"{a['appointment_date']} - {a['patient_first_name']} {a['patient_last_name']}" for a in completed_appts]
        selection = st.selectbox("Select appointment", selected_label, key="rx_select")
        idx = selected_label.index(selection)
        selected_apt = completed_appts[idx]

        with st.form("rx_form"):
            medicine = st.text_input("Medicine name")
            c1, c2 = st.columns(2)
            with c1:
                dosage = st.text_input("Dosage", placeholder="e.g. 500 mg")
                frequency = st.text_input("Frequency", placeholder="e.g. Twice daily")
            with c2:
                duration = st.text_input("Duration", placeholder="e.g. 7 days")
                instructions = st.text_input("Instructions", placeholder="e.g. Take after food")
            doctor_notes = st.text_area("Doctor notes", height=80)
            submitted = st.form_submit_button("Save prescription", icon=":material/medication:", type="primary")

        if submitted:
            if not medicine:
                st.error("Medicine name is required.", icon=":material/error:")
            else:
                from services.prescription_service import PrescriptionService
                result = PrescriptionService.create_prescription(
                    appointment_id=selected_apt["id"],
                    doctor_id=doctor["id"],
                    patient_id=selected_apt["patient_db_id"],
                    medicine_name=medicine,
                    dosage=dosage,
                    frequency=frequency,
                    duration=duration,
                    instructions=instructions,
                    doctor_notes=doctor_notes,
                )
                if result["success"]:
                    patient_row = PatientService.get_patient_by_id(selected_apt["patient_db_id"])
                    if patient_row:
                        from services.auth_service import AuthService
                        patient_user = AuthService.get_user_by_id(patient_row["user_id"])
                        if patient_user:
                            NotificationService.notify_prescription(
                                f"{user['first_name']} {user['last_name']}",
                                patient_user["id"],
                                selected_apt["id"],
                            )
                    st.success("Prescription created!", icon=":material/check_circle:")
                    st.rerun()
                else:
                    st.error(result["error"], icon=":material/error:")