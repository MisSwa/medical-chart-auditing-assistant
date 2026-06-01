from report_exporter import export_report_to_pdf

SAMPLE_REPORT = {
    "filename": "chart.pdf",
    "extraction": {
        "vitals": {
            "blood_pressure": {"value": "138/88 mmHg", "source_text": "BP 138/88", "confidence": "high"},
            "heart_rate": None,
            "temperature": None,
            "weight": None,
        },
        "diagnoses": [
            {"value": "Type 2 Diabetes", "icd_code": "E11.65", "source_text": "T2DM", "confidence": "high"}
        ],
        "medications": [],
    },
    "rule_results": [
        {"rule_id": "R001", "description": "Diagnosis rule", "passed": True, "reason": "ICD found"},
        {"rule_id": "R002", "description": "BP rule", "passed": False, "reason": "BP too high"},
    ],
    "determination": "ESCALATE_TO_HUMAN",
    "reasoning": "One rule failed — escalated.",
    "cited_chunks": ["Policy excerpt A"],
    "escalation_reason": "Escalated due to failing rule(s): R002: BP rule",
    "generated_at": "2026-05-31T12:00:00+00:00",
}


def test_export_returns_bytes():
    result = export_report_to_pdf(SAMPLE_REPORT)
    assert isinstance(result, bytes)


def test_export_bytes_are_non_empty():
    result = export_report_to_pdf(SAMPLE_REPORT)
    assert len(result) > 0


def test_export_is_valid_pdf_header():
    result = export_report_to_pdf(SAMPLE_REPORT)
    assert result[:4] == b"%PDF"
