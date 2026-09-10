import streamlit as st
from components.ui import inject_global_styles
from components.account_danger import render_delete_account_trigger
from services.auth_service import AuthService
from services.patient_service import PatientService
from services.doctor_service import DoctorService
from services.prescription_service import PrescriptionService
from utils.validators import validate_phone, validate_email
from utils.helpers import calculate_age, format_date, get_profile_image_src


def require_login():
    inject_global_styles()
    if "user" not in st.session_state or not st.session_state.user:
        st.info("Please log in to view your profile.", icon=":material/lock:")
        if st.button("Go to login", icon=":material/login:"):
            st.switch_page("app_pages/login.py")
        st.stop()


require_login()

user = st.session_state.user
st.markdown("""
<div class="mk-section" style="margin-top: 0.5rem;">
    <div class="mk-eyebrow">Profile</div>
    <div class="mk-section-title">My profile</div>
    <div class="mk-section-sub">Manage your account and personal information.</div>
</div>
""", unsafe_allow_html=True)

tabs = st.tabs(["Basic info", "Password", "Account summary", "Delete account"])

with tabs[0]:
    st.markdown("### Basic information")
    with st.form("profile_form"):
        c1, c2 = st.columns(2)
        with c1:
            first_name = st.text_input("First name", value=user.get("first_name", ""))
        with c2:
            last_name = st.text_input("Last name", value=user.get("last_name", ""))

        db_user = AuthService.get_user_by_id(user["id"])
        phone = st.text_input("Phone", value=db_user.get("phone", "") if db_user else "")

        submitted = st.form_submit_button("Save changes", icon=":material/save:", type="primary")

    if submitted:
        if not first_name.strip() or not last_name.strip():
            st.error("First and last name are required.", icon=":material/error:")
        elif not validate_phone(phone):
            st.error("Invalid phone number.", icon=":material/error:")
        else:
            AuthService.update_profile(user["id"], first_name=first_name, last_name=last_name, phone=phone)
            user["first_name"] = first_name
            user["last_name"] = last_name
            user["full_name"] = f"{first_name} {last_name}"
            st.success("Profile updated.", icon=":material/check_circle:")
            st.rerun()

    st.markdown('<div style="height:1rem;"></div>', unsafe_allow_html=True)
    st.markdown("### Profile picture")
    db_user = AuthService.get_user_by_id(user["id"])
    pic_src = get_profile_image_src(db_user) if db_user else ""
    if pic_src:
        st.markdown(f"""
        <div style="width:130px; height:130px; border-radius:50%; overflow:hidden; border:3px solid var(--mk-border); box-shadow: var(--shadow-sm);">
            <img src="{pic_src}" style="width:100%; height:100%; object-fit:cover;" />
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="width:130px; height:130px; border-radius:50%; border:3px dashed var(--mk-border);
                    display:flex; align-items:center; justify-content:center; color:var(--mk-gray); font-size:0.85rem;">
            No photo yet
        </div>
        """, unsafe_allow_html=True)
    pic_file = st.file_uploader("Upload or change your profile picture", type=["jpg", "png"],
                                key="profile_pic_upload")
    if pic_file is not None:
        if st.button("Save profile picture", key="save_profile_pic", icon=":material/save:", type="primary"):
            AuthService.update_profile_image(user["id"], pic_file.getvalue())
            st.success("Profile picture updated.", icon=":material/check_circle:")
            st.rerun()

    if user.get("role") == "patient":
        patient = PatientService.get_patient_by_user_id(user["id"])
        if patient:
            st.markdown('<div style="height:1rem;"></div>', unsafe_allow_html=True)
            st.markdown("### Health profile (patients)")
            with st.form("health_form"):
                c1, c2 = st.columns(2)
                with c1:
                    dob = st.date_input("Date of birth", value=None)
                    gender = st.selectbox("Gender", ["Male", "Female", "Other", "Prefer not to say"],
                                          index=0, placeholder="Select")
                    blood_group = st.selectbox("Blood group",
                                               ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-", "Unknown"],
                                               index=8, placeholder="Select")
                with c2:
                    allergies = st.text_input("Allergies", placeholder="e.g. Penicillin")
                    emergency_contact = st.text_input("Emergency contact name")
                    emergency_phone = st.text_input("Emergency contact phone")
                medical_history = st.text_area("Medical history", height=90,
                                               placeholder="Chronic conditions, past surgeries, medications...")
                address = st.text_input("Address")
                city = st.text_input("City")
                submitted_health = st.form_submit_button("Save health profile", icon=":material/save:", type="primary")

            if submitted_health:
                dob_str = dob.isoformat() if dob else None
                PatientService.update_profile(
                    user["id"],
                    date_of_birth=dob_str,
                    gender=gender,
                    blood_group=blood_group,
                    allergies=allergies,
                    medical_history=medical_history,
                    emergency_contact=emergency_contact,
                    emergency_phone=emergency_phone,
                    address=address,
                    city=city,
                )
                st.success("Health profile saved.", icon=":material/check_circle:")
                st.rerun()

