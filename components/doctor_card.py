import streamlit as st

from utils.helpers import format_time, format_date


def render_doctor_card(doctor: dict, include_button: bool = True, key_prefix: str = "doc"):
    name = f"Dr. {doctor.get('first_name', '')} {doctor.get('last_name', '')}"
    spec = doctor.get("specialization", "")
    rating_value = doctor.get("rating") or 0
    total_ratings = doctor.get("total_ratings") or 0
    bio = (doctor.get('bio') or '')[:220]
    fee = doctor.get("consultation_fee") or 0
    languages = doctor.get("languages") or "English"

    if doctor.get("profile_image") or doctor.get("user_image"):
        img = doctor.get("profile_image") or doctor.get("user_image")
        avatar_html = f'<img src="{img}" alt="{name}" />'
    else:
        initials = f"{doctor.get('first_name', 'D')[:1]}{doctor.get('last_name', 'R')[:1]}"
        avatar_html = initials

    # ABSOLUTELY NO NEWLINES, NO INDENTATION in the final string
    html = (
        f'<div class="mk-doctor-card">'
        f'<div class="mk-card-head">'
        f'<div class="mk-doctor-avatar">{avatar_html}</div>'
        f'<div>'
        f'<div class="mk-doctor-name">{name}</div>'
        f'<div class="mk-doctor-spec">{spec}</div>'
        f'</div>'
        f'</div>'
        f'<div style="margin: 0.4rem 0; display:flex; align-items:center; gap:0.6rem; flex-wrap:wrap;">'
        f'<span class="mk-star">★ {rating_value:.1f}</span>'
        f'<span style="font-size:0.78rem; color:#6b7f94;">({total_ratings} ratings)</span>'
        f'<span class="mk-badge mk-badge-blue mk-badge-sm">{doctor.get("experience_years", 0)} yrs exp</span>'
        f'{"<span class=\'mk-badge mk-badge-green mk-badge-sm\'>Verified</span>" if doctor.get("is_verified") else ""}'
        f'</div>'
        f'<div class="mk-bio">{bio}</div>'
        f'<div class="mk-card-foot">'
        f'<span class="mk-fee">₹{fee:.0f}</span>'
        f'<span class="mk-lang">{languages}</span>'
        f'</div>'
        f'</div>'
    )

    st.markdown(html, unsafe_allow_html=True)

    if include_button:
        button_key = f"{key_prefix}_select_{doctor['id']}_{st.session_state.get('_ui_rand', 1)}"
        if st.button("View details", key=button_key, icon=":material/visibility:", type="primary", width="stretch"):
            st.session_state.selected_doctor_id = doctor["id"]
            st.session_state.from_doctor_card = True
            st.rerun()
