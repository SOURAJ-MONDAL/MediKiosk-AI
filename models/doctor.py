from dataclasses import dataclass
from typing import Optional


@dataclass
class Doctor:
    id: Optional[int] = None
    user_id: int = 0
    specialization: str = ""
    qualification: str = ""
    experience_years: int = 0
    bio: str = ""
    consultation_fee: float = 0.0
    rating: float = 0.0
    total_ratings: int = 0
    languages: str = "English"
    profile_image: str = ""
    is_verified: int = 0
