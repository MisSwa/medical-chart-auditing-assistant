# Phase 3 — Validation
## How to know Phase 3 is complete and ready to merge

---

## Automated Test Suite

All unit tests must pass with `pytest -v` and zero failures.

---

### Report Builder tests — `tests/test_report_builder.py`

| Test | Assertion |
|---|---|
| `test_build_report_contains_required_keys` | Output dict contains all of: `filename`, `extraction`, `rule_results`, `determination`, `reasoning`, `cited_chunks`, `generated_at` |
| `test_build_report_extraction_preserved` | `report["extraction"]` equals the input extraction dict exactly |
| `test_build_report_generated_at_is_iso` | `report["generated_at"]` parses without error as an ISO 8601 datetime string |

---

### Escalation tests — `tests/test_escalation.py`

| Test | Assertion |
|---|---|
| `test_no_escalation_when_all_rules_pass_and_approved` | All rules `passed: True` + determination `APPROVED` → `should_escalate` returns `False` |
| `test_escalation_when_any_rule_fails` | One rule `passed: False` regardless of determination → `should_escalate` returns `True` |
| `test_escalation_when_determination_is_flagged` | All rules pass but determination is `FLAGGED` → `should_escalate` returns `True` |
| `test_escalation_when_determination_is_already_escalate` | Determination is `ESCALATE_TO_HUMAN` → `should_escalate` returns `True` |
| `test_apply_escalation_adds_escalation_reason` | When escalation is triggered, output dict contains a non-empty `escalation_reason` string |
| `test_apply_escalation_does_not_mutate_input` | Input `determination_result` dict is unchanged after calling `apply_escalation` |

---

### Session tests — extend `tests/test_session.py`

| Test | Assertion |
|---|---|
| `test_log_audit_event_appends_entry` | After one call to `log_audit_event`, `state["audit_trail"]` has exactly one entry |
| `test_log_audit_event_entry_has_required_keys` | Each appended entry has `timestamp`, `event_type`, `filename`, and `payload` keys |
| `test_clear_session_resets_audit_trail` | After `clear_session`, `state["audit_trail"]` is an empty list |

---

### Report Exporter tests — `tests/test_report_exporter.py`

| Test | Assertion |
|---|---|
| `test_export_returns_bytes` | `export_report_to_pdf(report)` returns a `bytes` object |
| `test_export_bytes_are_non_empty` | Returned bytes have length > 0 |
| `test_export_is_valid_pdf_header` | First 4 bytes of the output equal `b"%PDF"` |

---

### Regression

| Check | Assertion |
|---|---|
| Phase 1 tests pass | `pytest tests/test_extractor.py tests/test_claude_extraction.py tests/test_session.py -v` exits with code 0 |
| Phase 2 tests pass | `pytest tests/test_policy_store.py tests/test_rules_engine.py tests/test_policy_reasoner.py -v` exits with code 0 |

---

## Manual Smoke Check

Before merge, run `streamlit run app.py` and verify each item:

**Escalation trigger:**
- [ ] Upload a policy document and a chart; run policy check with a chart that fails at least one structured rule → determination shown is `ESCALATE_TO_HUMAN` (red badge), even if Claude's raw reasoning said `APPROVED` or `FLAGGED`
- [ ] Upload a chart that satisfies all rules → if determination is `APPROVED`, it displays as `APPROVED` (green badge)
- [ ] Escalation reason is visible below the determination badge whenever escalation is triggered

**Structured report view:**
- [ ] After running policy check, the main panel shows a two-column layout: extracted fields on the left, rule results and determination on the right
- [ ] Each extracted field in the left column shows its `source_text` citation (truncated; full text on expand)
- [ ] Rule results show ✓ / ✗ per rule with reason text
- [ ] Claude's reasoning expander is open by default and non-empty
- [ ] Cited policy excerpts are visible and non-empty

**Audit trail:**
- [ ] After uploading a document, the sidebar shows a `"document_uploaded"` event with timestamp and filename
- [ ] After running extraction, the sidebar shows an `"extraction_complete"` event with field count
- [ ] After running policy check, the sidebar shows a `"policy_check_complete"` event with determination value
- [ ] Events are listed most-recent-first
- [ ] Clicking "Clear session" resets the audit trail to empty in the sidebar

**PDF export:**
- [ ] "Download audit report (PDF)" button appears after a policy check is complete
- [ ] Clicking the button downloads a `.pdf` file with a non-zero file size
- [ ] Opened PDF contains: document filename, extracted clinical data with citations, rule results, determination, escalation reason (if applicable), Claude's reasoning, and cited policy excerpts
- [ ] Download button is not shown when no report exists for the current case

---

## Merge Criteria

Phase 3 is ready to merge when all of the following are true:

1. All unit tests pass (`pytest -v` exits with code 0)
2. Phase 1 and Phase 2 regression tests show zero failures
3. Manual smoke check completed with no failures
4. `ESCALATE_TO_HUMAN` is the displayed determination for every case where any structured rule failed — zero exceptions confirmed by manual testing
5. Every determination in the UI is accompanied by Claude's reasoning and escalation reason (if applicable) — no silent determinations
6. The PDF download button produces a valid, non-empty PDF confirmed by opening the downloaded file
7. `apply_escalation` is called before any determination is stored to session state — no raw pre-escalation determination is ever stored or displayed
8. No API keys (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`) hardcoded anywhere in new files
