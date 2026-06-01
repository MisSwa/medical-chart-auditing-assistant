# Phase 1 — Plan
## Foundation: App Scaffold & Document Ingestion

Tasks are grouped as vertical slices. Each slice produces something runnable before the next begins.

---

## Slice 1 — File Upload Works

**Deliverable:** An auditor can open the Streamlit app, upload a clinical document, and see it saved locally with confirmation.

1.1 Set up Python project with `uv` or `poetry`; pin Python 3.11+
1.2 Add dependencies: `streamlit`, `anthropic`, `pdfplumber`, `pillow`, `python-dotenv`
1.3 Create `app.py` — Streamlit single-page entry point with title and layout
1.4 Add `st.file_uploader` accepting `.pdf` and `.txt` file types
1.5 Write uploaded file to `uploads/` directory; create directory if absent
1.6 Display upload confirmation: filename, file type, size, and save path

---

## Slice 2 — Text Extraction Works

**Deliverable:** Given an uploaded document, the app extracts and displays its raw text content.

2.1 Implement `extract_text_from_pdf(filepath)` using `pdfplumber` — returns page-by-page text
2.2 Implement `extract_text_from_txt(filepath)` — reads and returns plain text / EHR exports
2.3 Add format detection: route uploaded file to the correct extractor based on file extension
2.4 Implement text normalization: strip excessive whitespace, normalize line breaks
2.5 Display raw extracted text in a Streamlit expander (`st.expander("Raw extracted text")`)

---

## Slice 3 — Claude Extraction Works

**Deliverable:** Given extracted text, Claude returns a structured JSON object with clinical fields, source citations, and confidence scores.

3.1 Load `ANTHROPIC_API_KEY` from environment (`.env` file via `python-dotenv`); fail loudly if absent
3.2 Design extraction prompt: instruct Claude to extract vitals (BP, HR, temp, weight), diagnoses / ICD codes, and medications & dosages
3.3 Define output schema: each field as `{ "value": ..., "source_text": ..., "confidence": "high" | "medium" | "low" }`
3.4 Call `claude-sonnet-4-6` with the extraction prompt and document text; parse JSON response
3.5 Handle Claude API errors gracefully — surface error message in the UI, do not crash
3.6 Display structured extraction result in Streamlit using `st.json` and `st.expander`

---

## Slice 4 — Session State & Confidence Flags

**Deliverable:** Extraction results persist in session state; low-confidence fields are visually flagged.

4.1 Store extraction result in `st.session_state["extraction"]` keyed by filename
4.2 Visually flag fields with `confidence: "low"` using a warning indicator in the UI (`st.warning`)
4.3 Show a summary count: how many fields extracted, how many flagged as low-confidence
4.4 Add a "Clear session" button that resets `st.session_state` and removes uploaded files from `uploads/`

---

## Slice 5 — Tests

**Deliverable:** A passing `pytest` suite covering extraction correctness against synthetic fixtures.

5.1 Set up `pytest` with a `tests/` directory and `conftest.py`
5.2 Create 2–3 synthetic clinical note fixtures: one PDF and one plain text; cover at least one note with vitals, one with diagnoses, and one with medications
5.3 Write unit tests for `extract_text_from_pdf` and `extract_text_from_txt` — assert non-empty output
5.4 Write integration tests for the Claude extraction step — assert all required field keys are present in the response, source_text is non-empty for each field, and confidence is one of the valid enum values
5.5 All tests pass with `pytest -v`
