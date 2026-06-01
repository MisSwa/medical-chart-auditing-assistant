"""
Structured rules engine for coverage determination.

Rules are hardcoded constants in Phase 2. UI-based rule management is deferred.
The engine consumes only the Phase 1 extraction schema — it never reads document files directly.
"""
import re

COVERAGE_RULES = [
    {
        "rule_id": "R001",
        "description": "Treatment requires a confirmed Type 2 Diabetes diagnosis (ICD-10: E11.x)",
        "type": "required_diagnosis",
        "required_icd_prefix": "E11",
    },
    {
        "rule_id": "R002",
        "description": "Systolic blood pressure must be below 160 mmHg for standard coverage",
        "type": "vital_threshold",
        "vital_field": "blood_pressure",
        "threshold_type": "systolic_max",
        "threshold_value": 160,
    },
    {
        "rule_id": "R003",
        "description": "Metformin requires prior authorization documentation",
        "type": "prior_auth",
        "medication_name": "Metformin",
    },
]


def evaluate_rules(extraction: dict, rules: list[dict]) -> list[dict]:
    """
    Evaluate each rule against the Phase 1 extraction dict.

    Returns a list of dicts:
        {"rule_id": str, "description": str, "passed": bool, "reason": str}
    """
    return [_evaluate_single_rule(extraction, rule) for rule in rules]


def _evaluate_single_rule(extraction: dict, rule: dict) -> dict:
    base = {"rule_id": rule["rule_id"], "description": rule["description"]}
    rule_type = rule["type"]

    if rule_type == "required_diagnosis":
        return {**base, **_check_required_diagnosis(extraction, rule)}
    if rule_type == "vital_threshold":
        return {**base, **_check_vital_threshold(extraction, rule)}
    if rule_type == "prior_auth":
        return {**base, **_check_prior_auth(extraction, rule)}
    return {**base, "passed": False, "reason": f"Unknown rule type: {rule_type}"}


def _check_required_diagnosis(extraction: dict, rule: dict) -> dict:
    prefix = rule["required_icd_prefix"]
    diagnoses = extraction.get("diagnoses") or []
    for dx in diagnoses:
        icd = (dx.get("icd_code") or "").strip()
        if icd.startswith(prefix):
            return {"passed": True, "reason": f"Found diagnosis with ICD code: {icd}"}
    return {
        "passed": False,
        "reason": f"No diagnosis with ICD-10 prefix '{prefix}' found in extraction.",
    }


def _check_vital_threshold(extraction: dict, rule: dict) -> dict:
    vital_field = rule["vital_field"]
    threshold_type = rule["threshold_type"]
    threshold_value = rule["threshold_value"]

    vitals = extraction.get("vitals") or {}
    field_data = vitals.get(vital_field)

    if field_data is None:
        return {"passed": False, "reason": f"Vital '{vital_field}' not present in extraction."}

    value_str = field_data.get("value", "")

    if threshold_type == "systolic_max":
        systolic = _parse_systolic(value_str)
        if systolic is None:
            return {
                "passed": False,
                "reason": f"Could not parse systolic value from: '{value_str}'",
            }
        if systolic < threshold_value:
            return {
                "passed": True,
                "reason": (
                    f"Systolic BP ({systolic} mmHg) is below threshold ({threshold_value} mmHg)."
                ),
            }
        return {
            "passed": False,
            "reason": (
                f"Systolic BP ({systolic} mmHg) meets or exceeds threshold ({threshold_value} mmHg)."
            ),
        }

    return {"passed": False, "reason": f"Unknown threshold_type: {threshold_type}"}


def _parse_systolic(value_str: str) -> int | None:
    """Extract the systolic integer from a BP string like '138/88 mmHg'."""
    match = re.search(r"(\d+)\s*/\s*\d+", value_str)
    return int(match.group(1)) if match else None


def _check_prior_auth(extraction: dict, rule: dict) -> dict:
    medication_name = rule["medication_name"].lower()
    medications = extraction.get("medications") or []
    for med in medications:
        if medication_name in (med.get("value") or "").lower():
            return {
                "passed": False,
                "reason": (
                    f"'{rule['medication_name']}' requires prior authorization. "
                    "Manual review required before coverage can be approved."
                ),
            }
    return {
        "passed": True,
        "reason": (
            f"'{rule['medication_name']}' not found in prescription list; "
            "prior authorization not required for this case."
        ),
    }
