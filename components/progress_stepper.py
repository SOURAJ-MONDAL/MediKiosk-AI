import streamlit as st

STEPS = ["Doctor", "Location", "Date", "Time", "Confirm"]


def render_progress_stepper(current_step: int):
    current_step = max(0, min(current_step, len(STEPS) - 1))
    parts = []
    for i, label in enumerate(STEPS):
        if i < current_step:
            state_class = "completed"
            dot_content = "✓"
        elif i == current_step:
            state_class = "active"
            dot_content = str(i + 1)
        else:
            state_class = ""
            dot_content = str(i + 1)
        parts.append(f"""
        <div class="mk-step {state_class}">
            <div class="mk-step-line"></div>
            <div class="mk-step-dot">{dot_content}</div>
            <div class="mk-step-label">{label}</div>
        </div>
        """)
    st.markdown(f'<div class="mk-stepper">{"".join(parts)}</div>', unsafe_allow_html=True)