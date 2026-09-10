from database.db import get_db


class MatchingService:
    @staticmethod
    def find_matching_doctors(specialties: list = None, city: str = None,
                              max_fee: float = None) -> list:
        conn = get_db()
        try:
            query = """
                SELECT d.*, u.first_name, u.last_name, u.email, u.phone
                FROM doctors d
                JOIN users u ON d.user_id = u.id
                WHERE u.is_active = 1
            """
            params = []
            if specialties:
                placeholders = ",".join("?" * len(specialties))
                query += f" AND d.specialization IN ({placeholders})"
                params.extend(specialties)
            if max_fee is not None:
                query += " AND d.consultation_fee <= ?"
                params.append(max_fee)
            query += " ORDER BY d.rating DESC, d.experience_years DESC"
            results = conn.execute(query, params).fetchall()
            return [dict(r) for r in results]
        finally:
            conn.close()

    @staticmethod
    def get_top_rated_doctors(specialization: str = None, limit: int = 5) -> list:
        conn = get_db()
        try:
            query = """
                SELECT d.*, u.first_name, u.last_name
                FROM doctors d
                JOIN users u ON d.user_id = u.id
                WHERE u.is_active = 1 AND d.total_ratings > 0
            """
            params = []
            if specialization:
                query += " AND d.specialization = ?"
                params.append(specialization)
            query += " ORDER BY d.rating DESC LIMIT ?"
            params.append(limit)
            doctors = conn.execute(query, params).fetchall()
            return [dict(d) for d in doctors]
        finally:
            conn.close()

    @staticmethod
    def update_doctor_rating(doctor_id: int, new_rating: float):
        conn = get_db()
        try:
            doctor = conn.execute(
                "SELECT rating, total_ratings FROM doctors WHERE id = ?", (doctor_id,)
            ).fetchone()
            if not doctor:
                return
            total = doctor["total_ratings"]
            current_avg = doctor["rating"]
            new_total = total + 1
            new_avg = ((current_avg * total) + new_rating) / new_total
            conn.execute(
                "UPDATE doctors SET rating = ?, total_ratings = ? WHERE id = ?",
                (round(new_avg, 2), new_total, doctor_id)
            )
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def submit_rating(patient_id: int, doctor_id: int, rating: int,
                      review: str = "", appointment_id: int = None) -> dict:
        conn = get_db()
        try:
            existing = conn.execute(
                "SELECT id FROM ratings WHERE patient_id = ? AND doctor_id = ?",
                (patient_id, doctor_id)
            ).fetchone()
            if existing:
                return {"success": False, "error": "You have already rated this doctor"}
            conn.execute(
                """INSERT INTO ratings (patient_id, doctor_id, appointment_id, rating, review)
                   VALUES (?, ?, ?, ?, ?)""",
                (patient_id, doctor_id, appointment_id, rating, review)
            )
            conn.commit()
            MatchingService.update_doctor_rating(doctor_id, rating)
            return {"success": True}
        finally:
            conn.close()

    @staticmethod
    def get_doctor_reviews(doctor_id: int) -> list:
        conn = get_db()
        try:
            reviews = conn.execute("""
                SELECT r.*, u.first_name, u.last_name
                FROM ratings r
                JOIN patients p ON r.patient_id = p.id
                JOIN users u ON p.user_id = u.id
                WHERE r.doctor_id = ?
                ORDER BY r.created_at DESC
            """, (doctor_id,)).fetchall()
            return [dict(r) for r in reviews]
        finally:
            conn.close()
