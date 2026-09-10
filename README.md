# MediKiosk 🏥

> **Your Intelligent Healthcare Companion**

MediKiosk is an AI-assisted healthcare platform that connects patients, symptoms, and doctors.
Describe how you feel to the **MediKiosk AI Health Assistant**, receive a structured health
summary with urgency guidance, discover the right specialist, and book an appointment in
minutes.

Built for hackathons and demos — a polished, runnable AI healthcare MVP.

---

## Overview

```
PATIENT
   ↓
SYMPTOM / HEALTH CONCERN
   ↓
MEDIKIOSK AI HEALTH ASSISTANT
   ↓
STRUCTURED HEALTH SUMMARY
   ↓
TRIAGE / URGENCY
   ↓
DOCTOR RECOMMENDATIONS
   ↓
DOCTOR + LOCATION SELECTION
   ↓
DATE + TIME
   ↓
APPOINTMENT BOOKING
   ↓
CONFIRMATION
   ↓
DOCTOR REVIEW
   ↓
PRESCRIPTION / FOLLOW-UP
```

## Features

### 🤖 AI Health Assistant
- Conversational symptom gathering with intelligent follow-up questions
- Structured health summaries (symptoms, duration, severity, urgency, next steps)
- **Emergency symptom detection** with prominent safety alerts
- Safe offline fallback mode when the Gemini API is unavailable
- Visual AI companion with idle / listening / thinking / success states

### 🩺 Doctor discovery
- 10+ specialties including Cardiology, Neurology, Dermatology, Pediatrics and more
- Search by specialty, city, and consultation fee
- Doctor cards with ratings, experience, languages, bio, and verification badges
- AI-recommended specialties based on your symptoms (presented as suggestions)

### 📅 Appointment booking
- 5-step booking flow: Doctor → Location → Date → Time → Confirm
- Real schedule-based slot generation (no fake availability)
- Transactional booking with **duplicate-slot prevention**
- Location-aware scheduling across hospitals, clinics, and chambers
- Polished confirmation screen with success animation

### 👤 Patient experience
- Personal dashboard with upcoming/completed appointments
- Health documents (lab reports, prescriptions, imaging) with safe upload validation
- Prescriptions from your consultations
- Rate & review doctors after completed visits
- Notifications for bookings, cancellations, prescriptions

### 👨⚕️ Doctor experience
- Doctor dashboard: today's appointments, patient list, location & schedule management
- Start / complete / cancel appointments
- Create prescriptions (per-medicine with dosage, frequency, duration, instructions)
- AI-assisted prescription drafts that require doctor approval

### 🔐 Security
- Password hashing (PBKDF2-SHA256) — no plaintext storage
- Parameterized SQL everywhere — no injection
- Role-based access: patient vs doctor views
- Session-protected routes and authorization checks
- Prompt-injection-resistant AI prompts with isolated Gemini service

## Technology stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.11+ |
| Frontend | Streamlit + custom HTML/CSS design system |
| AI | Google Gemini (generative AI SDK) |
| Database | SQLite (with foreign keys, indexes, constraints) |
| Auth | PBKDF2-SHA256 password hashing |
| Testing | pytest |

## Project structure

```
MediKiosk/
├── app.py                      # Entry point (st.navigation + sidebar)
├── requirements.txt
├── README.md
├── .env.example
├── .gitignore
├── .streamlit/
│   └── config.toml             # Light health-tech theme
├── database/
│   ├── db.py                   # SQLite connection + init
│   ├── schema.sql              # 14-table schema
│   └── seed.py                 # Demo doctors, patients, locations, schedules
├── models/                     # Dataclasses (user, doctor, patient, ...)
├── services/                   # Business logic (auth, ai, appointments, ...)
├── components/                 # Reusable UI (cards, stepper, AI companion, CSS)
├── app_pages/                  # Streamlit pages (home, dashboards, booking, ...)
├── utils/                      # Security, validation, constants, helpers
├── assets/                     # Images / icons / styles
└── tests/                      # pytest suite
```

