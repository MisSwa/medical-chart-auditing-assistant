"""
PDF report exporter using fpdf2.

Returns PDF as bytes — no temp files written to disk.
Font: Helvetica (fpdf2 built-in). No external font dependencies.
"""
from fpdf import FPDF


def _safe(text: str) -> str:
    """Replace characters outside latin-1 to prevent fpdf2 encoding errors."""
    return str(text).encode("latin-1", errors="replace").decode("latin-1")


def _write_section_header(pdf: FPDF, title: str) -> None:
    pdf.set_font("Helvetica", style="B", size=13)
    pdf.ln(4)
    pdf.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", size=10)


def _write_subsection(pdf: FPDF, title: str) -> None:
    pdf.set_font("Helvetica", style="B", size=11)
    pdf.cell(0, 7, title, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", size=10)


def _write_field(pdf: FPDF, label: str, value: str, source: str = "") -> None:
    """Write a single labelled field with an optional source citation."""
    pdf.set_font("Helvetica", size=10)
    pdf.multi_cell(0, 6, _safe(f"{label}: {value}"))
    if source:
        pdf.set_font("Helvetica", style="I", size=9)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(0, 5, _safe(f"Source: {source}"))
        pdf.set_font("Helvetica", size=10)
        pdf.set_x(pdf.l_margin)


def export_report_to_pdf(report: dict) -> bytes:
    """
    Convert a report dict (from build_report) to PDF bytes.

    Args:
        report: dict with keys: filename, extraction, rule_results, determination,
                reasoning, cited_chunks, escalation_reason, generated_at

    Returns:
        PDF content as bytes (starts with b'%PDF').
    """
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", size=10)

    # ── Header ─────────────────────────────────────────────────────────────
    pdf.set_font("Helvetica", style="B", size=16)
    pdf.cell(0, 10, "Medical Chart Audit Report", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", size=10)
    pdf.cell(0, 6, _safe(f"Document: {report['filename']}"), new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, _safe(f"Generated: {report['generated_at']}"), new_x="LMARGIN", new_y="NEXT")

    # ── Section 1: Extracted Clinical Data ─────────────────────────────────
    _write_section_header(pdf, "Section 1 - Extracted Clinical Data")

    extraction = report.get("extraction", {})

    # Vitals
    _write_subsection(pdf, "Vitals")
    vitals = extraction.get("vitals") or {}
    has_vitals = any(v is not None for v in vitals.values())
    if has_vitals:
        for field_name, field_data in vitals.items():
            if field_data is None:
                continue
            label = field_name.replace("_", " ").title()
            value = str(field_data.get("value", "-"))
            conf = str(field_data.get("confidence", ""))
            source = (field_data.get("source_text") or "")[:120]
            _write_field(pdf, label, f"{value} (confidence: {conf})", source)
    else:
        pdf.cell(0, 6, "No vitals found.", new_x="LMARGIN", new_y="NEXT")

    # Diagnoses
    _write_subsection(pdf, "Diagnoses")
    diagnoses = extraction.get("diagnoses") or []
    if diagnoses:
        for dx in diagnoses:
            icd = f" ({dx.get('icd_code', '')})" if dx.get("icd_code") else ""
            name = f"{dx.get('value', '-')}{icd}"
            source = (dx.get("source_text") or "")[:120]
            _write_field(pdf, "Diagnosis", name, source)
    else:
        pdf.cell(0, 6, "No diagnoses found.", new_x="LMARGIN", new_y="NEXT")

    # Medications
    _write_subsection(pdf, "Medications")
    medications = extraction.get("medications") or []
    if medications:
        for med in medications:
            source = (med.get("source_text") or "")[:120]
            _write_field(pdf, "Medication", str(med.get("value", "-")), source)
    else:
        pdf.cell(0, 6, "No medications found.", new_x="LMARGIN", new_y="NEXT")

    # ── Section 2: Rule Evaluation ─────────────────────────────────────────
    _write_section_header(pdf, "Section 2 - Rule Evaluation")
    for rule in report.get("rule_results", []):
        status = "PASS" if rule.get("passed") else "FAIL"
        pdf.set_font("Helvetica", size=10)
        pdf.multi_cell(0, 6, _safe(f"[{status}] {rule.get('rule_id', '')} - {rule.get('description', '')}"))
        pdf.set_x(pdf.l_margin)
        pdf.set_font("Helvetica", style="I", size=9)
        pdf.multi_cell(0, 5, _safe(f"Reason: {rule.get('reason', '')}"))
        pdf.set_x(pdf.l_margin)
        pdf.set_font("Helvetica", size=10)

    # ── Section 3: Audit Determination ─────────────────────────────────────
    _write_section_header(pdf, "Section 3 - Audit Determination")
    pdf.set_font("Helvetica", style="B", size=12)
    pdf.cell(0, 7, _safe(f"Determination: {report.get('determination', '')}"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", size=10)

    escalation_reason = report.get("escalation_reason", "")
    if escalation_reason:
        pdf.set_font("Helvetica", style="I", size=10)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(0, 6, _safe(f"Escalation note: {escalation_reason}"))
        pdf.set_x(pdf.l_margin)
        pdf.set_font("Helvetica", size=10)

    pdf.ln(3)
    pdf.set_font("Helvetica", style="B", size=11)
    pdf.cell(0, 7, "Claude's Reasoning:", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", size=10)
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(0, 6, _safe(report.get("reasoning", "")))

    cited = report.get("cited_chunks") or []
    if cited:
        pdf.ln(3)
        pdf.set_font("Helvetica", style="B", size=11)
        pdf.cell(0, 7, "Cited Policy Excerpts:", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", size=10)
        for i, excerpt in enumerate(cited, 1):
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(0, 6, _safe(f"[{i}] {excerpt}"))

    return bytes(pdf.output())
