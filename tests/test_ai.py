import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.ai_service import AIService


def make_ai():
    ai = AIService.__new__(AIService)
    ai._model = None
    ai._available = False
    return ai


def test_emergency_detection():
    ai = make_ai()
    assert ai.detect_emergency("I have severe chest pain")
    assert ai.detect_emergency("hard time breathing")
    assert ai.detect_emergency("I feel suicidal")
    assert ai.detect_emergency("severe bleeding from my arm")
    assert not ai.detect_emergency("I have a mild headache")
    assert not ai.detect_emergency("my stomach hurts after eating")


def test_specialty_suggestion():
    ai = make_ai()
    specialties = ai.suggest_specialties("I have a headache")
    assert "Neurologist" in specialties
    specialties = ai.suggest_specialties("my skin has a rash")
    assert "Dermatologist" in specialties
    specialties = ai.suggest_specialties("stomach pain")
    assert "Gastroenterologist" in specialties
    specialties = ai.suggest_specialties("random health concern")
    assert "General Physician" in specialties


def test_fallback_response():
    ai = make_ai()
    # OFFLINE: needs only 2 questions (symptom + severity) before summary
    result = ai.chat([{"role": "user", "content": "I have a headache"}])
    assert "response" in result
    assert "structured_summary" in result
    assert result["structured_summary"]["suggested_specialties"] == []
    assert result["structured_summary"]["suggested_medicines"] == []
    assert result["conversation_complete"] is False
    # After 2 questions, offline allows summary and specialties (no medicines offline)
    history = [
        {"role": "user", "content": "headache for 2 days"},
        {"role": "assistant", "content": "When did it start?"},
        {"role": "user", "content": "2 days, moderate"},
    ]
    result2 = ai.chat(history)
    assert result2["conversation_complete"] is True
    assert result2["structured_summary"]["suggested_specialties"]
    assert result2["structured_summary"]["suggested_medicines"] == []


def test_fallback_emergency():
    ai = make_ai()
    result = ai.chat([{"role": "user", "content": "severe chest pain, can't breathe"}])
    assert result["is_emergency"] is True
    assert "emergency" in result["structured_summary"]["urgency"].lower()


def test_parse_valid_json():
    ai = make_ai()
    text = '{"response": "Hello", "follow_up_questions": ["Q?"], "structured_summary": {"symptoms": ["x"], "urgency": "low"}, "is_emergency": false, "conversation_complete": false}'
    result = ai._parse_response(text, [{"role": "user", "content": "test"}])
    assert result["response"] == "Hello"
    assert result["is_emergency"] is False


def test_parse_malformed_json():
    ai = make_ai()
    text = "This is not a JSON response at all, just random words"
    result = ai._parse_response(text, [{"role": "user", "content": "I have a headache"}])
    assert "response" in result
    assert "structured_summary" in result
    assert result["structured_summary"]["suggested_specialties"]