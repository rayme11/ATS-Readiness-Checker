import io
import logging
import re
from pathlib import Path
from typing import List

import pdfplumber
from docx import Document

logger = logging.getLogger(__name__)


def parse_resume(file_content: bytes, file_name: str) -> str:
    """
    Extract text from a resume file.

    Supports PDF, DOCX, and TXT.
    Returns normalized plain text.
    Raises ValueError for unsupported file types.
    """
    ext = Path(file_name).suffix.lower()
    logger.info("[Parser] Parsing file: %s (type: %s)", file_name, ext)

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
    """
    Extract text from a PDF, using column-aware layout analysis.

    Multi-column resumes (common in modern templates) are handled
    by grouping words into left/right columns based on x-position,
    then interleaving them in reading order (top-to-bottom per column).
    Falls back to standard extract_text if layout analysis fails.
    """
    text_parts = []
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        logger.info("[Parser] PDF has %d page(s)", len(pdf.pages))
        for page_num, page in enumerate(pdf.pages, 1):
            page_text = _extract_page_text(page, page_num)
            if page_text:
                text_parts.append(page_text)

    full_text = _normalize_text("\n".join(text_parts))
    logger.info("[Parser] Extracted %d characters total", len(full_text))
    return full_text


def _extract_page_text(page, page_num: int) -> str:
    """
    Extract text from a single PDF page using column-aware analysis.

    Detects two-column layouts by clustering word x-positions.
    If a two-column layout is found, each column is extracted separately
    and concatenated so section headings don't bleed into each other.
    """
    try:
        words = page.extract_words(
            x_tolerance=3,
            y_tolerance=3,
            keep_blank_chars=False,
            use_text_flow=False,
        )
    except Exception as exc:
        logger.warning("[Parser] Page %d: word extraction failed (%s), using fallback", page_num, exc)
        return page.extract_text() or ""

    if not words:
        return ""

    page_width = float(page.width)
    mid = page_width / 2

    # Detect whether this page has two distinct x-position clusters
    left_words = [w for w in words if float(w["x0"]) < mid - page_width * 0.05]
    right_words = [w for w in words if float(w["x0"]) >= mid + page_width * 0.05]

    # If both sides have substantial content, treat as two-column layout
    if len(left_words) > 10 and len(right_words) > 10:
        logger.info(
            "[Parser] Page %d: two-column layout detected (%d left words, %d right words)",
            page_num, len(left_words), len(right_words),
        )
        left_text = _words_to_text(left_words)
        right_text = _words_to_text(right_words)
        return left_text + "\n" + right_text

    # Single column — fall back to standard extraction (better hyphenation)
    fallback = page.extract_text() or ""
    logger.info("[Parser] Page %d: single-column layout, %d chars", page_num, len(fallback))
    return fallback


def _words_to_text(words: List[dict]) -> str:
    """Reconstruct lines from a list of pdfplumber word dicts sorted by y then x."""
    if not words:
        return ""
    # Sort top-to-bottom, left-to-right
    words = sorted(words, key=lambda w: (round(float(w["top"]) / 4) * 4, float(w["x0"])))

    lines: List[str] = []
    current_y = None
    current_line: List[str] = []

    for word in words:
        y = round(float(word["top"]) / 4) * 4  # bucket into 4-pt rows
        if current_y is None or abs(y - current_y) > 6:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word["text"]]
            current_y = y
        else:
            current_line.append(word["text"])

    if current_line:
        lines.append(" ".join(current_line))

    return "\n".join(lines)


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
