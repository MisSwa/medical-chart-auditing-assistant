# Phase 3 — Plan
## Audit Report Generation & Escalation Logic

Tasks are vertical slices. The report view is built first because it integrates Phase 1 and 2 outputs into one visible, testable artefact. The escalation trigger is hardened next as an explicit, independently testable module. The audit trail is added third so every subsequent slice is fully logged. PDF export is last — a thin rendering layer over already-complete data.

---

## Slice 1 — Structured Audit Report View Works

**Deliverable:** After running a policy check, the auditor sees a single unified report in the main panel: extracted clinical data, rule results, determination, and reasoning — all in one layout with source traceability.

1.1 Implement `report_builder.py`:
- `build_report(filename, extraction, rule_results, determination_result)` — assembles a single report dict with keys: `filename`, `extraction`, `rule_results`, `determination`, `reasoning`, `cited_chunks`, `generated_at` (ISO timestamp)
- Pure function: no Claude calls, no file I/O; consumes existing session state data only
- Returns a typed dict suitable for display and export

1.2 Store the assembled report in `st.session_state["reports"][filename]` immediately after each policy check completes

1.3 Redesign the post-determination section in `app.py` to render from the assembled report dict:
- Two-column layout: left column shows extracted fields (vitals, diagnoses, medications with citations); right column shows rule evaluation results and determination badge
- Determination badge always rendered first in right column; reasoning expander directly beneath it
- Cited policy excerpts rendered below reasoning in the right column
- The debug retrieval expander is retained but collapsed by default

1.4 `st.caption` on each extracted field shows its `source_text` inline (truncated to 120 chars); clicking expands the full source via `st.expander`

---

## Slice 2 — Escalation Trigger is Explicit and Enforced

**Deliverable:** The escalation rule is implemented as a standalone, testable module. Any case that does not fully and unambiguously satisfy all approval criteria routes to `ESCALATE_TO_HUMAN` — no exceptions.

2.1 Implement `escalation.py`:
- `should_escalate(rule_results, determination_result)` — returns `True` if any structured rule `passed == False`, or if `determination_result["determination"]` is not `"APPROVED"`; returns `False` only when all rules pass and determination is `"APPROVED"`
- `apply_escalation(rule_results, determination_result)` — calls `should_escalate`; if True, returns a copy of `determination_result` with `determination` overridden to `"ESCALATE_TO_HUMAN"` and an `escalation_reason` field explaining which rule(s) failed; if False, returns the original result unchanged

2.2 Call `apply_escalation` in `app.py` after `reason_against_policy` returns, before storing to `st.session_state["determinations"]`

2.3 The report builder (`build_report`) always receives the post-escalation determination — it must never render a raw pre-escalation result

2.4 Unit tests for `should_escalate` and `apply_escalation` cover: all-pass → not escalated, one-rule-fail → escalated, all-rules-pass but FLAGGED determination → escalated, ambiguous determination → escalated

---

## Slice 3 — Session Audit Trail in Sidebar

**Deliverable:** The sidebar shows a live, timestamped log of every significant event in the session (document upload, extraction, policy check, determination). The log persists for the duration of the session.

3.1 Add `audit_trail` key to `session.py`:
- `initialize_session` adds `state["audit_trail"] = []` if not present
- `log_audit_event(state, event_type, filename, payload)` — appends `{"timestamp": ISO8601 string, "event_type": str, "filename": str, "payload": dict}` to `state["audit_trail"]`
- `clear_session` resets `audit_trail` to `[]`

3.2 Call `log_audit_event` at each of these points in `app.py`:
- After a document is saved to disk: event type `"document_uploaded"`, payload `{"size_kb": float, "format": str}`
- After a successful extraction: event type `"extraction_complete"`, payload `{"total_fields": int, "low_confidence_count": int}`
- After a successful policy check: event type `"policy_check_complete"`, payload `{"determination": str, "rules_passed": int, "rules_failed": int}`

3.3 Sidebar displays the audit trail below the existing session controls:
- `st.subheader("Audit Trail")`
- If trail is empty: `st.caption("No events yet.")`
- Otherwise: render each event as `st.markdown` with timestamp, event type, filename, and key payload fields; most recent event shown first (reversed list)
- Trail is not expandable/collapsible — always visible in sidebar

---

## Slice 4 — PDF Report Export

**Deliverable:** An auditor can download the current case's audit report as a PDF with a single button click.

4.1 Add dependency: `fpdf2` to `requirements.txt` and `pyproject.toml`

4.2 Implement `report_exporter.py`:
- `export_report_to_pdf(report)` — accepts the report dict from `build_report`; returns PDF as `bytes`
- PDF layout (single-column, paginated):
  - Header: document filename and report generation timestamp
  - Section 1 — Extracted Clinical Data: vitals, diagnoses, medications; each field shows value and source citation
  - Section 2 — Rule Evaluation: table of rule ID, description, pass/fail, reason
  - Section 3 — Audit Determination: determination value, escalation note if applicable, Claude's reasoning, cited policy excerpts
- Font: built-in `fpdf2` Helvetica; no external font dependencies
- No images or custom styling — readable plain layout only

4.3 In `app.py`, after the report is rendered, add a `st.download_button`:
- Label: `"Download audit report (PDF)"`
- `data`: result of `export_report_to_pdf(report)`
- `file_name`: `f"audit_report_{filename}.pdf"`
- `mime`: `"application/pdf"`
- Button is only shown when a report exists for the current case

---

## Slice 5 — Tests

**Deliverable:** All new modules have unit test coverage. No Phase 1 or Phase 2 tests regress.

5.1 `tests/test_report_builder.py`:
- `test_build_report_contains_required_keys` — output dict has all required top-level keys
- `test_build_report_extraction_preserved` — extraction data is included unchanged
- `test_build_report_generated_at_is_iso` — `generated_at` parses as a valid ISO 8601 timestamp

5.2 `tests/test_escalation.py`:
- `test_no_escalation_when_all_rules_pass_and_approved`
- `test_escalation_when_any_rule_fails`
- `test_escalation_when_determination_is_flagged`
- `test_escalation_when_determination_is_already_escalate`
- `test_apply_escalation_adds_escalation_reason`
- `test_apply_escalation_does_not_mutate_input`

5.3 `tests/test_session.py` — extend with:
- `test_log_audit_event_appends_entry`
- `test_log_audit_event_entry_has_required_keys`
- `test_clear_session_resets_audit_trail`

5.4 `tests/test_report_exporter.py`:
- `test_export_returns_bytes`
- `test_export_bytes_are_non_empty`
- `test_export_is_valid_pdf_header` — first 4 bytes are `%PDF`

5.5 Regression: all Phase 1 and Phase 2 tests still pass with `pytest -v`
