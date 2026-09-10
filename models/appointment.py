from dataclasses import dataclass
from typing import Optional


@dataclass
class Appointment:
    id: Optional[int] = None
    patient_id: int = 0
    doctor_id: int = 0
    location_id: int = 0
    appointment_date: str = ""
    appointment_time: str = ""
    status: str = "booked"
    reason: str = ""
    notes: str = ""
    created_at: str = ""
    updated_at: str = ""
