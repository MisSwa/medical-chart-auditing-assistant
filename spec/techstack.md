# Tech Stack

## Guiding Constraints

- Python backend (project requirement)
- Anti-hallucination: all AI outputs must be grounded and cited
- Human-in-the-loop: the stack must support a review/escalation workflow, not just a pipeline
- Simple infrastructure: in-memory session state and local file storage only

---

## Application

| Layer | Choice | Rationale |
|---|---|---|
| Language | Python 3.11+ | Required; strong ecosystem for AI and document processing |
| Framework | Streamlit | Python-native full-stack app; handles UI, session state, and file upload without a separate frontend |

---

## AI / LLM

| Layer | Choice | Rationale |
|---|---|---|
| Primary model | Claude (Anthropic API) | Strong instruction-following, structured output, long context for full chart ingestion |
| Extraction tasks | claude-sonnet-4-6 | Balanced accuracy and cost for structured extraction |
| Complex policy reasoning | claude-opus-4-6 | For nuanced multi-rule cross-referencing where accuracy is critical |
| SDK | `anthropic` Python SDK | Official SDK; supports streaming, tool use, and structured outputs |
| Anti-hallucination | Citation-grounded prompts + confidence scoring | Every extracted field must reference the source span; no field is emitted without a document anchor |

---

## Document Processing

| Task | Library | Notes |
|---|---|---|
| PDF extraction | `pdfplumber` or `pymupdf` | Text-native PDFs |
| OCR (scanned images) | `pytesseract` + Tesseract | For image-based documents and scanned charts |
| Image pre-processing | `Pillow` | Normalize images before OCR |
| Text normalization | Custom utilities | Standardize EHR export formats |

---

## Policy Document Reasoning (RAG)

| Layer | Choice | Rationale |
|---|---|---|
| Vector store | FAISS (in-memory) | Local, no infrastructure required; reloaded per session |
| Embeddings | `text-embedding-3-small` (OpenAI) | Fast, cost-effective embeddings via `openai` Python SDK |
| Chunking strategy | Fixed-size chunking | Simple and predictable; consistent chunk sizes across all policy documents |

---

## Streamlit UI Components

| Component | Streamlit Feature | Notes |
|---|---|---|
| Session state | `st.session_state` | In-memory state scoped to each user session |
| File upload | `st.file_uploader` | Built-in multi-format document upload |
| Report display | `st.json`, `st.dataframe`, `st.expander` | Structured display of extracted data and audit results |
| Escalation queue | `st.sidebar` + page routing | Auditor review and decision workflow |

---

## Storage

| Asset | Storage | Notes |
|---|---|---|
| Uploaded documents | Local filesystem | Written to a local `uploads/` directory during the session |
| Extracted data & reports | In-memory (session state) | Held in `st.session_state`; not persisted between sessions |
| Policy document chunks | In-memory FAISS index | Built at upload time; lives for the duration of the session |

---

## Deployment (Decision Pending)

Deployment environment has not yet been decided. Given the local-first storage model, the application is well-suited to run locally or on a single server. Infrastructure requirements are minimal — no managed database or object storage needed.

---

## Development Tooling

| Tool | Purpose |
|---|---|
| `uv` or `poetry` | Python dependency management |
| `pytest` | Unit and integration testing |
| `ruff` | Linting and formatting |
