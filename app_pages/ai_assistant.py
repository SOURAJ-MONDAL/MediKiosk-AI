import streamlit as st
import json as _json
from components.ui import inject_global_styles
from services.ai_service import get_ai_service
from components.ai_companion import render_ai_companion
from utils.constants import SPECIALTIES
from services.patient_service import PatientService


def require_patient():
    inject_global_styles()
    if "user" not in st.session_state or not st.session_state.user:
        st.info("Please log in to use the AI assistant.", icon=":material/lock:")
        if st.button("Go to login", icon=":material/login:"):
            st.switch_page("app_pages/login.py")
        st.stop()


require_patient()

ai = get_ai_service()

st.session_state.setdefault("chat_history", [])
st.session_state.setdefault("ai_state", "idle")
st.session_state.setdefault("ai_summary", None)
st.session_state.setdefault("ai_emergency", False)
st.session_state.setdefault("chat_ready", False)

_need_q = 2 if not ai.is_available else 4
st.markdown(f"""
<div class="mk-section" style="margin-top: 0.5rem;">
    <div class="mk-eyebrow">MediKiosk AI</div>
    <div class="mk-section-title">AI Health Assistant</div>
    <div class="mk-section-sub">
        Describe how you're feeling. The AI will ask at least {_need_q} short questions before preparing a structured
        summary{" and suggesting medicines (online only)" if ai.is_available else ""} and recommending relevant specialties. It is not a diagnosis.
    </div>
</div>
""", unsafe_allow_html=True)

if not ai.is_available:
    st.info(
        "AI service is currently operating in limited offline mode. "
        "You can still describe symptoms, browse doctors, and book appointments.",
        icon=":material/info:",
    )
    st.caption("To enable full AI responses, add a GEMINI_API_KEY to your .env file.")

col_left, col_center, col_right = st.columns([1, 1, 1])
with col_center:
    render_ai_companion(st.session_state.ai_state)

if st.session_state.ai_emergency:
    st.markdown("""
    <div class="mk-emergency">
        <div class="mk-emergency-title">⚠ URGENT MEDICAL ATTENTION</div>
        <div class="mk-emergency-body">
            Your symptoms may require immediate medical attention.
            Please contact your local emergency service or go to the nearest
            emergency department right away.
            <br><br>
            Do not wait for an online consultation.
        </div>
    </div>
    """, unsafe_allow_html=True)

if st.session_state.chat_history:
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            with st.chat_message("user"):
                st.markdown(msg["content"])
        else:
            with st.chat_message("assistant"):
                st.markdown(msg["content"])

if not st.session_state.chat_history:
    _need_empty = 2 if not ai.is_available else 4
    st.markdown(f"""
    <div class="mk-empty">
        <div class="mk-empty-icon">💬</div>
        <div class="mk-empty-title">Start a conversation</div>
        <div class="mk-empty-text">
            Tell the AI how you're feeling — for example "I've had headaches for three days."
            It will ask at least {_need_empty} short questions to understand your situation before summarizing and recommending doctors.
        </div>
    </div>
    """, unsafe_allow_html=True)

    quick_replies = [
        "I have a headache",
        "I have stomach pain",
        "I have a fever",
        "I need a doctor",
        "I want to understand my symptoms",
    ]
    st.markdown('<div style="height:0.75rem;"></div>', unsafe_allow_html=True)
    st.caption("Try a quick reply:")
    for qr in quick_replies:
        if st.button(qr, key=f"qr_{qr}", icon=":material/send:"):
            st.session_state.chat_history.append({"role": "user", "content": qr})
            emergency_now = ai.detect_emergency(qr)
            result = ai.chat(st.session_state.chat_history)
            ai_response = result.get("response", "")
            st.session_state.chat_history.append({"role": "assistant", "content": ai_response})
            user_count = sum(1 for m in st.session_state.chat_history if m.get("role") == "user")
            _need = 2 if not ai.is_available else 4
            is_emergency = bool(result.get("is_emergency") or emergency_now)
            is_complete = bool(result.get("conversation_complete")) and (user_count >= _need or is_emergency)
            if result.get("follow_up_questions"):
                st.session_state.ai_follow_ups = result["follow_up_questions"]
            if result.get("structured_summary"):
                st.session_state.ai_summary = result["structured_summary"]
            st.session_state.conversation_complete = is_complete
            if is_emergency:
                st.session_state.ai_state = "concerned"
                st.session_state.chat_ready = True
            elif is_complete:
                st.session_state.ai_state = "success"
                st.session_state.chat_ready = True
            else:
                st.session_state.ai_state = "listening"
                st.session_state.chat_ready = False
            if not is_complete and not is_emergency:
                st.session_state.ai_progress = f"Question {min(user_count,_need)} of {_need} — please type a short answer to continue"
            else:
                st.session_state.ai_progress = None
            st.rerun()

