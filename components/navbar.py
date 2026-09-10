import streamlit as st


def render_logo():
    st.markdown("""
    <div class="mk-logo">
        <div class="mk-logo-mark">+</div>
        <div class="mk-logo-text">MediKiosk</div>
    </div>
    """, unsafe_allow_html=True)


def render_navbar():
    render_logo()

    if "user" in st.session_state and st.session_state.user:
        user = st.session_state.user
        st.markdown(f"""
        <div style="padding: 0.6rem 0.4rem; margin-top: 0.2rem;">
            <div style="font-size: 0.78rem; color: #6b7f94; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em;">Signed in as</div>
            <div style="font-weight: 700; color: #1a2a3a; font-size: 0.95rem; margin-top: 0.1rem;">{user.get('full_name', 'User')}</div>
            <div style="font-size: 0.8rem; color: #6b7f94;">{user.get('role', '').title()}</div>
            <div style="font-size: 0.75rem; color: #9aa9b9; margin-top: 0.15rem;">{user.get('email', '')}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="padding: 0.6rem 0.4rem;">
            <span class="mk-badge mk-badge-blue">Healthcare + AI</span>
        </div>
        """, unsafe_allow_html=True)


def render_safety_disclaimer():
    st.markdown("""
    <div class="mk-alert mk-alert-info" style="margin-top: 1.5rem; font-size: 0.75rem;">
        <strong>Medical disclaimer:</strong> MediKiosk provides AI-assisted health
        information and appointment support. It is not a substitute for professional
        medical advice, diagnosis, or treatment. For emergencies, contact local
        emergency services immediately.
    </div>
    """, unsafe_allow_html=True)