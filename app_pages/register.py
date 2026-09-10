import re
import streamlit as st
import streamlit.components.v1 as components
from components.ui import inject_global_styles
from services.auth_service import AuthService
from utils.validators import validate_email, validate_password, validate_phone_10, validate_age

DIGIT_FIELDS = {
    "reg_phone": 10,
    "reg_age": 2,
}


def sanitize_digit_fields():
    for key, max_len in DIGIT_FIELDS.items():
        if key in st.session_state:
            cleaned = re.sub(r"\D", "", str(st.session_state[key]))
            if cleaned != st.session_state[key]:
                st.session_state[key] = cleaned[:max_len]


NUMERIC_GUARD_SCRIPT = """
<div style="display:none"></div>
<script>
(function () {
  try {
    var host = window.parent;
    if (host.__mkNumericGuard) { return; }
    host.__mkNumericGuard = true;

    var blockKeys = function (evt) {
      if (evt.key && evt.key.length === 1 && !/[0-9]/.test(evt.key) &&
          !evt.ctrlKey && !evt.metaKey && !evt.altKey) {
        evt.preventDefault();
      }
    };
    var blockPaste = function (evt) { evt.preventDefault(); };
    var sanitize = function (evt) {
      var el = evt.target;
      if (el && el.value !== undefined) {
        var digits = el.value.replace(/\\D/g, '');
        if (digits !== el.value) { el.value = digits; }
      }
    };
    var attach = function (el) {
      if (el.__mkNumBound) { return; }
      el.__mkNumBound = true;
      el.setAttribute('inputmode', 'numeric');
      el.addEventListener('keydown', blockKeys, true);
      el.addEventListener('paste', blockPaste, true);
      el.addEventListener('input', sanitize, true);
    };
    var SELECTOR = [
      'input[placeholder="e.g. 9876543210"]',
      'input[placeholder="e.g. 30"]'
    ].join(', ');
    var apply = function () {
      try { host.document.querySelectorAll(SELECTOR).forEach(attach); } catch (e) {}
    };
    apply();
    try {
      var mo = new MutationObserver(apply);
      mo.observe(host.document.body, { childList: true, subtree: true });
    } catch (e) {}
    setInterval(apply, 1000);
  } catch (err) {}
})();
</script>
"""


def inject_numeric_guard():
    components.html(NUMERIC_GUARD_SCRIPT, height=0)


