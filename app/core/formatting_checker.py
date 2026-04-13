import re

from app.models.scoring_models import FormattingResult

_STANDARD_HEADINGS = ["experience", "education", "skills"]

_SYMBOL_PATTERN = re.compile(r"[■□▪▸►▶✓✔★☆✦●○◆◇→←↑↓]")

_DATE_FORMATS = [
    re.compile(r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}\b"),
    re.compile(r"\b\d{1,2}/\d{4}\b"),
    re.compile(r"\b\d{4}\s*[-–]\s*\d{4}\b"),
    re.compile(
        r"\b(January|February|March|April|May|June|July|August|"
        r"September|October|November|December)\s+\d{4}\b"
    ),
]


def check_formatting(raw_text: str) -> FormattingResult:
    """
    Inspect raw resume text for common ATS formatting risks.

    Returns a FormattingResult with score (0-100), a list of warnings,
    and corresponding recommendations.
    """
    warnings: list[str] = []
    recommendations: list[str] = []
    penalty = 0

    text_lower = raw_text.lower()

    # ── 1. Missing standard sections ────────────────────────────────────────
    for heading in _STANDARD_HEADINGS:
        if heading not in text_lower:
            warnings.append(f"Missing standard section: '{heading.title()}'")
            recommendations.append(
                f"Add a clearly labelled '{heading.title()}' section"
            )
            penalty += 10

    # ── 2. Excessive decorative symbols ─────────────────────────────────────
    symbol_matches = _SYMBOL_PATTERN.findall(raw_text)
    if len(symbol_matches) > 5:
        warnings.append(
            f"{len(symbol_matches)} special symbols detected — may confuse ATS parsers"
        )
        recommendations.append(
            "Replace decorative symbols with plain-text bullets (- or •)"
        )
        penalty += 15

    # ── 3. Multi-column layout (pipe characters as column separators) ────────
    pipe_lines = sum(1 for line in raw_text.splitlines() if "|" in line)
    if pipe_lines > 3:
        warnings.append(
            "Possible multi-column layout (pipe characters found) — ATS may scramble order"
        )
        recommendations.append("Convert to single-column layout for safer ATS parsing")
        penalty += 20

    # ── 4. Inconsistent date formats ────────────────────────────────────────
    found_formats = {i for i, pat in enumerate(_DATE_FORMATS) if pat.search(raw_text)}
    if len(found_formats) > 1:
        warnings.append("Inconsistent date formats detected across the resume")
        recommendations.append(
            "Use one consistent date format throughout (e.g. 'Jan 2022 – Mar 2024')"
        )
        penalty += 10

    # ── 5. Missing email ────────────────────────────────────────────────────
    if not re.search(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b", raw_text):
        warnings.append("No email address detected in resume")
        recommendations.append("Add a professional email address in the contact section")
        penalty += 10

    # ── 6. Missing phone number ──────────────────────────────────────────────
    if not re.search(r"\(?\d{3}\)?[\s.\-]?\d{3}[\s.\-]?\d{4}", raw_text):
        warnings.append("No phone number detected")
        recommendations.append("Add a phone number to the contact section")
        penalty += 5

    # ── 7. Heavy tab usage (possible table/column formatting) ───────────────
    tab_heavy_lines = sum(
        1 for line in raw_text.splitlines() if line.count("\t") > 2
    )
    if tab_heavy_lines > 3:
        warnings.append(
            "Heavy tab usage suggests table or column formatting — ATS may mis-parse this"
        )
        recommendations.append(
            "Remove tables and use plain-text bullet lists for better ATS compatibility"
        )
        penalty += 15

    score = max(0.0, 100.0 - penalty)

    return FormattingResult(
        score=round(score, 1),
        warnings=warnings,
        recommendations=recommendations,
    )
