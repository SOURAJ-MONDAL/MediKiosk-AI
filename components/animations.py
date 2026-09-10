import streamlit as st


def render_animation(name: str):
    animations = {
        "fade-in": '<div style="animation: fade-in 0.6s ease;"></div>',
        "slide-up": '<div style="animation: slide-up 0.5s ease;"></div>',
        "soft-pulse": '<div class="mk-soft-pulse"></div>',
        "success-check": """
        <div class="mk-success-check"><span>✓</span></div>
        """,
    }
    if name in animations:
        st.markdown(animations[name], unsafe_allow_html=True)