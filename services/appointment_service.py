from typing import Optional
from database.db import get_db


class AppointmentService:
    @staticmethod
    def book_appointment(patient_id: int, doctor_id: int, location_id: int,
                         date_str: str, time_str: str, reason: str = "",
                         ai_summary: str = None, ai_chat_history: str = None) -> dict:
        conn = get_db()
        try:
            existing = conn.execute(
                """SELECT id FROM appointments
                   WHERE doctor_id = ? AND appointment_date = ? AND appointment_time = ?
                   AND status IN ('booked', 'confirmed')""",
                (doctor_id, date_str, time_str)
            ).fetchone()
            if existing:
                return {"success": False, "error": "This slot is already booked"}

            # store AI summary/chat if provided (for doctor to view)
            cursor = conn.execute(
                """INSERT INTO appointments (patient_id, doctor_id, location_id, appointment_date, appointment_time, reason, ai_summary, ai_chat_history)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (patient_id, doctor_id, location_id, date_str, time_str, reason, ai_summary, ai_chat_history)
            )
            appointment_id = cursor.lastrowid
            conn.commit()
            return {"success": True, "appointment_id": appointment_id}
        except Exception as e:
            conn.rollback()
            return {"success": False, "error": str(e)}
        finally:
            conn.close()

    @staticmethod
    def get_patient_appointments(patient_id: int, status: str = None) -> list:
        conn = get_db()
        try:
            query = """
                SELECT a.*, d.specialization, d.consultation_fee,
                       u.first_name as doctor_first_name, u.last_name as doctor_last_name,
                       l.name as location_name, l.city as location_city
                FROM appointments a
                JOIN doctors d ON a.doctor_id = d.id
                JOIN users u ON d.user_id = u.id
                JOIN locations l ON a.location_id = l.id
                WHERE a.patient_id = ?
            """
            params = [patient_id]
            if status:
                query += " AND a.status = ?"
                params.append(status)
            query += " ORDER BY a.appointment_date DESC, a.appointment_time DESC"
            appointments = conn.execute(query, params).fetchall()
            return [dict(a) for a in appointments]
        finally:
            conn.close()

    @staticmethod
    def get_doctor_appointments(doctor_id: int, date_str: str = None,
                                status: str = None) -> list:
        conn = get_db()
        try:
            query = """
                SELECT a.*, p.id as patient_db_id,
                       u.first_name as patient_first_name, u.last_name as patient_last_name,
                       u.email as patient_email, u.phone as patient_phone,
                       l.name as location_name, l.city as location_city
                FROM appointments a
                JOIN patients p ON a.patient_id = p.id
                JOIN users u ON p.user_id = u.id
                JOIN locations l ON a.location_id = l.id
                WHERE a.doctor_id = ?
            """
            params = [doctor_id]
            if date_str:
                query += " AND a.appointment_date = ?"
                params.append(date_str)
            if status:
                query += " AND a.status = ?"
                params.append(status)
            query += " ORDER BY a.appointment_date, a.appointment_time"
            appointments = conn.execute(query, params).fetchall()
            return [dict(a) for a in appointments]
        finally:
            conn.close()

    @staticmethod
    def get_appointment_by_id(appointment_id: int) -> Optional[dict]:
        conn = get_db()
        try:
            appointment = conn.execute("""
                SELECT a.*, d.specialization, d.consultation_fee,
                       u_doc.first_name as doctor_first_name, u_doc.last_name as doctor_last_name,
                       l.name as location_name, l.city as location_city, l.address as location_address,
                       p.id as patient_db_id, u_pat.first_name as patient_first_name,
                       u_pat.last_name as patient_last_name, u_pat.email as patient_email
                FROM appointments a
                JOIN doctors d ON a.doctor_id = d.id
                JOIN users u_doc ON d.user_id = u_doc.id
                JOIN locations l ON a.location_id = l.id
                JOIN patients p ON a.patient_id = p.id
                JOIN users u_pat ON p.user_id = u_pat.id
                WHERE a.id = ?
            """, (appointment_id,)).fetchone()
            return dict(appointment) if appointment else None
        finally:
            conn.close()

    @staticmethod
    def update_status(appointment_id: int, status: str, notes: str = None) -> bool:
        allowed = {"booked", "confirmed", "completed", "cancelled", "no_show"}
        if status not in allowed:
            return False
        conn = get_db()
        try:
            if notes:
                conn.execute(
                    "UPDATE appointments SET status = ?, notes = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (status, notes, appointment_id)
                )
            else:
                conn.execute(
                    "UPDATE appointments SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (status, appointment_id)
                )
            conn.commit()
            return True
        finally:
            conn.close()

    @staticmethod
    def cancel_appointment(appointment_id: int) -> dict:
        conn = get_db()
        try:
            apt = conn.execute(
                "SELECT status FROM appointments WHERE id = ?", (appointment_id,)
            ).fetchone()
            if not apt:
                return {"success": False, "error": "Appointment not found"}
            if apt["status"] in ("completed", "cancelled"):
                return {"success": False, "error": "Cannot cancel this appointment"}
            conn.execute(
                "UPDATE appointments SET status = 'cancelled', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (appointment_id,)
            )
            conn.commit()
            return {"success": True}
        finally:
            conn.close()

    @staticmethod
    def get_upcoming_for_patient(patient_id: int) -> list:
        from datetime import date
        today = date.today().isoformat()
        conn = get_db()
        try:
            appointments = conn.execute("""
                SELECT a.*, d.specialization, d.consultation_fee,
                       u.first_name as doctor_first_name, u.last_name as doctor_last_name,
                       l.name as location_name
                FROM appointments a
                JOIN doctors d ON a.doctor_id = d.id
                JOIN users u ON d.user_id = u.id
                JOIN locations l ON a.location_id = l.id
                WHERE a.patient_id = ? AND a.appointment_date >= ? AND a.status IN ('booked', 'confirmed')
                ORDER BY a.appointment_date, a.appointment_time
            """, (patient_id, today)).fetchall()
            return [dict(a) for a in appointments]
        finally:
            conn.close()

    @staticmethod
    def get_upcoming_for_doctor(doctor_id: int) -> list:
        from datetime import date
        today = date.today().isoformat()
        conn = get_db()
        try:
            appointments = conn.execute("""
                SELECT a.*, p.id as patient_db_id,
                       u.first_name as patient_first_name, u.last_name as patient_last_name,
                       l.name as location_name
                FROM appointments a
                JOIN patients p ON a.patient_id = p.id
                JOIN users u ON p.user_id = u.id
                JOIN locations l ON a.location_id = l.id
                WHERE a.doctor_id = ? AND a.appointment_date >= ? AND a.status IN ('booked', 'confirmed')
                ORDER BY a.appointment_date, a.appointment_time
            """, (doctor_id, today)).fetchall()
            return [dict(a) for a in appointments]
        finally:
            conn.close()
