"""
Report builder: assembles a single unified audit report dict from existing session data.

Pure function — no Claude calls, no file I/O.
"""
from datetime import datetime, timezone


def build_report(
    filename: str,
    extraction: dict,
    rule_results: list[dict],
    determination_result: dict,
) -> dict:
    """
    Assemble a complete audit report dict.

    Args:
        filename: The source document filename.
        extraction: Phase 1 clinical extraction dict (vitals, diagnoses, medications).
        rule_results: List of rule evaluation result dicts from rules_engine.evaluate_rules.
        determination_result: Post-escalation determination dict from apply_escalation.
                              Must include "determination", "reasoning", "cited_chunks".
                              May include "escalation_reason".

    Returns:
        dict with keys: filename, extraction, rule_results, determination,
                        reasoning, cited_chunks, escalation_reason, generated_at
    """
    return {
        "filename": filename,
        "extraction": extraction,
        "rule_results": rule_results,
        "determination": determination_result.get("determination", ""),
        "reasoning": determination_result.get("reasoning", ""),
        "cited_chunks": determination_result.get("cited_chunks", []),
        "escalation_reason": determination_result.get("escalation_reason", ""),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
