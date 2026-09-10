import re


def validate_email(email: str) -> bool:
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_password(password: str) -> tuple[bool, str]:
    if len(password) < 8:
        return False, "Password must be at least 8 characters long. Please recreate password with at least 8 characters including uppercase, lowercase, number and special character."
    missing = []
    if not re.search(r'[A-Z]', password):
        missing.append("uppercase letter (A-Z)")
    if not re.search(r'[a-z]', password):
        missing.append("lowercase letter (a-z)")
    if not re.search(r'[0-9]', password):
        missing.append("number (0-9)")
    if not re.search(r'[^A-Za-z0-9]', password):
        missing.append("special character (e.g. !@#$%^&*)")
    if missing:
        return False, f"Password missing: {', '.join(missing)}. Please recreate password with all required parameters: uppercase, lowercase, number and special character."
    return True, "Valid"


def validate_name(name: str) -> bool:
    return len(name.strip()) >= 2


def validate_phone(phone: str) -> bool:
    pattern = r'^[\+]?[\d\s\-\(\)]{7,15}$'
    return bool(re.match(pattern, phone)) if phone else True


def validate_phone_10(phone: str) -> bool:
    return bool(re.fullmatch(r'\d{10}', phone))


def validate_age(age) -> bool:
    return isinstance(age, int) and 1 <= age <= 99


def validate_rating(rating: int) -> bool:
    return 1 <= rating <= 5
