from datetime import datetime, date
import base64
from urllib.parse import quote


def get_profile_image_src(row: dict) -> str:
    data = row.get("profile_image_data")
    if data:
        return f"data:image/jpeg;base64,{base64.b64encode(data).decode('ascii')}"
    return row.get("profile_image") or row.get("user_image") or ""


def generate_avatar_url(seed: str) -> str:
    return (f"https://api.dicebear.com/7.x/avataaars/svg"
            f"?seed={quote(seed)}&backgroundColor=b6e3f4,c0aede,d1d4f9,ffd5dc")


def format_date(date_str: str) -> str:
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d")
        return d.strftime("%B %d, %Y")
    except (ValueError, TypeError):
        return date_str


def format_time(time_str: str) -> str:
    try:
        t = datetime.strptime(time_str, "%H:%M")
        return t.strftime("%I:%M %p")
    except (ValueError, TypeError):
        return time_str


def get_day_name(day_number: int) -> str:
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    return days[day_number] if 0 <= day_number <= 6 else ""


def get_greeting() -> str:
    hour = datetime.now().hour
    if hour < 12:
        return "Good morning"
    elif hour < 17:
        return "Good afternoon"
    return "Good evening"


def generate_slot_times(start_time: str, end_time: str, duration_minutes: int = 30) -> list:
    slots = []
    start = datetime.strptime(start_time, "%H:%M")
    end = datetime.strptime(end_time, "%H:%M")
    current = start
    while current + __import__('datetime').timedelta(minutes=duration_minutes) <= end:
        slots.append(current.strftime("%H:%M"))
        current += __import__('datetime').timedelta(minutes=duration_minutes)
    return slots


def calculate_age(date_of_birth: str) -> int:
    try:
        birth = datetime.strptime(date_of_birth, "%Y-%m-%d").date()
        today = date.today()
        return today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
    except (ValueError, TypeError):
        return 0
