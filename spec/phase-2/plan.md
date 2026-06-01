# Phase 2 — Plan
## Multi-Format Support & Policy Engine

Tasks are vertical slices. Policy engine is built first (it operates on Phase 1 text extraction output immediately). OCR is added second as a format extension that feeds the same pipeline.

---

## Slice 1 — Policy Document Ingestion Works

**Deliverable:** An auditor can upload an insurance policy PDF, have it chunked and embedded, and see a FAISS index stored in session state ready for retrieval.

1.1 Add dependencies: `openai`, `faiss-cpu`, `numpy` to `requirements.txt` and `pyproject.toml`
1.2 Load `OPENAI_API_KEY` from `.env`; fail loudly at startup if absent (same pattern as `ANTHROPIC_API_KEY`)
1.3 Implement `policy_store.py`:
- `chunk_text(text, chunk_size, overlap)` — fixed-size character chunking with overlap
- `embed_chunks(chunks)` — calls `text-embedding-3-small` via OpenAI SDK, returns list of vectors
- `build_faiss_index(chunks, embeddings)` — builds in-memory `faiss.IndexFlatL2`, returns `(index, chunks)`
- `ingest_policy_document(filepath)` — orchestrates: extract text → chunk → embed → build index
1.4 Add a "Policy Document" upload section to `app.py` (above the chart upload)
1.5 On upload, run `ingest_policy_document` and store `(index, chunks)` in `st.session_state["policy_store"]`
1.6 Display confirmation: document name, number of chunks created, index ready indicator

---

## Slice 2 — RAG Retrieval Works

**Deliverable:** Given a query string, the system retrieves the most relevant policy chunks from the FAISS index.

2.1 Implement `retrieve_policy_chunks(query, index, chunks, k=5)` in `policy_store.py`:
- Embed the query using `text-embedding-3-small`
- Search FAISS index for top-k nearest neighbours
- Return list of retrieved chunk strings with their relevance rank
2.2 Write a retrieval smoke test: given a known policy snippet and a matching query, the correct chunk is returned in the top results
2.3 Display retrieved chunks in a debug expander in the UI (collapsed by default) so auditors can verify what policy context was used

---

## Slice 3 — Structured Rules Engine Works

**Deliverable:** A rules engine that evaluates extracted clinical data against hardcoded coverage criteria and returns a per-rule pass/fail result.

3.1 Implement `rules_engine.py`:
- Define `COVERAGE_RULES` — a list of hardcoded rule dicts covering at least three rule types:
  - Diagnosis code required (e.g. treatment X requires ICD-10 code Y to be present)
  - Vital threshold (e.g. BP must be within a specified range for a given treatment)
  - Prior authorisation condition (e.g. specific medication requires prior auth flag)
- `evaluate_rules(extraction, rules)` — checks each rule against the Phase 1 extraction dict, returns a list of `{"rule_id", "description", "passed": bool, "reason": str}`
3.2 Display rule evaluation results in the UI as a colour-coded table (pass = ✓, fail = ✗)
3.3 Unit tests for each rule type with fixtures that exercise pass, fail, and missing-data cases

---

## Slice 4 — Policy Reasoning & Audit Determination

**Deliverable:** Claude reasons over the extracted data, retrieved policy chunks, and rule results to produce a traceable `APPROVED` / `FLAGGED` / `ESCALATE_TO_HUMAN` determination.

4.1 Implement `policy_reasoner.py`:
- `build_reasoning_prompt(extraction, rule_results, policy_chunks)` — assembles the full context prompt
- `reason_against_policy(extraction, rule_results, policy_chunks)` — calls `claude-opus-4-6`, returns `{"determination": "APPROVED"|"FLAGGED"|"ESCALATE_TO_HUMAN", "reasoning": str, "cited_chunks": [str]}`
- Escalation default: if determination cannot be clearly established, always return `ESCALATE_TO_HUMAN`
4.2 Store determination in `st.session_state["determinations"][filename]`
4.3 Display determination prominently in the UI: green (APPROVED), amber (FLAGGED), red (ESCALATE_TO_HUMAN)
4.4 Display Claude's reasoning and the policy chunks it cited — every determination must be auditor-explainable

---

## Slice 5 — OCR Pipeline for Scanned PDFs

**Deliverable:** Scanned (image-based) PDFs are automatically detected and OCR'd, then fed into the existing Phase 1 extraction pipeline without any change to downstream code.

5.1 Add dependency: `pytesseract` to `requirements.txt` / `pyproject.toml`
5.2 Implement `is_scanned_pdf(filepath)` in `extractor.py` — heuristic: if pdfplumber returns no text on any page, treat as scanned
5.3 Implement `extract_text_from_scanned_pdf(filepath)` in `extractor.py`:
- Render each page to an image using `pdfplumber` page rendering (or `Pillow`)
- Pre-process with Pillow: convert to grayscale, apply threshold for clarity
- Run `pytesseract.image_to_string` on each processed page image
- Return concatenated OCR text
5.4 Update `extract_text()` format detection: auto-detect scanned PDFs and route to OCR extractor
5.5 Phase 1 extraction and Phase 2 policy pipeline consume OCR output without modification
5.6 Regression: all Phase 1 tests still pass

---

## Slice 6 — Tests

**Deliverable:** Full test coverage with mocked unit tests and one real integration test for the RAG pipeline.

6.1 `tests/test_policy_store.py` — mocked unit tests:
- `test_chunk_text_produces_correct_sizes` — chunks respect `chunk_size` and `overlap`
- `test_chunk_text_covers_full_document` — no text is dropped between chunks
- `test_build_faiss_index_stores_all_chunks` — index size equals chunk count
- `test_retrieve_returns_k_results` — retrieval returns exactly k results (mocked embeddings)
- `test_retrieve_integration` — real `text-embedding-3-small` call; `@pytest.mark.integration`; skipped if `OPENAI_API_KEY` not set

6.2 `tests/test_rules_engine.py` — unit tests:
- `test_diagnosis_rule_passes_when_code_present`
- `test_diagnosis_rule_fails_when_code_absent`
- `test_vital_threshold_rule_passes_within_range`
- `test_vital_threshold_rule_fails_outside_range`
- `test_rule_evaluation_on_missing_data_does_not_crash`

6.3 `tests/test_policy_reasoner.py` — mocked unit tests:
- `test_determination_is_valid_enum` — result is one of APPROVED, FLAGGED, ESCALATE_TO_HUMAN
- `test_reasoning_is_non_empty`
- `test_cited_chunks_are_non_empty`
- `test_determination_defaults_to_escalate_on_ambiguous_response`

6.4 `tests/test_extractor.py` — extend with OCR tests:
- `test_is_scanned_pdf_returns_true_for_image_pdf`
- `test_is_scanned_pdf_returns_false_for_text_pdf`
- `test_scanned_pdf_extraction_returns_text`
