# Phase 3 — Requirements
## Audit Report Generation & Escalation Logic

---

## Scope

**In scope for this phase:**
- Structured audit report view: one unified layout showing extracted data, rule results, determination, and reasoning for a case
- Escalation trigger: a standalone module that enforces the escalation rule; overrides any non-APPROVED determination to ESCALATE_TO_HUMAN if any structured rule failed
- Session audit trail: timestamped log of all session events, displayed in the sidebar for the duration of the session
- PDF export: download the audit report for the current case as a PDF file
- Extend session state schema with `reports` and `audit_trail` keys
- All Phase 1 and Phase 2 tests continue to pass (no regressions)

**Explicitly out of scope for this phase:**
- Multi-case escalation queue (Phase 4)
- Auditor actions: approve, reject, add notes (Phase 4)
- Case state tracking: PENDING → IN_REVIEW → APPROVED / REJECTED (Phase 4)
- Persistent audit trail across sessions (deferred — in-memory only)
- JSON export (PDF only in Phase 3)
- Rule editing via the UI (remains hardcoded)

---

## Key Decisions

### Report assembly: pure function, no re-extraction
`report_builder.py` is a pure assembly module. It consumes existing session state data (extraction, rule results, determination result) and produces a single report dict. It makes no Claude calls and reads no files. This keeps the report layer completely decoupled from the ingestion and reasoning layers.

The assembled report is stored in `st.session_state["reports"][filename]` immediately after each policy check. The UI renders exclusively from this stored report — not directly from `st.session_state["extractions"]` or `st.session_state["determinations"]`.

### Escalation trigger: separate module, called before storage
The escalation rule is implemented in `escalation.py`, not inside `policy_reasoner.py` or `app.py`. It is called in `app.py` after `reason_against_policy` returns, before storing the result. This makes the rule independently testable and ensures no raw pre-escalation determination ever reaches the UI or the report builder.

Escalation rule (no exceptions):
- If any structured rule result has `passed == False` → escalate
- If `determination` is `"FLAGGED"` → escalate
- If `determination` is not `"APPROVED"` for any other reason → escalate
- Only `"APPROVED"` + all rules passing → not escalated

The `escalation_reason` field added on escalation names the specific failing rules or the ambiguous determination. It is included in the PDF report.

### Audit trail: new session state key, sidebar display
A new key `audit_trail` is added to session state by `initialize_session`. The trail is a list of event dicts. `log_audit_event` appends to this list; it never mutates existing entries. `clear_session` resets it to an empty list.

The sidebar renders the trail in reverse chronological order (most recent first). It is always visible — not behind an expander — so auditors can see the session history at a glance.

Event types logged:
- `"document_uploaded"` — when a chart or policy file is saved to disk
- `"extraction_complete"` — after `extract_clinical_data` returns successfully
- `"policy_check_complete"` — after escalation is applied and the determination is stored

### PDF export: fpdf2, no external fonts or images
`fpdf2` is chosen for its zero-dependency rendering. The export function returns `bytes`, which Streamlit's `st.download_button` accepts directly. No temporary file is written to disk.

The PDF is a straightforward single-column document. No images, no custom fonts, no complex layout. The goal is a readable, printable record — not a formatted report card. `fpdf2`'s built-in Helvetica is sufficient.

### New session state keys

| Key | Type | Description |
|---|---|---|
| `reports` | `dict[str, dict]` | Assembled report dicts, keyed by filename. Added by `initialize_session`. |
| `audit_trail` | `list[dict]` | Ordered list of audit events for the session. Added by `initialize_session`. |

`clear_session` must reset both new keys.

---

## New Dependencies

| Package | Purpose |
|---|---|
| `fpdf2` | PDF generation for report export |

No new AI model dependencies. No new API keys required beyond those already loaded in Phase 2.

---

## Context

Phase 3 makes the work of Phase 1 and Phase 2 legible to an auditor. Phases 1 and 2 produce data; Phase 3 assembles and presents that data in a form an auditor can act on and download.

The escalation trigger is the most important correctness requirement in this phase. It must be impossible for a case with any failing rule or ambiguous determination to appear as APPROVED in the UI or in an exported PDF. The module-level separation of `escalation.py` exists specifically to make this auditable and testable outside of the full app flow.

The audit trail is intentionally simple. It is not a full event-sourcing system — it is a session-scoped list that gives auditors and developers visibility into what the system did during a session. Persistence across sessions is deferred.
