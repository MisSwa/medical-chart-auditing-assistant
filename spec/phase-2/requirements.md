# Phase 2 — Requirements
## Multi-Format Support & Policy Engine

---

## Scope

**In scope for this phase:**
- Policy document ingestion: upload insurance policy PDFs, chunk with fixed-size chunking, embed with `text-embedding-3-small`, store in in-memory FAISS index
- RAG retrieval: query the FAISS index to retrieve relevant policy chunks for a given case
- Structured rules engine: evaluate extracted clinical data against hardcoded coverage rules
- Policy reasoning: Claude (`claude-opus-4-6`) reasons over retrieved policy chunks + rule results to produce an audit determination
- Audit determination: `APPROVED`, `FLAGGED`, or `ESCALATE_TO_HUMAN` — with traceable reasoning
- OCR pipeline: scanned (image-based) PDF detection and text extraction via pytesseract
- All Phase 1 tests continue to pass (no regressions)

**Explicitly out of scope for this phase:**
- Full structured audit report (Phase 3)
- Human escalation workflow and queue (Phase 4)
- PNG / JPEG / TIFF standalone image support (deferred — scanned PDFs only in Phase 2)
- TIFF support (deferred)
- Persistent FAISS index across sessions (in-memory only)
- Rule editing via the UI (rules are hardcoded in Phase 2)

---

## Key Decisions

### Build order
Policy engine is built before OCR. The policy engine works immediately against Phase 1 text-native extraction output. OCR is added last as a format extension — it feeds into the same pipeline without any changes to the reasoning or rules layers.

### Structured rules: hardcoded constants
Coverage rules are defined as Python constants in `rules_engine.py`. No file I/O, no UI configuration. This is intentional for Phase 2 — the rules engine interface is what matters, not the management of rules. UI-based rule management is deferred.

The rule structure:
```python
{
    "rule_id": "R001",
    "description": "Treatment requires a confirmed Type 2 Diabetes diagnosis (ICD-10: E11.x)",
    "type": "required_diagnosis",
    "required_icd_prefix": "E11",
}
```
At minimum, Phase 2 must include rules covering:
- Required diagnosis code (at least one ICD-10 prefix check)
- Vital sign threshold (e.g. systolic BP must be below a threshold)
- Prior authorisation flag (a named medication requires prior auth)

### Embedding model
`text-embedding-3-small` via the `openai` Python SDK. Requires `OPENAI_API_KEY` set in `.env`. The app must fail loudly at startup if the key is absent — same pattern as `ANTHROPIC_API_KEY`.

### Chunking parameters
- `chunk_size`: 1000 characters
- `overlap`: 100 characters

These are sensible defaults for insurance policy documents. They can be adjusted in later phases if retrieval quality warrants it.

### FAISS index
`faiss.IndexFlatL2` — exact nearest-neighbour search. Simple, no approximation, appropriate for the document sizes in this phase. Stored as `(index, chunks)` tuple in `st.session_state["policy_store"]`.

### Retrieval top-k
`k = 5` chunks retrieved per query. The full extraction result is used as the query text.

### Policy reasoning model
`claude-opus-4-6` as specified in `techstack.md`. Opus is used here (not Sonnet) because policy cross-referencing requires careful multi-rule reasoning where accuracy is critical.

### Escalation default
If Claude's reasoning response cannot be cleanly parsed into one of the three determination values, the system **always defaults to `ESCALATE_TO_HUMAN`**. This is a hard rule — ambiguity routes to a human, never to a fabricated determination.

### OCR: scanned PDF detection heuristic
A PDF is treated as scanned if `pdfplumber` returns empty or near-empty text on every page. Threshold: fewer than 20 characters of extracted text across all pages = scanned.

### OCR image formats
Scanned PDFs only in Phase 2. Standalone PNG/JPEG/TIFF support is deferred.

---

## New Dependencies

| Package | Purpose |
|---|---|
| `openai` | `text-embedding-3-small` embeddings |
| `faiss-cpu` | In-memory vector store |
| `numpy` | Required by FAISS |
| `pytesseract` | OCR for scanned PDFs |

`pytesseract` requires the Tesseract binary installed on the system (`brew install tesseract` on macOS).

---

## Context

Phase 2 is the core intelligence layer. Phase 1 answered "what's in this document?" — Phase 2 answers "does this document satisfy coverage criteria?" The two layers must stay cleanly separated: the policy engine consumes the Phase 1 extraction schema as its input contract; it must not reach into document files directly.

The most significant risk in this phase is the RAG pipeline producing irrelevant chunks that mislead Claude's reasoning. Retrieval quality should be spot-checked manually using the debug expander in the UI before treating any determination output as trustworthy. The one real integration test (`test_retrieve_integration`) exists specifically to catch embedding or retrieval regressions that mocked tests cannot detect.
