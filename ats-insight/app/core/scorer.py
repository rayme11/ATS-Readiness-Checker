import re
from typing import Optional

from app.models.resume_models import ParsedResume
from app.models.scoring_models import (
    CategoryScore,
    FormattingResult,
    KeywordMatchResult,
    ScoringResult,
)

# Action verbs that indicate impactful bullet points
_ACTION_VERBS = [
    "led", "built", "developed", "managed", "created", "improved",
    "increased", "reduced", "launched", "designed", "architected",
    "engineered", "delivered", "drove", "deployed", "scaled",
    "optimised", "optimized", "established", "spearheaded",
]


def calculate_score(
    resume: ParsedResume,
    formatting: FormattingResult,
    keyword_match: Optional[KeywordMatchResult] = None,
) -> ScoringResult:
    """
    Combine five category scores into a weighted 0-100 ATS readiness score.

    Weights:
      - Resume Structure    20 %
      - Parsing Safety      20 %
      - Keyword Relevance   30 %
      - Achievement Quality 15 %
      - Recruiter Readability 15 %
    """
    categories = [
        _score_structure(resume),
        _score_parsing_safety(formatting),
        _score_keyword_relevance(keyword_match),
        _score_achievement_quality(resume),
        _score_readability(resume),
    ]

    total = sum(c.score * c.weight for c in categories)

    strengths = [s for c in categories for s in c.strengths]
    weaknesses = [i for c in categories for i in c.issues]

    recommendations: list[str] = list(formatting.recommendations)
    if keyword_match:
        if keyword_match.critical_missing:
            recommendations.append(
                "Add critical missing keywords: "
                + ", ".join(keyword_match.critical_missing[:5])
            )
        if keyword_match.missing_keywords:
            recommendations.append(
                "Consider including these JD terms: "
                + ", ".join(keyword_match.missing_keywords[:5])
            )

    return ScoringResult(
        total_score=round(total, 1),
        categories=categories,
        strengths=strengths[:5],
        weaknesses=weaknesses[:5],
        recommendations=recommendations[:8],
    )


# ─────────────────────────────────────────────────────────────────────────────
# Individual category scorers
# ─────────────────────────────────────────────────────────────────────────────

def _score_structure(resume: ParsedResume) -> CategoryScore:
    score = 100.0
    issues: list[str] = []
    strengths: list[str] = []

    if not resume.contact.email:
        score -= 20
        issues.append("No email address found")
    else:
        strengths.append("Email address present")

    if not resume.contact.phone:
        score -= 10
        issues.append("No phone number found")

    if not resume.experience:
        score -= 25
        issues.append("No experience section detected")
    else:
        strengths.append("Experience section found")

    if not resume.education:
        score -= 15
        issues.append("No education section detected")
    else:
        strengths.append("Education section found")

    if not resume.skills:
        score -= 15
        issues.append("No skills section detected")
    else:
        strengths.append("Skills section found")

    if not resume.summary:
        score -= 10
        issues.append("No summary/objective section found")
    else:
        strengths.append("Summary/profile section present")

    return CategoryScore(
        name="Resume Structure",
        score=max(0.0, score),
        weight=0.20,
        strengths=strengths,
        issues=issues,
    )


def _score_parsing_safety(formatting: FormattingResult) -> CategoryScore:
    strengths = (
        ["No major ATS formatting risks found"] if not formatting.warnings else []
    )
    return CategoryScore(
        name="Parsing Safety",
        score=formatting.score,
        weight=0.20,
        strengths=strengths,
        issues=formatting.warnings[:3],
    )


def _score_keyword_relevance(
    keyword_match: Optional[KeywordMatchResult],
) -> CategoryScore:
    if keyword_match is None:
        return CategoryScore(
            name="Keyword Relevance",
            score=50.0,
            weight=0.30,
            strengths=[],
            issues=["No job description provided — keyword score set to 50"],
        )

    strengths: list[str] = []
    issues: list[str] = []

    if keyword_match.matched_keywords:
        strengths.append(
            f"{len(keyword_match.matched_keywords)} keywords matched from the JD"
        )
    if keyword_match.missing_keywords:
        issues.append(f"{len(keyword_match.missing_keywords)} JD keywords not found in resume")
    if keyword_match.critical_missing:
        issues.append(
            f"{len(keyword_match.critical_missing)} critical/required terms missing"
        )

    return CategoryScore(
        name="Keyword Relevance",
        score=keyword_match.score,
        weight=0.30,
        strengths=strengths,
        issues=issues,
    )


def _score_achievement_quality(resume: ParsedResume) -> CategoryScore:
    score = 60.0
    strengths: list[str] = []
    issues: list[str] = []

    exp_text = resume.experience or resume.raw_text

    # Metrics / numbers
    has_metrics = bool(
        re.search(
            r"\d+\s*%|\$[\d,]+|\d+x\b|\d+\s*people|\d+\s*engineers|\d+\s*team",
            exp_text,
            re.IGNORECASE,
        )
    )
    if has_metrics:
        score += 20
        strengths.append("Quantified achievements found (numbers / metrics)")
    else:
        issues.append(
            "No quantified achievements — add numbers, percentages, or dollar figures"
        )

    # Action verbs
    found_verbs = [
        v for v in _ACTION_VERBS
        if re.search(r"\b" + v + r"\b", exp_text, re.IGNORECASE)
    ]
    if len(found_verbs) >= 5:
        score += 20
        strengths.append(
            f"Strong use of action verbs ({', '.join(found_verbs[:3])}…)"
        )
    elif found_verbs:
        score += 10
        strengths.append(f"Some action verbs found ({', '.join(found_verbs[:3])})")
    else:
        issues.append("Few or no action verbs — start bullets with strong action words")

    return CategoryScore(
        name="Achievement Quality",
        score=min(100.0, score),
        weight=0.15,
        strengths=strengths,
        issues=issues,
    )


def _score_readability(resume: ParsedResume) -> CategoryScore:
    score = 100.0
    strengths: list[str] = []
    issues: list[str] = []

    # Location detection
    if re.search(r"\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)?,\s*[A-Z]{2}\b", resume.raw_text):
        strengths.append("Location detected (City, ST format)")
    else:
        score -= 15
        issues.append("No clear location found — add 'City, ST' to contact info")

    # Bullet style consistency
    bullet_types: set[str] = set()
    for line in resume.raw_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("•"):
            bullet_types.add("•")
        elif stripped.startswith("-"):
            bullet_types.add("-")
        elif stripped.startswith("*"):
            bullet_types.add("*")
        elif re.match(r"^\d+\.", stripped):
            bullet_types.add("numbered")

    if len(bullet_types) > 2:
        score -= 10
        issues.append("Inconsistent bullet styles detected — standardise to one style")
    elif bullet_types:
        strengths.append("Consistent bullet formatting")

    # Very long lines suggest multi-column extraction artefacts
    long_lines = sum(
        1 for line in resume.raw_text.splitlines() if len(line) > 200
    )
    if long_lines > 5:
        score -= 10
        issues.append(
            "Several very long lines detected — may indicate multi-column parsing issue"
        )

    return CategoryScore(
        name="Recruiter Readability",
        score=max(0.0, score),
        weight=0.15,
        strengths=strengths,
        issues=issues,
    )
