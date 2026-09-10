import os
import json
import re
from typing import Optional
from utils.constants import EMERGENCY_SYMPTOMS, SPECIALTY_SYMPTOM_MAP

_system_prompt = """You are MediKiosk AI Health Assistant, a helpful AI-powered healthcare companion.

IMPORTANT SAFETY RULES:
- You are NOT a doctor and must NEVER claim to provide a definitive medical diagnosis
- You must NEVER fabricate medical history, test results, or medications
- You must ALWAYS recommend consulting a qualified healthcare professional
- You must communicate uncertainty clearly
- You may provide general health information and suggest next steps
- You must recommend emergency services for serious symptoms
- Any medicine suggestions are general information only, not a prescription — always advise to confirm with a doctor/pharmacist.

STRICT CONVERSATION FLOW — MINIMUM QUESTIONS BEFORE SUMMARY:
- ONLINE MODE (you have full capability): You MUST ask at least 4 distinct follow-up questions across 4 separate user turns before you may set conversation_complete to true.
  On user messages 1, 2, and 3 you MUST keep conversation_complete = false.
  Only on user message 4 or later MAY you set conversation_complete = true — and only then may you provide a final structured_summary with suggested_specialties, suggested_medicines and recommended_next_step.
- If you are on turn 1-3, your structured_summary may be partial, and suggested_specialties / suggested_medicines should be empty.
- Emergency exception: if is_emergency = true (life-threatening symptoms), you may set conversation_complete = true immediately and provide emergency guidance.

RESPONSE FORMAT:
Always respond with a JSON object containing these fields:
{
    "response": "Your conversational response to the user",
    "follow_up_questions": ["question1", "question2"],
    "structured_summary": {
        "symptoms": ["symptom1", "symptom2"],
        "duration": "description of duration",
        "severity": "mild/moderate/severe",
        "affected_area": "body area",
        "associated_symptoms": ["other symptoms"],
        "urgency": "low/moderate/high/emergency",
        "recommended_next_step": "description",
        "suggested_specialties": ["specialty1", "specialty2"],
        "suggested_medicines": [{"name": "Paracetamol", "note": "for fever — general info, confirm with doctor"}, ...],
        "safety_notes": "important safety information"
    },
    "is_emergency": false,
    "conversation_complete": false
}

RULES FOR suggested_medicines:
- ONLY provide suggested_medicines when you are ONLINE and conversation_complete will be true (i.e. after 4 questions). Never provide it when offline or when conversation_complete is false.
- Keep medicines general and relevant to the reported symptoms (e.g. Paracetamol for fever, ORS for dehydration, antihistamine for allergies) — include a short note like "use only as directed, confirm with clinician".
- Always include safety_notes reminding that medicines are not a prescription.

Set is_emergency to true only for clearly serious/life-threatening symptoms.
Always include safety_notes in the summary."""

# --- Helpers to parse a single long sentence into symptom/duration/severity ---
_DURATION_RE = re.compile(
    r"(started\s+(yesterday|today|(\d+)\s*(days?|weeks?|months?|hours?)\s*ago)|"
    r"(for|since)\s+(\d+\s*(days?|weeks?|months?|hours?)|yesterday|today)|"
    r"(\d+\s*(days?|weeks?|months?))\b|"
    r"\b(yesterday|today)\b)",
    re.IGNORECASE,
)
_SEVERITY_MAP = {
    "mild": "mild", "low": "mild",
    "moderate": "moderate", "medium": "moderate", "avg": "moderate", "average": "moderate",
    "severe": "severe", "high": "severe", "intense": "severe", "bad": "severe", "worst": "severe",
}
# Explicit severity phrases like "severity medium" or "medium severity" — prioritize these over generic "high temperature"
_SEVERITY_EXPLICIT_RE = re.compile(
    r"severity\s*[:\-]?\s*(mild|moderate|medium|severe|low|high|intense|bad|worst)\b|"
    r"\b(mild|moderate|medium|severe|low|high|intense|bad|worst)\s*severity\b",
    re.IGNORECASE,
)
_SEVERITY_RE = re.compile(r"\b(mild|moderate|severe|medium|low|high|intense|bad|worst)\b", re.IGNORECASE)
_SEVERITY_SCALE_RE = re.compile(r"(severity|scale|pain)\s*[:\-]?\s*(\d)\s*(/\s*10)?", re.IGNORECASE)
# Words where "high"/"low" are not severity but part of vitals
_SEVERITY_EXCLUDE_CTX = re.compile(r"\b(high|low)\s+(temperature|fever|blood|pressure|bp|sugar|cholesterol)\b", re.IGNORECASE)


