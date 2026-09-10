import streamlit as st

STATES = {
    "idle": ("🤖", "AI Health Assistant ready", ""),
    "listening": ("🎧", "Listening...", "listening"),
    "thinking": ("🧠", "Analyzing your symptoms...", "thinking"),
    "responding": ("✨", "Generating response...", ""),
    "concerned": ("⚠️", "Please review this carefully", "concerned"),
    "success": ("✓", "Complete", "success"),
}


def render_ai_companion(state: str = "idle", size: str = "normal"):
    if state not in STATES:
        state = "idle"
    icon, status, extra_class = STATES[state]
    size_class = "mk-ai-lg" if size == "large" else ""

    st.markdown(f"""
    <div class="mk-ai-wrap">
        <div class="mk-ai-orb {extra_class} {size_class}">
            <div class="mk-ai-inner">
                <div class="mk-ai-pulse">{icon}</div>
            </div>
        </div>
    </div>
    <div class="mk-ai-status mk-soft-pulse">{status}</div>
    """, unsafe_allow_html=True)


def render_typing_indicator():
    st.markdown("""
    <div class="mk-typing">
        <span></span><span></span><span></span>
    </div>
    """, unsafe_allow_html=True)