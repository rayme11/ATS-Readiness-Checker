import re
from typing import Set

from app.models.scoring_models import KeywordMatchResult

# Words that carry no signal for keyword matching
_STOP_WORDS: Set[str] = {
    # Articles / conjunctions / prepositions
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "will", "would",
    "shall", "should", "may", "might", "must", "can", "could", "not",
    # Pronouns / determiners
    "we", "you", "they", "he", "she", "it", "i", "my", "your", "our",
    "their", "this", "that", "these", "those", "as", "about", "which",
    "who", "whom",
    # Generic connectives / modifiers
    "also", "well", "both", "new", "other", "more", "etc",
    "highly", "hands", "fast", "key", "core", "deep", "great", "clear",
    # Resume / JD boilerplate — these aren't skills
    "work", "experience", "skills", "ability", "including",
    "strong", "excellent", "good", "team", "environment", "using", "use",
    "need", "needs", "required", "requirement", "requirements",
    "necessary", "preferred", "desired", "seeking", "looking",
    "role", "position", "job", "company", "candidate", "ideal",
    "responsibilities", "qualifications", "description",
    "bonus", "plus", "ideally", "passion", "passionate",
    "responsible", "day", "days", "year", "years", "month", "months",
    "business", "product", "products", "service", "services",
    "support", "focus", "apply", "please", "join", "help",
    "make", "ensure", "maintain", "provide",
    "solutions", "solution", "implement", "implementation",
}

# Phrases in the JD that signal a required skill/qualification
_CRITICAL_INDICATORS = [
    "required", "must have", "must-have", "essential", "minimum",
    "years of experience", "proficiency in", "expertise in", "knowledge of",
    "mandatory", "necessary",
]


def match_keywords(resume_text: str, jd_text: str) -> KeywordMatchResult:
    """
    Compare resume keywords against a job description.

    Returns matched keywords, missing keywords, critical missing terms,
    and a weighted score (0-100).
    """
    resume_terms = _extract_terms(resume_text)
    jd_terms = _extract_terms(jd_text)

    if not jd_terms:
        return KeywordMatchResult(score=50.0)

    matched = sorted(resume_terms & jd_terms)
    missing = sorted(jd_terms - resume_terms)

    critical = _find_critical_terms(jd_text, missing)

    # ── Scoring ──────────────────────────────────────────────────────────────
    # Use ONLY single-word JD terms as the denominator.  Including every
    # two-word phrase in the denominator inflates it by 2-3× and makes even
    # very relevant resumes score near 0 on a long job description.
    jd_singles = {t for t in jd_terms if " " not in t}
    matched_singles = {t for t in matched if " " not in t}
    matched_phrases = [t for t in matched if " " in t]

    if not jd_singles:
        return KeywordMatchResult(score=50.0)

    # Base: % of JD keywords (single words) found in resume
    base_score = len(matched_singles) / len(jd_singles) * 100
    # Bonus: every matched multi-word skill phrase is worth extra weight
    phrase_bonus = min(len(matched_phrases) * 5, 20)
    # Penalty: missing critical/mandatory terms (capped lower to avoid 0-floor)
    critical_penalty = min(len(critical) * 5, 20)

    score = max(0.0, min(100.0, base_score + phrase_bonus - critical_penalty))

    return KeywordMatchResult(
        matched_keywords=matched,
        missing_keywords=missing[:20],   # cap for readability
        critical_missing=critical[:10],
        score=round(score, 1),
    )


def _extract_terms(text: str) -> Set[str]:
    """Extract meaningful single words and two-word phrases from text."""
    text_lower = text.lower()

    # Single words: letters/numbers only (allows things like "c++", "node.js").
    # Minimum length 2 so short but important terms like "js", "ai", "ml",
    # "qa", "ui", "ux" are included; stop words handle common 2-char noise.
    words = re.findall(r"\b[a-z][a-z0-9+#.\-]{1,30}\b", text_lower)
    singles = {w for w in words if w not in _STOP_WORDS and len(w) >= 2}

    # Two-word skill phrases (e.g. "machine learning", "ci cd", "rest api")
    phrase_re = re.compile(
        r"\b([a-z][a-z0-9+#.\-]{1,20})\s+([a-z][a-z0-9+#.\-]{1,20})\b"
    )
    phrases: Set[str] = set()
    for m in phrase_re.finditer(text_lower):
        w1, w2 = m.group(1), m.group(2)
        if w1 not in _STOP_WORDS and w2 not in _STOP_WORDS:
            phrases.add(f"{w1} {w2}")

    return singles | phrases


def _find_critical_terms(jd_text: str, missing_terms: list[str]) -> list[str]:
    """
    Return the subset of missing_terms that appear near mandatory-language
    phrases in the job description (within ±150 characters of the term).
    """
    jd_lower = jd_text.lower()
    critical: list[str] = []

    for term in missing_terms:
        idx = jd_lower.find(term)
        if idx == -1:
            continue
        context = jd_lower[max(0, idx - 150) : idx + 150]
        if any(indicator in context for indicator in _CRITICAL_INDICATORS):
            critical.append(term)

    return critical
