from dataclasses import dataclass
from typing import Optional


@dataclass
class Notification:
    id: Optional[int] = None
    user_id: int = 0
    title: str = ""
    message: str = ""
    type: str = "info"
    is_read: int = 0
    related_id: Optional[int] = None
    related_type: Optional[str] = None
    created_at: str = ""
