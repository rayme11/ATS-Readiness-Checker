"""
ATS Insight — main Streamlit entry point.

Run with:
    streamlit run app/main.py
"""

import os
import sys

# Ensure the project root is importable as a package root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

from app.ai.ai_feedback import get_ai_feedback
from app.core.extractor import extract_sections
from app.core.formatting_checker import check_formatting
from app.core.keyword_matcher import match_keywords
from app.core.parser import parse_resume
from app.core.recommendations import generate_recommendations
from app.core.scorer import calculate_score
from app.ui.results_page import render_results
from app.ui.settings_page import render_settings
from app.ui.upload_page import render_upload

st.set_page_config(
    page_title="ATS Insight",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def _init_session_state() -> None:
    defaults = {
        "ai_provider": "none",
        "ollama_base_url": "http://localhost:11434",
        "ollama_model": "llama3",
        "openai_model": "gpt-4o-mini",
        "groq_model": "llama3-8b-8192",
        "anthropic_model": "claude-3-haiku-20240307",
        "jd_text": "",
        "uploaded_file": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def main() -> None:
    _init_session_state()

    st.title("📄 ATS Insight")
    st.markdown(
        "*Open-source resume ATS readiness analyzer — "
        "free rule-based scoring with optional local or cloud AI.*"
    )

    tab_analyze, tab_settings = st.tabs(["🔍 Analyze Resume", "⚙️ AI Settings"])

    with tab_settings:
        render_settings()

    with tab_analyze:
        analyze_clicked = render_upload()

        if analyze_clicked:
            _run_analysis()


def _run_analysis() -> None:
    """Execute the full analysis pipeline and display results."""
    uploaded_file = st.session_state.get("uploaded_file")
    jd_text: str = st.session_state.get("jd_text", "")

    if not uploaded_file:
        st.error("Please upload a resume file first.")
        return

    with st.spinner("Parsing and analysing your resume…"):
        try:
            # ── Step 1: Parse file ───────────────────────────────────────────
            file_bytes = uploaded_file.read()
            raw_text = parse_resume(file_bytes, uploaded_file.name)

            if not raw_text.strip():
                st.error(
                    "Could not extract any text from this file. "
                    "Try saving it as plain PDF or DOCX."
                )
                return

            # ── Step 2: Extract sections ─────────────────────────────────────
            file_ext = uploaded_file.name.rsplit(".", 1)[-1].lower()
            resume = extract_sections(raw_text, file_type=file_ext)

            # ── Step 3: Formatting check ─────────────────────────────────────
            formatting = check_formatting(raw_text)

            # ── Step 4: Keyword matching ─────────────────────────────────────
            keyword_match = None
            if jd_text.strip():
                keyword_match = match_keywords(raw_text, jd_text)

            # ── Step 5: Score ────────────────────────────────────────────────
            scoring = calculate_score(resume, formatting, keyword_match)

            # ── Step 6: Recommendations ───────────────────────────────────────
            scoring.recommendations = generate_recommendations(
                scoring, formatting, keyword_match
            )

        except ValueError as exc:
            st.error(str(exc))
            return
        except Exception as exc:
            st.error(f"Unexpected error during analysis: {exc}")
            return

    # ── Step 7: Optional AI feedback ─────────────────────────────────────────
    ai_feedback = None
    provider = st.session_state.get("ai_provider", "none")

    if provider == "ollama":
        with st.spinner(
            f"Getting AI feedback from Ollama "
            f"({st.session_state.get('ollama_model', 'llama3')})…"
        ):
            ai_feedback = get_ai_feedback(
                resume=resume,
                scoring=scoring,
                job_description=jd_text,
                provider="ollama",
                ollama_base_url=st.session_state.get("ollama_base_url"),
                ollama_model=st.session_state.get("ollama_model", "llama3"),
            )

    elif provider == "openai":
        api_key = st.session_state.get("openai_api_key", "")
        if api_key:
            with st.spinner("Getting AI feedback from OpenAI…"):
                ai_feedback = get_ai_feedback(
                    resume=resume,
                    scoring=scoring,
                    job_description=jd_text,
                    provider="openai",
                    openai_api_key=api_key,
                    openai_model=st.session_state.get("openai_model", "gpt-4o-mini"),
                )
        else:
            st.warning(
                "OpenAI is selected but no API key has been entered. "
                "Add one in the **AI Settings** tab."
            )
    elif provider == "groq":
        api_key = st.session_state.get("groq_api_key", "")
        if api_key:
            with st.spinner(
                f"Getting AI feedback from Groq "
                f"({st.session_state.get('groq_model', 'llama3-8b-8192')})…"
            ):
                ai_feedback = get_ai_feedback(
                    resume=resume,
                    scoring=scoring,
                    job_description=jd_text,
                    provider="groq",
                    groq_api_key=api_key,
                    groq_model=st.session_state.get("groq_model", "llama3-8b-8192"),
                )
        else:
            st.warning(
                "Groq is selected but no API key has been entered. "
                "Add one in the **AI Settings** tab."
            )

    elif provider == "anthropic":
        api_key = st.session_state.get("anthropic_api_key", "")
        if api_key:
            with st.spinner(
                f"Getting AI feedback from Anthropic Claude "
                f"({st.session_state.get('anthropic_model', 'claude-3-haiku-20240307')})…"
            ):
                ai_feedback = get_ai_feedback(
                    resume=resume,
                    scoring=scoring,
                    job_description=jd_text,
                    provider="anthropic",
                    anthropic_api_key=api_key,
                    anthropic_model=st.session_state.get(
                        "anthropic_model", "claude-3-haiku-20240307"
                    ),
                )
        else:
            st.warning(
                "Anthropic is selected but no API key has been entered. "
                "Add one in the **AI Settings** tab."
            )
    # ── Render results ────────────────────────────────────────────────────────
    render_results(scoring, keyword_match, formatting, ai_feedback)

    with st.expander("📋 View Extracted Resume Text"):
        st.text_area(
            "Raw extracted text (first 4 000 characters)",
            value=raw_text[:4000],
            height=300,
            disabled=True,
        )


if __name__ == "__main__":
    main()
