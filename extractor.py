import re
from pathlib import Path

import pdfplumber
import pytesseract
from PIL import Image


def extract_text_from_pdf(filepath: str) -> str:
    """Extract text from a text-native PDF, page by page."""
    text_parts = []
    with pdfplumber.open(filepath) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n\n".join(text_parts)


def extract_text_from_txt(filepath: str) -> str:
    """Read plain text or EHR text export."""
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def is_scanned_pdf(filepath: str) -> bool:
    """
    Detect scanned (image-based) PDFs.
    Returns True if pdfplumber extracts fewer than 20 characters total across all pages.
    """
    total_chars = 0
    with pdfplumber.open(filepath) as pdf:
        for page in pdf.pages:
            total_chars += len(page.extract_text() or "")
    return total_chars < 20


def extract_text_from_scanned_pdf(filepath: str) -> str:
    """
    OCR a scanned PDF by rendering each page to an image and running pytesseract.

    Pre-processes with Pillow: converts to grayscale and applies a threshold for clarity.
    Requires the Tesseract binary to be installed (brew install tesseract on macOS).
    """
    text_parts = []
    with pdfplumber.open(filepath) as pdf:
        for page in pdf.pages:
            page_image = page.to_image(resolution=300)
            pil_image: Image.Image = page_image.original
            pil_image = pil_image.convert("L")
            pil_image = pil_image.point(lambda x: 255 if x > 128 else 0)
            text = pytesseract.image_to_string(pil_image)
            if text.strip():
                text_parts.append(text)
    return "\n\n".join(text_parts)


def normalize_text(text: str) -> str:
    """Strip excessive whitespace and normalize line breaks."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.strip()
    # Collapse runs of 3+ blank lines to at most 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Strip trailing whitespace from each line
    lines = [line.rstrip() for line in text.split("\n")]
    return "\n".join(lines)


def extract_text(filepath: str) -> str:
    """Detect format, extract text, and normalize. Raises ValueError for unsupported types."""
    suffix = Path(filepath).suffix.lower()
    if suffix == ".pdf":
        if is_scanned_pdf(filepath):
            raw = extract_text_from_scanned_pdf(filepath)
        else:
            raw = extract_text_from_pdf(filepath)
    elif suffix in (".txt", ".text"):
        raw = extract_text_from_txt(filepath)
    else:
        raise ValueError(f"Unsupported file type: {suffix}. Supported types: .pdf, .txt")
    return normalize_text(raw)
