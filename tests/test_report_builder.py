from datetime import datetime

from report_builder import build_report

SAMPLE_EXTRACTION = {
    "vitals": {
        "blood_pressure": {"value": "138/88 mmHg", "source_text": "BP 138/88", "confidence": "high"},
        "heart_rate": None,
        "temperature": None,
        "weight": None,
    },
    "diagnoses": [
        {"value": "Type 2 Diabetes", "icd_code": "E11.65", "source_text": "T2DM noted", "confidence": "high"}
    ],
    "medications": [],
}

SAMPLE_RULE_RESULTS = [
    {"rule_id": "R001", "description": "Diagnosis rule", "passed": True, "reason": "ICD found"},
]

SAMPLE_DETERMINATION = {
    "determination": "APPROVED",
    "reasoning": "All criteria satisfied.",
    "cited_chunks": ["Policy excerpt A"],
}

REQUIRED_KEYS = {
    "filename", "extraction", "rule_results", "determination",
    "reasoning", "cited_chunks", "generated_at",
}


def test_build_report_contains_required_keys():
    report = build_report("chart.pdf", SAMPLE_EXTRACTION, SAMPLE_RULE_RESULTS, SAMPLE_DETERMINATION)
    for key in REQUIRED_KEYS:
        assert key in report, f"Missing required key: {key}"


def test_build_report_extraction_preserved():
    report = build_report("chart.pdf", SAMPLE_EXTRACTION, SAMPLE_RULE_RESULTS, SAMPLE_DETERMINATION)
    assert report["extraction"] == SAMPLE_EXTRACTION


def test_build_report_generated_at_is_iso():
    report = build_report("chart.pdf", SAMPLE_EXTRACTION, SAMPLE_RULE_RESULTS, SAMPLE_DETERMINATION)
    parsed = datetime.fromisoformat(report["generated_at"])
    assert parsed is not None
