import streamlit as st
from components.ui import inject_global_styles
from services.auth_service import AuthService


def render_login():
    inject_global_styles()

    st.markdown("""
    <div class="mk-section" style="margin-top: 1.5rem;">
        <div class="mk-eyebrow">Welcome back</div>
        <div class="mk-section-title">Login to MediKiosk</div>
        <div class="mk-section-sub">Sign in to manage your health journey.</div>
    </div>
    """, unsafe_allow_html=True)

    if "user" in st.session_state and st.session_state.user:
        user = st.session_state.user
        if user.get("role") == "doctor":
            st.switch_page("app_pages/doctor_dashboard.py")
        else:
            st.switch_page("app_pages/patient_dashboard.py")
        st.stop()

    with st.form("login_form"):
        email = st.text_input("Email", key="login_email", value="")
        password = st.text_input("Password", type="password", key="login_password")
        submitted = st.form_submit_button("Login", icon=":material/login:", width="stretch", type="primary")

    if submitted:
        if not email or not password:
            st.error("Please enter both email and password.", icon=":material/error:")
        else:
            result = AuthService.login(email.strip(), password)
            if result["success"]:
                user = AuthService.get_user_by_id(result["user_id"])
                st.session_state.user = {
                    "id": user["id"],
                    "email": user["email"],
                    "role": user["role"],
                    "first_name": user["first_name"],
                    "last_name": user["last_name"],
                    "full_name": f"{user['first_name']} {user['last_name']}",
                }
                token = AuthService.create_persistent_token(user["id"])
                st.session_state._auth_token = token
                st.session_state._pending_cookie = token
                st.rerun()
            else:
                st.error(result["error"], icon=":material/error:")

    st.markdown('<div style="height:1rem;"></div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("**Demo credentials**")

    with st.expander("View demo accounts"):
        st.markdown("""
        **Patients:**
        - `john.smith@example.com` / `Patient123!`
        - `amit.sharma@example.com` / `Patient123!`
        - `emma.wilson@example.com` / `Patient123!`
        - `david.brown@example.com` / `Patient123!`

        **Doctors:**
        - `sarah.johnson@medikiosk.com` / `Doctor123!`
        - `mark.chen@medikiosk.com` / `Doctor123!`
        - `priya.patel@medikiosk.com` / `Doctor123!`
        - `james.wilson@medikiosk.com` / `Doctor123!`
        """)

    st.markdown('<div style="height:1rem;"></div>', unsafe_allow_html=True)

    if st.button("Create a new account", icon=":material/person_add:"):
        st.switch_page("app_pages/register.py")


render_login()