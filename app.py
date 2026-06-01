import json
import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from claude_client import extract_clinical_data
from extractor import extract_text
from policy_reasoner import reason_against_policy
from policy_store import ingest_policy_document, retrieve_policy_chunks
from rules_engine import COVERAGE_RULES, evaluate_rules
from session import clear_session, count_fields, initialize_session, store_extraction

load_dotenv()

UPLOADS_DIR = Path("uploads")
UPLOADS_DIR.mkdir(exist_ok=True)

st.set_page_config(page_title="Medical Chart Auditing Assistant", layout="wide")
st.title("Medical Chart Auditing Assistant")
st.caption("Phase 2 — Policy Engine & Audit Determination")

# ── API key validation at startup — fail loudly ─────────────────────────────
if not os.environ.get("ANTHROPIC_API_KEY"):
    st.error(
        "**ANTHROPIC_API_KEY is not set.**\n\n"
        "Add it to a `.env` file in the project root and restart the app:\n\n"
        "```\nANTHROPIC_API_KEY=your_key_here\n```"
    )
    st.stop()

if not os.environ.get("OPENAI_API_KEY"):
    st.error(
        "**OPENAI_API_KEY is not set.**\n\n"
        "Add it to a `.env` file in the project root and restart the app:\n\n"
        "```\nOPENAI_API_KEY=your_key_here\n```"
    )
    st.stop()

initialize_session(st.session_state)

# ── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Session")
    if st.button("Clear session", use_container_width=True):
        clear_session(st.session_state, str(UPLOADS_DIR))
        st.rerun()

    if st.session_state.get("policy_filename"):
        st.markdown(f"**Policy:** {st.session_state['policy_filename']} ✓")

    extractions = st.session_state.get("extractions", {})
    if extractions:
        st.markdown("**Processed charts:**")
        for fname in extractions:
            st.markdown(f"- {fname}")

# ── 1. Policy Document ───────────────────────────────────────────────────────
st.header("1. Policy Document")

policy_file = st.file_uploader(
    "Upload an insurance policy document",
    type=["pdf", "txt"],
    key="policy_upload",
    help="The policy will be chunked, embedded with text-embedding-3-small, and indexed for retrieval.",
)

if policy_file is not None:
    policy_save_path = UPLOADS_DIR / f"policy_{policy_file.name}"
    with open(policy_save_path, "wb") as f:
        f.write(policy_file.getbuffer())

    # Only re-ingest if the policy file has changed or the index is not yet built
    if (
        st.session_state.get("policy_store") is None
        or st.session_state.get("policy_filename") != policy_file.name
    ):
        with st.spinner("Chunking and indexing policy document..."):
            try:
                index, chunks = ingest_policy_document(str(policy_save_path))
                st.session_state["policy_store"] = (index, chunks)
                st.session_state["policy_filename"] = policy_file.name
            except Exception as e:
                st.error(f"Policy ingestion failed: {e}")
                st.stop()

    _, chunks = st.session_state["policy_store"]
    st.success(
        f"Policy indexed: **{policy_file.name}** — {len(chunks)} chunk(s) — index ready ✓"
    )
else:
    st.info("Upload a policy document to enable coverage determination.")

st.divider()

# ── 2. Clinical Chart ────────────────────────────────────────────────────────
st.header("2. Clinical Chart")

uploaded_file = st.file_uploader(
    "Upload a clinical document",
    type=["pdf", "txt"],
    key="chart_upload",
    help="Accepted formats: PDF (text-native or scanned), plain text / EHR export",
)

if uploaded_file is None:
    st.info("Upload a clinical document above to begin.")
    st.stop()

save_path = UPLOADS_DIR / uploaded_file.name
with open(save_path, "wb") as f:
    f.write(uploaded_file.getbuffer())

size_kb = save_path.stat().st_size / 1024
st.success(f"Uploaded: **{uploaded_file.name}** ({size_kb:.1f} KB) — saved to `{save_path}`")

# ── Text extraction ──────────────────────────────────────────────────────────
try:
    document_text = extract_text(str(save_path))
except Exception as e:
    st.error(f"Text extraction failed: {e}")
    st.stop()

with st.expander("Raw extracted text"):
    st.text(document_text)

# ── Claude extraction ────────────────────────────────────────────────────────
st.divider()

if st.button("Extract clinical data", type="primary"):
    with st.spinner("Extracting clinical data with Claude..."):
        try:
            extraction = extract_clinical_data(document_text)
            store_extraction(st.session_state, uploaded_file.name, extraction)
        except Exception as e:
            st.error(f"Extraction failed: {e}")
            st.stop()

result = st.session_state.get("extractions", {}).get(uploaded_file.name)
if result is None:
    st.stop()

# ── Extraction results ───────────────────────────────────────────────────────
total, low_count = count_fields(result)

