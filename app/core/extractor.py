import logging
import re
from typing import List, Optional, Tuple

from app.models.resume_models import ParsedResume, ResumeContact, ResumeSection

logger = logging.getLogger(__name__)

# Maps canonical section keys to common heading aliases (lowercase, no trailing spaces)
SECTION_HEADINGS: dict[str, list[str]] = {
    "summary": [
        "summary", "objective", "profile", "about me",
        "professional summary", "career summary", "overview",
        "executive summary", "career objective", "professional profile",
        "personal statement", "professional overview", "career profile",
        "about", "introduction", "bio",
    ],
    "experience": [
        "experience", "work experience", "employment history",
        "work history", "professional experience", "employment",
        "additional professional experience", "additional experience",
        "career history", "relevant experience", "work background",
        "professional background", "positions held", "experience & achievements",
        "core experience", "experience highlights",
    ],
    "skills": [
        "skills", "technical skills", "core competencies",
        "competencies", "expertise", "key skills", "technologies",
        "technical expertise", "tools", "technologies used",
        "core skills", "skill set", "skills & expertise",
        "areas of expertise", "skill summary", "technology stack",
        "core leadership", "leadership skills", "soft skills",
        "hard skills", "languages & technologies",
    ],
    "education": [
        "education", "academic background", "qualifications",
        "academic qualifications", "academics", "training",
        "academic history", "educational background",
        "education & training", "education & certifications",
        "degrees", "schooling",
    ],
    "certifications": [
        "certifications", "certificates", "licenses", "credentials",
        "professional development", "certifications & licenses",
        "awards & certifications", "training & certifications",
        "professional certifications",
    ],
    "languages": ["languages", "language skills", "spoken languages"],
    "projects": [
        "projects", "personal projects", "open source", "portfolio",
        "side projects", "notable projects",
    ],
    "awards": [
        "awards", "honors", "achievements", "accomplishments",
        "recognition", "awards & honors",
    ],
    "volunteer": [
        "volunteer", "volunteering", "community", "community involvement",
        "volunteer work", "community service",
    ],
}

# ALL-CAPS heading pattern (e.g. "PROFESSIONAL EXPERIENCE", "EDUCATION & CERTIFICATIONS")
_HEADING_PATTERN = re.compile(r"^[A-Z][A-Z0-9\s&/\-\.]{1,60}$")

# Title Case heading pattern (e.g. "Work Experience", "Professional Summary")
_TITLE_CASE_PATTERN = re.compile(r"^[A-Z][a-z]+(?:[\s&/\-]+[A-Z][a-z0-9]+){0,6}$")

# Flat alias set for fast O(1) lookup (populated below)
_ALL_ALIASES: set[str] = {
    alias
    for aliases in SECTION_HEADINGS.values()
    for alias in aliases
}


def _is_heading(stripped: str) -> bool:
    """
    Return True if *stripped* looks like a section heading.

    Checks:
    1. Exact or prefix match against known aliases (case-insensitive, generous tolerance)
    2. ALL-CAPS pattern match (short enough to be a heading, not a sentence)
    3. Title Case pattern match against known aliases
    """
    if not stripped or len(stripped) > 65:
        return False

    lower = stripped.lower()

    # 1. Known alias — exact or "starts with alias + space/&"
    for alias in _ALL_ALIASES:
        if lower == alias:
            return True
        # Allow heading to be longer than alias (e.g. "ADDITIONAL PROFESSIONAL EXPERIENCE")
        if lower.startswith(alias) and len(lower) - len(alias) <= 20:
            return True

    # 2. ALL-CAPS pattern (whole line is uppercase letters, spaces, &, /, -)
    if _HEADING_PATTERN.match(stripped) and len(stripped.split()) <= 8:
        return True

    # 3. Title Case pattern against known aliases
    if _TITLE_CASE_PATTERN.match(stripped):
        if any(lower == alias or lower.startswith(alias) for alias in _ALL_ALIASES):
            return True

    return False


def _try_split_inline_heading(
    line: str,
) -> Optional[Tuple[str, str]]:
    """
    Detect multi-column bleed like "MARKO WORK EXPERIENCE" or
    "EDUCATION Validated automation..."

    If the line starts with a known heading phrase followed by extra content,
    return (heading_part, remainder). Otherwise return None.
    """
    stripped = line.strip()
    words = stripped.split()
    if len(words) < 2:
        return None

    # Never split a line that is already a fully known heading alias
    lower = stripped.lower()
    if lower in _ALL_ALIASES:
        return None

    # Try longest-first so "PROFESSIONAL EXPERIENCE" wins over "EXPERIENCE"
    best: Optional[Tuple[str, str]] = None
    best_len = 0

    for alias in sorted(_ALL_ALIASES, key=len, reverse=True):
        alias_words = alias.split()
        n = len(alias_words)
        if n >= len(words):
            continue
        candidate = " ".join(words[:n]).lower()
        if candidate == alias:
            remainder = " ".join(words[n:])
            # Accept the split when the remainder is either body text or another heading.
            # Reject only if there is no meaningful remainder.
            if len(remainder) > 2:
                if n > best_len:
                    best = (" ".join(words[:n]), remainder)
                    best_len = n

    return best


