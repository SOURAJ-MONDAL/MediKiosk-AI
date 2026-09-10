import streamlit as st
from components.navbar import render_navbar, render_safety_disclaimer
from components.account_danger import render_delete_account_trigger
from services.auth_service import AuthService
from services.notification_service import NotificationService


def render_sidebar():
    with st.sidebar:
        render_navbar()

        if "user" in st.session_state and st.session_state.user:
            user = st.session_state.user
            unread = NotificationService.get_unread_count(user["id"])
            st.markdown(f"<span class='mk-badge mk-badge-blue'>Notifications: {unread} unread</span>", unsafe_allow_html=True)

            if st.button("Logout", icon=":material/logout:", width="stretch"):
                token = st.session_state.get("_auth_token")
                if token:
                    AuthService.revoke_token(token)
                st.session_state._pending_cookie = ""
                st.session_state.user = None
                st.session_state._auth_token = None
                st.rerun()

            st.markdown('<div style="height:0.4rem;"></div>', unsafe_allow_html=True)
            render_delete_account_trigger("Delete account", key="sidebar_delete_account")

        render_safety_disclaimer()