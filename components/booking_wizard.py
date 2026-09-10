import streamlit as st
from datetime import datetime, timedelta, date

from services.doctor_service import DoctorService
from services.appointment_service import AppointmentService
from services.patient_service import PatientService
from services.notification_service import NotificationService
from services.auth_service import AuthService
from utils.helpers import format_date, format_time, get_day_name

BOOKING_KEYS = [
    "booking_step", "booking_doctor_id", "booking_location_id",
    "booking_date", "booking_time", "booking_reason", "booking_confirmed",
]


def start_booking(doctor_id: int):
    for key in BOOKING_KEYS:
        if key in st.session_state:
            del st.session_state[key]
    st.session_state.booking_doctor_id = doctor_id
    st.session_state.booking_step = 2
    st.rerun()


def cancel_booking():
    for key in BOOKING_KEYS:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()


def render_booking_wizard():
    user = st.session_state.get("user")
    if not user or user.get("role") != "patient":
        return

    patient = PatientService.get_patient_by_user_id(user["id"])
    if not patient:
        st.error("Patient profile not found.", icon=":material/error:")
        return

    if not st.session_state.get("booking_doctor_id"):
        return

    if st.session_state.get("booking_confirmed"):
        render_confirmation()
        return

    step = st.session_state.get("booking_step")
    if step == 2:
        render_step_location()
    elif step == 3:
        render_step_date()
    elif step == 4:
        render_step_time()
    elif step == 5:
        render_step_confirm()


