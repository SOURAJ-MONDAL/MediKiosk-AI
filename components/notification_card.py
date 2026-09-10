import streamlit as st
from utils.helpers import format_date


def render_notification_card(notification: dict):
    unread_class = "unread" if not notification.get("is_read") else ""
    dot = '<span style="font-size:1rem;">●</span>' if not notification.get("is_read") else ""

    st.markdown(f"""
    <div class="mk-notif {unread_class}">
        <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:0.5rem;">
            <div class="mk-notif-title">{notification.get('title', '')}</div>
            <span style="font-size:0.75rem; color:#9aa9b9;">{format_date((notification.get('created_at') or '')[:10])}</span>
        </div>
        <div class="mk-notif-msg">{notification.get('message', '')}</div>
    </div>
    """, unsafe_allow_html=True)


def render_empty_notifications():
    st.markdown("""
    <div class="mk-empty">
        <div class="mk-empty-icon">🔔</div>
        <div class="mk-empty-title">You're all caught up</div>
        <div class="mk-empty-text">No notifications right now.</div>
    </div>
    """, unsafe_allow_html=True)