with tabs[1]:
    st.markdown("### Change password")
    st.caption("At least 8 characters with uppercase, lowercase, number and special character (e.g. !@#$%).")
    with st.form("password_form"):
        current_password = st.text_input("Current password", type="password")
        c1, c2 = st.columns(2)
        with c1:
            new_password = st.text_input("New password", type="password")
        with c2:
            confirm_password = st.text_input("Confirm new password", type="password")
        submitted_pwd = st.form_submit_button("Update password", icon=":material/key:", type="primary")

    if submitted_pwd:
        if new_password != confirm_password:
            st.error("Passwords do not match.", icon=":material/error:")
        else:
            result = AuthService.change_password(user["id"], current_password, new_password)
            if result["success"]:
                st.success("Password updated.", icon=":material/check_circle:")
            else:
                st.error(result["error"], icon=":material/error:")

with tabs[2]:
    st.markdown("### Account summary")
    db_user = AuthService.get_user_by_id(user["id"])
    if db_user:
        st.markdown(f"""
        <div class="mk-card">
            <div class="mk-info-row"><div class="mk-info-icon">👤</div><div><div class="mk-info-label">Role</div><div class="mk-info-value">{db_user['role'].title()}</div></div></div>
            <div class="mk-info-row"><div class="mk-info-icon">📧</div><div><div class="mk-info-label">Email</div><div class="mk-info-value">{db_user['email']}</div></div></div>
            <div class="mk-info-row"><div class="mk-info-icon">📞</div><div><div class="mk-info-label">Phone</div><div class="mk-info-value">{db_user.get('phone', '—')}</div></div></div>
            <div class="mk-info-row"><div class="mk-info-icon">📅</div><div><div class="mk-info-label">Joined</div><div class="mk-info-value">{format_date(db_user.get('created_at', '')[:10])}</div></div></div>
        </div>
        """, unsafe_allow_html=True)

    if user.get("role") == "patient":
        patient = PatientService.get_patient_by_user_id(user["id"])
        if patient:
            age = calculate_age(patient.get("date_of_birth", "")) if patient.get("date_of_birth") else None
            st.markdown("""
            <div style="margin-top:0.5rem;" class="mk-info-label">Health details</div>
            """, unsafe_allow_html=True)
            st.markdown(f"""
            <div class="mk-card">
                <div class="mk-info-row"><div class="mk-info-icon">🎂</div><div><div class="mk-info-value">{patient.get('date_of_birth') or 'Not set'} {f"({age} years)" if age else ''}</div></div></div>
                <div class="mk-info-row"><div class="mk-info-icon">⚧</div><div><div class="mk-info-value">{patient.get('gender') or 'Not set'}</div></div></div>
                <div class="mk-info-row"><div class="mk-info-icon">🩸</div><div><div class="mk-info-value">{patient.get('blood_group') or 'Not set'}</div></div></div>
                {f"<div class='mk-info-row'><div class='mk-info-icon'>⚠️</div><div><div class='mk-info-value'>{patient['allergies']}</div></div></div>" if patient.get('allergies') else ''}
                {f"<div class='mk-info-row'><div class='mk-info-icon'>📋</div><div><div class='mk-info-value'>{patient['medical_history']}</div></div></div>" if patient.get('medical_history') else ''}
            </div>
            """, unsafe_allow_html=True)

    if user.get("role") == "doctor":
        doctor = DoctorService.get_doctor_by_user_id(user["id"])
        if doctor:
            license_status = "Verified on file" if doctor.get("license_filename") else "Not uploaded"
            cert_status = "Verified on file" if doctor.get("pass_certificate_filename") else "Not uploaded"
            hospitals = DoctorService.get_doctor_hospitals(doctor["id"])
            chambers = DoctorService.get_doctor_chambers(doctor["id"])
            schedule_rows = DoctorService.get_doctor_schedule_entries(doctor["id"])
            hospitals_text = ", ".join(h["hospital_name"] for h in hospitals) or "—"
            chambers_text = ", ".join(c["address"] for c in chambers) or "—"
            schedule_text = "; ".join(
                f"{s['day']} {s['start_time']}–{s['end_time']} "
                f"({(s['hospital_name'] or s['chamber_address'] or '')})"
                for s in schedule_rows
            ) or "No schedule added"
            st.markdown(f"""
            <div class="mk-card">
                <div class="mk-info-row"><div class="mk-info-icon">🩺</div><div><div class="mk-info-label">Specialization</div><div class="mk-info-value">{doctor['specialization']}</div></div></div>
                <div class="mk-info-row"><div class="mk-info-icon">🎂</div><div><div class="mk-info-label">Age</div><div class="mk-info-value">{doctor.get('age', 0)} years</div></div></div>
                <div class="mk-info-row"><div class="mk-info-icon">🏥</div><div><div class="mk-info-label">Hospitals</div><div class="mk-info-value">{hospitals_text}</div></div></div>
                <div class="mk-info-row"><div class="mk-info-icon">🏠</div><div><div class="mk-info-label">Personal chambers</div><div class="mk-info-value">{chambers_text}</div></div></div>
                <div class="mk-info-row"><div class="mk-info-icon">🪪</div><div><div class="mk-info-label">License</div><div class="mk-info-value">{license_status}</div></div></div>
                <div class="mk-info-row"><div class="mk-info-icon">📜</div><div><div class="mk-info-label">Pass certificate</div><div class="mk-info-value">{cert_status}</div></div></div>
                <div class="mk-info-row"><div class="mk-info-icon">🎓</div><div><div class="mk-info-label">Qualification</div><div class="mk-info-value">{doctor.get('qualification', '—')}</div></div></div>
                <div class="mk-info-row"><div class="mk-info-icon">⏳</div><div><div class="mk-info-label">Experience</div><div class="mk-info-value">{doctor.get('experience_years', 0)} years</div></div></div>
                <div class="mk-info-row"><div class="mk-info-icon">💰</div><div><div class="mk-info-label">Consultation fee</div><div class="mk-info-value">₹{doctor.get('consultation_fee', 0):.0f}</div></div></div>
                <div class="mk-info-row"><div class="mk-info-icon">🕐</div><div><div class="mk-info-label">Schedule</div><div class="mk-info-value">{schedule_text}</div></div></div>
                <div class="mk-info-row"><div class="mk-info-icon">⭐</div><div><div class="mk-info-label">Rating</div><div class="mk-info-value">★ {doctor.get('rating', 0):.1f} ({doctor.get('total_ratings', 0)} ratings)</div></div></div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown('<div style="height:1rem;"></div>', unsafe_allow_html=True)
            st.markdown("### Consultation fee")
            st.caption("Professional details (specialization, qualification, schedule and more) are set at sign-up.")
            with st.form("doctor_fee_form"):
                fee = st.number_input("Consultation fee (₹)", 0.0, 1000.0,
                                      float(doctor.get("consultation_fee", 0)), step=10.0)
                submitted_fee = st.form_submit_button("Save fee", icon=":material/save:", type="primary")

            if submitted_fee:
                DoctorService.update_doctor_profile(doctor["id"], consultation_fee=fee)
                st.success("Consultation fee updated.", icon=":material/check_circle:")
                st.rerun()

            st.markdown('<div style="height:1.5rem;"></div>', unsafe_allow_html=True)
            st.markdown("### Manage schedule")
            st.caption("Add or remove your weekly visiting hours. These appear on your public doctor profile.")

            # --- existing entries ---
            if schedule_rows:
                for s in schedule_rows:
                    loc = s.get("hospital_name") or s.get("chamber_address") or ""
                    place = "Hospital" if s.get("sitting_type") == "hospital" else "Chamber"
                    c1, c2 = st.columns([5, 1])
                    with c1:
                        st.markdown(f"""
                        <div class="mk-card" style="padding:0.7rem 1rem; margin-bottom:0.4rem;">
                            <div style="font-weight:600; color:#1a2a3a; font-size:0.92rem;">{s['day']} · {s['start_time']} – {s['end_time']}</div>
                            <div style="font-size:0.82rem; color:#6b7f94;">{place}: {loc}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with c2:
                        if st.button("Delete", key=f"del_sched_{s['id']}", icon=":material/delete:"):
                            DoctorService.delete_doctor_schedule_entry(s["id"], doctor["id"])
                            st.success("Schedule entry removed.", icon=":material/check_circle:")
                            st.rerun()
            else:
                st.info("No schedule entries yet. Add your first one below.", icon=":material/calendar_month:")

            st.markdown('<div style="height:0.5rem;"></div>', unsafe_allow_html=True)
            st.markdown("#### Add new schedule")
            WEEK_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            TIME_SLOTS = [f"{h:02d}:{m:02d}" for h in range(6, 22) for m in (0, 30)]

            hosp_names = [h["hospital_name"] for h in hospitals]
            chamber_addrs = [c["address"] for c in chambers]

            with st.form("add_schedule_form", clear_on_submit=True):
                sc1, sc2, sc3 = st.columns(3)
                with sc1:
                    new_day = st.selectbox("Day", WEEK_DAYS, key="add_sched_day")
                    new_place = st.selectbox("Sitting in", ["Hospital", "Personal chamber"], key="add_sched_place")
                with sc2:
                    new_start = st.selectbox("Start at", TIME_SLOTS, index=6, key="add_sched_start")
                with sc3:
                    new_end = st.selectbox("End at", TIME_SLOTS, index=18, key="add_sched_end")

                loc_val_input = st.text_input(
                    "Location (hospital name or chamber address)",
                    placeholder="e.g. Apollo Hospital or 12, Green Park, New Delhi",
                    key="add_sched_location"
                )

                submitted_sched = st.form_submit_button("Add schedule", icon=":material/add_circle:", type="primary")

            if submitted_sched:
                day_val = st.session_state.get("add_sched_day", "Monday")
                start_val = st.session_state.get("add_sched_start", "09:00")
                end_val = st.session_state.get("add_sched_end", "15:00")
                place_val = st.session_state.get("add_sched_place", "Hospital")
                loc_raw = (st.session_state.get("add_sched_location", "") or "").strip()
                hosp_val = chamber_val = None
                if start_val >= end_val:
                    st.error("End time must be after start time.", icon=":material/error:")
                elif not loc_raw:
                    lbl = "Hospital name" if place_val == "Hospital" else "Chamber address"
                    st.error(f"{lbl} is required.", icon=":material/error:")
                else:
                    if place_val == "Hospital":
                        hosp_val = loc_raw
                    else:
                        chamber_val = loc_raw

                    if (place_val == "Hospital" and hosp_val) or (place_val == "Personal chamber" and chamber_val):
                        sitting = "hospital" if place_val == "Hospital" else "chamber"
                        new_id = DoctorService.add_doctor_schedule_entry(
                            doctor["id"], day_val, start_val, end_val, sitting, hosp_val, chamber_val
                        )
                        if new_id:
                            st.success(f"Schedule added: {day_val} {start_val}–{end_val}", icon=":material/check_circle:")
                            st.rerun()
                        else:
                            st.error("Could not add schedule. Check inputs.", icon=":material/error:")

with tabs[3]:
    st.markdown("### Delete account")
    st.markdown("""
    <div style="border:1px solid var(--mk-danger); border-left:4px solid var(--mk-danger);
                background:rgba(220,38,38,0.06); border-radius:var(--radius-sm);
                padding:0.9rem 1rem; margin:0.5rem 0 1rem;">
        <div style="font-weight:700; color:var(--mk-danger); margin-bottom:0.3rem;">⚠️ Danger zone</div>
        <div style="font-size:0.9rem; color:#6b7f94; line-height:1.6;">
            Deleting your account will permanently remove your profile, appointments,
            prescriptions, documents, and all associated data from MediKiosk.
            This action <b>cannot be undone</b>.
        </div>
    </div>
    """, unsafe_allow_html=True)

    render_delete_account_trigger("Delete my account", key="profile_delete_account")