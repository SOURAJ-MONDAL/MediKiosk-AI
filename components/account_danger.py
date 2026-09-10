import streamlit as st
from services.auth_service import AuthService


@st.dialog("Delete account")
def delete_account_confirmation():
    st.warning("Deleting account will erase all data permanently!")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Go back", key="del_go_back", width="stretch"):
            st.rerun()
    with c2:
        if st.button("Delete anyway", key="del_confirm", type="primary", width="stretch"):
            user = st.session_state.get("user")
            token = st.session_state.get("_auth_token")
            if token:
                AuthService.revoke_token(token)
            if user:
                AuthService.delete_user(user["id"])
            st.session_state._pending_cookie = ""
            st.session_state.user = None
            st.session_state._auth_token = None
            st.session_state.account_deleted = True
            st.switch_page("app_pages/home.py")


def render_delete_account_trigger(label="Delete account", key="delete_account_option"):
    if st.button(label, icon=":material/delete:", width="stretch", key=key):
        delete_account_confirmation()