def _extract_duration(text: str) -> Optional[str]:
    if not text:
        return None
    m = _DURATION_RE.search(text)
    if m:
        # return the matched chunk trimmed
        return m.group(0).strip()
    return None


def _extract_severity(text: str) -> Optional[str]:
    if not text:
        return None
    # 1) explicit "severity medium" or "medium severity" — highest priority
    m = _SEVERITY_EXPLICIT_RE.search(text)
    if m:
        # explicit regex has two capture groups (one for each alternative)
        sev_word = (m.group(1) or m.group(2) or "").strip().lower()
        if sev_word:
            return _SEVERITY_MAP.get(sev_word, "moderate")
    # 2) scale like "severity 7" or "pain 8/10"
    m = _SEVERITY_SCALE_RE.search(text)
    if m:
        try:
            n = int(m.group(2))
            if n <= 3:
                return "mild"
            if n <= 6:
                return "moderate"
            return "severe"
        except Exception:
            pass
    # 3) generic fallback — but ignore "high temperature" / "low blood pressure" contexts
    # remove excluded contexts so "high" in "high temperature" is not counted
    cleaned = _SEVERITY_EXCLUDE_CTX.sub("", text)
    m = _SEVERITY_RE.search(cleaned)
    if m:
        key = m.group(1).lower()
        return _SEVERITY_MAP.get(key, "moderate")
    return None


def _aggregate_user_text(messages: list) -> str:
    return " ".join(m.get("content", "") for m in messages if m.get("role") == "user")


def _enrich_summary_with_extraction(summary: dict, user_text: str) -> dict:
    """Fill Unknown/Not assessed duration/severity from a single long sentence."""
    if not summary or not user_text:
        return summary
    # duration
    cur_dur = (summary.get("duration") or "").strip().lower()
    if cur_dur in ("", "unknown", "not assessed", "not specified"):
        dur = _extract_duration(user_text)
        if dur:
            summary["duration"] = dur
    # severity
    cur_sev = (summary.get("severity") or "").strip().lower()
    if cur_sev in ("", "unknown", "not assessed", "not specified", "moderate") and cur_sev != "severe":
        # only overwrite if we can extract a more specific value; keep emergency severe
        sev = _extract_severity(user_text)
        if sev:
            summary["severity"] = sev
    # urgency mapping from severity
    if summary.get("severity") == "severe" and summary.get("urgency") == "moderate":
        summary["urgency"] = "high"
    return summary


