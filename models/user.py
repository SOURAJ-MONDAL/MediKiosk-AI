from dataclasses import dataclass
from typing import Optional


@dataclass
class User:
    id: Optional[int] = None
    email: str = ""
    password_hash: str = ""
    role: str = "patient"
    first_name: str = ""
    last_name: str = ""
    phone: str = ""
    created_at: str = ""
    updated_at: str = ""
    is_active: int = 1

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
