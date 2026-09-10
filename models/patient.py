from dataclasses import dataclass
from typing import Optional


@dataclass
class Patient:
    id: Optional[int] = None
    user_id: int = 0
    date_of_birth: str = ""
    gender: str = ""
    blood_group: str = ""
    allergies: str = ""
    medical_history: str = ""
    emergency_contact: str = ""
    emergency_phone: str = ""
    address: str = ""
    city: str = ""
    profile_image: str = ""
