import pytest

from app.core.parser import _normalize_text, parse_resume


def test_normalize_strips_leading_trailing_whitespace():
    result = _normalize_text("  Hello World  ")
    assert result == "Hello World"


def test_normalize_collapses_consecutive_blank_lines():
    text = "Line 1\n\n\n\nLine 2"
    result = _normalize_text(text)
    assert "\n\n\n" not in result
    assert "Line 1" in result
    assert "Line 2" in result


def test_parse_txt_file():
    content = b"Jane Smith\njane@example.com\n\nEXPERIENCE\nSoftware Engineer at Acme"
    result = parse_resume(content, "resume.txt")
    assert "Jane Smith" in result
    assert "EXPERIENCE" in result
    assert "jane@example.com" in result


def test_parse_unsupported_extension_raises():
    with pytest.raises(ValueError, match="Unsupported file type"):
        parse_resume(b"data", "resume.pages")


def test_parse_txt_strips_extra_blank_lines():
    content = b"Line 1\n\n\n\n\nLine 2"
    result = parse_resume(content, "resume.txt")
    assert "\n\n\n" not in result
