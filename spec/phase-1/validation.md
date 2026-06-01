# Phase 1 — Validation
## How to know Phase 1 is complete and ready to merge

---

## Automated Test Suite

All of the following must pass with `pytest -v` and zero failures before Phase 1 is considered done.

### Document ingestion tests

| Test | Assertion |
|---|---|
| `test_pdf_extraction_returns_text` | `extract_text_from_pdf()` on a synthetic PDF fixture returns a non-empty string |
| `test_txt_extraction_returns_text` | `extract_text_from_txt()` on a synthetic `.txt` fixture returns a non-empty string |
| `test_format_detection_routes_correctly` | PDF files route to the PDF extractor; `.txt` files route to the text extractor |
| `test_normalization_strips_whitespace` | Normalized text contains no leading/trailing whitespace and no runs of 3+ blank lines |

### Claude extraction tests

| Test | Assertion |
|---|---|
| `test_extraction_returns_all_required_fields` | Response contains keys for at least one field in each category: vitals, diagnoses, medications |
| `test_every_field_has_source_text` | No extracted field has an empty or null `source_text` |
| `test_confidence_values_are_valid_enum` | Every `confidence` value is one of `"high"`, `"medium"`, `"low"` |
| `test_extraction_on_vitals_fixture` | Given a note containing BP, HR, and temperature, all three are extracted with non-null values |
| `test_extraction_on_diagnosis_fixture` | Given a note containing a diagnosis, at least one diagnosis entry is returned with a non-empty value |
| `test_extraction_on_medication_fixture` | Given a note listing medications, at least one medication entry is returned |
| `test_missing_fields_return_null_not_hallucinated` | Given a note with no medications, the medications field is returned as `null` or an empty list — not a fabricated value |

### Session state tests

| Test | Assertion |
|---|---|
| `test_session_state_stores_extraction` | After extraction, `st.session_state["extraction"]` is populated with the correct filename as key |
| `test_clear_session_resets_state` | After clear, `st.session_state["extraction"]` is empty and `uploads/` contains no files from the session |

---

## Synthetic Fixtures Required

The test suite must include at least these three synthetic clinical note fixtures. These must be authored — not copied from real patient data.

| Fixture | Format | Contents |
|---|---|---|
| `fixture_vitals.txt` | Plain text | Note containing BP, HR, temperature, and weight values in typical clinical prose |
| `fixture_diagnosis.pdf` | PDF | Note containing a primary diagnosis with an ICD-10 code and a secondary diagnosis |
| `fixture_medications.txt` | Plain text | Note listing 2–3 medications with dosages; no vitals or diagnoses present |

---

## Manual Smoke Check

Before merge, run the app locally (`streamlit run app.py`) and verify:

- [ ] App loads without errors
- [ ] Upload a `.pdf` file — confirmation displays with filename and path
- [ ] Upload a `.txt` file — confirmation displays correctly
- [ ] Extraction runs and returns structured output in the UI
- [ ] At least one field shows a low-confidence warning (test with an ambiguous fixture)
- [ ] "Clear session" removes results and cleans `uploads/`
- [ ] Missing or invalid `ANTHROPIC_API_KEY` shows a clear error message, not a Python traceback

---

## Merge Criteria

Phase 1 is ready to merge when all of the following are true:

1. All automated tests pass (`pytest -v` exits with code 0)
2. Manual smoke check above is completed with no failures
3. No hardcoded API keys or credentials anywhere in the codebase
4. `source_text` is non-empty for every extracted field in all test fixtures — zero hallucination tolerance
5. The extraction schema (`value` / `source_text` / `confidence`) is consistent across all fixtures and matches the structure defined in `requirements.md`
6. `uploads/` directory is in `.gitignore`
7. `.env` is in `.gitignore`