## Installation

### 1. Create a virtual environment

```bash
python -m venv .venv
```

**Windows:**
```bash
.venv\Scripts\activate
```

**macOS / Linux:**
```bash
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure the environment

```bash
copy .env.example .env
```

**Windows (PowerShell):**
```powershell
Copy-Item .env.example .env
```

Open `.env` and add your Google Gemini API key:

```
GEMINI_API_KEY=your_api_key_here
```

Get a key from [Google AI Studio](https://aistudio.google.com/apikey).

> **No API key?** The app still works. The AI runs in a safe offline fallback mode
> with rule-based emergency detection and specialty suggestions. You can browse
> doctors and book appointments normally.

### 4. Run the app

```bash
streamlit run app.py
```

The application auto-creates the database and seeds demo data on first launch.

### 5. Run the tests

```bash
pytest
```

## Demo credentials

The database is seeded automatically with demo accounts.

**Patient accounts:**
| Email | Password |
|-------|----------|
| `john.smith@example.com` | `Patient123!` |
| `amit.sharma@example.com` | `Patient123!` |
| `emma.wilson@example.com` | `Patient123!` |
| `david.brown@example.com` | `Patient123!` |

**Doctor accounts:**
| Email | Password |
|-------|----------|
| `sarah.johnson@medikiosk.com` | `Doctor123!` |
| `mark.chen@medikiosk.com` | `Doctor123!` |
| `priya.patel@medikiosk.com` | `Doctor123!` |
| `james.wilson@medikiosk.com` | `Doctor123!` |
| `robert.taylor@medikiosk.com` | `Doctor123!` |

## Hackathon demo flow

1. Open MediKiosk — polished landing page with hero, features, stats.
2. Click **Talk to MediKiosk AI** (or log in as a patient).
3. Type `I have been having headaches for three days.`
4. The AI asks follow-up questions and builds a structured summary.
5. Review the urgency badge and recommended specialties.
6. Click **Find matching doctors** → browse cardiologist/neurologist cards.
7. Open a doctor profile → **Book appointment**.
8. Walk the 5-step booking flow (doctor → location → date → time → confirm).
9. See the success confirmation with booking ID.
10. Open **My Dashboard** → upcoming appointment is listed; check notifications.
11. Log out, log in as a doctor (`james.wilson@medikiosk.com`).
12. Open **Doctor Dashboard** → today's appointments and patient list.
13. Mark an appointment complete → create a prescription.
14. The patient receives a prescription notification.

## Medical safety disclaimer

MediKiosk provides **AI-assisted health information and appointment support**.
It is **not** a substitute for professional medical advice, diagnosis, or treatment.

- The AI assistant offers general guidance only — it cannot diagnose you.
- AI recommendations are suggestions, not medical prescriptions.
- Doctor matching is based on symptom patterns and user preference, not a diagnosis.
- If you believe you're experiencing a medical emergency, contact your local
  emergency services or seek immediate in-person care.

This prototype is intended for demonstration and educational purposes only.
It does not claim HIPAA compliance or regulatory certification.

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `streamlit: command not found` | Activate your virtual environment first, then `pip install -r requirements.txt` |
| AI says "limited offline mode" | Add `GEMINI_API_KEY` to `.env` and restart the app |
| Port 8501 already in use | `streamlit run app.py --server.port 8502` |
| Database already has demo data | Delete `medikiosk.db` and restart — it re-seeds automatically |
| Tests fail on `google` import | Ensure `pip install -r requirements.txt` completed |

## Architecture

- **database/** — SQLite access and schema. All queries are parameterized.
- **services/** — pure-Python business logic, independently testable, no Streamlit imports.
- **components/** — reusable UI primitives + the global design-system CSS.
- **app_pages/** — one script per view; each validates the session and renders UI.
- **utils/** — security helpers, input validation, constants, and formatting.

The **AI service** is fully isolated in `services/ai_service.py` and degrades
gracefully to rule-based fallbacks, so the app never crashes without an API key.