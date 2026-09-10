from typing import Optional
from database.db import get_db


class NotificationService:
    @staticmethod
    def create_notification(user_id: int, title: str, message: str,
                            notification_type: str = "info",
                            related_id: int = None, related_type: str = None) -> Optional[int]:
        conn = get_db()
        try:
            cursor = conn.execute(
                """INSERT INTO notifications (user_id, title, message, type, related_id, related_type)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (user_id, title, message, notification_type, related_id, related_type)
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    @staticmethod
    def get_user_notifications(user_id: int, unread_only: bool = False) -> list:
        conn = get_db()
        try:
            query = "SELECT * FROM notifications WHERE user_id = ?"
            params = [user_id]
            if unread_only:
                query += " AND is_read = 0"
            query += " ORDER BY created_at DESC LIMIT 50"
            notifications = conn.execute(query, params).fetchall()
            return [dict(n) for n in notifications]
        finally:
            conn.close()

    @staticmethod
    def get_unread_count(user_id: int) -> int:
        conn = get_db()
        try:
            result = conn.execute(
                "SELECT COUNT(*) as count FROM notifications WHERE user_id = ? AND is_read = 0",
                (user_id,)
            ).fetchone()
            return result["count"] if result else 0
        finally:
            conn.close()

    @staticmethod
    def mark_read(notification_id: int) -> bool:
        conn = get_db()
        try:
            conn.execute("UPDATE notifications SET is_read = 1 WHERE id = ?", (notification_id,))
            conn.commit()
            return True
        finally:
            conn.close()

    @staticmethod
    def mark_all_read(user_id: int) -> bool:
        conn = get_db()
        try:
            conn.execute("UPDATE notifications SET is_read = 1 WHERE user_id = ? AND is_read = 0", (user_id,))
            conn.commit()
            return True
        finally:
            conn.close()

    @staticmethod
    def notify_appointment_booked(patient_user_id: int, doctor_name: str,
                                  date_str: str, time_str: str, appointment_id: int):
        NotificationService.create_notification(
            patient_user_id,
            "Appointment booked",
            f"Your appointment with Dr. {doctor_name} has been booked for {date_str} at {time_str}.",
            "appointment",
            appointment_id,
            "appointment",
        )

    @staticmethod
    def notify_appointment_cancelled(patient_user_id: int, doctor_name: str, appointment_id: int):
        NotificationService.create_notification(
            patient_user_id,
            "Appointment cancelled",
            f"Your appointment with Dr. {doctor_name} has been cancelled.",
            "warning",
            appointment_id,
            "appointment",
        )

    @staticmethod
    def notify_prescription(doctor_name: str, patient_user_id: int, appointment_id: int):
        NotificationService.create_notification(
            patient_user_id,
            "Prescription available",
            f"Dr. {doctor_name} has added a prescription for your appointment.",
            "prescription",
            appointment_id,
            "prescription",
        )
