from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def vitals_txt_path():
    return str(FIXTURES_DIR / "fixture_vitals.txt")


@pytest.fixture
def medications_txt_path():
    return str(FIXTURES_DIR / "fixture_medications.txt")


@pytest.fixture
def policy_txt_path():
    return str(FIXTURES_DIR / "fixture_policy.txt")


@pytest.fixture
def diagnosis_pdf_path(tmp_path):
    """Generate a synthetic diagnosis-only PDF for testing using fpdf2."""
    from fpdf import FPDF

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)

    lines = [
        "CLINICAL NOTE - SYNTHETIC TEST DATA (NOT REAL PATIENT DATA)",
        "",
        "Patient: John Doe (Synthetic)",
        "Date of Visit: 2024-01-15",
        "",
        "ASSESSMENT AND PLAN:",
        "",
        "Primary Diagnosis: Type 2 Diabetes Mellitus, uncontrolled (ICD-10: E11.65)",
        "The patient presents with uncontrolled Type 2 Diabetes Mellitus as evidenced by",
        "HbA1c of 9.2% and fasting glucose of 245 mg/dL.",
        "",
        "Secondary Diagnosis: Essential Hypertension (ICD-10: I10)",
        "Patient also has a history of essential hypertension, currently managed.",
        "",
        "No vitals were recorded at this visit. No medications were reviewed.",
        "",
        "Signed: Dr. C. Test (Synthetic)",
    ]

    for line in lines:
        pdf.cell(0, 8, line, new_x="LMARGIN", new_y="NEXT")

    pdf_path = tmp_path / "fixture_diagnosis.pdf"
    pdf.output(str(pdf_path))
    return str(pdf_path)


@pytest.fixture
def scanned_pdf_path(tmp_path):
    """Generate a synthetic image-only PDF for OCR testing using fpdf2 + Pillow."""
    from fpdf import FPDF
    from PIL import Image, ImageDraw

    # Create a white image with printed text (simulates a scanned page)
    img = Image.new("RGB", (800, 400), color="white")
    draw = ImageDraw.Draw(img)
    draw.text((50, 50), "SYNTHETIC SCANNED DOCUMENT", fill="black")
    draw.text((50, 100), "Patient: Test Patient (Synthetic)", fill="black")
    draw.text((50, 150), "This is a scanned document test fixture.", fill="black")
    draw.text((50, 200), "Diagnosis: Test Condition", fill="black")

    img_path = tmp_path / "scanned_page.png"
    img.save(str(img_path))

    # Embed the image into a PDF (no text layer — image-only)
    pdf = FPDF()
    pdf.add_page()
    pdf.image(str(img_path), x=5, y=5, w=200)

    pdf_path = tmp_path / "fixture_scanned.pdf"
    pdf.output(str(pdf_path))
    return str(pdf_path)
