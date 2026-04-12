"""
Prompt templates for AI-powered resume analysis.

Keeping prompts in one place makes it easy to iterate on them
without touching business logic.
"""

SYSTEM_PROMPT = (
    "You are an expert resume coach and ATS specialist. "
    "Your job is to provide clear, practical, actionable feedback to help job seekers "
    "improve their resumes for both ATS systems and human reviewers. "
    "Be direct, helpful, and specific. Avoid generic platitudes."
)


def build_feedback_prompt(
    resume_text: str,
    job_description: str,
    score_summary: str,
    weaknesses: list[str],
) -> str:
    """
    Build the main analysis prompt.

    resume_text     – extracted plain text of the resume (capped at 3 000 chars)
    job_description – pasted JD text, optional (capped at 2 000 chars)
    score_summary   – e.g. "74/100"
    weaknesses      – list of rule-based issues already identified
    """
    jd_section = (
        f"\n\nJOB DESCRIPTION:\n{job_description[:2000]}"
        if job_description.strip()
        else ""
    )
    weaknesses_str = (
        "\n".join(f"- {w}" for w in weaknesses) if weaknesses else "None identified"
    )

    return f"""Analyze this resume and provide specific improvement suggestions.

RESUME TEXT:
{resume_text[:3000]}{jd_section}

CURRENT RULE-BASED SCORE: {score_summary}

IDENTIFIED WEAKNESSES:
{weaknesses_str}

Please provide:
1. 3-5 specific, actionable improvements the candidate should make immediately
2. One honest paragraph about this resume's current ATS readiness
3. If a job description was provided, 2-3 suggestions for better keyword alignment

Keep your response concise and practical. Focus on what will have the most impact."""


def build_summary_rewrite_prompt(
    current_summary: str,
    job_description: str = "",
) -> str:
    """Prompt for rewriting a resume summary/objective section."""
    jd_section = (
        f"\n\nTarget role context (from JD):\n{job_description[:1000]}"
        if job_description.strip()
        else ""
    )

    return f"""Rewrite the following resume summary to be more impactful, ATS-friendly, and compelling.

CURRENT SUMMARY:
{current_summary}{jd_section}

Requirements:
- 3-4 sentences maximum
- Include relevant keywords naturally
- Lead with the candidate's strongest value proposition
- Be specific, not generic

Provide only the rewritten summary text, nothing else."""
