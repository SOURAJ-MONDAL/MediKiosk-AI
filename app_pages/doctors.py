import streamlit as st
from components.ui import inject_global_styles
from services.doctor_service import DoctorService
from services.matching_service import MatchingService
from components.doctor_card import render_doctor_card
from components.booking_wizard import render_booking_wizard, start_booking
from utils.constants import SPECIALTIES


def require_login():
    inject_global_styles()
    if "user" not in st.session_state or not st.session_state.user:
        st.info("Please log in to browse doctors.", icon=":material/lock:")
        if st.button("Go to login", icon=":material/login:"):
            st.switch_page("app_pages/login.py")
        st.stop()


require_login()

user = st.session_state.user

st.markdown("""
<div class="mk-section" style="margin-top: 0.5rem;">
    <div class="mk-eyebrow">Doctor discovery</div>
    <div class="mk-section-title">Find the right doctor</div>
    <div class="mk-section-sub">
        Browse specialists, compare ratings and fees, then book an appointment.
        Recommendations from the AI are suggestions — always trust your own judgement.
    </div>
</div>
""", unsafe_allow_html=True)

preferred = st.session_state.get("preferred_specialties", [])
if preferred:
    st.markdown("##### AI-recommended specialties for your symptoms:")
    st.markdown(" ".join(f"<span class='mk-badge mk-badge-cyan'>{s}</span>" for s in preferred), unsafe_allow_html=True)
    st.markdown('<div style="height:0.5rem;"></div>', unsafe_allow_html=True)

# Handle clear before widgets are instantiated (avoids StreamlitWidgetAlreadyInstantiatedError)
if st.session_state.get("_clear_filters_pending"):
    st.session_state.mk_spec_filter = "All"
    st.session_state.mk_city_filter = "All"
    st.session_state.preferred_specialties = []
    st.session_state._clear_filters_pending = False

c1, c2, c3 = st.columns(3)
with c1:
    spec_filter = st.selectbox("Specialty", ["All"] + SPECIALTIES, key="mk_spec_filter")
with c2:
    city_filter = st.selectbox("City", ["All", "New York", "San Francisco", "Chicago", "Houston"], key="mk_city_filter")
with c3:
    st.markdown('<div style="height:0.5rem;"></div>', unsafe_allow_html=True)
    if st.button("Clear filters", icon=":material/filter_alt_off:"):
        st.session_state._clear_filters_pending = True
        st.rerun()

