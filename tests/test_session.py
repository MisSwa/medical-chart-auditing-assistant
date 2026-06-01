from session import clear_session, count_fields, get_extraction, initialize_session, store_extraction

SAMPLE_EXTRACTION = {
    "vitals": {
        "blood_pressure": {"value": "120/80", "source_text": "BP 120/80", "confidence": "high"},
        "heart_rate": {"value": "72 bpm", "source_text": "HR 72", "confidence": "high"},
        "temperature": None,
        "weight": {"value": "180 lbs", "source_text": "Weight 180 lbs", "confidence": "low"},
    },
    "diagnoses": [
        {"value": "Hypertension", "icd_code": "I10", "source_text": "HTN diagnosed", "confidence": "high"}
    ],
    "medications": [],
}


def test_initialize_creates_extractions_key():
    state = {}
    initialize_session(state)
    assert "extractions" in state
    assert state["extractions"] == {}


def test_initialize_is_idempotent():
    state = {"extractions": {"file.txt": SAMPLE_EXTRACTION}}
    initialize_session(state)
    assert "file.txt" in state["extractions"]


def test_session_state_stores_extraction():
    state = {}
    store_extraction(state, "chart.pdf", SAMPLE_EXTRACTION)
    assert "chart.pdf" in state["extractions"]
    assert state["extractions"]["chart.pdf"] == SAMPLE_EXTRACTION


def test_get_extraction_returns_stored_value():
    state = {}
    store_extraction(state, "chart.pdf", SAMPLE_EXTRACTION)
    assert get_extraction(state, "chart.pdf") == SAMPLE_EXTRACTION


def test_get_extraction_returns_none_for_missing():
    state = {}
    initialize_session(state)
    assert get_extraction(state, "nonexistent.pdf") is None


def test_clear_session_resets_state(tmp_path):
    state = {"extractions": {"file.txt": SAMPLE_EXTRACTION}}
    uploads = tmp_path / "uploads"
    uploads.mkdir()
    (uploads / "file.txt").write_text("dummy content")

    clear_session(state, str(uploads))

    assert state["extractions"] == {}
    assert uploads.exists()
    assert list(uploads.iterdir()) == []


def test_count_fields_counts_non_null():
    total, low = count_fields(SAMPLE_EXTRACTION)
    # vitals: BP (high), HR (high), temperature (None — skipped), weight (low) = 3
    # diagnoses: 1 (high)
    # medications: 0
    assert total == 4
    assert low == 1


def test_count_fields_on_empty_extraction():
    empty = {
        "vitals": {"blood_pressure": None, "heart_rate": None, "temperature": None, "weight": None},
        "diagnoses": [],
        "medications": [],
    }
    total, low = count_fields(empty)
    assert total == 0
    assert low == 0