if prompt := st.chat_input("Describe your symptoms... (short answer: 1-2 sentences)", key="ai_chat_input"):
    # Enforce short answers — follow-up questions should be answered briefly
    if len(prompt.strip()) > 300:
        st.warning("Please keep your answer short — 1-2 sentences (under 300 characters) as requested for follow-ups.", icon=":material/warning:")
        # still accept but trim to 300 for AI
        prompt = prompt.strip()[:300]
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    st.session_state.ai_state = "thinking"

    if "ai_chat_input" in st.session_state:
        pass
    with st.chat_message("user"):
        st.markdown(prompt)

    emergency_now = ai.detect_emergency(prompt)
    if emergency_now:
        st.session_state.ai_emergency = True
        st.session_state.ai_state = "concerned"
    else:
        st.session_state.ai_state = "listening"
        st.session_state.ai_emergency = False

    result = ai.chat(st.session_state.chat_history)
    ai_response = result.get("response", "")
    with st.chat_message("assistant"):
        st.markdown(ai_response)

    st.session_state.chat_history.append({"role": "assistant", "content": ai_response})

    # Track follow-ups and gate summary until required questions have been asked (2 offline, 4 online)
    user_count = sum(1 for m in st.session_state.chat_history if m.get("role") == "user")
    _need = 2 if not ai.is_available else 4
    is_emergency = bool(result.get("is_emergency") or emergency_now)
    is_complete = bool(result.get("conversation_complete")) and (user_count >= _need or is_emergency)

    # Store follow-up questions for rendering
    fu_qs = result.get("follow_up_questions") or []
    if fu_qs:
        st.session_state.ai_follow_ups = fu_qs

    summary = result.get("structured_summary", {})
    # Only store final summary when complete; keep partial otherwise but don't mark ready
    if summary:
        st.session_state.ai_summary = summary
    st.session_state.conversation_complete = is_complete
    if is_emergency:
        st.session_state.ai_emergency = True
        st.session_state.ai_state = "concerned"
        st.session_state.chat_ready = True
    elif is_complete:
        st.session_state.ai_state = "success"
        st.session_state.ai_emergency = False
        st.session_state.chat_ready = True
    else:
        st.session_state.ai_state = "listening"
        st.session_state.ai_emergency = False
        st.session_state.chat_ready = False

    # Progress hint
    if not is_complete and not is_emergency:
        st.session_state.ai_progress = f"Question {min(user_count,_need)} of {_need} — please type a short answer to continue"
    else:
        st.session_state.ai_progress = None

    st.rerun()

 # Show progress / follow-up questions until required questions are completed — only short answers via chat input are accepted
if not st.session_state.get("conversation_complete") and st.session_state.get("ai_follow_ups"):
    qs = st.session_state.ai_follow_ups
    # threshold depends on online vs offline
    _need = 4 if ai.is_available else 2
    if st.session_state.get("ai_progress"):
        st.caption(st.session_state.ai_progress)
    st.markdown("**Follow-up questions — please type short answers (1-2 sentences) in the chat box below:**")
    for q in qs[:3]:
        st.markdown(f"- {q}")
    st.markdown('<div style="height:0.5rem;"></div>', unsafe_allow_html=True)
    st.caption(f"Please answer at least {_need} questions with short answers before the AI generates a summary and recommends doctors. Clicking the questions above does not submit them — type your answer in chat.")

