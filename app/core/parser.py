import io
import re
from pathlib import Path

import pdfplumber
from docx import Document


def parse_resume(file_content: bytes, file_name: str) -> str:
    """
    Extract text from a resume file.

    Supports PDF, DOCX, and TXT.
    Returns normalized plain text.
    Raises ValueError for unsupported file types.
    """
    ext = Path(file_name).suffix.lower()

    if ext == ".pdf":
        return _parse_pdf(file_content)
    elif ext == ".docx":
        return _parse_docx(file_content)
    elif ext == ".txt":
        raw = file_content.decode("utf-8", errors="ignore")
        return _normalize_text(raw)
    else:
        raise ValueError(
            f"Unsupported file type: '{ext}'. Please upload a PDF, DOCX, or TXT file."
        )


def _parse_pdf(content: bytes) -> str:
    text_parts = []
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return _normalize_text("\n".join(text_parts))


def _parse_docx(content: bytes) -> str:
    doc = Document(io.BytesIO(content))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return _normalize_text("\n".join(paragraphs))


def _normalize_text(text: str) -> str:
    """Strip extra whitespace and collapse consecutive blank lines."""
    lines = text.splitlines()
    cleaned = [line.strip() for line in lines]

    result = []
    blank_count = 0
    for line in cleaned:
        if line == "":
            blank_count += 1
            if blank_count <= 1:
                result.append(line)
        else:
            blank_count = 0
            result.append(line)

    return "\n".join(result).strip()