def render_confirmation():
    apt = st.session_state.booking_confirmed
    st.markdown('<div style="height:1rem;"></div>', unsafe_allow_html=True)
    c = st.columns([1, 2, 1])[1]
    with c:
        st.markdown("""
        <div class="mk-success-check"><span>✓</span></div>
        <div style="text-align:center; margin-top:1rem;">
            <div style="font-size:1.5rem; font-weight:800; color:#1a2a3a;">Appointment Confirmed</div>
            <div style="color:#6b7f94; font-size:0.95rem; margin-top:0.3rem;">Booking ID: #APP-{}</div>
        </div>
        """.format(apt["id"]), unsafe_allow_html=True)

        st.markdown('<div style="height:1rem;"></div>', unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown(f"""
            <div style="text-align:center;">
                <div style="font-weight:700; font-size:1.2rem; color:#1a2a3a;">Dr. {apt['doctor_first_name']} {apt['doctor_last_name']}</div>
                <div style="color:#0a66c2; font-size:0.9rem; margin-top:0.15rem;">{apt['specialization']}</div>
            </div>
            <div style="display:grid; grid-template-columns:1fr; gap:0.4rem; margin-top:1rem; text-align:center;">
                <div><span style="color:#6b7f94; font-size:0.82rem;">Location</span><br><span style="font-weight:600; color:#1f2937;">{apt['location_name']}</span></div>
                <div><span style="color:#6b7f94; font-size:0.82rem;">Date</span><br><span style="font-weight:600; color:#1f2937;">{format_date(apt['appointment_date'])}</span></div>
                <div><span style="color:#6b7f94; font-size:0.82rem;">Time</span><br><span style="font-weight:600; color:#1f2937;">{format_time(apt['appointment_time'])}</span></div>
                <div><span style="color:#6b7f94; font-size:0.82rem;">Status</span><br><span class="mk-badge mk-badge-green">Booked</span></div>
                <div><span style="color:#6b7f94; font-size:0.82rem;">Fee</span><br><span style="font-weight:600; color:#1f2937;">₹{apt.get('consultation_fee', 0):.0f}</span></div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('<div style="height:1rem;"></div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Book another", icon=":material/add_circle:", width="stretch"):
                cancel_booking()
        with c2:
            if st.button("Go to dashboard", icon=":material/dashboard:", width="stretch"):
                st.switch_page("app_pages/patient_dashboard.py")


def render_step_location():
    doctor = DoctorService.get_doctor_by_id(st.session_state.booking_doctor_id)
    if not doctor:
        st.error("Doctor not found. Start again.", icon=":material/error:")
        cancel_booking()
        return

    st.markdown('<div style="height:1.5rem;"></div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="mk-section">
        <div class="mk-eyebrow">Step 1 of 4</div>
        <div class="mk-section-title">Choose location</div>
        <div class="mk-section-sub">Where would you like to see Dr. {doctor['first_name']} {doctor['last_name']}?</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('<div style="height:0.5rem;"></div>', unsafe_allow_html=True)

    locations = DoctorService.get_booking_locations(doctor["id"])
    if locations:
        for loc in locations:
            # Show both name and address — handle empty city / duplicate name==address
            addr_city = ", ".join(p for p in [loc.get('address') or "", loc.get('city') or ""] if p.strip())
            # if address duplicates name, avoid "Hospital · Apollo, Apollo"
            subtitle_addr = addr_city if addr_city else "—"
            # Avoid showing "Hospital · Apollo, " when name==address and no city
            if loc.get('address') and loc['address'] == loc['name'] and not loc.get('city'):
                subtitle_addr = loc.get('city') or loc['address']
                if not subtitle_addr.strip():
                    subtitle_addr = loc['address']
            st.markdown(f"""
            <div class="mk-card" style="margin-bottom:0.6rem;">
                <div style="display:flex; align-items:center; gap:1rem; flex-wrap:wrap;">
                    <div style="flex:1; min-width:200px;">
                        <div style="font-weight:700; color:#1a2a3a;">{loc['name']}</div>
                        <div style="font-size:0.82rem; color:#6b7f94;">{loc['type'].title()} · {subtitle_addr}</div>
                        <div style="font-size:0.8rem; color:#6b7f94;">{loc.get('phone', '')}</div>
                    </div>
                    <span style="font-weight:700; color:#1a2a3a;">₹{loc.get('location_fee') or loc.get('consultation_fee') or doctor.get('consultation_fee', 0):.0f}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"Select {loc['name']}", key=f"bk_loc_{loc['id']}", width="stretch"):
                st.session_state.booking_location_id = loc["id"]
                st.session_state.booking_step = 3
                st.rerun()
    else:
        st.info("No locations available for this doctor.", icon=":material/info:")

    if st.button("← Cancel", icon=":material/arrow_back:"):
        cancel_booking()


def render_step_date():
    doctor = DoctorService.get_doctor_by_id(st.session_state.booking_doctor_id)
    if not doctor:
        st.error("Doctor not found.", icon=":material/error:")
        st.session_state.booking_step = 2
        return
    location = None
    locations = DoctorService.get_booking_locations(doctor["id"])
    for loc in locations:
        if loc["id"] == st.session_state.get("booking_location_id"):
            location = loc
            break
    loc_name = location['name'] if location else "Clinic"

    st.markdown('<div style="height:1.5rem;"></div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="mk-section">
        <div class="mk-eyebrow">Step 2 of 4</div>
        <div class="mk-section-title">Choose date</div>
        <div class="mk-section-sub">Dr. {doctor['first_name']} {doctor['last_name']} · {loc_name}</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('<div style="height:0.5rem;"></div>', unsafe_allow_html=True)

    # Build list of doctor's available dates from his weekly schedule (instead of free date picker)
    today = date.today()
    # collect available weekdays from both schedule systems
    available_weekdays = set()
    day_name_to_num = {"Monday":0, "Tuesday":1, "Wednesday":2, "Thursday":3, "Friday":4, "Saturday":5, "Sunday":6}
    # 1) legacy doctor_schedules
    try:
        sched_entries = DoctorService.get_doctor_schedule_entries(doctor["id"])
        for e in sched_entries:
            d = e.get("day")
            if d in day_name_to_num:
                available_weekdays.add(day_name_to_num[d])
    except Exception:
        pass
    # 2) real schedules for this location (if any)
    try:
        loc_id = st.session_state.get("booking_location_id")
        real_scheds = DoctorService.get_doctor_schedule(doctor["id"], location_id=loc_id) if loc_id else DoctorService.get_doctor_schedule(doctor["id"])
        for s in real_scheds:
            if "day_of_week" in s:
                available_weekdays.add(int(s["day_of_week"]))
    except Exception:
        pass

    # If no schedule at all, show all weekdays as fallback but warn
    if not available_weekdays:
        st.warning("This doctor hasn't set a weekly schedule yet. Showing all upcoming dates.", icon=":material/info:")
        available_weekdays = set(range(7))

    # Generate next 30 available dates (starting tomorrow) that match the doctor's weekdays
    upcoming_dates = []
    d = today + timedelta(days=1)
    # look ahead up to 60 days to find 30 matching dates
    for _ in range(60):
        if d.weekday() in available_weekdays:
            upcoming_dates.append(d)
            if len(upcoming_dates) >= 30:
                break
        d += timedelta(days=1)

    if not upcoming_dates:
        st.warning("No available dates found for this doctor's schedule.", icon=":material/warning:")
        if st.button("← Back", icon=":material/arrow_back:"):
            st.session_state.booking_step = 2
            st.rerun()
        return

    st.caption("Select a date from the doctor's available schedule (recurs weekly until changed):")
    # Show as grid of buttons — 3 per row
    cols_per_row = 3
    # Highlight already selected date
    selected_iso = st.session_state.get("booking_date")
    for i in range(0, len(upcoming_dates), cols_per_row):
        row_dates = upcoming_dates[i:i+cols_per_row]
        cols = st.columns(cols_per_row)
        for col, dt in zip(cols, row_dates):
            with col:
                is_selected = (dt.isoformat() == selected_iso)
                label = f"{get_day_name(dt.weekday())[:3]}, {dt.strftime('%b %d')}"
                # Show schedule time range for this weekday if available
                # Find a schedule entry for this weekday to show hours
                time_hint = ""
                for e in sched_entries if 'sched_entries' in locals() else []:
                    if day_name_to_num.get(e.get("day")) == dt.weekday():
                        time_hint = f"{e.get('start_time','')}–{e.get('end_time','')}"
                        break
                full_label = f"{label}\n{time_hint}" if time_hint else label
                btn_type = "primary" if is_selected else "secondary"
                if st.button(full_label, key=f"pick_date_{dt.isoformat()}", width="stretch", type=btn_type):
                    st.session_state.booking_date = dt.isoformat()
                    st.session_state.booking_step = 4
                    st.rerun()
        # fill remaining cols if needed
        if len(row_dates) < cols_per_row:
            for j in range(cols_per_row - len(row_dates)):
                with cols[len(row_dates)+j]:
                    st.empty()

    st.markdown('<div style="height:0.75rem;"></div>', unsafe_allow_html=True)
    if selected_iso:
        try:
            sel_dt = date.fromisoformat(selected_iso)
            st.info(f"Selected: {get_day_name(sel_dt.weekday())}, {format_date(selected_iso)}", icon=":material/calendar_month:")
        except Exception:
            pass
        if st.button("Continue to time selection", icon=":material/arrow_forward:", type="primary"):
            st.session_state.booking_step = 4
            st.rerun()

    if st.button("← Back", icon=":material/arrow_back:"):
        st.session_state.booking_step = 2
        st.rerun()


def render_step_time():
    doctor = DoctorService.get_doctor_by_id(st.session_state.get("booking_doctor_id"))
    if not doctor:
        st.error("Doctor not found.", icon=":material/error:")
        return
    locations = DoctorService.get_booking_locations(doctor["id"])
    location = next((l for l in locations if l["id"] == st.session_state.get("booking_location_id")), None)
    date_str = st.session_state.get("booking_date")
    if not date_str:
        st.warning("Please select a date first.", icon=":material/warning:")
        st.session_state.booking_step = 3
        if st.button("← Go to date selection", icon=":material/arrow_back:"):
            st.rerun()
        return

    st.markdown('<div style="height:1.5rem;"></div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="mk-section">
        <div class="mk-eyebrow">Step 3 of 4</div>
        <div class="mk-section-title">Choose time</div>
        <div class="mk-section-sub">{format_date(date_str)} · {location['name'] if location else ''}</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('<div style="height:0.5rem;"></div>', unsafe_allow_html=True)

    slots = DoctorService.get_available_slots(st.session_state.get("booking_doctor_id"),
                                              st.session_state.get("booking_location_id"), date_str)
    if not slots:
        st.warning("No available slots for this day. Please select another date.")
        st.session_state.booking_step = 3
        if st.button("← Back to date selection", icon=":material/arrow_back:"):
            st.rerun()
    else:
        st.caption("Available time slots:")
        dt_obj = datetime.strptime(date_str, "%Y-%m-%d")
        st.markdown(f"<span class='mk-badge mk-badge-cyan'>{get_day_name(dt_obj.weekday())}</span>", unsafe_allow_html=True)
        st.markdown('<div style="height:0.5rem;"></div>', unsafe_allow_html=True)

        slot_cols = st.columns(4)
        for i, slot in enumerate(slots):
            col = slot_cols[i % 4]
            with col:
                if st.button(format_time(slot), key=f"slot_{slot}_{date_str}", width="stretch"):
                    st.session_state.booking_time = slot
                    st.session_state.booking_step = 5
                    st.rerun()

    if st.button("← Back", icon=":material/arrow_back:"):
        st.session_state.booking_step = 3
        st.rerun()


def render_step_confirm():
    doctor = DoctorService.get_doctor_by_id(st.session_state.get("booking_doctor_id"))
    if not doctor:
        st.error("Doctor not found.", icon=":material/error:")
        return
    locations = DoctorService.get_booking_locations(doctor["id"])
    location = next((l for l in locations if l["id"] == st.session_state.get("booking_location_id")), None)
    if location is None:
        from database.db import get_db as _get_db
        _conn = _get_db()
        try:
            _row = _conn.execute("SELECT * FROM locations WHERE id = ?", (st.session_state.get("booking_location_id"),)).fetchone()
            location = dict(_row) if _row else {"name": "Clinic", "consultation_fee": doctor.get('consultation_fee', 0)}
        finally:
            _conn.close()
    date_str = st.session_state.get("booking_date")
    time_str = st.session_state.get("booking_time")
    if not date_str or not time_str:
        st.warning("Missing booking details. Please restart booking.", icon=":material/warning:")
        if st.button("← Restart", icon=":material/refresh:"):
            cancel_booking()
        return
    user = st.session_state.user
    patient = PatientService.get_patient_by_user_id(user["id"])

    st.markdown('<div style="height:1.5rem;"></div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="mk-section">
        <div class="mk-eyebrow">Step 4 of 4</div>
        <div class="mk-section-title">Confirm booking</div>
    </div>
    """, unsafe_allow_html=True)
    # Auto-attach what patient said (from AI chat) — not the JSON summary
    ai_summary = st.session_state.get("ai_summary_for_booking") or st.session_state.get("ai_summary")
    ai_chat = st.session_state.get("ai_chat_for_booking") or st.session_state.get("chat_history")
    has_ai = bool(ai_chat and st.session_state.get("conversation_complete") and any(m.get("role")=="user" for m in (ai_chat or [])))

    with st.container(border=True):
        st.markdown(f"""
        <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap:0.8rem;">
            <div><div class="mk-info-label">Doctor</div><div class="mk-info-value">Dr. {doctor['first_name']} {doctor['last_name']}</div></div>
            <div><div class="mk-info-label">Specialty</div><div class="mk-info-value">{doctor['specialization']}</div></div>
            <div><div class="mk-info-label">Location</div><div class="mk-info-value">{location['name']}</div></div>
            <div><div class="mk-info-label">Date</div><div class="mk-info-value">{format_date(date_str)}</div></div>
            <div><div class="mk-info-label">Time</div><div class="mk-info-value">{format_time(time_str)}</div></div>
            <div><div class="mk-info-label">Fee</div><div class="mk-info-value">₹{location.get('consultation_fee', doctor.get('consultation_fee', 0)):.0f}</div></div>
        </div>
        """, unsafe_allow_html=True)
        if has_ai:
            st.markdown('<div style="height:0.6rem;"></div>', unsafe_allow_html=True)
            st.markdown('<div class="mk-badge mk-badge-blue">A summary of what you said will be sent to the doctor</div>', unsafe_allow_html=True)
            with st.expander("Preview summary to be sent to doctor", expanded=False):
                # Show summarized version, not raw messages
                try:
                    _sym = ", ".join(ai_summary.get("symptoms", [])) if ai_summary else ""
                    _dur = ai_summary.get("duration", "") if ai_summary else ""
                    _sev = ai_summary.get("severity", "") if ai_summary else ""
                    _urg = ai_summary.get("urgency", "") if ai_summary else ""
                    _spec = ", ".join(ai_summary.get("suggested_specialties", [])) if ai_summary else ""
                    _area = ai_summary.get("affected_area", "") if ai_summary else ""
                    _assoc = ", ".join(ai_summary.get("associated_symptoms", [])) if ai_summary and ai_summary.get("associated_symptoms") else ""
                    st.markdown(f"**Symptoms:** {_sym or 'Not specified'}")
                    st.markdown(f"**Duration:** {_dur or 'Not specified'}")
                    st.markdown(f"**Severity:** {_sev.title() if _sev else 'Not specified'}")
                    if _area and _area.lower() not in ("not specified", ""):
                        st.markdown(f"**Affected area:** {_area}")
                    if _assoc:
                        st.markdown(f"**Associated symptoms:** {_assoc}")
                    st.markdown(f"**Urgency:** {_urg.title() if _urg else 'Moderate'}")
                    if _spec:
                        st.markdown(f"**Suggested specialties:** {_spec}")
                    if ai_summary and ai_summary.get("suggested_medicines"):
                        _meds = ai_summary["suggested_medicines"]
                        _med_names = ", ".join(m.get("name","") if isinstance(m, dict) else str(m) for m in _meds)
                        st.markdown(f"**Suggested medicines (info only):** {_med_names}")
                    if ai_summary and ai_summary.get("safety_notes"):
                        st.caption(f"ℹ️ {ai_summary['safety_notes']}")
                except Exception:
                    st.json(ai_summary)
        # Always show forward past chats option if any past chats exist (even without current summary)
        st.markdown('<div style="height:0.6rem;"></div>', unsafe_allow_html=True)
        st.markdown("**Forward past chats with chatbot (optional)**")
        st.caption("Select previous AI conversations to share with the doctor with this booking.")
        try:
            from services.ai_service import get_ai_service as _get_ai
            _ai_svc = _get_ai()
            _patient = PatientService.get_patient_by_user_id(user["id"])
            _past = _ai_svc.get_patient_consultations(_patient["id"], limit=10) if _patient else []
        except Exception:
            _past = []
        if _past:
            _options = {f"{c.get('created_at','')[:16]} — {(c.get('symptoms') or 'Chat')[:40]} ({c.get('urgency','')})": c["id"] for c in _past}
            _selected_labels = st.multiselect("Choose past chats to forward", list(_options.keys()), key="booking_forward_chats", placeholder="Select past chats (optional)")
            _selected_ids = [_options[l] for l in _selected_labels]
            st.session_state.booking_forward_chat_ids = _selected_ids
            if _selected_ids:
                st.caption(f"{len(_selected_ids)} past chat(s) will be forwarded with this booking.")
        else:
            st.caption("No past chats available to forward. Chat with the AI assistant and save chats to create history.")
            # keep any previous selection cleared
            if "booking_forward_chat_ids" not in st.session_state:
                st.session_state.booking_forward_chat_ids = []
        st.markdown('<div style="height:0.75rem;"></div>', unsafe_allow_html=True)
        reason = st.text_area("Reason for visit (optional)", key="booking_reason_input",
                              placeholder="Briefly describe why you'd like to see the doctor.")
        st.session_state.booking_reason = reason

        st.markdown('<div style="height:0.75rem;"></div>', unsafe_allow_html=True)
        st.markdown("**Attach document / prescription (optional)**")
        st.caption("Upload a previous prescription, lab report or other file to share with the doctor at booking.")
        doc_type_labels = {"lab_report": "Lab report", "prescription": "Prescription", "imaging": "Imaging / scan", "other": "Other"}
        c_doc1, c_doc2 = st.columns(2)
        with c_doc1:
            booking_doc_title = st.text_input("Document title", key="booking_doc_title", placeholder="e.g. Previous prescription")
        with c_doc2:
            booking_doc_type = st.selectbox("Document type", list(doc_type_labels.keys()), format_func=lambda x: doc_type_labels.get(x, x), key="booking_doc_type")
        booking_uploaded = st.file_uploader("Choose file to attach", type=["pdf", "jpg", "jpeg", "png", "gif", "doc", "docx"], key="booking_doc_file")
        booking_doc_notes = st.text_input("Document notes (optional)", key="booking_doc_notes", placeholder="e.g. For doctor reference")
        # file bytes need manual session storage (not a widget key) — do not touch booking_doc_title/type/notes keys after widget creation
        if booking_uploaded is not None:
            st.session_state.booking_doc_bytes = booking_uploaded.getvalue()
            st.session_state.booking_doc_filename = booking_uploaded.name
            st.caption(f"Selected: {booking_uploaded.name} ({len(booking_uploaded.getvalue())/1024:.0f} KB)")
        else:
            # clear file bytes if no file
            if "booking_doc_bytes" in st.session_state:
                del st.session_state.booking_doc_bytes
            if "booking_doc_filename" in st.session_state:
                del st.session_state.booking_doc_filename

    c1, c2 = st.columns(2)
    with c1:
        if st.button("← Back", icon=":material/arrow_back:"):
            st.session_state.booking_step = 4
            st.rerun()
    with c2:
        if st.button("Confirm booking", icon=":material/check_circle:", type="primary", width="stretch"):
            # Prepare AI payload — summarized version + optionally forwarded past chats
            _ai_sum = st.session_state.get("ai_summary_for_booking") or st.session_state.get("ai_summary")
            _ai_chat = st.session_state.get("ai_chat_for_booking") or st.session_state.get("chat_history")
            _forward_ids = st.session_state.get("booking_forward_chat_ids", [])
            # If past chats forwarded, append their messages to the payload
            if _forward_ids:
                try:
                    from services.ai_service import get_ai_service as _get_ai2
                    _ai_svc2 = _get_ai2()
                    _patient2 = PatientService.get_patient_by_user_id(user["id"])
                    if _patient2:
                        _past_all = _ai_svc2.get_patient_consultations(_patient2["id"], limit=20)
                        _past_map = {c["id"]: c for c in _past_all}
                        _forward_chats = []
                        for fid in _forward_ids:
                            c = _past_map.get(fid)
                            if c and c.get("messages"):
                                _forward_chats.append({"forwarded_chat_id": fid, "messages": c["messages"], "summary": c.get("parsed_summary")})
                        if _forward_chats:
                            # store forwarded chats as JSON in a separate session key and later in appointment notes
                            import json as _json2
                            st.session_state.booking_forwarded_chats_json = _json2.dumps(_forward_chats)
                        # also merge forwarded messages into chat history for doctor view
                        for fc in _forward_chats:
                            _ai_chat = (_ai_chat or []) + [{"role": "assistant", "content": f"[Forwarded past chat {fc['forwarded_chat_id']}]"}] + fc["messages"]
                except Exception:
                    pass
            _ai_sum_str = None
            _ai_chat_str = None
            # Send summarized version + forwarded past chats — allow forwarding even without current summary
            _has_forward = bool(st.session_state.get("booking_forward_chat_ids"))
            if (_ai_sum and st.session_state.get("conversation_complete")) or _has_forward:
                import json as _json
                try:
                    _ai_sum_str = _json.dumps(_ai_sum) if _ai_sum else None
                except Exception:
                    _ai_sum_str = str(_ai_sum) if _ai_sum else None
                try:
                    _ai_chat_str = _json.dumps(_ai_chat) if _ai_chat else None
                except Exception:
                    _ai_chat_str = None
            # Also prepare forwarded chats JSON for storage in appointment notes if needed
            _forward_json = st.session_state.get("booking_forwarded_chats_json")
            result = AppointmentService.book_appointment(
                patient_id=patient["id"],
                doctor_id=st.session_state.get("booking_doctor_id"),
                location_id=st.session_state.get("booking_location_id"),
                date_str=date_str,
                time_str=time_str,
                reason=st.session_state.get("booking_reason", ""),
                ai_summary=_ai_sum_str,
                ai_chat_history=_ai_chat_str,
            )
            if result["success"]:
                # If a document/prescription was attached during booking, save it now
                _doc_bytes = st.session_state.get("booking_doc_bytes")
                _doc_name = st.session_state.get("booking_doc_filename")
                _doc_title = st.session_state.get("booking_doc_title", "").strip()
                _doc_type = st.session_state.get("booking_doc_type", "other")
                _doc_notes = st.session_state.get("booking_doc_notes", "")
                if _doc_bytes and _doc_name:
                    if not _doc_title:
                        _doc_title = _doc_name
                    try:
                        from services.document_service import DocumentService
                        # include appointment reference in notes
                        _notes_with_apt = f"{_doc_notes} [Attached to appointment #{result['appointment_id']} on {date_str}]".strip() if _doc_notes else f"Attached to appointment #{result['appointment_id']} on {date_str}"
                        DocumentService.upload_document(
                            patient_id=patient["id"],
                            title=_doc_title,
                            file_bytes=_doc_bytes,
                            filename=_doc_name,
                            document_type=_doc_type,
                            notes=_notes_with_apt,
                        )
                    except Exception:
                        pass
                    # clear upload state
                    for k in ["booking_doc_bytes", "booking_doc_filename", "booking_doc_title", "booking_doc_type", "booking_doc_notes"]:
                        if k in st.session_state:
                            del st.session_state[k]
                    # clear forwarded chats state
                    for k in ["booking_forward_chat_ids", "booking_forwarded_chats_json"]:
                        if k in st.session_state:
                            del st.session_state[k]
                apt = AppointmentService.get_appointment_by_id(result["appointment_id"])
                st.session_state.booking_confirmed = apt
                NotificationService.notify_appointment_booked(
                    user["id"],
                    f"{doctor['first_name']} {doctor['last_name']}",
                    format_date(date_str),
                    format_time(time_str),
                    result["appointment_id"],
                )
                doctor_user = AuthService.get_user_by_id(doctor["user_id"])
                if doctor_user:
                    NotificationService.create_notification(
                        doctor_user["id"],
                        "New appointment",
                        f"A new patient appointment was booked for {format_date(date_str)} at {format_time(time_str)}.",
                        "appointment",
                        result["appointment_id"],
                        "appointment",
                    )
                st.rerun()
            else:
                st.error("Appointment could not be booked. " + result["error"] +
                         ". Please select another available slot.", icon=":material/error:")