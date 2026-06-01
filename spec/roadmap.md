# Roadmap

MVP target: End-to-end audit flow — ingest a chart, extract clinical data, check against policy, generate a report, escalate to human if criteria are not fully met.

Four phases, ordered by dependency. Each phase must be stable before the next begins.

---

## Phase 1 — Foundation: App Scaffold & Document Ingestion

**Goal:** A working Streamlit app that accepts clinical documents and returns structured clinical data extracted by Claude.

- Streamlit app scaffold: page layout, session state structure, file upload UI
- Document ingestion pipeline: PDF (text-native), plain text, EHR text exports
- Claude integration: prompt design for structured clinical data extraction (vitals, diagnoses, medications, dates)
- Citation-grounded output: every extracted field references its source location in the document
- Confidence scoring: flag low-confidence extractions for human review
- Local file storage: uploaded documents written to `uploads/` directory
- Unit tests for extraction accuracy against sample documents

**Exit criteria:** An auditor can upload a clinical document and get back a structured, citation-grounded extraction result in the Streamlit UI.

---

## Phase 2 — Multi-Format Support & Policy Engine

**Goal:** Handle all document formats and introduce policy rule matching against both structured rules and uploaded policy documents.

- OCR pipeline: pytesseract + image pre-processing for scanned PDFs and image-based charts
- Format detection: automatically route documents to the correct ingestion path (text-native vs OCR)
- Policy document ingestion: upload insurance policy PDFs, chunk with fixed-size chunking, embed with `text-embedding-3-small`
- In-memory FAISS index: built at upload time, held in session state for the duration of the session
- Structured rules engine: define and evaluate explicit coverage criteria (diagnosis codes, vitals thresholds, prior auth conditions)
- RAG-based policy reasoning: retrieve relevant policy chunks and use Claude to reason against extracted clinical data
- Audit determination logic: output one of — `APPROVED`, `FLAGGED`, or `ESCALATE_TO_HUMAN`

**Exit criteria:** Given a chart (any format) and a policy document, the system produces a structured audit determination with traceable reasoning.

---

## Phase 3 — Audit Report Generation & Escalation Logic

**Goal:** Produce a complete, human-readable audit report and implement the escalation trigger.

- Structured audit report: extracted clinical data, matched policy rules, determination, and reasoning — all in one view
- Escalation trigger: any case that does not fully and unambiguously meet all approval criteria routes to `ESCALATE_TO_HUMAN`; no exceptions
- Report display in Streamlit: clean layout showing source document, extracted fields, policy matches, and final determination side by side
- Audit trail: log of every extraction, policy match, and determination produced during the session (stored in session state)
- Export: allow auditors to download the audit report as a structured JSON or PDF

**Exit criteria:** The system produces a complete, readable audit report for any uploaded case, with a clear determination and an explicit escalation flag where criteria are not fully met.

---

## Phase 4 — Human Review Workflow & Escalation Queue

**Goal:** Give auditors a full review and decision workflow within the Streamlit app.

- Escalation queue: session-scoped list of all cases flagged for human review
- Auditor actions: approve, reject, add notes, mark for follow-up
- Case state tracking: `PENDING` → `IN_REVIEW` → `APPROVED` / `REJECTED` (held in session state)
- Decision log: every auditor action recorded with a timestamp and the auditor's notes
- Multi-case workflow: auditors can move between cases in a session without losing prior work
- End-to-end walkthrough test: full flow from document upload to auditor decision on a representative case set

**Exit criteria:** An auditor can complete the full workflow — upload, review AI report, make a decision, and move to the next case — entirely within the Streamlit app.

---

## Deferred / Future

- Persistent storage (database or file-backed) to retain cases and decisions across sessions
- Multi-user support with per-user case assignment
- Direct integration with insurance carrier systems or EHR platforms
- Feedback loop: use auditor decisions to improve extraction prompt quality over time
