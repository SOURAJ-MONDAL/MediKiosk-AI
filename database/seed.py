import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import get_db, init_db
from utils.security import hash_password


def seed_database():
    init_db()
    conn = get_db()
    try:
        existing = conn.execute("SELECT COUNT(*) as count FROM users").fetchone()
        if existing["count"] > 0:
            print("Database already seeded. Skipping.")
            return

        doctors_data = [
            ("sarah.johnson@medikiosk.com", "Doctor123!", "Sarah", "Johnson", "Cardiologist",
             "MBBS, MD (Cardiology), FACC", 15,
             "Board-certified cardiologist with 15 years of experience in interventional cardiology and preventive heart care.",
             150.0, 4.9, 214, "English, Spanish", True, "+1 555-0301"),
            ("mark.chen@medikiosk.com", "Doctor123!", "Mark", "Chen", "Neurologist",
             "MBBS, MD (Neurology)", 12,
             "Specialist in headache medicine, stroke care, and movement disorders.",
             180.0, 4.8, 176, "English, Chinese, Cantonese", True, "+1 555-0302"),
            ("alex.martinez@medikiosk.com", "Doctor123!", "Alex", "Martinez", "Dermatologist",
             "MBBS, MD (Dermatology)", 8,
             "Clinical dermatologist focused on acne, eczema, and skin cancer screening.",
             120.0, 4.7, 143, "English, Spanish", True, "+1 555-0303"),
            ("priya.patel@medikiosk.com", "Doctor123!", "Priya", "Patel", "Pediatrician",
             "MBBS, MD (Pediatrics)", 10,
             "Compassionate pediatrician caring for newborns, children, and adolescents.",
             100.0, 4.9, 268, "English, Hindi, Gujarati", True, "+1 555-0304"),
            ("james.wilson@medikiosk.com", "Doctor123!", "James", "Wilson", "General Physician",
             "MBBS, MD (Internal Medicine)", 7,
             "General internal medicine physician for adult primary care and chronic condition management.",
             80.0, 4.6, 192, "English", True, "+1 555-0305"),
            ("emily.davis@medikiosk.com", "Doctor123!", "Emily", "Davis", "Gynecologist",
             "MBBS, MS (OB/GYN)", 11,
             "OB/GYN specialist in women's health, prenatal care, and reproductive medicine.",
             140.0, 4.8, 187, "English", True, "+1 555-0306"),
            ("david.kim@medikiosk.com", "Doctor123!", "David", "Kim", "Orthopedic",
             "MBBS, MS (Orthopedics)", 9,
             "Orthopedic surgeon specializing in sports injuries, joint replacement, and spine conditions.",
             160.0, 4.7, 154, "English, Korean", True, "+1 555-0307"),
            ("lisa.anderson@medikiosk.com", "Doctor123!", "Lisa", "Anderson", "ENT",
             "MBBS, MS (ENT)", 6,
             "ENT specialist for ear, nose, throat conditions including chronic sinusitis and hearing loss.",
             110.0, 4.6, 121, "English", True, "+1 555-0308"),
            ("robert.taylor@medikiosk.com", "Doctor123!", "Robert", "Taylor", "Psychiatrist",
             "MBBS, MD (Psychiatry)", 13,
             "Psychiatrist specializing in anxiety, depression, bipolar disorders, and mental wellness.",
             170.0, 4.8, 165, "English", True, "+1 555-0309"),
            ("maria.garcia@medikiosk.com", "Doctor123!", "Maria", "Garcia", "Dentist",
             "BDS, MDS (Conservative Dentistry)", 8,
             "Dentist specializing in preventive care, cosmetic dentistry, and root canal treatment.",
             90.0, 4.7, 208, "English, Spanish", True, "+1 555-0310"),
        ]

        patient_data = [
            ("john.smith@example.com", "Patient123!", "John", "Smith", "1990-03-15", "Male", "O+", "Penicillin",
             "Asthma", "Jane Smith", "+1 555-0101", "123 Main St", "New York"),
            ("amit.sharma@example.com", "Patient123!", "Amit", "Sharma", "1985-07-22", "Male", "A+", "",
             "Hypertension", "Rita Sharma", "+1 555-0102", "456 Oak Ave", "San Francisco"),
            ("emma.wilson@example.com", "Patient123!", "Emma", "Wilson", "1995-11-02", "Female", "B-", "Sulfa drugs",
             "", "Tom Wilson", "+1 555-0103", "789 Pine Rd", "Chicago"),
            ("david.brown@example.com", "Patient123!", "David", "Brown", "1978-01-30", "Male", "AB+", "",
             "Diabetes Type 2", "Sarah Brown", "+1 555-0104", "321 Elm St", "Houston"),
        ]

        locations_data = [
            ("Apollo Health Center", "hospital", "100 Medical Plaza Drive", "New York", "NY",
             "+1 555-0201", "contact@apollohealth.com"),
            ("CityCare Clinic", "clinic", "45 Wellness Way", "San Francisco", "CA",
             "+1 555-0202", "care@citycareclinic.com"),
            ("GreenField Medical", "clinic", "789 Health Boulevard", "Chicago", "IL",
             "+1 555-0203", "info@greenfieldmed.com"),
            ("MediPoint Diagnostic Center", "chamber", "234 Cure Lane", "Houston", "TX",
             "+1 555-0204", "hello@medipoint.com"),
            ("Summit Medical Hospital", "hospital", "567 Recovery Road", "New York", "NY",
             "+1 555-0205", "care@summitmed.com"),
            ("Northside Family Clinic", "clinic", "890 Care Drive", "San Francisco", "CA",
             "+1 555-0206", "info@northsideclinic.com"),
        ]

        doctor_location_map = {
            1: [1, 5],
            2: [2, 6],
            3: [3],
            4: [1, 2],
            5: [2, 3],
            6: [1, 6],
            7: [5],
            8: [3, 4],
            9: [2, 6],
            10: [4, 5],
        }

        schedule_data = [
            (1, 1, 0, "09:00", "17:00", 30),
            (1, 1, 2, "09:00", "13:00", 30),
            (1, 1, 4, "13:00", "17:00", 30),
            (1, 5, 1, "10:00", "16:00", 30),
            (1, 5, 3, "09:00", "13:00", 30),
            (2, 2, 0, "09:00", "15:00", 45),
            (2, 2, 3, "10:00", "16:00", 45),
            (2, 6, 1, "13:00", "18:00", 45),
            (3, 3, 1, "10:00", "16:00", 30),
            (3, 3, 4, "09:00", "13:00", 30),
            (4, 1, 2, "09:00", "17:00", 20),
            (4, 2, 4, "10:00", "16:00", 20),
            (5, 2, 0, "10:00", "17:00", 30),
            (5, 2, 2, "09:00", "13:00", 30),
            (5, 3, 5, "10:00", "15:00", 30),
            (6, 1, 1, "09:00", "16:00", 30),
            (6, 6, 4, "10:00", "15:00", 30),
            (7, 5, 2, "10:00", "17:00", 45),
            (7, 5, 5, "09:00", "14:00", 45),
            (8, 3, 0, "09:00", "16:00", 20),
            (8, 4, 3, "10:00", "15:00", 20),
            (9, 2, 1, "10:00", "17:00", 50),
            (9, 6, 5, "09:00", "15:00", 50),
            (10, 4, 0, "09:00", "17:00", 30),
            (10, 5, 5, "09:00", "14:00", 30),
        ]

        avatar_for = lambda seed: f"https://api.dicebear.com/7.x/avataaars/svg?seed={seed}&backgroundColor=b6e3f4,c0aede,d1d4f9,ffd5dc"

        for loc in locations_data:
            conn.execute(
                "INSERT INTO locations (name, type, address, city, state, phone, email) VALUES (?, ?, ?, ?, ?, ?, ?)",
                loc
            )

        doctor_ids = {}
        for i, (email, pwd, fn, ln, spec, qual, exp, bio, fee, rating, total, languages, verified, phone) in enumerate(doctors_data):
            pwd_hash = hash_password(pwd)
            cursor = conn.execute(
                "INSERT INTO users (email, password_hash, role, first_name, last_name, phone, profile_image) VALUES (?, ?, 'doctor', ?, ?, ?, ?)",
                (email, pwd_hash, fn, ln, phone, avatar_for(f"Dr{fn}{ln}"))
            )
            user_id = cursor.lastrowid
            cursor = conn.execute(
                """INSERT INTO doctors (user_id, specialization, qualification, experience_years,
                   bio, consultation_fee, rating, total_ratings, languages, is_verified)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (user_id, spec, qual, exp, bio, fee, rating, total, languages, 1 if verified else 0)
            )
            doctor_ids[i + 1] = cursor.lastrowid

        for doc_key, loc_list in doctor_location_map.items():
            doctor_id = doctor_ids[doc_key]
            for loc_id in loc_list:
                fee = doctors_data[doc_key - 1][8]
                conn.execute(
                    "INSERT INTO doctor_locations (doctor_id, location_id, consultation_fee) VALUES (?, ?, ?)",
                    (doctor_id, loc_id, fee)
                )

        patient_ids = {}
        for i, (email, pwd, fn, ln, dob, gender, blood, allergies, history, emergency_contact, emergency_phone, address, city) in enumerate(patient_data):
            pwd_hash = hash_password(pwd)
            phone = f"+1 555-01{i + 1:02d}"
            avatar = avatar_for(f"Pt{fn}{ln}")
            cursor = conn.execute(
                "INSERT INTO users (email, password_hash, role, first_name, last_name, phone, profile_image) VALUES (?, ?, 'patient', ?, ?, ?, ?)",
                (email, pwd_hash, fn, ln, phone, avatar)
            )
            uid = cursor.lastrowid
            cursor = conn.execute(
                """INSERT INTO patients (user_id, date_of_birth, gender, blood_group, allergies, medical_history,
                   emergency_contact, emergency_phone, address, city, profile_image)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (uid, dob, gender, blood, allergies, history, emergency_contact, emergency_phone, address, city, avatar)
            )
            patient_ids[i + 1] = cursor.lastrowid

        for (doctor_id, location_id, day, start, end, duration) in schedule_data:
            conn.execute(
                """INSERT INTO schedules (doctor_id, location_id, day_of_week, start_time, end_time, slot_duration)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (doctor_id, location_id, day, start, end, duration)
            )

        from datetime import date, timedelta
        today = date.today()
        for n in range(6):
            conn.execute(
                """INSERT INTO appointments (patient_id, doctor_id, location_id, appointment_date, appointment_time, status, reason)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (patient_ids[n % 4 + 1], doctor_ids[n % 10 + 1], ((n % 6) + 1),
                 (today + timedelta(days=n + 2)).isoformat(), f"09:0{n % 3}0", "booked",
                 "Routine consultation")
            )

        conn.commit()
        print(f"Database seeded with {len(doctors_data)} doctors, {len(patient_data)} patients, {len(locations_data)} locations.")
    finally:
        conn.close()


if __name__ == "__main__":
    seed_database()