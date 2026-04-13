import re
from typing import List, Tuple

from app.models.resume_models import ParsedResume, ResumeContact, ResumeSection

# Maps canonical section keys to common heading aliases
SECTION_HEADINGS: dict[str, list[str]] = {
    "summary": [
        "summary", "objective", "profile", "about me",
        "professional summary", "career summary", "overview",
    ],
    "experience": [
        "experience", "work experience", "employment history",
        "work history", "professional experience", "employment",
    ],
    "skills": [
        "skills", "technical skills", "core competencies",
        "competencies", "expertise", "key skills", "technologies",
    ],
    "education": [
        "education", "academic background", "qualifications",
        "academic qualifications", "academics",
    ],
    "certifications": [
        "certifications", "certificates", "licenses", "credentials",
        "professional development",
    ],
    "languages": ["languages", "language skills"],
}

# Any line that is ALL-CAPS (or Title Case) and short is likely a heading
_HEADING_PATTERN = re.compile(r"^[A-Z][A-Z\s&/\-]{2,50}$")


def extract_sections(raw_text: str, file_type: str = "unknown") -> ParsedResume:
    """
    Parse raw resume text into a structured ParsedResume.

    Heuristically splits text into sections using common heading names
    and ALL-CAPS line detection.
    """
    lines = raw_text.splitlines()
    raw_sections = _split_into_sections(lines)

    resume = ParsedResume(raw_text=raw_text, file_type=file_type)
    resume.sections = [ResumeSection(heading=h, content=c) for h, c in raw_sections]

    for heading, content in raw_sections:
        normalized = heading.lower().strip()
        for key, aliases in SECTION_HEADINGS.items():
            if any(normalized == alias or normalized.startswith(alias) for alias in aliases):
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
    return resume


def _split_into_sections(lines: List[str]) -> List[Tuple[str, str]]:
    """
    Walk lines and yield (heading, body_text) pairs.

    A line is treated as a heading when:
      - it matches the ALL-CAPS pattern, OR
      - it matches a known section alias (case-insensitive) within ±5 chars
    """
    sections: List[Tuple[str, str]] = []
    current_heading = "header"
    current_lines: List[str] = []

    all_aliases = [alias for aliases in SECTION_HEADINGS.values() for alias in aliases]

    for line in lines:
        stripped = line.strip()

        if not stripped:
            current_lines.append("")
            continue

        is_all_caps_heading = bool(_HEADING_PATTERN.match(stripped)) and len(stripped) < 60
        is_known_heading = any(
            stripped.lower() == alias or stripped.lower().startswith(alias)
            for alias in all_aliases
            if abs(len(stripped) - len(alias)) <= 8
        )

        if (is_all_caps_heading or is_known_heading) and len(stripped) < 60:
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
