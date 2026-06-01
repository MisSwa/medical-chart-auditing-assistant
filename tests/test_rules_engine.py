import pytest

from rules_engine import COVERAGE_RULES, evaluate_rules


def _make_extraction(diagnoses=None, bp=None, medications=None):
    return {
        "vitals": {
            "blood_pressure": (
                {"value": bp, "source_text": bp, "confidence": "high"} if bp else None
            ),
            "heart_rate": None,
            "temperature": None,
            "weight": None,
        },
        "diagnoses": diagnoses or [],
        "medications": medications or [],
    }


def test_diagnosis_rule_passes_when_code_present():
    extraction = _make_extraction(
        diagnoses=[
            {
                "value": "Type 2 Diabetes Mellitus",
                "icd_code": "E11.65",
                "source_text": "...",
                "confidence": "high",
            }
        ]
    )
    rule = {
        "rule_id": "R001",
        "description": "Requires E11.x diagnosis",
        "type": "required_diagnosis",
        "required_icd_prefix": "E11",
    }
    results = evaluate_rules(extraction, [rule])
    assert results[0]["passed"] is True


def test_diagnosis_rule_fails_when_code_absent():
    extraction = _make_extraction(
        diagnoses=[
            {"value": "Essential Hypertension", "icd_code": "I10", "source_text": "...", "confidence": "high"}
        ]
    )
    rule = {
        "rule_id": "R001",
        "description": "Requires E11.x diagnosis",
        "type": "required_diagnosis",
        "required_icd_prefix": "E11",
    }
    results = evaluate_rules(extraction, [rule])
    assert results[0]["passed"] is False
    assert len(results[0]["reason"]) > 0


def test_vital_threshold_rule_passes_within_range():
    extraction = _make_extraction(bp="130/85 mmHg")
    rule = {
        "rule_id": "R002",
        "description": "Systolic BP must be below 160 mmHg",
        "type": "vital_threshold",
        "vital_field": "blood_pressure",
        "threshold_type": "systolic_max",
        "threshold_value": 160,
    }
    results = evaluate_rules(extraction, [rule])
    assert results[0]["passed"] is True


def test_vital_threshold_rule_fails_outside_range():
    extraction = _make_extraction(bp="170/95 mmHg")
    rule = {
        "rule_id": "R002",
        "description": "Systolic BP must be below 160 mmHg",
        "type": "vital_threshold",
        "vital_field": "blood_pressure",
        "threshold_type": "systolic_max",
        "threshold_value": 160,
    }
    results = evaluate_rules(extraction, [rule])
    assert results[0]["passed"] is False
    assert len(results[0]["reason"]) > 0


def test_rule_evaluation_on_missing_data_does_not_crash():
    extraction = {
        "vitals": {
            "blood_pressure": None,
            "heart_rate": None,
            "temperature": None,
            "weight": None,
        },
        "diagnoses": [],
        "medications": [],
    }
    results = evaluate_rules(extraction, COVERAGE_RULES)
    assert isinstance(results, list)
    assert len(results) == len(COVERAGE_RULES)
    # Each result must have all required keys
    for result in results:
        assert "rule_id" in result
        assert "description" in result
        assert "passed" in result
        assert "reason" in result