def render_register():
    inject_global_styles()
    inject_numeric_guard()

    if "user" in st.session_state and st.session_state.user:
        user = st.session_state.user
        if user.get("role") == "doctor":
            st.switch_page("app_pages/doctor_dashboard.py")
        else:
            st.switch_page("app_pages/patient_dashboard.py")
        st.stop()

    if "reg_age" not in st.session_state:
        st.session_state["reg_age"] = "30"
    sanitize_digit_fields()

    st.markdown("""
    <div class="mk-section" style="margin-top: 1.5rem;">
        <div class="mk-eyebrow">Join MediKiosk</div>
        <div class="mk-section-title">Create an account</div>
        <div class="mk-section-sub">Start your safer, smarter healthcare journey.</div>
    </div>
    """, unsafe_allow_html=True)

    role = st.segmented_control(
        "I am a...",
        options=["Patient", "Doctor"],
        default="Patient",
        key="reg_role",
    )

    if role == "Doctor":
        st.markdown("#### 1 · Personal details")
        full_name = st.text_input("Full name", key="reg_full_name",
                                  placeholder="e.g. Priya Sharma")
        c1, c2 = st.columns(2)
        with c1:
            phone = st.text_input("Phone number (10 digits)", key="reg_phone",
                                  placeholder="e.g. 9876543210", max_chars=10)
        with c2:
            age = st.text_input("Age (max 2 digits)", key="reg_age", max_chars=2,
                                placeholder="e.g. 30")

        st.markdown("#### 2 · Practice details")
        from utils.constants import SPECIALTIES
        c1, c2 = st.columns(2)
        with c1:
            specialization = st.selectbox("Specialization", SPECIALTIES, key="reg_specialization")
            qualification = st.text_input("Qualification", key="reg_qualification",
                                          placeholder="e.g. MD (General Medicine)")
            experience = st.number_input("Years of experience", 0, 60, 3, key="reg_experience")
        with c2:
            hospital_count = st.number_input("Number of hospitals you practice at", 1, 8, 1,
                                             key="reg_hosp_count")
            chamber_count = st.number_input("Number of personal chambers", 0, 8, 0,
                                            key="reg_chamber_count")
        languages = st.text_input("Languages", value="English", key="reg_languages",
                                  placeholder="e.g. English, Hindi")
        bio = st.text_area("Professional bio (optional)", height=90, key="reg_bio",
                           placeholder="Brief intro, experience, approach to care...")
        st.caption("Adding a hospital or chamber adds a matching field below.")
        for i in range(hospital_count):
            st.text_input(f"Hospital {i + 1} name", key=f"reg_hosp_{i}",
                          placeholder="e.g. Apollo Hospital")
        for i in range(chamber_count):
            st.text_input(f"Personal chamber {i + 1} address", key=f"reg_chamber_{i}",
                          placeholder="e.g. 12, Green Park, New Delhi")
        consult_fee = st.number_input("Consultation fee (₹)", 0.0, 1000.0, 100.0,
                                      step=10.0, key="reg_fee")
        st.caption("You can update your fee later anytime from your profile.")

        st.markdown("#### 3 · Visiting hours (weekly schedule)")
        schedule_count = st.number_input("Number of schedule entries", 1, 14, 1,
                                         key="reg_sched_count")
        WEEK_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        TIME_SLOTS = [f"{h:02d}:{m:02d}" for h in range(6, 22) for m in (0, 30)]
        for i in range(schedule_count):
            st.markdown(f"<div style='font-weight:600; color:#1a2a3a; margin:0.6rem 0 0.2rem;'>Schedule entry {i + 1}</div>",
                        unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            with c1:
                st.selectbox("Day", WEEK_DAYS, key=f"reg_sched_day_{i}")
                st.selectbox("Sitting in", ["Hospital", "Personal chamber"],
                             key=f"reg_sched_place_{i}")
            with c2:
                st.selectbox("Start at", TIME_SLOTS, index=6, key=f"reg_sched_start_{i}")
            with c3:
                st.selectbox("End at", TIME_SLOTS, index=18, key=f"reg_sched_end_{i}")
            if st.session_state.get(f"reg_sched_place_{i}") == "Hospital":
                st.text_input(f"Sitting hospital {i + 1} name", key=f"reg_sched_hosp_{i}",
                              placeholder="e.g. Apollo Hospital")
            else:
                st.text_input(f"Sitting chamber {i + 1} address", key=f"reg_sched_chamber_{i}",
                              placeholder="e.g. 12, Green Park, New Delhi")

        st.markdown("#### 4 · Documents")
        c1, c2 = st.columns(2)
        with c1:
            license_file = st.file_uploader("Doctor's license (mandatory)",
                                            type=["jpg", "png", "pdf"], key="reg_license")
        with c2:
            cert_file = st.file_uploader("Pass certificate (mandatory)",
                                         type=["jpg", "png", "pdf"], key="reg_cert")
        profile_pic = st.file_uploader("Profile picture (optional)",
                                       type=["jpg", "png"], key="reg_pic")

        st.markdown("#### 5 · Login credentials")
        email = st.text_input("Email", key="reg_email")
        c1, c2 = st.columns(2)
        with c1:
            password = st.text_input("Password", type="password")
            st.caption("At least 8 characters with upper, lower, number and special character (e.g. !@#$%).")
        with c2:
            confirm = st.text_input("Confirm password", type="password")
    else:
        c1, c2 = st.columns(2)
        with c1:
            first_name = st.text_input("First name")
        with c2:
            last_name = st.text_input("Last name")

        email = st.text_input("Email")
        c1, c2 = st.columns(2)
        with c1:
            password = st.text_input("Password", type="password")
            st.caption("At least 8 characters with upper, lower, number and special character (e.g. !@#$%).")
        with c2:
            confirm = st.text_input("Confirm password", type="password")
        phone = st.text_input("Phone (optional)")

    create_clicked = st.button("Create account", icon=":material/check:",
                               width="stretch", type="primary", key="reg_submit")

    if create_clicked:
        errors = []
        if not validate_email(email.strip()):
            errors.append("Invalid email address.")
        if len(password) < 8:
            errors.append("Password must be at least 8 characters.")
        if password != confirm:
            errors.append("Passwords do not match.")

        if role == "Patient":
            if not first_name.strip() or not last_name.strip():
                errors.append("First and last name are required.")
        else:
            name_parts = full_name.strip().split()
            if len(name_parts) < 2:
                errors.append("Please enter your full name (first and last name).")
            if not validate_phone_10(phone.strip()):
                errors.append("Phone number must be exactly 10 digits (digits only, no letters).")
            age_raw = (st.session_state.get("reg_age") or "").strip()
            age = int(age_raw) if age_raw.isdigit() else None
            if age is None or not validate_age(age):
                errors.append("Age must be a number between 1 and 99 (max 2 digits).")
            hospitals = [(st.session_state.get(f"reg_hosp_{i}") or "").strip()
                         for i in range(hospital_count)]
            if any(not h for h in hospitals):
                errors.append("Please enter the name of every hospital you practice at.")
            chambers = [(st.session_state.get(f"reg_chamber_{i}") or "").strip()
                        for i in range(chamber_count)]
            if any(not c for c in chambers):
                errors.append("Please enter the address of every personal chamber.")
            schedule = []
            for i in range(schedule_count):
                day_key = st.session_state.get(f"reg_sched_day_{i}", "Monday")
                start = st.session_state.get(f"reg_sched_start_{i}", "09:00")
                end = st.session_state.get(f"reg_sched_end_{i}", "15:00")
                sitting = st.session_state.get(f"reg_sched_place_{i}", "Hospital")
                if start >= end:
                    errors.append(f"Schedule entry {i + 1}: end time must be after start time.")
                    break
                if sitting == "Hospital":
                    hosp_name = (st.session_state.get(f"reg_sched_hosp_{i}") or "").strip()
                    if not hosp_name:
                        errors.append(f"Schedule entry {i + 1}: please enter the sitting hospital name.")
                    schedule.append({
                        "day": day_key, "start": start, "end": end,
                        "sitting": "Hospital", "hospital_name": hosp_name, "chamber_address": None,
                    })
                else:
                    chamber_addr = (st.session_state.get(f"reg_sched_chamber_{i}") or "").strip()
                    if not chamber_addr:
                        errors.append(f"Schedule entry {i + 1}: please enter the sitting chamber address.")
                    schedule.append({
                        "day": day_key, "start": start, "end": end,
                        "sitting": "Personal chamber", "hospital_name": None, "chamber_address": chamber_addr,
                    })
            if license_file is None:
                errors.append("Doctor's license is mandatory — please upload it.")
            if cert_file is None:
                errors.append("Pass certificate is mandatory — please upload it.")

        if errors:
            for err in errors:
                st.error(err, icon=":material/error:")
        else:
            role_db = "doctor" if role == "Doctor" else "patient"
            if role_db == "doctor":
                name_parts = full_name.strip().split()
                first_name, last_name = name_parts[0], " ".join(name_parts[1:])
                hospital_names = [(st.session_state.get(f"reg_hosp_{i}") or "").strip()
                                  for i in range(hospital_count)]
                chamber_addresses = [(st.session_state.get(f"reg_chamber_{i}") or "").strip()
                                     for i in range(chamber_count)]
                doctor_info = {
                    "age": age,
                    "consultation_fee": float(consult_fee),
                    "specialization": specialization,
                    "qualification": qualification.strip(),
                    "experience_years": int(experience),
                    "languages": languages.strip() or "English",
                    "bio": bio.strip(),
                    "hospitals": hospital_names,
                    "chambers": chamber_addresses,
                    "schedule": schedule,
                    "license_file": license_file.getvalue(),
                    "license_filename": license_file.name,
                    "pass_certificate": cert_file.getvalue(),
                    "pass_certificate_filename": cert_file.name,
                    "profile_image_data": profile_pic.getvalue() if profile_pic else None,
                }
                result = AuthService.register(
                    email.strip(), password, first_name, last_name,
                    role=role_db, phone=phone.strip(), doctor_info=doctor_info
                )
            else:
                result = AuthService.register(
                    email.strip(), password, first_name.strip(), last_name.strip(),
                    role=role_db, phone=phone.strip()
                )
            if result["success"]:
                new_user = AuthService.get_user_by_id(result["user_id"])
                token = AuthService.create_persistent_token(result["user_id"])
                st.session_state._auth_token = token
                st.session_state._pending_cookie = token
                st.session_state.user = {
                    "id": new_user["id"],
                    "email": new_user["email"],
                    "role": new_user["role"],
                    "first_name": new_user["first_name"],
                    "last_name": new_user["last_name"],
                    "full_name": f"{new_user['first_name']} {new_user['last_name']}",
                }
                st.success("Account created! You are now signed in.",
                           icon=":material/check_circle:")
                st.rerun()
            else:
                st.error(result["error"], icon=":material/error:")

    st.markdown('<div style="height:1rem;"></div>', unsafe_allow_html=True)
    if st.button("Already have an account? Login", icon=":material/login:"):
        st.switch_page("app_pages/login.py")


render_register()