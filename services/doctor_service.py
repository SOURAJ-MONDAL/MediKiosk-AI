from typing import Optional
from database.db import get_db


def _normalize_doctor(row) -> dict:
    data = dict(row)
    for key in ("first_name", "last_name", "email", "phone", "profile_image", "user_image",
                "specialization", "qualification", "languages", "bio"):
        if data.get(key) is None:
            data[key] = ""
    for key in ("experience_years", "age", "total_ratings"):
        if data.get(key) is None:
            data[key] = 0
    for key in ("rating", "consultation_fee"):
        if data.get(key) is None:
            data[key] = 0.0
    if data.get("is_verified") is None:
        data["is_verified"] = 0
    return data


class DoctorService:
    @staticmethod
    def get_all_doctors(specialization: str = None, city: str = None,
                        min_fee: float = None, max_fee: float = None) -> list:
        conn = get_db()
        try:
            query = """
                SELECT d.*, u.first_name, u.last_name, u.email, u.phone,
                       u.profile_image as user_image
                FROM doctors d
                JOIN users u ON d.user_id = u.id
                WHERE u.is_active = 1
            """
            params = []
            if specialization:
                query += " AND d.specialization = ?"
                params.append(specialization)
            if min_fee is not None:
                query += " AND d.consultation_fee >= ?"
                params.append(min_fee)
            if max_fee is not None:
                query += " AND d.consultation_fee <= ?"
                params.append(max_fee)
            query += " ORDER BY d.rating DESC, d.experience_years DESC"
            doctors = conn.execute(query, params).fetchall()
            return [_normalize_doctor(d) for d in doctors]
        finally:
            conn.close()

    @staticmethod
    def get_doctor_by_id(doctor_id: int) -> Optional[dict]:
        conn = get_db()
        try:
            doctor = conn.execute("""
                SELECT d.*, u.first_name, u.last_name, u.email, u.phone,
                       u.profile_image as user_image
                FROM doctors d
                JOIN users u ON d.user_id = u.id
                WHERE d.id = ?
            """, (doctor_id,)).fetchone()
            return _normalize_doctor(doctor) if doctor else None
        finally:
            conn.close()

    @staticmethod
    def get_doctor_by_user_id(user_id: int) -> Optional[dict]:
        conn = get_db()
        try:
            doctor = conn.execute("""
                SELECT d.*, u.first_name, u.last_name, u.email, u.phone,
                       u.profile_image as user_image
                FROM doctors d
                JOIN users u ON d.user_id = u.id
                WHERE d.user_id = ?
            """, (user_id,)).fetchone()
            return _normalize_doctor(doctor) if doctor else None
        finally:
            conn.close()

    @staticmethod
    def get_doctor_locations(doctor_id: int) -> list:
        conn = get_db()
        try:
            locations = conn.execute("""
                SELECT l.*, dl.consultation_fee as location_fee
                FROM locations l
                JOIN doctor_locations dl ON l.id = dl.location_id
                WHERE dl.doctor_id = ? AND dl.is_active = 1
            """, (doctor_id,)).fetchall()
            return [dict(l) for l in locations]
        finally:
            conn.close()

    @staticmethod
    def get_booking_locations(doctor_id: int) -> list:
        """Unified locations for booking — real locations plus fallback from
        doctor_hospitals / doctor_chambers / doctor_schedules hospital names.
        Creates fallback location rows lazily so booking FK is satisfied.
        Always syncs so a newly added Thursday schedule appears every future Thursday
        until the doctor changes it manually."""
        # Always sync fallback locations — don't early-return when locs exists,
        # otherwise a newly added Thursday hospital never appears in booking.
        locs_before = DoctorService.get_doctor_locations(doctor_id)
        # fallback: build from hospitals / chambers
        conn = get_db()
        try:
            hospitals = conn.execute(
                "SELECT hospital_name FROM doctor_hospitals WHERE doctor_id = ?", (doctor_id,)
            ).fetchall()
            chambers = conn.execute(
                "SELECT address FROM doctor_chambers WHERE doctor_id = ?", (doctor_id,)
            ).fetchall()
            # also collect distinct hospital_name / chamber_address from schedules
            sched_rows = conn.execute(
                "SELECT DISTINCT hospital_name, chamber_address, sitting_type FROM doctor_schedules WHERE doctor_id = ?",
                (doctor_id,)
            ).fetchall()
            # aggregate names to create locations
            to_create = []
            for r in hospitals:
                n = (r["hospital_name"] or "").strip()
                if n:
                    to_create.append((n, "hospital", n, ""))
            for r in chambers:
                a = (r["address"] or "").strip()
                if a:
                    # avoid duplicates
                    if not any(x[0] == a for x in to_create):
                        to_create.append((a, "chamber", a, ""))
            for r in sched_rows:
                if r["sitting_type"] == "hospital" and r["hospital_name"]:
                    n = r["hospital_name"].strip()
                    if n and not any(x[0] == n for x in to_create):
                        to_create.append((n, "hospital", n, ""))
                elif r["sitting_type"] == "chamber" and r["chamber_address"]:
                    a = r["chamber_address"].strip()
                    if a and not any(x[0] == a for x in to_create):
                        to_create.append((a, "chamber", a, ""))

            # if still nothing and no real locations yet, create a generic entry so booking can proceed
            if not to_create and not locs_before:
                to_create.append(("Main Clinic", "clinic", "Main Clinic", ""))

            if not to_create:
                # already has locations and nothing new to sync
                conn.commit()
                return locs_before

            # fetch doctor fee for linking
            doctor = conn.execute("SELECT consultation_fee FROM doctors WHERE id = ?", (doctor_id,)).fetchone()
            fee = doctor["consultation_fee"] if doctor else 0

            for name, ltype, address, city in to_create:
                # check if location already exists with same name+address
                existing = conn.execute(
                    "SELECT id FROM locations WHERE name = ? AND address = ?", (name, address)
                ).fetchone()
                if existing:
                    loc_id = existing["id"]
                else:
                    cur = conn.execute(
                        "INSERT INTO locations (name, type, address, city) VALUES (?, ?, ?, ?)",
                        (name, ltype, address, city)
                    )
                    loc_id = cur.lastrowid
                # link if not already linked
                linked = conn.execute(
                    "SELECT 1 FROM doctor_locations WHERE doctor_id = ? AND location_id = ?",
                    (doctor_id, loc_id)
                ).fetchone()
                if not linked:
                    conn.execute(
                        "INSERT INTO doctor_locations (doctor_id, location_id, consultation_fee) VALUES (?, ?, ?)",
                        (doctor_id, loc_id, fee)
                    )
            conn.commit()
        finally:
            conn.close()
        # re-fetch
        return DoctorService.get_doctor_locations(doctor_id)

    @staticmethod
    def get_doctor_schedule(doctor_id: int, location_id: int = None) -> list:
        conn = get_db()
        try:
            query = """
                SELECT s.*, l.name as location_name, l.city as location_city
                FROM schedules s
                JOIN locations l ON s.location_id = l.id
                WHERE s.doctor_id = ? AND s.is_active = 1
            """
            params = [doctor_id]
            if location_id:
                query += " AND s.location_id = ?"
                params.append(location_id)
            query += " ORDER BY s.day_of_week, s.start_time"
            schedules = conn.execute(query, params).fetchall()
            return [dict(s) for s in schedules]
        finally:
            conn.close()

    @staticmethod
    def update_doctor_profile(doctor_id: int, **kwargs) -> bool:
        allowed = {"specialization", "qualification", "experience_years",
                   "bio", "consultation_fee", "languages", "age"}
        updates = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
        if not updates:
            return False
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [doctor_id]
        conn = get_db()
        try:
            conn.execute(f"UPDATE doctors SET {set_clause} WHERE id = ?", values)
            conn.commit()
            return True
        finally:
            conn.close()

    @staticmethod
    def get_doctor_hospitals(doctor_id: int) -> list:
        conn = get_db()
        try:
            rows = conn.execute(
                "SELECT id, hospital_name FROM doctor_hospitals WHERE doctor_id = ? ORDER BY id",
                (doctor_id,)
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    @staticmethod
    def get_doctor_chambers(doctor_id: int) -> list:
        conn = get_db()
        try:
            rows = conn.execute(
                "SELECT id, address FROM doctor_chambers WHERE doctor_id = ? ORDER BY id",
                (doctor_id,)
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    @staticmethod
    def get_doctor_schedule_entries(doctor_id: int) -> list:
        conn = get_db()
        try:
            rows = conn.execute(
                """SELECT id, day, start_time, end_time, sitting_type, hospital_name, chamber_address
                   FROM doctor_schedules WHERE doctor_id = ? ORDER BY id""",
                (doctor_id,)
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    @staticmethod
    def add_doctor_schedule_entry(doctor_id: int, day: str, start_time: str,
                                   end_time: str, sitting_type: str,
                                   hospital_name: str = None,
                                   chamber_address: str = None) -> Optional[int]:
        valid_days = {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"}
        if day not in valid_days:
            return None
        if not start_time or not end_time or start_time >= end_time:
            return None
        stype = sitting_type.lower()
        if stype not in ("hospital", "chamber"):
            return None
        if stype == "hospital" and not (hospital_name and hospital_name.strip()):
            return None
        if stype == "chamber" and not (chamber_address and chamber_address.strip()):
            return None
        conn = get_db()
        try:
            cur = conn.execute(
                """INSERT INTO doctor_schedules
                   (doctor_id, day, start_time, end_time, sitting_type, hospital_name, chamber_address)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (doctor_id, day, start_time, end_time, stype,
                 hospital_name.strip() if hospital_name else None,
                 chamber_address.strip() if chamber_address else None)
            )
            conn.commit()
            return cur.lastrowid
        finally:
            conn.close()

    @staticmethod
    def delete_doctor_schedule_entry(entry_id: int, doctor_id: int) -> bool:
        conn = get_db()
        try:
            cur = conn.execute(
                "DELETE FROM doctor_schedules WHERE id = ? AND doctor_id = ?",
                (entry_id, doctor_id)
            )
            conn.commit()
            return cur.rowcount > 0
        finally:
            conn.close()

    @staticmethod
    def add_location(name: str, location_type: str, address: str, city: str,
                     phone: str = "", email: str = "") -> Optional[int]:
        conn = get_db()
        try:
            cursor = conn.execute(
                "INSERT INTO locations (name, type, address, city, phone, email) VALUES (?, ?, ?, ?, ?, ?)",
                (name, location_type, address, city, phone, email)
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    @staticmethod
    def add_schedule(doctor_id: int, location_id: int, day_of_week: int,
                     start_time: str, end_time: str, slot_duration: int = 30) -> Optional[int]:
        conn = get_db()
        try:
            cursor = conn.execute(
                """INSERT INTO schedules (doctor_id, location_id, day_of_week, start_time, end_time, slot_duration)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (doctor_id, location_id, day_of_week, start_time, end_time, slot_duration)
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    @staticmethod
    def get_available_slots(doctor_id: int, location_id: int, date_str: str) -> list:
        from datetime import datetime
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            day_of_week = dt.weekday()
        except ValueError:
            return []

        DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        day_name = DAY_NAMES[day_of_week]

        conn = get_db()
        try:
            schedules = conn.execute(
                """SELECT s.* FROM schedules s
                   WHERE s.doctor_id = ? AND s.location_id = ? AND s.day_of_week = ? AND s.is_active = 1""",
                (doctor_id, location_id, day_of_week)
            ).fetchall()

            # Fallback to doctor_schedules (hospital/chamber weekly hours) when no formal schedules exist.
            # This lets newly registered doctors with only hospital_name/chamber entries be bookable.
            if not schedules:
                # try to match location name to schedule's hospital/chamber
                loc = conn.execute("SELECT name, address FROM locations WHERE id = ?", (location_id,)).fetchone()
                loc_name = (loc["name"] if loc else "") or ""
                loc_addr = (loc["address"] if loc else "") or ""
                # fetch schedules for that day — prefer those matching location
                all_day = conn.execute(
                    "SELECT day, start_time, end_time FROM doctor_schedules WHERE doctor_id = ? AND day = ?",
                    (doctor_id, day_name)
                ).fetchall()
                # filter by location match if possible
                filtered = []
                for r in all_day:
                    # if location name appears in schedule's hospital/chamber, keep it; otherwise keep all if no strong match
                    # check original schedule rows with location strings
                    sched_match = conn.execute(
                        """SELECT 1 FROM doctor_schedules
                           WHERE doctor_id = ? AND day = ? AND start_time = ? AND end_time = ?
                             AND (hospital_name = ? OR chamber_address = ? OR hospital_name = ? OR chamber_address = ?)""",
                        (doctor_id, r["day"], r["start_time"], r["end_time"], loc_name, loc_addr, loc_addr, loc_name)
                    ).fetchone()
                    if sched_match:
                        filtered.append(r)
                # if filtered empty but all_day has entries, use all_day (location-agnostic)
                use_rows = filtered if filtered else all_day
                if not use_rows:
                    return []
                # synthesize schedule-like rows with 30 min slots
                all_slots = []
                for sched in use_rows:
                    start = datetime.strptime(sched["start_time"], "%H:%M")
                    end = datetime.strptime(sched["end_time"], "%H:%M")
                    duration = 30
                    current = start
                    from datetime import timedelta
                    while current + timedelta(minutes=duration) <= end:
                        all_slots.append(current.strftime("%H:%M"))
                        current += timedelta(minutes=duration)
                # filter booked / blocked same as normal path
                booked = conn.execute(
                    """SELECT appointment_time FROM appointments
                       WHERE doctor_id = ? AND appointment_date = ? AND status IN ('booked', 'confirmed')""",
                    (doctor_id, date_str)
                ).fetchall()
                booked_times = {b["appointment_time"] for b in booked}
                blocked = conn.execute(
                    """SELECT bs.blocked_time FROM blocked_slots bs
                       JOIN schedules s ON bs.schedule_id = s.id
                       WHERE s.doctor_id = ? AND bs.blocked_date = ?""",
                    (doctor_id, date_str)
                ).fetchall()
                blocked_times = {b["blocked_time"] for b in blocked}
                return [s for s in all_slots if s not in booked_times and s not in blocked_times]

            all_slots = []
            for sched in schedules:
                start = datetime.strptime(sched["start_time"], "%H:%M")
                end = datetime.strptime(sched["end_time"], "%H:%M")
                duration = sched["slot_duration"]
                current = start
                from datetime import timedelta
                while current + timedelta(minutes=duration) <= end:
                    all_slots.append(current.strftime("%H:%M"))
                    current += timedelta(minutes=duration)

            booked = conn.execute(
                """SELECT appointment_time FROM appointments
                   WHERE doctor_id = ? AND appointment_date = ? AND status IN ('booked', 'confirmed')""",
                (doctor_id, date_str)
            ).fetchall()
            booked_times = {b["appointment_time"] for b in booked}

            blocked = conn.execute(
                """SELECT bs.blocked_time FROM blocked_slots bs
                   JOIN schedules s ON bs.schedule_id = s.id
                   WHERE s.doctor_id = ? AND bs.blocked_date = ?""",
                (doctor_id, date_str)
            ).fetchall()
            blocked_times = {b["blocked_time"] for b in blocked}

            available = [s for s in all_slots if s not in booked_times and s not in blocked_times]
            return available
        finally:
            conn.close()
