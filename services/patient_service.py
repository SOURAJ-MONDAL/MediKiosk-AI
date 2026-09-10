from typing import Optional
from database.db import get_db


class PatientService:
    @staticmethod
    def get_patient_by_user_id(user_id: int) -> Optional[dict]:
        conn = get_db()
        try:
            patient = conn.execute("""
                SELECT p.*, u.first_name, u.last_name, u.email, u.phone,
                       u.profile_image as user_image
                FROM patients p
                JOIN users u ON p.user_id = u.id
                WHERE p.user_id = ?
            """, (user_id,)).fetchone()
            return dict(patient) if patient else None
        finally:
            conn.close()

    @staticmethod
    def get_patient_by_id(patient_id: int) -> Optional[dict]:
        conn = get_db()
        try:
            patient = conn.execute("""
                SELECT p.*, u.first_name, u.last_name, u.email, u.phone
                FROM patients p
                JOIN users u ON p.user_id = u.id
                WHERE p.id = ?
            """, (patient_id,)).fetchone()
            return dict(patient) if patient else None
        finally:
            conn.close()

    @staticmethod
    def update_profile(user_id: int, **kwargs) -> bool:
        allowed = {"date_of_birth", "gender", "blood_group", "allergies",
                   "medical_history", "emergency_contact", "emergency_phone",
                   "address", "city"}
        updates = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
        if not updates:
            return False
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [user_id]
        conn = get_db()
        try:
            conn.execute(f"UPDATE patients SET {set_clause} WHERE user_id = ?", values)
            conn.commit()
            return True
        finally:
            conn.close()
