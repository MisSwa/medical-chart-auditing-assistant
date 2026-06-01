import pytest

from extractor import (
    extract_text,
    extract_text_from_pdf,
    extract_text_from_scanned_pdf,
    extract_text_from_txt,
    is_scanned_pdf,
    normalize_text,
)


def test_txt_extraction_returns_text(vitals_txt_path):
    text = extract_text_from_txt(vitals_txt_path)
    assert isinstance(text, str)
    assert len(text) > 0


def test_pdf_extraction_returns_text(diagnosis_pdf_path):
    text = extract_text_from_pdf(diagnosis_pdf_path)
    assert isinstance(text, str)
    assert len(text) > 0


def test_format_detection_routes_correctly(vitals_txt_path, diagnosis_pdf_path):
    txt_result = extract_text(vitals_txt_path)
    assert isinstance(txt_result, str) and len(txt_result) > 0

    pdf_result = extract_text(diagnosis_pdf_path)
    assert isinstance(pdf_result, str) and len(pdf_result) > 0


def test_format_detection_raises_on_unsupported(tmp_path):
    unsupported = tmp_path / "test.docx"
    unsupported.write_bytes(b"fake content")
    with pytest.raises(ValueError, match="Unsupported file type"):
        extract_text(str(unsupported))


def test_normalization_strips_whitespace():
    raw = "  hello world  \n\n\n\n\nmore text  "
    result = normalize_text(raw)
    assert not result.startswith(" ")
    assert not result.endswith(" ")
    assert "\n\n\n" not in result


def test_normalization_strips_trailing_line_whitespace():
    raw = "line one   \nline two   "
    result = normalize_text(raw)
    for line in result.split("\n"):
        assert not line.endswith(" "), f"Line has trailing whitespace: {repr(line)}"


# ── OCR / scanned PDF tests ──────────────────────────────────────────────────


def test_is_scanned_pdf_returns_true_for_image_pdf(scanned_pdf_path):
    assert is_scanned_pdf(scanned_pdf_path) is True


def test_is_scanned_pdf_returns_false_for_text_pdf(diagnosis_pdf_path):
    assert is_scanned_pdf(diagnosis_pdf_path) is False


def test_scanned_pdf_extraction_returns_text(scanned_pdf_path):
    import shutil

    if shutil.which("tesseract") is None:
        pytest.skip("Tesseract binary not installed — run `brew install tesseract` to enable OCR tests")
    text = extract_text_from_scanned_pdf(scanned_pdf_path)
    assert isinstance(text, str)
    assert len(text) > 0
