import streamlit as st


def update_page(name: str):
    st.session_state.page = name


def handle_login():
    st.session_state.user = None
    st.session_state.page = "home"
    st.rerun()