def extract_sections(raw_text: str, file_type: str = "unknown") -> ParsedResume:
    """
    Parse raw resume text into a structured ParsedResume.

    Heuristically splits text into sections using common heading names
    and ALL-CAPS / Title Case line detection.
    """
    lines = raw_text.splitlines()
    lines = _preprocess_lines(lines)
    raw_sections = _split_into_sections(lines)

    logger.info(
        "[Extractor] Detected %d section(s): %s",
        len(raw_sections),
        [h for h, _ in raw_sections],
    )

    resume = ParsedResume(raw_text=raw_text, file_type=file_type)
    resume.sections = [ResumeSection(heading=h, content=c) for h, c in raw_sections]

    for heading, content in raw_sections:
        normalized = heading.lower().strip()
        for key, aliases in SECTION_HEADINGS.items():
            if any(normalized == alias or normalized.startswith(alias) for alias in aliases):
                logger.debug("[Extractor] Mapped heading '%s' → '%s'", heading, key)
                if key == "summary":
                    resume.summary = content
                elif key == "experience":
                    resume.experience = content
                elif key == "skills":
                    resume.skills = content
                elif key == "education":
                    resume.education = content
                elif key == "certifications":
                    resume.certifications = content
                elif key == "languages":
                    resume.languages = content
                break

    resume.contact = _extract_contact(raw_text)
    logger.info(
        "[Extractor] Populated fields — summary:%s experience:%s skills:%s education:%s",
        bool(resume.summary),
        bool(resume.experience),
        bool(resume.skills),
        bool(resume.education),
    )
    return resume


def _preprocess_lines(lines: List[str]) -> List[str]:
    """
    Fix two common multi-column PDF artefacts before section splitting:

    1. Cross-line heading merge: consecutive short ALL-CAPS lines that together
       form a known heading (e.g. "EDUCATION &" + "CERTIFICATIONS").
    2. Inline heading split: a line that starts with a known heading phrase
       followed by unrelated content (e.g. "EDUCATION Validated automation...").
    """
    # Pass 1 — merge two consecutive lines into one heading if result is known
    merged: List[str] = []
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        if (
            i + 1 < len(lines)
            and stripped
            and re.match(r"^[A-Z][A-Z\s&/\-]{1,30}$", stripped)
            and not stripped.endswith((".", ",", ";"))
        ):
            next_stripped = lines[i + 1].strip()
            combined = stripped + " " + next_stripped
            # Merge when the combined line is a known heading and the partial line
            # alone is NOT a standalone known alias (avoids merging valid adjacent headings).
            partial_is_standalone_alias = stripped.lower() in _ALL_ALIASES
            if _is_heading(combined) and not partial_is_standalone_alias:
                merged.append(combined)
                i += 2
                continue
        merged.append(lines[i])
        i += 1

    # Pass 2 — split inline headings ("HEADING extra content → two lines")
    result: List[str] = []
    for line in merged:
        split = _try_split_inline_heading(line)
        if split:
            heading_part, remainder = split
            logger.debug(
                "[Extractor] Split inline heading: '%s' | '%s'", heading_part, remainder
            )
            result.append(heading_part)
            result.append(remainder)
        else:
            result.append(line)

    return result


def _split_into_sections(lines: List[str]) -> List[Tuple[str, str]]:
    """
    Walk lines and yield (heading, body_text) pairs.

    A line is treated as a heading when _is_heading() returns True.
    """
    sections: List[Tuple[str, str]] = []
    current_heading = "header"
    current_lines: List[str] = []

    for line in lines:
        stripped = line.strip()

        if not stripped:
            current_lines.append("")
            continue

        if _is_heading(stripped):
            body = "\n".join(current_lines).strip()
            if body:
                sections.append((current_heading, body))
            current_heading = stripped
            current_lines = []
        else:
            current_lines.append(line)

    # Flush last section
    body = "\n".join(current_lines).strip()
    if body:
        sections.append((current_heading, body))

    return sections


def _extract_contact(text: str) -> ResumeContact:
    """Extract contact info from raw text using regex heuristics."""
    contact = ResumeContact()

    # Email
    email_match = re.search(
        r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b", text
    )
    if email_match:
        contact.email = email_match.group()

    # Phone – basic North American patterns
    phone_match = re.search(
        r"(\+?1[\s.\-]?)?\(?\d{3}\)?[\s.\-]?\d{3}[\s.\-]?\d{4}", text
    )
    if phone_match:
        contact.phone = phone_match.group().strip()

    # LinkedIn
    linkedin_match = re.search(r"linkedin\.com/in/[\w\-]+", text, re.IGNORECASE)
    if linkedin_match:
        contact.linkedin = linkedin_match.group()

    # Location – "City, ST" or "City, State"
    location_match = re.search(r"\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)?,\s*[A-Z]{2}\b", text)
    if location_match:
        contact.location = location_match.group()

    # Name – assume first non-empty, non-email, non-phone line
    for line in text.strip().splitlines():
        line = line.strip()
        if line and len(line) < 60 and not re.search(r"[@\d|/\\]", line):
            contact.name = line
            break

    return contact
