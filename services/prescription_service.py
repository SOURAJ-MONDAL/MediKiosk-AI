from typing import Optional
from database.db import get_db


class PrescriptionService:
    @staticmethod
    def create_prescription(appointment_id: int, doctor_id: int, patient_id: int,
                            medicine_name: str, dosage: str = "", frequency: str = "",
                            duration: str = "", instructions: str = "", doctor_notes: str = "",
                            is_ai_suggested: int = 0) -> dict:
        conn = get_db()
        try:
            cursor = conn.execute(
                """INSERT INTO prescriptions (appointment_id, doctor_id, patient_id,
                   medicine_name, dosage, frequency, duration, instructions, doctor_notes, is_ai_suggested, is_approved)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (appointment_id, doctor_id, patient_id, medicine_name, dosage,
                 frequency, duration, instructions, doctor_notes, is_ai_suggested, 1 if not is_ai_suggested else 0)
            )
            prescription_id = cursor.lastrowid
            conn.commit()
            return {"success": True, "prescription_id": prescription_id}
        except Exception as e:
            conn.rollback()
            return {"success": False, "error": str(e)}
        finally:
            conn.close()

    @staticmethod
    def get_patient_prescriptions(patient_id: int) -> list:
        conn = get_db()
        try:
            prescriptions = conn.execute("""
                SELECT pr.*, a.appointment_date, a.appointment_time,
                       u.first_name as doctor_first_name, u.last_name as doctor_last_name,
                       doc.specialization
                FROM prescriptions pr
                JOIN appointments a ON pr.appointment_id = a.id
                JOIN doctors doc ON pr.doctor_id = doc.id
                JOIN users u ON doc.user_id = u.id
                WHERE pr.patient_id = ?
                ORDER BY pr.created_at DESC
            """, (patient_id,)).fetchall()
            return [dict(p) for p in prescriptions]
        finally:
            conn.close()

    @staticmethod
    def get_appointment_prescriptions(appointment_id: int) -> list:
        conn = get_db()
        try:
            prescriptions = conn.execute(
                "SELECT * FROM prescriptions WHERE appointment_id = ? ORDER BY created_at DESC",
                (appointment_id,)
            ).fetchall()
            return [dict(p) for p in prescriptions]
        finally:
            conn.close()

    @staticmethod
    def approve_prescription(prescription_id: int) -> bool:
        conn = get_db()
        try:
            conn.execute(
                "UPDATE prescriptions SET is_approved = 1 WHERE id = ?",
                (prescription_id,)
            )
            conn.commit()
            return True
        finally:
            conn.close()

    @staticmethod
    def get_doctor_prescriptions(doctor_id: int) -> list:
        conn = get_db()
        try:
            prescriptions = conn.execute("""
                SELECT pr.*, a.appointment_date,
                       u.first_name as patient_first_name, u.last_name as patient_last_name
                FROM prescriptions pr
                JOIN appointments a ON pr.appointment_id = a.id
                JOIN patients p ON pr.patient_id = p.id
                JOIN users u ON p.user_id = u.id
                WHERE pr.doctor_id = ?
                ORDER BY pr.created_at DESC
            """, (doctor_id,)).fetchall()
            return [dict(p) for p in prescriptions]
        finally:
            conn.close()
