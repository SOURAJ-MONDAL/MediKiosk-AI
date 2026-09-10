from dataclasses import dataclass
from typing import Optional


@dataclass
class Prescription:
    id: Optional[int] = None
    appointment_id: int = 0
    doctor_id: int = 0
    patient_id: int = 0
    medicine_name: str = ""
    dosage: str = ""
    frequency: str = ""
    duration: str = ""
    instructions: str = ""
    doctor_notes: str = ""
    is_ai_suggested: int = 0
    is_approved: int = 0
    created_at: str = ""
