import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.validators import validate_email, validate_password, validate_name, validate_rating, validate_phone


def test_valid_emails():
    assert validate_email("user@example.com")
    assert validate_email("first.last@domain.co")
    assert validate_email("user+tag@domain.org")


def test_invalid_emails():
    assert not validate_email("not-an-email")
    assert not validate_email("user@")
    assert not validate_email("@domain.com")
    assert not validate_email("user@domain")
    assert not validate_email("user domain.com")


def test_password_validation():
    valid, _ = validate_password("StrongPass1!")
    assert valid
    valid, msg = validate_password("StrongPass1")
    assert not valid
    assert "special character" in msg.lower()
    valid, msg = validate_password("Sh1!")
    assert not valid
    assert "at least 8" in msg.lower()
    valid, msg = validate_password("lowercaseonly1!")
    assert not valid
    assert "uppercase" in msg.lower()
    valid, msg = validate_password("UPPERCASEONLY1!")
    assert not valid
    assert "lowercase" in msg.lower()
    valid, msg = validate_password("NoNumberHere!")
    assert not valid
    assert "number" in msg.lower()
    valid, msg = validate_password("NoSpecial123")
    assert not valid
    assert "special character" in msg.lower()
    # Valid with all parameters for patient and doctor
    valid, _ = validate_password("Patient123!")
    assert valid
    valid, _ = validate_password("Doctor123@")
    assert valid


def test_name_validation():
    assert validate_name("John")
    assert not validate_name("J")
    assert not validate_name("")


def test_rating_validation():
    assert validate_rating(1)
    assert validate_rating(5)
    assert not validate_rating(0)
    assert not validate_rating(6)


def test_phone_validation():
    assert validate_phone("+1 555-0101")
    assert validate_phone("5550101")
    assert validate_phone("")
    assert validate_phone("+8801712345678")