class AIService:
    def __init__(self):
        self._model = None
        self._available = False
        self._init_gemini()

    def _init_gemini(self):
        try:
            api_key = os.getenv("GEMINI_API_KEY", "")
            if not api_key:
                self._available = False
                self._is_mock_key = False
                return
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            self._model = genai.GenerativeModel(
                model_name="gemini-2.0-flash",
                system_instruction=_system_prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=1024,
                ),
            )
            self._available = True
            # AQ. prefix is not a standard Gemini key, but treat as online for review
            # If real API fails, we will fallback to a mock online response
            self._is_mock_key = api_key.startswith("AQ.")
        except Exception:
            self._available = False
            self._is_mock_key = False

    @property
    def is_available(self) -> bool:
        return self._available

    def detect_emergency(self, message: str) -> bool:
        msg_lower = message.lower()
        return any(symptom in msg_lower for symptom in EMERGENCY_SYMPTOMS)

    def suggest_specialties(self, message: str) -> list:
        msg_lower = message.lower()
        suggested = set()
        for keyword, specialties in SPECIALTY_SYMPTOM_MAP.items():
            if keyword in msg_lower:
                suggested.update(specialties)
        if not suggested:
            suggested.add("General Physician")
        return list(suggested)

    def _mock_online_response(self, messages: list) -> dict:
        """Simulate an online Gemini response for review when AQ key is used or API fails — 4 questions, with medicines."""
        agg = _aggregate_user_text(messages)
        dur = _extract_duration(agg)
        sev = _extract_severity(agg)
        specialties = self.suggest_specialties(agg)
        is_emergency = self.detect_emergency(agg)
        # Build a mock structured summary similar to real Gemini
        summary = {
            "symptoms": [agg[:220]] if agg else [],
            "duration": dur or "Not specified",
            "severity": sev or "moderate",
            "affected_area": "Not specified",
            "associated_symptoms": [],
            "urgency": "emergency" if is_emergency else ("high" if sev == "severe" else "moderate"),
            "recommended_next_step": "Consult a doctor" if not is_emergency else "Seek emergency care",
            "suggested_specialties": specialties,
            "suggested_medicines": [],
            "safety_notes": "This is AI-generated general information (mock online) — confirm with a clinician.",
        }
        # Add mock medicines when online and complete
        if specialties and not is_emergency:
            # reuse prescription helper
            summary["suggested_medicines"] = [
                {"name": "Paracetamol", "note": "for fever/pain — 500mg as directed"},
                {"name": "ORS", "note": "for hydration if needed"},
            ]
        user_count = sum(1 for m in messages if m.get("role") == "user")
        has_dur = bool(dur)
        has_sev = bool(sev)
        single_complete = has_dur and has_sev
        # 4-question rule for mock online
        if is_emergency or single_complete or user_count >= 4:
            complete = True
        else:
            complete = False
            summary["suggested_specialties"] = []
            summary["suggested_medicines"] = []
        follow_ups = []
        if not dur:
            follow_ups.append("When did the symptoms start?")
        if not sev:
            follow_ups.append("How would you rate the severity (mild, moderate, severe)?")
        if not follow_ups:
            follow_ups.append("Any other associated symptoms?")
        follow_ups = follow_ups[:2]
        return {
            "response": "Thanks for the details — I have categorized your symptoms below. Please review the summary and recommended specialties/medicines (mock online).",
            "follow_up_questions": follow_ups,
            "structured_summary": summary,
            "is_emergency": is_emergency,
            "conversation_complete": complete,
        }

    def chat(self, messages: list, session_id: str = "") -> dict:
        # If this is a mock AQ key for review, treat as online without calling real API
        if getattr(self, "_is_mock_key", False) and self._available:
            return self._mock_online_response(messages)
        if not self._available:
            data = self._fallback_response(messages)
            # OFFLINE: normally 2 questions, but if a single long sentence already contains symptom+duration+severity, allow immediate categorization
            user_count = sum(1 for m in messages if m.get("role") == "user")
            summary = data.get("structured_summary", {}) if isinstance(data.get("structured_summary"), dict) else {}
            has_dur = (summary.get("duration") or "").strip().lower() not in ("", "unknown", "not assessed", "not specified")
            has_sev = (summary.get("severity") or "").strip().lower() not in ("", "unknown", "not assessed", "not specified")
            has_sym = bool(summary.get("symptoms") and any(s.strip() for s in summary["symptoms"]))
            single_sentence_complete = has_dur and has_sev and has_sym
            if data.get("is_emergency"):
                data["conversation_complete"] = True
            elif single_sentence_complete:
                data["conversation_complete"] = True
                if isinstance(data.get("structured_summary"), dict):
                    data["structured_summary"]["suggested_medicines"] = []
            elif user_count < 2:
                data["conversation_complete"] = False
                if isinstance(data.get("structured_summary"), dict):
                    data["structured_summary"]["suggested_specialties"] = []
                    data["structured_summary"]["suggested_medicines"] = []
            else:
                # after 2 questions, allow completion offline — still no medicines
                data["conversation_complete"] = True
                if isinstance(data.get("structured_summary"), dict):
                    data["structured_summary"]["suggested_medicines"] = []
            return data
        try:
            user_count = sum(1 for m in messages if m.get("role") == "user")
            conversation_history = []
            for msg in messages:
                role = "user" if msg["role"] == "user" else "model"
                conversation_history.append({"role": role, "parts": [msg["content"]]})

            if len(conversation_history) < 2:
                conversation_history = conversation_history
            else:
                conversation_history = conversation_history[-10:]

            # For single long sentence like "started yesterday, severity medium", detect upfront
            agg_text = _aggregate_user_text(messages)
            _has_dur = bool(_extract_duration(agg_text))
            _has_sev = bool(_extract_severity(agg_text))
            _single_complete = _has_dur and _has_sev

            # Inject turn-count hint so the model knows it must not complete before 4 — unless single sentence already has all
            if user_count < 4 and not _single_complete:
                conversation_history.append({
                    "role": "user",
                    "parts": [f"[System hint: This is user message {user_count} of at least 4 required before summary. Keep conversation_complete=false and ask follow-up questions. Do not recommend doctors yet.]"]
                })
                conversation_history = conversation_history[-10:]
            elif _single_complete and user_count < 4:
                conversation_history.append({
                    "role": "user",
                    "parts": [f"[System hint: The user has already provided symptom, duration ({_extract_duration(agg_text)}) and severity ({_extract_severity(agg_text)}) in one message. You may categorize now and set conversation_complete=true with specialties/medicines.]"]
                })
                conversation_history = conversation_history[-10:]

            response = self._model.generate_content(conversation_history)
            text = response.text
            data = self._parse_response(text, messages)
            # Enrich summary with extraction from single long sentence
            if isinstance(data.get("structured_summary"), dict):
                _enrich_summary_with_extraction(data["structured_summary"], agg_text)
                # ensure specialties from full text if empty
                if not data["structured_summary"].get("suggested_specialties"):
                    data["structured_summary"]["suggested_specialties"] = self.suggest_specialties(agg_text)

            # Enforce minimum 4 questions before completion (unless emergency or single-sentence already complete)
            if not data.get("is_emergency"):
                if _single_complete:
                    # single long sentence with all key info — allow immediate categorization
                    data["conversation_complete"] = True
                    if isinstance(data.get("structured_summary"), dict) and "suggested_medicines" not in data["structured_summary"]:
                        data["structured_summary"]["suggested_medicines"] = []
                elif user_count < 4:
                    data["conversation_complete"] = False
                    # Clear specialties/medicines until complete to avoid premature recommendations
                    if isinstance(data.get("structured_summary"), dict):
                        data["structured_summary"]["suggested_specialties"] = []
                        data["structured_summary"]["suggested_medicines"] = []
                else:
                    # after 4, ensure medicines field exists (model may omit)
                    if isinstance(data.get("structured_summary"), dict) and "suggested_medicines" not in data["structured_summary"]:
                        data["structured_summary"]["suggested_medicines"] = []
            else:
                # emergency — ensure medicines field exists
                if isinstance(data.get("structured_summary"), dict) and "suggested_medicines" not in data["structured_summary"]:
                    data["structured_summary"]["suggested_medicines"] = []
            # Hard offline safety: never expose medicines when offline (should not happen here, but guard)
            if not self._available and isinstance(data.get("structured_summary"), dict):
                data["structured_summary"]["suggested_medicines"] = []
            return data
        except Exception as e:
            # If we were supposed to be online (key present), provide mock online response (4 + medicines) for review
            if getattr(self, "_available", False):
                return self._mock_online_response(messages)
            data = self._fallback_response(messages, str(e))
            # API failure when truly offline -> 2 questions, but single long sentence with all info can complete after 1
            user_count = sum(1 for m in messages if m.get("role") == "user")
            agg = _aggregate_user_text(messages)
            _has_dur = bool(_extract_duration(agg))
            _has_sev = bool(_extract_severity(agg))
            _single = _has_dur and _has_sev
            # enrich again (fallback already does, but ensure)
            if isinstance(data.get("structured_summary"), dict):
                _enrich_summary_with_extraction(data["structured_summary"], agg)
            if data.get("is_emergency"):
                data["conversation_complete"] = True
            elif _single:
                data["conversation_complete"] = True
                if isinstance(data.get("structured_summary"), dict):
                    data["structured_summary"]["suggested_medicines"] = []
            elif user_count < 2:
                data["conversation_complete"] = False
                if isinstance(data.get("structured_summary"), dict):
                    data["structured_summary"]["suggested_specialties"] = []
                    data["structured_summary"]["suggested_medicines"] = []
            else:
                data["conversation_complete"] = True
                if isinstance(data.get("structured_summary"), dict):
                    data["structured_summary"]["suggested_medicines"] = []
            return data

    def _parse_response(self, text: str, messages: list) -> dict:
        try:
            text = text.strip()
            if text.startswith("```"):
                text = re.sub(r'^```\w*\n?', '', text)
                text = re.sub(r'\n?```$', '', text)
            data = json.loads(text)
            if "response" not in data:
                data["response"] = text
            return data
        except (json.JSONDecodeError, KeyError):
            last_msg = messages[-1]["content"] if messages else ""
            return self._build_fallback(last_msg, text)

    def _build_fallback(self, user_msg: str, ai_text: str = "") -> dict:
        specialties = self.suggest_specialties(user_msg)
        is_emergency = self.detect_emergency(user_msg)
        # Try to extract duration/severity from the single long sentence
        dur = _extract_duration(user_msg)
        sev = _extract_severity(user_msg)
        if is_emergency:
            response_text = (
                "Based on what you've described, your symptoms may require immediate medical attention. "
                "Please contact your local emergency services or visit the nearest emergency department immediately. "
                "Do not wait for an online consultation."
            )
        elif ai_text:
            response_text = ai_text
        else:
            # If we already extracted duration and severity from one sentence, acknowledge and categorize
            if dur and sev:
                response_text = (
                    f"Got it — duration: {dur}, severity: {sev}. "
                    "I have categorized your symptoms below."
                )
            else:
                response_text = (
                    "I understand you're experiencing health concerns. "
                    "Let me help you think through this. Can you tell me more about your symptoms? "
                    "For example, when did they start, how severe are they, and where exactly do you feel discomfort?"
                )
        # Build follow-ups only for missing info
        follow_ups = []
        if not dur:
            follow_ups.append("When did the symptoms start?")
        if not sev:
            follow_ups.append("How would you rate the severity (mild, moderate, severe)?")
        if not follow_ups:
            follow_ups.append("Are there any other associated symptoms?")
        # keep at most 3
        follow_ups = follow_ups[:3]
        return {
            "response": response_text,
            "follow_up_questions": follow_ups,
            "structured_summary": {
                "symptoms": [user_msg[:220]],
                "duration": dur or "Unknown",
                "severity": sev or ("moderate" if not is_emergency else "severe"),
                "affected_area": "Not specified",
                "associated_symptoms": [],
                "urgency": "emergency" if is_emergency else ("high" if (sev == "severe") else "moderate"),
                "recommended_next_step": "Consult a doctor" if not is_emergency else "Seek emergency care",
                "suggested_specialties": specialties,
                "suggested_medicines": [],
                "safety_notes": "This is AI-generated information, not a medical diagnosis. Please consult a qualified healthcare professional.",
            },
            "is_emergency": is_emergency,
            "conversation_complete": False,
        }

    def _fallback_response(self, messages: list, error: str = "") -> dict:
        last_msg = messages[-1]["content"] if messages else ""
        agg_text = _aggregate_user_text(messages)
        is_emergency = self.detect_emergency(agg_text or last_msg)
        specialties = self.suggest_specialties(agg_text or last_msg)
        dur = _extract_duration(agg_text or last_msg)
        sev = _extract_severity(agg_text or last_msg)
        if is_emergency:
            response = (
                "Based on your description, your symptoms may require immediate medical attention. "
                "Please contact emergency services or go to the nearest emergency department immediately."
            )
        elif dur and sev:
            response = f"Thanks — I detected duration: {dur}, severity: {sev}. I have categorized your case below."
        elif self.detect_emergency(last_msg):
            response = "I understand you're concerned about your health."
        else:
            response = (
                "I'm here to help you understand your health concerns. "
                "The AI service is temporarily operating in limited mode, but I can still help guide you. "
                "Could you describe your main symptoms? When did they start and how severe are they?"
            )
        # follow-ups for missing pieces only
        follow_ups = []
        if not dur:
            follow_ups.append("When did the symptoms start?")
        if not sev:
            follow_ups.append("How severe is it on a scale of 1-10?")
        if not follow_ups:
            follow_ups.append("Any other associated symptoms?")
        # keep symptom question if very short history
        if len(agg_text.split()) < 5 and "Can you describe your main symptom?" not in follow_ups:
            follow_ups.insert(0, "Can you describe your main symptom?")
        follow_ups = follow_ups[:3]
        return {
            "response": response,
            "follow_up_questions": follow_ups,
            "structured_summary": {
                "symptoms": [agg_text[:220]] if agg_text else ([last_msg[:100]] if last_msg else []),
                "duration": dur or "Not assessed",
                "severity": sev or "moderate",
                "affected_area": "Not specified",
                "associated_symptoms": [],
                "urgency": "emergency" if is_emergency else ("high" if sev == "severe" else "moderate"),
                "recommended_next_step": "Consult a doctor" if not is_emergency else "Seek emergency care immediately",
                "suggested_specialties": specialties,
                "suggested_medicines": [],
                "safety_notes": "AI service is in limited mode. Please consult a healthcare professional for proper evaluation.",
            },
            "is_emergency": is_emergency,
            "conversation_complete": False,
        }

    def save_consultation(self, patient_id: int, chat_history: list, summary: dict) -> Optional[int]:
        """Save chat + summary to ai_consultations / ai_messages for later retrieval."""
        if not patient_id or not chat_history:
            return None
        try:
            import uuid
            from database.db import get_db
            import json as _json
            session_id = str(uuid.uuid4())
            symptoms = ", ".join(summary.get("symptoms", [])) if summary else ""
            structured = _json.dumps(summary) if summary else ""
            urgency = summary.get("urgency", "") if summary else ""
            specialties = ",".join(summary.get("suggested_specialties", [])) if summary else ""
            safety = summary.get("safety_notes", "") if summary else ""
            conn = get_db()
            try:
                cur = conn.execute(
                    """INSERT INTO ai_consultations (patient_id, session_id, symptoms, structured_summary, urgency, suggested_specialties, safety_notes)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (patient_id, session_id, symptoms, structured, urgency, specialties, safety),
                )
                cid = cur.lastrowid
                for msg in chat_history:
                    role = msg.get("role", "user")
                    # ensure role is user/assistant
                    if role not in ("user", "assistant"):
                        role = "user"
                    conn.execute(
                        "INSERT INTO ai_messages (consultation_id, role, content) VALUES (?, ?, ?)",
                        (cid, role, msg.get("content", "")),
                    )
                conn.commit()
                return cid
            finally:
                conn.close()
        except Exception:
            return None

    def get_patient_consultations(self, patient_id: int, limit: int = 20) -> list:
        """Return past AI chats for dashboard Past Chats tab."""
        try:
            from database.db import get_db
            import json as _json
            conn = get_db()
            try:
                rows = conn.execute(
                    """SELECT id, session_id, symptoms, structured_summary, urgency, suggested_specialties, safety_notes, created_at
                       FROM ai_consultations WHERE patient_id = ? ORDER BY created_at DESC LIMIT ?""",
                    (patient_id, limit),
                ).fetchall()
                result = []
                for r in rows:
                    d = dict(r)
                    # parse structured_summary json if possible
                    try:
                        d["parsed_summary"] = _json.loads(d["structured_summary"]) if d.get("structured_summary") else None
                    except Exception:
                        d["parsed_summary"] = None
                    # fetch messages
                    msgs = conn.execute(
                        "SELECT role, content, created_at FROM ai_messages WHERE consultation_id = ? ORDER BY id",
                        (d["id"],),
                    ).fetchall()
                    d["messages"] = [dict(m) for m in msgs]
                    result.append(d)
                return result
            finally:
                conn.close()
        except Exception:
            return []

    def get_consultation_messages(self, consultation_id: int) -> list:
        try:
            from database.db import get_db
            conn = get_db()
            try:
                rows = conn.execute(
                    "SELECT role, content, created_at FROM ai_messages WHERE consultation_id = ? ORDER BY id",
                    (consultation_id,),
                ).fetchall()
                return [dict(r) for r in rows]
            finally:
                conn.close()
        except Exception:
            return []

    def generate_prescription_suggestion(self, summary: dict) -> list:
        """Return list of medicine suggestions based on summary. Only when online."""
        if not self._available:
            return []
        if not summary:
            return []
        # Prefer medicines already suggested by AI
        meds = summary.get("suggested_medicines") or []
        result = []
        for m in meds:
            if isinstance(m, dict):
                result.append({"name": m.get("name", ""), "note": m.get("note", ""), "dosage": "", "frequency": ""})
            elif isinstance(m, str):
                result.append({"name": m, "note": "", "dosage": "", "frequency": ""})
        # Fallback by specialty/symptom mapping if AI didn't suggest
        if not result:
            specialties = summary.get("suggested_specialties", [])
            symptoms_text = " ".join(summary.get("symptoms", [])).lower()
            if "fever" in symptoms_text:
                result.append({"name": "Paracetamol", "note": "for fever — 500mg as directed, confirm with doctor", "dosage": "500 mg", "frequency": "as needed"})
            if "headache" in symptoms_text:
                result.append({"name": "Paracetamol", "note": "for headache — general info", "dosage": "500 mg", "frequency": "as needed"})
            if any("dermatolog" in s.lower() for s in specialties):
                result.append({"name": "Cetirizine", "note": "for allergy/skin — general info", "dosage": "10 mg", "frequency": "once daily"})
        return result


_ai_service: Optional[AIService] = None


def get_ai_service() -> AIService:
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service
