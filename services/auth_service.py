import os
import hashlib
import secrets
from typing import Optional
from database.db import get_db
from utils.security import hash_password, verify_password
from utils.validators import validate_email, validate_password
from utils.helpers import generate_avatar_url


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class AuthService:
    @staticmethod
    def register(email: str, password: str, first_name: str, last_name: str,
                 role: str = "patient", phone: str = "",
                 doctor_info: Optional[dict] = None) -> dict:
        if not validate_email(email):
            return {"success": False, "error": "Invalid email address"}
        is_valid, msg = validate_password(password)
        if not is_valid:
            return {"success": False, "error": msg}
        if not first_name.strip() or not last_name.strip():
            return {"success": False, "error": "First and last name are required"}

        avatar_url = generate_avatar_url(f"{first_name.strip()} {last_name.strip()}")
        profile_image_data = None
        age = None
        specialization = "General Physician"
        qualification = ""
        experience_years = 0
        languages = "English"
        bio = ""
        consultation_fee = 0.0
        hospitals = []
        chambers = []
        schedule = []
        license_file = license_filename = None
        pass_certificate = pass_cert_filename = None
        if doctor_info:
            avatar_url = doctor_info.get("avatar_url") or avatar_url
            profile_image_data = doctor_info.get("profile_image_data")
            if role == "doctor":
                age = doctor_info.get("age")
                specialization = doctor_info.get("specialization") or "General Physician"
                qualification = doctor_info.get("qualification") or ""
                experience_years = int(doctor_info.get("experience_years") or 0)
                languages = doctor_info.get("languages") or "English"
                bio = doctor_info.get("bio") or ""
                consultation_fee = float(doctor_info.get("consultation_fee") or 0.0)
                hospitals = doctor_info.get("hospitals") or []
                chambers = doctor_info.get("chambers") or []
                schedule = doctor_info.get("schedule") or []
                license_file = doctor_info.get("license_file")
                license_filename = doctor_info.get("license_filename")
                pass_certificate = doctor_info.get("pass_certificate")
                pass_cert_filename = doctor_info.get("pass_certificate_filename")

        conn = get_db()
        try:
            existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
            if existing:
                return {"success": False, "error": "Email already registered"}
            pwd_hash = hash_password(password)
            cursor = conn.execute(
                """INSERT INTO users (email, password_hash, role, first_name, last_name, phone,
                                     profile_image, profile_image_data)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (email, pwd_hash, role, first_name.strip(), last_name.strip(), phone,
                 avatar_url, profile_image_data)
            )
            user_id = cursor.lastrowid
            if role == "patient":
                conn.execute("INSERT INTO patients (user_id) VALUES (?)", (user_id,))
            elif role == "doctor":
                cursor = conn.execute(
                    """INSERT INTO doctors (user_id, specialization, age, qualification,
                                            license_file, license_filename,
                                            pass_certificate, pass_certificate_filename,
                                            experience_years, languages, bio, consultation_fee)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (user_id, specialization, age, qualification,
                     license_file, license_filename,
                     pass_certificate, pass_cert_filename,
                     experience_years, languages, bio, consultation_fee)
                )
                doctor_id = cursor.lastrowid
                for hospital in hospitals:
                    if hospital and hospital.strip():
                        conn.execute(
                            "INSERT INTO doctor_hospitals (doctor_id, hospital_name) VALUES (?, ?)",
                            (doctor_id, hospital.strip())
                        )
                for chamber in chambers:
                    if chamber and chamber.strip():
                        conn.execute(
                            "INSERT INTO doctor_chambers (doctor_id, address) VALUES (?, ?)",
                            (doctor_id, chamber.strip())
                        )
                for entry in schedule:
                    if not entry or not entry.get("day"):
                        continue
                    sitting_type = "hospital" if entry.get("sitting") == "Hospital" else "chamber"
                    conn.execute(
                        """INSERT INTO doctor_schedules (doctor_id, day, start_time, end_time,
                                                         sitting_type, hospital_name, chamber_address)
                           VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (doctor_id, entry["day"],
                         entry.get("start", ""), entry.get("end", ""),
                         sitting_type, entry.get("hospital_name"), entry.get("chamber_address"))
                    )
            conn.commit()
            return {"success": True, "user_id": user_id, "role": role}
        except Exception as e:
            conn.rollback()
            return {"success": False, "error": str(e)}
        finally:
            conn.close()

    @staticmethod
    def login(email: str, password: str) -> dict:
        if not email or not password:
            return {"success": False, "error": "Email and password are required"}
        conn = get_db()
        try:
            user = conn.execute(
                "SELECT * FROM users WHERE email = ? AND is_active = 1", (email,)
            ).fetchone()
            if not user:
                return {"success": False, "error": "Invalid email or password"}
            if not verify_password(password, user["password_hash"]):
                return {"success": False, "error": "Invalid email or password"}
            return {
                "success": True,
                "user_id": user["id"],
                "role": user["role"],
                "first_name": user["first_name"],
                "last_name": user["last_name"],
                "email": user["email"],
            }
        finally:
            conn.close()

    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[dict]:
        conn = get_db()
        try:
            user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
            return dict(user) if user else None
        finally:
            conn.close()

    @staticmethod
    def update_profile(user_id: int, **kwargs) -> bool:
        allowed_fields = {"first_name", "last_name", "phone"}
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields and v is not None}
        if not updates:
            return False
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [user_id]
        conn = get_db()
        try:
            conn.execute(f"UPDATE users SET {set_clause} WHERE id = ?", values)
            conn.commit()
            return True
        finally:
            conn.close()

    @staticmethod
    def update_profile_image(user_id: int, image_data: bytes) -> bool:
        conn = get_db()
        try:
            conn.execute(
                "UPDATE users SET profile_image_data = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (image_data, user_id)
            )
            conn.commit()
            return True
        finally:
            conn.close()

    @staticmethod
    def delete_user(user_id: int) -> bool:
        conn = get_db()
        try:
            cursor = conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    @staticmethod
    def change_password(user_id: int, current_password: str, new_password: str) -> dict:
        conn = get_db()
        try:
            user = conn.execute("SELECT password_hash FROM users WHERE id = ?", (user_id,)).fetchone()
            if not user:
                return {"success": False, "error": "User not found"}
            if not verify_password(current_password, user["password_hash"]):
                return {"success": False, "error": "Current password is incorrect"}
            is_valid, msg = validate_password(new_password)
            if not is_valid:
                return {"success": False, "error": msg}
            conn.execute("UPDATE users SET password_hash = ? WHERE id = ?",
                         (hash_password(new_password), user_id))
            conn.commit()
            return {"success": True}
        finally:
            conn.close()

    @staticmethod
    def create_persistent_token(user_id: int) -> str:
        token = secrets.token_urlsafe(32)
        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO auth_tokens (user_id, token_hash) VALUES (?, ?)",
                (user_id, _hash_token(token))
            )
            conn.commit()
            return token
        finally:
            conn.close()

    @staticmethod
    def get_user_by_token(token: str) -> Optional[dict]:
        if not token or len(token) > 128:
            return None
        conn = get_db()
        try:
            row = conn.execute(
                """SELECT u.id, u.first_name, u.last_name, u.email, u.role, u.phone
                   FROM auth_tokens t
                   JOIN users u ON t.user_id = u.id
                   WHERE t.token_hash = ? AND u.is_active = 1""",
                (_hash_token(token),)
            ).fetchone()
            if not row:
                return None
            conn.execute(
                "UPDATE auth_tokens SET last_used_at = CURRENT_TIMESTAMP WHERE token_hash = ?",
                (_hash_token(token),)
            )
            conn.commit()
            return {
                "id": row["id"],
                "email": row["email"],
                "role": row["role"],
                "first_name": row["first_name"],
                "last_name": row["last_name"],
                "full_name": f"{row['first_name']} {row['last_name']}",
                "phone": row["phone"],
            }
        finally:
            conn.close()

    @staticmethod
    def revoke_token(token: str) -> bool:
        if not token or len(token) > 128:
            return False
        conn = get_db()
        try:
            cursor = conn.execute("DELETE FROM auth_tokens WHERE token_hash = ?", (_hash_token(token),))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    @staticmethod
    def revoke_user_tokens(user_id: int) -> None:
        conn = get_db()
        try:
            conn.execute("DELETE FROM auth_tokens WHERE user_id = ?", (user_id,))
            conn.commit()
        finally:
            conn.close()