col1, col2 = st.columns(2)
col1.metric("Fields extracted", total)
col2.metric("Low-confidence fields", low_count)

if low_count > 0:
    st.warning(
        f"{low_count} field(s) flagged as low confidence — review these carefully before use."
    )

# Vitals
st.subheader("Vitals")
vitals = result.get("vitals") or {}
vitals_found = [v for v in vitals.values() if v is not None]
if vitals_found:
    for field_name, field_data in vitals.items():
        if field_data is None:
            continue
        label = field_name.replace("_", " ").title()
        value = field_data.get("value", "—")
        conf = field_data.get("confidence", "unknown")
        source = field_data.get("source_text", "")
        with st.expander(f"{label}: **{value}** — confidence: `{conf}`"):
            st.caption("Source text:")
            st.markdown(f"> {source}")
        if conf == "low":
            st.warning(f"Low confidence: {label}")
else:
    st.info("No vitals found in this document.")

# Diagnoses
st.subheader("Diagnoses")
diagnoses = result.get("diagnoses") or []
if diagnoses:
    for dx in diagnoses:
        icd = f" ({dx['icd_code']})" if dx.get("icd_code") else ""
        conf = dx.get("confidence", "unknown")
        with st.expander(f"{dx.get('value', '—')}{icd} — confidence: `{conf}`"):
            st.caption("Source text:")
            st.markdown(f"> {dx.get('source_text', '')}")
        if conf == "low":
            st.warning(f"Low confidence: {dx.get('value')}")
else:
    st.info("No diagnoses found in this document.")

# Medications
st.subheader("Medications")
medications = result.get("medications") or []
if medications:
    for med in medications:
        conf = med.get("confidence", "unknown")
        with st.expander(f"{med.get('value', '—')} — confidence: `{conf}`"):
            st.caption("Source text:")
            st.markdown(f"> {med.get('source_text', '')}")
        if conf == "low":
            st.warning(f"Low confidence: {med.get('value')}")
else:
    st.info("No medications found in this document.")

with st.expander("Full JSON output"):
    st.json(result)

# ── 3. Policy Coverage Check ─────────────────────────────────────────────────
st.divider()
st.header("3. Policy Coverage Check")

if st.session_state.get("policy_store") is None:
    st.warning("Upload a policy document in section 1 to enable coverage determination.")
else:
    if st.button("Run policy check", type="primary"):
        with st.spinner("Evaluating coverage rules and reasoning against policy..."):
            try:
                # Structured rules evaluation
                rule_results = evaluate_rules(result, COVERAGE_RULES)

                # RAG: retrieve relevant policy chunks using the full extraction as query
                index, chunks = st.session_state["policy_store"]
                query = json.dumps(result)
                retrieved_chunks = retrieve_policy_chunks(query, index, chunks)

                # Claude Opus reasons over extraction + rules + retrieved chunks
                determination_result = reason_against_policy(result, rule_results, retrieved_chunks)

                st.session_state["determinations"][uploaded_file.name] = {
                    "determination_result": determination_result,
                    "rule_results": rule_results,
                    "retrieved_chunks": retrieved_chunks,
                }
            except Exception as e:
                st.error(f"Policy check failed: {e}")
                st.stop()

    policy_check = st.session_state.get("determinations", {}).get(uploaded_file.name)

    if policy_check:
        rule_results = policy_check["rule_results"]
        determination_result = policy_check["determination_result"]
        retrieved_chunks = policy_check["retrieved_chunks"]

        # Rule results
        st.subheader("Rule Evaluation")
        for rule in rule_results:
            icon = "✓" if rule["passed"] else "✗"
            with st.expander(f"{icon} {rule['description']}"):
                st.markdown(f"**Rule ID:** `{rule['rule_id']}`")
                st.markdown(f"**Status:** {'Pass' if rule['passed'] else 'Fail'}")
                st.markdown(f"**Reason:** {rule['reason']}")

        # Determination badge
        st.subheader("Audit Determination")
        determination = determination_result["determination"]
        if determination == "APPROVED":
            st.success(f"## {determination}")
        elif determination == "FLAGGED":
            st.warning(f"## {determination}")
        else:
            st.error(f"## {determination}")

        # Reasoning — always shown, never silent
        with st.expander("Claude's reasoning", expanded=True):
            st.markdown(determination_result["reasoning"])

        # Cited policy excerpts
        cited = determination_result.get("cited_chunks") or []
        if cited:
            with st.expander("Cited policy excerpts"):
                for i, excerpt in enumerate(cited, 1):
                    st.markdown(f"**Excerpt {i}:**")
                    st.markdown(f"> {excerpt}")

        # Debug: all retrieved policy chunks
        with st.expander("Debug: retrieved policy chunks"):
            for i, chunk in enumerate(retrieved_chunks, 1):
                st.markdown(f"**Chunk {i}:**")
                st.text(chunk)
