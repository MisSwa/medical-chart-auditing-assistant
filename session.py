"""
Session state helpers.

All functions operate on a plain dict so they can be unit-tested without Streamlit.
In app.py, pass st.session_state directly.
"""
import shutil
from pathlib import Path


def initialize_session(state: dict) -> None:
    """Set up required session state keys if not already present."""
    if "extractions" not in state:
        state["extractions"] = {}
    if "policy_store" not in state:
        state["policy_store"] = None
    if "policy_filename" not in state:
        state["policy_filename"] = None
    if "determinations" not in state:
        state["determinations"] = {}


def store_extraction(state: dict, filename: str, extraction: dict) -> None:
    """Store an extraction result keyed by filename."""
    initialize_session(state)
    state["extractions"][filename] = extraction


def get_extraction(state: dict, filename: str) -> dict | None:
    """Retrieve a stored extraction by filename, or None if not present."""
    return state.get("extractions", {}).get(filename)


def clear_session(state: dict, uploads_dir: str) -> None:
    """Clear all session state and remove uploaded files from disk."""
    state["extractions"] = {}
    state["policy_store"] = None
    state["policy_filename"] = None
    state["determinations"] = {}
    uploads_path = Path(uploads_dir)
    if uploads_path.exists():
        shutil.rmtree(uploads_path)
    uploads_path.mkdir(parents=True, exist_ok=True)


def count_fields(extraction: dict) -> tuple[int, int]:
    """
    Return (total_extracted_fields, low_confidence_count).
    Only counts non-null leaf fields across vitals, diagnoses, and medications.
    """
    total = 0
    low_confidence = 0

    for field_data in (extraction.get("vitals") or {}).values():
        if field_data is not None:
            total += 1
            if field_data.get("confidence") == "low":
                low_confidence += 1

    for item in extraction.get("diagnoses") or []:
        total += 1
        if item.get("confidence") == "low":
            low_confidence += 1

    for item in extraction.get("medications") or []:
        total += 1
        if item.get("confidence") == "low":
            low_confidence += 1

    return total, low_confidence
