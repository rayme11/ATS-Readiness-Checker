from typing import Optional

from app.models.scoring_models import FormattingResult, KeywordMatchResult, ScoringResult


def generate_recommendations(
    scoring: ScoringResult,
    formatting: FormattingResult,
    keyword_match: Optional[KeywordMatchResult] = None,
) -> list[str]:
    """
    Build a ranked list of practical improvement recommendations.

    Priority order:
      1. Critical ATS formatting issues
      2. Missing resume sections
      3. Critical missing keywords from JD
      4. Achievement quality issues
      5. Readability improvements
    """
    recs: list[str] = []

    # 1. Formatting / parsing safety
    for cat in scoring.categories:
        if cat.name == "Parsing Safety" and cat.score < 70:
            recs.extend(formatting.recommendations[:3])

    # 2. Structural issues
    for cat in scoring.categories:
        if cat.name == "Resume Structure":
            recs.extend(cat.issues[:3])

    # 3. Critical keyword gaps
    if keyword_match and keyword_match.critical_missing:
        recs.append(
            "Add critical missing keywords: "
            + ", ".join(keyword_match.critical_missing[:5])
        )

    # 4. Achievement quality
    for cat in scoring.categories:
        if cat.name == "Achievement Quality" and cat.score < 80:
            recs.extend(cat.issues[:2])

    # 5. Readability
    for cat in scoring.categories:
        if cat.name == "Recruiter Readability" and cat.score < 80:
            recs.extend(cat.issues[:2])

    # Deduplicate while preserving priority order
    seen: set[str] = set()
    unique: list[str] = []
    for r in recs:
        if r not in seen:
            seen.add(r)
            unique.append(r)

    return unique[:10]
