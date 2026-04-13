"""
High-level AI feedback functions.

These functions accept a provider name and arbitrary keyword arguments
(api_key, model, etc.) so the caller never needs to import a specific
client class directly.
"""

import logging

from app.ai.llm_client import get_llm_client
from app.ai.prompts import (
    SYSTEM_PROMPT,
    build_feedback_prompt,
    build_summary_rewrite_prompt,
)
from app.models.resume_models import ParsedResume
from app.models.scoring_models import ScoringResult

logger = logging.getLogger(__name__)

_NO_AI_MSG = (
    "AI feedback is not available. "
    "Enable Ollama or enter an OpenAI API key in the AI Settings tab."
)


def get_ai_feedback(
    resume: ParsedResume,
    scoring: ScoringResult,
    job_description: str = "",
    provider: str = "none",
    **client_kwargs,
) -> str:
    """
    Return AI-generated feedback for the resume.

    Falls back to a friendly message when no AI provider is configured
    or an error occurs.
    """
    client = get_llm_client(provider, **client_kwargs)
    if client is None:
        logger.info("[AI] No provider configured (provider=%r) — skipping AI feedback", provider)
        return _NO_AI_MSG

    prompt = build_feedback_prompt(
        resume_text=resume.raw_text,
        job_description=job_description,
        score_summary=f"{scoring.total_score}/100",
        weaknesses=scoring.weaknesses,
    )

    logger.info("[AI] Requesting feedback via provider=%r", provider)
    try:
        result = client.chat(prompt=prompt, system=SYSTEM_PROMPT)
        logger.info("[AI] Feedback received successfully")
        return result
    except Exception as exc:
        logger.error("[AI] Feedback request failed: %s", exc)
        return f"AI feedback unavailable: {exc}"


def get_summary_rewrite(
    current_summary: str,
    job_description: str = "",
    provider: str = "none",
    **client_kwargs,
) -> str:
    """
    Return an AI-rewritten version of the resume summary section.
    """
    client = get_llm_client(provider, **client_kwargs)
    if client is None:
        logger.info("[AI] No provider configured — skipping summary rewrite")
        return _NO_AI_MSG

    prompt = build_summary_rewrite_prompt(current_summary, job_description)

    logger.info("[AI] Requesting summary rewrite via provider=%r", provider)
    try:
        result = client.chat(prompt=prompt, system=SYSTEM_PROMPT)
        logger.info("[AI] Summary rewrite received successfully")
        return result
    except Exception as exc:
        logger.error("[AI] Summary rewrite failed: %s", exc)
        return f"Could not generate rewrite: {exc}"