if st.session_state.get("chat_ready") and st.session_state.get("ai_summary") and st.session_state.get("conversation_complete"):
    st.markdown("""
    <div class="mk-section">
        <div class="mk-section-title">Structured health summary</div>
        <div class="mk-section-sub">Prepared by MediKiosk AI — review before your consultation.</div>
    </div>
    """, unsafe_allow_html=True)

    summary = st.session_state.ai_summary

    urgency = summary.get("urgency", "moderate")
    urgency_map = {
        "low": ("mk-badge-green", "Low urgency"),
        "moderate": ("mk-badge-orange", "Moderate"),
        "high": ("mk-badge-red", "High urgency"),
        "emergency": ("mk-badge-red", "Emergency"),
    }
    badge_class, urgency_label = urgency_map.get(urgency, urgency_map["moderate"])

    with st.container(border=True):
        st.markdown(f"""
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:0.5rem;">
            <div>
                <div class="mk-eyebrow" style="margin-bottom:0.25rem;">Urgency assessment</div>
                <span class="mk-badge {badge_class}">{urgency_label}</span>
            </div>
            <div>
                <div class="mk-eyebrow" style="margin-bottom:0.25rem;">Recommended specialties</div>
                <div>{' '.join(f"<span class='mk-badge mk-badge-blue'>{s}</span>" for s in (summary.get('suggested_specialties') or []))}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div style="height:0.5rem;"></div>', unsafe_allow_html=True)
        symptoms = summary.get("symptoms") or []
        st.markdown("**Symptoms:** " + ", ".join(symptoms) if symptoms else "**Symptoms:** Not specified")

        st.markdown("**Duration:** " + (summary.get("duration") or "Not specified"))
        st.markdown("**Severity:** " + (summary.get("severity") or "Not specified").title())
        if summary.get("associated_symptoms"):
            st.markdown("**Associated symptoms:** " + ", ".join(summary["associated_symptoms"]))
        st.markdown("")
        st.markdown("**Recommended next step:** " + (summary.get("recommended_next_step") or "Consult a doctor"))

        # Medicines — only when online and after completion, per training
        meds = summary.get("suggested_medicines") or []
        if ai.is_available and meds:
            st.markdown('<div style="height:0.4rem;"></div>', unsafe_allow_html=True)
            st.markdown("**Suggested medicines (general info — confirm with doctor/pharmacist):**")
            for m in meds:
                if isinstance(m, dict):
                    name = m.get("name", "")
                    note = m.get("note", "")
                    st.markdown(f"- **{name}** — {note}" if note else f"- **{name}**")
                else:
                    st.markdown(f"- {m}")
            st.caption("⚠️ Medicines listed are for information only, not a prescription. Consult a qualified professional before use.")

        if summary.get("safety_notes"):
            st.caption("ℹ️ " + summary["safety_notes"])

    # Merged Find & Book + Save chat + Generate prescription (online only) — per new spec
    st.markdown('<div style="height:1rem;"></div>', unsafe_allow_html=True)
    # Row 1: merged primary action
    if st.button("Find & Book Doctor", icon=":material/search:", width="stretch", type="primary"):
        # store summary for auto-send on booking
        st.session_state.preferred_specialties = st.session_state.ai_summary.get("suggested_specialties", [])
        st.session_state.ai_summary_for_booking = st.session_state.ai_summary
        st.session_state.ai_chat_for_booking = st.session_state.get("chat_history", [])
        st.switch_page("app_pages/doctors.py")

    st.markdown('<div style="height:0.6rem;"></div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Save chat & Generate Summary", icon=":material/save:", width="stretch"):
            # save to ai_consultations
            user = st.session_state.get("user")
            patient = PatientService.get_patient_by_user_id(user["id"]) if user else None
            if patient:
                cid = ai.save_consultation(patient["id"], st.session_state.get("chat_history", []), st.session_state.ai_summary)
                if cid:
                    st.success(f"Chat saved (consultation #{cid}). Summary ready for doctor.", icon=":material/check_circle:")
                    st.session_state.ai_consultation_id = cid
                else:
                    st.error("Could not save chat.", icon=":material/error:")
            else:
                st.error("Patient profile not found.", icon=":material/error:")
            # also show summary download
            summary_json = _json.dumps(st.session_state.ai_summary, indent=2)
            st.download_button("Download summary JSON", data=summary_json, file_name="medikiosk_summary.json", mime="application/json", width="stretch")
    with c2:
        # Generate prescription — online only
        if not ai.is_available:
            st.button("Generate Prescription (Online only)", icon=":material/medication:", width="stretch", disabled=True, help="Available only when AI is online")
            st.caption("Prescription generation requires online AI.")
        else:
            if st.button("Generate Prescription", icon=":material/medication:", width="stretch"):
                meds = ai.generate_prescription_suggestion(st.session_state.ai_summary)
                if not meds:
                    st.info("No medicines suggested for this summary.", icon=":material/info:")
                else:
                    st.session_state.ai_prescription_suggestion = meds
                    st.success("Prescription suggestion generated (for info only — not a prescription).", icon=":material/check_circle:")
                    # show preview inline
                    for m in meds:
                        st.markdown(f"- **{m.get('name','')}** — {m.get('note','')}  *{m.get('dosage','')} {m.get('frequency','')}*")
                    st.caption("⚠️ This is AI-generated general information, not a prescription. Doctor approval required.")
                    # Save as chatbot-generated prescriptions so they appear in Prescription tab
                    try:
                        from services.prescription_service import PrescriptionService
                        from services.appointment_service import AppointmentService
                        user = st.session_state.get("user")
                        patient = PatientService.get_patient_by_user_id(user["id"]) if user else None
                        if patient:
                            # link to most recent appointment if any, otherwise to the booked one from this chat session
                            appts = AppointmentService.get_patient_appointments(patient["id"])
                            target_apt = None
                            # prefer the AI-booked appointment if exists
                            _chat_apt_id = st.session_state.get("ai_summary_for_booking") and st.session_state.get("booking_confirmed", {}).get("id")
                            if _chat_apt_id:
                                target_apt = next((a for a in appts if a["id"] == _chat_apt_id), None)
                            if not target_apt and appts:
                                # most recent (first is latest due to ORDER BY DESC)
                                target_apt = appts[0]
                            if target_apt:
                                # avoid duplicate chatbot prescriptions for same appointment
                                existing = PrescriptionService.get_appointment_prescriptions(target_apt["id"])
                                existing_names = {e.get("medicine_name","").lower() for e in existing if e.get("is_ai_suggested")}
                                for m in meds:
                                    name = m.get("name","").strip()
                                    if not name or name.lower() in existing_names:
                                        continue
                                    PrescriptionService.create_prescription(
                                        appointment_id=target_apt["id"],
                                        doctor_id=target_apt["doctor_id"],
                                        patient_id=patient["id"],
                                        medicine_name=name,
                                        dosage=m.get("dosage",""),
                                        frequency=m.get("frequency",""),
                                        duration="",
                                        instructions=m.get("note",""),
                                        doctor_notes="Chatbot generated — pending doctor approval",
                                        is_ai_suggested=1,
                                    )
                                st.info(f"Saved {len(meds)} chatbot prescription(s) to your Prescriptions tab (linked to appointment {target_apt['id']}).", icon=":material/info:")
                                st.caption("View them under Dashboard → Prescriptions — marked as 'Chatbot generated'.")
                            else:
                                st.warning("No appointment found to attach prescription. Book an appointment first, then generate.", icon=":material/warning:")
                    except Exception as e:
                        st.error(f"Could not save chatbot prescription: {e}", icon=":material/error:")

st.markdown('<div style="height:1rem;"></div>', unsafe_allow_html=True)

with st.expander("Clear conversation", icon=":material/delete:"):
    st.caption("Start fresh with the AI assistant.")
    if st.button("Clear chat", icon=":material/delete_sweep:"):
        for key in ["chat_history", "ai_summary", "ai_emergency", "chat_ready", "conversation_complete", "ai_follow_ups", "ai_progress"]:
            if key in st.session_state:
                del st.session_state[key]
        st.session_state.ai_state = "idle"
        st.rerun()

st.markdown("---")
st.caption(
    "MediKiosk AI provides general health information and guidance only. "
    "It cannot diagnose conditions or replace professional medical care. "
    "Doctor recommendations are suggestions based on symptom patterns, not diagnoses."
)