selected_doctor_id = st.session_state.get("selected_doctor_id")
if selected_doctor_id:
    doctor = DoctorService.get_doctor_by_id(selected_doctor_id)
    if doctor:
        st.markdown('<div style="height:1rem;"></div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="mk-section" id="doctor-profile">
            <div class="mk-section-title">Doctor profile</div>
        </div>
        """, unsafe_allow_html=True)

        name = f"Dr. {doctor['first_name']} {doctor['last_name']}"
        profile_img = doctor.get('profile_image') or doctor.get('user_image') or 'https://api.dicebear.com/7.x/avataaars/svg?seed=Unknown'
        bio_text = doctor.get('bio') or ''

        # Remove all newlines and indentation from the HTML string
        profile_html = (
            f'<div class="mk-doctor-card" id="doctor-profile-card">'
            f'<div style="display:flex; align-items:center; gap:1.2rem; flex-wrap:wrap;">'
            f'<div style="width:110px; height:110px; border-radius:50%; overflow:hidden; border:3px solid #dbe7f5;">'
            f'<img src="{profile_img}" style="width:100%; height:100%; object-fit:cover;" />'
            f'</div>'
            f'<div style="flex:1; min-width:240px;">'
            f'<div class="mk-doctor-name" style="font-size:1.3rem;">{name}</div>'
            f'<div class="mk-doctor-spec" style="font-size:0.95rem;">{doctor.get("specialization", "")} · {doctor.get("qualification", "")}</div>'
            f'<div style="margin-top:0.5rem; display:flex; gap:0.75rem; flex-wrap:wrap; align-items:center;">'
            f'<span class="mk-star">★ {doctor.get("rating", 0):.1f}</span>'
            f'<span style="font-size:0.8rem; color:#6b7f94;">{doctor.get("total_ratings", 0)} ratings</span>'
            f'<span class="mk-badge mk-badge-blue">{doctor.get("experience_years", 0)} years experience</span>'
            f'<span class="mk-badge mk-badge-gray">{doctor.get("languages", "English")}</span>'
            f'</div>'
            f'</div>'
            f'<div style="text-align:right;">'
            f'<div style="font-size:1.5rem; font-weight:800; color:#1a2a3a;">₹{doctor.get("consultation_fee", 0):.0f}</div>'
            f'<div style="font-size:0.75rem; color:#6b7f94;">per consultation</div>'
            f'</div>'
            f'</div>'
            f'<div style="margin-top:1rem; font-size:0.95rem; color:#374151; line-height:1.7;">{bio_text}</div>'
            f'</div>'
        )
        st.markdown(profile_html, unsafe_allow_html=True)

        locations = DoctorService.get_doctor_locations(doctor["id"])
        if locations:
            st.markdown('<div style="height:0.75rem;"></div>', unsafe_allow_html=True)
            st.markdown("**Practice locations:**")
            for loc in locations:
                st.markdown(f"""
                <div class="mk-info-row">
                    <div class="mk-info-icon">🏥</div>
                    <div>
                        <div class="mk-info-value">{loc['name']}</div>
                        <div style="font-size:0.8rem; color:#6b7f94;">{loc['address']}, {loc['city']}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        if st.button("Book appointment", icon=":material/calendar_month:", type="primary", width="stretch"):
                start_booking(doctor["id"])

        reviews = MatchingService.get_doctor_reviews(doctor["id"])
        if reviews:
            st.markdown('<div style="height:1rem;"></div>', unsafe_allow_html=True)
            st.markdown("**Recent reviews:**")
            for r in reviews:
                stars = "★" * r["rating"] + "☆" * (5 - r["rating"])
                st.markdown(f"""
                <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:0.8rem 1rem; margin-bottom:0.5rem;">
                    <div style="font-weight:600; font-size:0.88rem; color:#1f2937;">{r['first_name']} {r['last_name']}</div>
                    <div style="color:#f59e0b; font-size:0.85rem;">{stars}</div>
                    {f"<div style='font-size:0.85rem; color:#374151; margin-top:0.3rem;'>{r['review']}</div>" if r.get('review') else ""}
                </div>
                """, unsafe_allow_html=True)

        st.markdown('<div style="height:1rem;"></div>', unsafe_allow_html=True)

        render_booking_wizard()

        st.markdown('<div style="height:1rem;"></div>', unsafe_allow_html=True)
        st.markdown('<div class="mk-section"><div class="mk-section-title">All doctors</div></div>', unsafe_allow_html=True)

doctors = DoctorService.get_all_doctors()

if spec_filter != "All":
    doctors = [d for d in doctors if d["specialization"] == spec_filter]
elif preferred:
    doctors = [d for d in doctors if d["specialization"] in preferred]
if city_filter != "All":
    location_cities = []
    for d in doctors:
        for loc in DoctorService.get_doctor_locations(d["id"]):
            if loc["city"] == city_filter:
                location_cities.append(d["id"])
                break
    doctors = [d for d in doctors if d["id"] in location_cities]

if not doctors:
    st.markdown("""
    <div class="mk-empty">
        <div class="mk-empty-icon">🔍</div>
        <div class="mk-empty-title">No doctors found</div>
        <div class="mk-empty-text">Try adjusting your filters.</div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"**{len(doctors)} doctors found**")
    st.markdown('<div style="height:0.5rem;"></div>', unsafe_allow_html=True)

    for i in range(0, len(doctors), 2):
        row = st.columns(2)
        for col, doc in zip(row, doctors[i:i + 2]):
            with col:
                render_doctor_card(doc, key_prefix=f"browse_{i}")