import json
from unittest.mock import MagicMock, patch

import pytest

from claude_client import extract_clinical_data, get_client

# ── Mock responses ──────────────────────────────────────────────────────────────

MOCK_VITALS = {
    "vitals": {
        "blood_pressure": {"value": "138/88 mmHg", "source_text": "Blood pressure was recorded at 138/88 mmHg", "confidence": "high"},
        "heart_rate": {"value": "82 bpm", "source_text": "Heart rate measured at 82 beats per minute", "confidence": "high"},
        "temperature": {"value": "98.9°F", "source_text": "Temperature: 98.9 degrees F, taken orally", "confidence": "high"},
        "weight": {"value": "172 lbs", "source_text": "Patient weight: 172 lbs (78 kg)", "confidence": "high"},
    },
    "diagnoses": [],
    "medications": [],
}

MOCK_DIAGNOSES = {
    "vitals": {"blood_pressure": None, "heart_rate": None, "temperature": None, "weight": None},
    "diagnoses": [
        {"value": "Type 2 Diabetes Mellitus", "icd_code": "E11.65", "source_text": "Primary Diagnosis: Type 2 Diabetes Mellitus, uncontrolled (ICD-10: E11.65)", "confidence": "high"},
        {"value": "Essential Hypertension", "icd_code": "I10", "source_text": "Secondary Diagnosis: Essential Hypertension (ICD-10: I10)", "confidence": "high"},
    ],
    "medications": [],
}

MOCK_MEDICATIONS = {
    "vitals": {"blood_pressure": None, "heart_rate": None, "temperature": None, "weight": None},
    "diagnoses": [],
    "medications": [
        {"value": "Metformin 500mg twice daily", "source_text": "Metformin 500mg twice daily - prescribed for glucose management", "confidence": "high"},
        {"value": "Lisinopril 10mg once daily", "source_text": "Lisinopril 10mg once daily - prescribed for blood pressure control", "confidence": "high"},
        {"value": "Atorvastatin 20mg once daily", "source_text": "Atorvastatin 20mg once daily at bedtime - prescribed for cholesterol management", "confidence": "high"},
    ],
}


def _mock_response(data: dict) -> MagicMock:
    msg = MagicMock()
    msg.content = [MagicMock(text=json.dumps(data))]
    return msg


# ── Tests ───────────────────────────────────────────────────────────────────────

@patch("claude_client.get_client")
def test_extraction_returns_all_required_fields(mock_get_client):
    mock_get_client.return_value.messages.create.return_value = _mock_response(MOCK_VITALS)
    result = extract_clinical_data("some document text")
    assert "vitals" in result
    assert "diagnoses" in result
    assert "medications" in result


@patch("claude_client.get_client")
def test_every_field_has_source_text(mock_get_client):
    mock_get_client.return_value.messages.create.return_value = _mock_response(MOCK_VITALS)
    result = extract_clinical_data("some document text")

    for name, data in (result.get("vitals") or {}).items():
        if data is not None:
            assert data.get("source_text"), f"Vital '{name}' missing source_text"

    for dx in result.get("diagnoses") or []:
        assert dx.get("source_text"), f"Diagnosis '{dx.get('value')}' missing source_text"

    for med in result.get("medications") or []:
        assert med.get("source_text"), f"Medication '{med.get('value')}' missing source_text"


@patch("claude_client.get_client")
def test_confidence_values_are_valid_enum(mock_get_client):
    mock_get_client.return_value.messages.create.return_value = _mock_response(MOCK_VITALS)
    result = extract_clinical_data("some document text")
    valid = {"high", "medium", "low"}

    for data in (result.get("vitals") or {}).values():
        if data is not None:
            assert data.get("confidence") in valid

    for dx in result.get("diagnoses") or []:
        assert dx.get("confidence") in valid

    for med in result.get("medications") or []:
        assert med.get("confidence") in valid


@patch("claude_client.get_client")
def test_extraction_on_vitals_fixture(mock_get_client):
    mock_get_client.return_value.messages.create.return_value = _mock_response(MOCK_VITALS)
    result = extract_clinical_data("vitals note")
    vitals = result.get("vitals") or {}
    assert vitals.get("blood_pressure") is not None
    assert vitals.get("heart_rate") is not None
    assert vitals.get("temperature") is not None


@patch("claude_client.get_client")
def test_extraction_on_diagnosis_fixture(mock_get_client):
    mock_get_client.return_value.messages.create.return_value = _mock_response(MOCK_DIAGNOSES)
    result = extract_clinical_data("diagnosis note")
    diagnoses = result.get("diagnoses") or []
    assert len(diagnoses) > 0
    assert all(dx.get("value") for dx in diagnoses)


@patch("claude_client.get_client")
def test_extraction_on_medication_fixture(mock_get_client):
    mock_get_client.return_value.messages.create.return_value = _mock_response(MOCK_MEDICATIONS)
    result = extract_clinical_data("medications note")
    medications = result.get("medications") or []
    assert len(medications) > 0
    assert all(med.get("value") for med in medications)


@patch("claude_client.get_client")
def test_missing_fields_return_null_not_hallucinated(mock_get_client):
    """Medications-only note: diagnoses must be empty, vitals must all be null."""
    mock_get_client.return_value.messages.create.return_value = _mock_response(MOCK_MEDICATIONS)
    result = extract_clinical_data("medications only note")

    diagnoses = result.get("diagnoses")
    assert diagnoses == [] or diagnoses is None, "Diagnoses should be empty, not hallucinated"

    for name, data in (result.get("vitals") or {}).items():
        assert data is None, f"Vital '{name}' should be null in a medications-only note"


def test_get_client_raises_without_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(EnvironmentError, match="ANTHROPIC_API_KEY"):
        get_client()
