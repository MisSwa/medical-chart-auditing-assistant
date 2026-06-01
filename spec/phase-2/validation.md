# Phase 2 — Validation
## How to know Phase 2 is complete and ready to merge

---

## Automated Test Suite

All unit tests must pass with `pytest -v` and zero failures. The integration test is skipped unless `OPENAI_API_KEY` is set.

---

### Policy Store tests — `tests/test_policy_store.py`

| Test | Assertion |
|---|---|
| `test_chunk_text_produces_correct_sizes` | Every chunk is ≤ `chunk_size` characters; overlap text appears at the start of the next chunk |
| `test_chunk_text_covers_full_document` | Concatenating unique portions of all chunks reconstructs the full source text with no dropped content |
| `test_build_faiss_index_stores_all_chunks` | `index.ntotal` equals the number of chunks passed in |
| `test_retrieve_returns_k_results` | `retrieve_policy_chunks()` returns exactly `k` results for any valid query (embeddings mocked) |
| `test_retrieve_integration` *(integration)* | Real call to `text-embedding-3-small`; a query matching a known policy snippet returns that snippet in the top-3 results. Marked `@pytest.mark.integration`; skipped if `OPENAI_API_KEY` is not set |

---

### Rules Engine tests — `tests/test_rules_engine.py`

| Test | Assertion |
|---|---|
| `test_diagnosis_rule_passes_when_code_present` | Extraction containing the required ICD prefix → rule result `passed: True` |
| `test_diagnosis_rule_fails_when_code_absent` | Extraction with no matching ICD code → rule result `passed: False` with a non-empty `reason` |
| `test_vital_threshold_rule_passes_within_range` | BP within the allowed threshold → rule passes |
| `test_vital_threshold_rule_fails_outside_range` | BP outside the allowed threshold → rule fails with a non-empty `reason` |
| `test_rule_evaluation_on_missing_data_does_not_crash` | Extraction with null vitals and empty diagnoses → `evaluate_rules()` returns results without raising |

---

### Policy Reasoner tests — `tests/test_policy_reasoner.py`

| Test | Assertion |
|---|---|
| `test_determination_is_valid_enum` | Result `determination` is one of `APPROVED`, `FLAGGED`, `ESCALATE_TO_HUMAN` (Claude mocked) |
| `test_reasoning_is_non_empty` | `reasoning` field is a non-empty string |
| `test_cited_chunks_are_non_empty` | `cited_chunks` list contains at least one entry |
| `test_determination_defaults_to_escalate_on_ambiguous_response` | If Claude returns an unparseable or unexpected determination value, output is `ESCALATE_TO_HUMAN` |

---

### Extractor tests — extend `tests/test_extractor.py`

| Test | Assertion |
|---|---|
| `test_is_scanned_pdf_returns_true_for_image_pdf` | A synthetic image-only PDF is detected as scanned |
| `test_is_scanned_pdf_returns_false_for_text_pdf` | The Phase 1 `fixture_diagnosis.pdf` is not detected as scanned |
| `test_scanned_pdf_extraction_returns_text` | OCR on a synthetic scanned PDF fixture returns non-empty text |

---

### Regression

| Check | Assertion |
|---|---|
| All Phase 1 tests still pass | `pytest tests/test_extractor.py tests/test_claude_extraction.py tests/test_session.py -v` exits with code 0 |

---

## Synthetic Fixtures Required

| Fixture | Format | Contents |
|---|---|---|
| `fixture_policy.txt` | Plain text | Synthetic insurance policy excerpt with at least two coverage rules stated in prose (used for RAG integration test) |
| Scanned PDF | Generated in `conftest.py` | An image-only PDF (page rendered to PNG, embedded back into PDF) with synthetic text — used for OCR tests |

---

## Manual Smoke Check

Before merge, run `streamlit run app.py` and verify:

- [ ] `OPENAI_API_KEY` missing → clear error shown at startup, app stops
- [ ] Upload a policy PDF → confirmation shows chunk count and "index ready"
- [ ] Upload a text-native clinical chart → extraction runs as in Phase 1
- [ ] Click "Run policy check" → rule results table appears with ✓ / ✗ per rule
- [ ] Determination badge appears: green (APPROVED), amber (FLAGGED), or red (ESCALATE_TO_HUMAN)
- [ ] Reasoning and cited policy chunks are visible and non-empty
- [ ] Upload a scanned PDF → OCR runs, extracted text appears, policy check proceeds normally
- [ ] Debug expander shows the retrieved policy chunks used in reasoning
- [ ] Clear session removes both the chart extraction and policy store from session state

---

## Merge Criteria

Phase 2 is ready to merge when all of the following are true:

1. All unit tests pass (`pytest -v` exits with code 0, integration test optionally skipped)
2. Manual smoke check completed with no failures
3. `ESCALATE_TO_HUMAN` is returned in every test case where the determination is ambiguous or unparseable — zero exceptions
4. Every determination in the UI shows Claude's reasoning and the policy chunks it cited — no silent determinations
5. Phase 1 tests show zero regressions
6. No `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` hardcoded anywhere
7. The policy engine consumes only the Phase 1 extraction schema — it does not read document files directly
