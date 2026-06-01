"""
Session state helpers.

All functions operate on a plain dict so they can be unit-tested without Streamlit.
In app.py, pass st.session_state directly.
"""
import shutil
from datetime import datetime, timezone
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
    if "reports" not in state:
        state["reports"] = {}
    if "audit_trail" not in state:
        state["audit_trail"] = []


def store_extraction(state: dict, filename: str, extraction: dict) -> None:
    """Store an extraction result keyed by filename."""
    initialize_session(state)
    state["extractions"][filename] = extraction


def get_extraction(state: dict, filename: str) -> dict | None:
    """Retrieve a stored extraction by filename, or None if not present."""
    return state.get("extractions", {}).get(filename)


def log_audit_event(state: dict, event_type: str, filename: str, payload: dict) -> None:
    """
    Append a timestamped audit event to state["audit_trail"].
    Never mutates existing entries — only appends.

    Args:
        state: The session state dict.
        event_type: One of "document_uploaded", "extraction_complete", "policy_check_complete".
        filename: The document filename associated with the event.
        payload: Event-specific data dict.
    """
    initialize_session(state)
    state["audit_trail"].append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "filename": filename,
        "payload": payload,
    })


def clear_session(state: dict, uploads_dir: str) -> None:
    """Clear all session state and remove uploaded files from disk."""
    state["extractions"] = {}
    state["policy_store"] = None
    state["policy_filename"] = None
    state["determinations"] = {}
    state["reports"] = {}
    state["audit_trail"] = []
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
