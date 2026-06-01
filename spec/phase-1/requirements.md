# Phase 1 — Requirements
## Foundation: App Scaffold & Document Ingestion

---

## Scope

**In scope for this phase:**
- Streamlit single-page app scaffold
- Document ingestion: PDF (text-native) and plain text / EHR text exports
- Clinical data extraction via Claude with citation grounding and confidence scoring
- Fields: vitals (BP, HR, temp, weight), diagnoses / ICD codes, medications & dosages
- Local file storage: uploaded files written to `uploads/`
- In-memory session state: extraction results held in `st.session_state`
- Automated test suite with synthetic fixtures

**Explicitly out of scope for this phase:**
- OCR / scanned image support (Phase 2)
- Policy engine and rule matching (Phase 2)
- Audit report generation (Phase 3)
- Human escalation workflow and queue (Phase 4)
- Multi-page Streamlit routing (added in Phase 4)
- Date extraction (deferred — not selected for Phase 1)

---

## Key Decisions

### App structure
Single-page Streamlit app. No multi-page routing in Phase 1. Navigation will be introduced in Phase 4 when the escalation queue requires a separate view.

### PDF library
`pdfplumber` — chosen for its straightforward page-by-page text extraction API and readable output. If extraction quality proves insufficient on complex layouts, switch to `pymupdf` in Phase 2 during the OCR integration pass.

### Claude model
`claude-sonnet-4-6` for all Phase 1 extraction tasks. Sonnet provides the accuracy needed for clinical field extraction at lower cost than Opus. Opus is reserved for complex policy reasoning in Phase 2+.

### Extraction output schema
Every extracted field must include three properties. No exceptions:
```json
{
  "field_name": {
    "value": "120/80 mmHg",
    "source_text": "Blood pressure was measured at 120/80 mmHg on admission",
    "confidence": "high"
  }
}
```
`confidence` must be one of: `"high"`, `"medium"`, `"low"`.
A field with no source text anchor must not be emitted — it is better to return `null` with a low confidence than to hallucinate a value.

### API key handling
`ANTHROPIC_API_KEY` loaded from a `.env` file at startup via `python-dotenv`. The app must fail with a clear error message if the key is absent. The key must never be hardcoded or logged.

### Storage
- Uploaded files: `uploads/` directory relative to project root. Created automatically if absent.
- Extraction results: `st.session_state` only. Nothing written to disk beyond the original uploaded file.
- No database, no external storage service.

### Dependency management
`uv` preferred. `poetry` is an acceptable alternative. A `requirements.txt` must also be kept in sync for portability.

---

## Context

This phase establishes the foundation all subsequent phases build on. The extraction schema and prompt design defined here will be extended — not replaced — in later phases. Decisions made about output structure, session state keys, and file handling will propagate forward, so correctness and clarity matter more than feature completeness.

The primary risk in this phase is extraction quality: Claude hallucinating clinical values that have no basis in the source document. The citation-grounded schema (`source_text` required on every field) and explicit confidence scoring are the primary mitigations. This must be validated in the test suite before Phase 1 is considered complete.
