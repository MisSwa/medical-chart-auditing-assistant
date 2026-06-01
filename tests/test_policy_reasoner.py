import json
from unittest.mock import MagicMock, patch

from policy_reasoner import reason_against_policy

VALID_DETERMINATIONS = {"APPROVED", "FLAGGED", "ESCALATE_TO_HUMAN"}

SAMPLE_EXTRACTION = {
    "vitals": {
        "blood_pressure": {"value": "138/88 mmHg", "source_text": "BP 138/88", "confidence": "high"},
        "heart_rate": None,
        "temperature": None,
        "weight": None,
    },
    "diagnoses": [
        {
            "value": "Type 2 Diabetes Mellitus",
            "icd_code": "E11.65",
            "source_text": "Type 2 DM uncontrolled",
            "confidence": "high",
        }
    ],
    "medications": [
        {"value": "Metformin 500mg daily", "source_text": "Metformin 500mg", "confidence": "high"}
    ],
}

SAMPLE_RULE_RESULTS = [
    {"rule_id": "R001", "description": "Requires E11.x", "passed": True, "reason": "ICD E11.65 found"},
    {"rule_id": "R002", "description": "BP below 160", "passed": True, "reason": "130 mmHg within range"},
    {"rule_id": "R003", "description": "Metformin prior auth", "passed": False, "reason": "Prior auth required"},
]

SAMPLE_CHUNKS = [
    "Coverage for Type 2 Diabetes management requires ICD-10 code E11.x.",
    "Metformin requires prior authorization before coverage is approved.",
]


def _mock_response(determination: str, reasoning: str = "Detailed reasoning.", cited: list = None):
    mock_msg = MagicMock()
    mock_msg.content = [
        MagicMock(
            text=json.dumps({
                "determination": determination,
                "reasoning": reasoning,
                "cited_chunks": cited or [SAMPLE_CHUNKS[0]],
            })
        )
    ]
    return mock_msg


@patch("policy_reasoner._get_client")
def test_determination_is_valid_enum(mock_get_client):
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _mock_response("APPROVED")
    mock_get_client.return_value = mock_client

    result = reason_against_policy(SAMPLE_EXTRACTION, SAMPLE_RULE_RESULTS, SAMPLE_CHUNKS)
    assert result["determination"] in VALID_DETERMINATIONS


@patch("policy_reasoner._get_client")
def test_reasoning_is_non_empty(mock_get_client):
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _mock_response(
        "FLAGGED", reasoning="Prior auth for Metformin not confirmed."
    )
    mock_get_client.return_value = mock_client

    result = reason_against_policy(SAMPLE_EXTRACTION, SAMPLE_RULE_RESULTS, SAMPLE_CHUNKS)
    assert isinstance(result["reasoning"], str)
    assert len(result["reasoning"]) > 0


@patch("policy_reasoner._get_client")
def test_cited_chunks_are_non_empty(mock_get_client):
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _mock_response(
        "FLAGGED", cited=["Metformin requires prior authorization."]
    )
    mock_get_client.return_value = mock_client

    result = reason_against_policy(SAMPLE_EXTRACTION, SAMPLE_RULE_RESULTS, SAMPLE_CHUNKS)
    assert isinstance(result["cited_chunks"], list)
    assert len(result["cited_chunks"]) >= 1


@patch("policy_reasoner._get_client")
def test_determination_defaults_to_escalate_on_ambiguous_response(mock_get_client):
    mock_client = MagicMock()
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text="This is not valid JSON at all — ambiguous response.")]
    mock_client.messages.create.return_value = mock_msg
    mock_get_client.return_value = mock_client

    result = reason_against_policy(SAMPLE_EXTRACTION, SAMPLE_RULE_RESULTS, SAMPLE_CHUNKS)
    assert result["determination"] == "ESCALATE_TO_HUMAN"
