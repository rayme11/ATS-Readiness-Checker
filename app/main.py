"""
ATS Insight — main Streamlit entry point.

Run with:
    streamlit run app/main.py
"""

import logging
import os
import sys

# ── Logging configuration — shows in the terminal that runs `streamlit run` —
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)

# Ensure the project root is importable as a package root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

from app.ai.ai_feedback import get_ai_feedback
from app.core.extractor import extract_sections
from app.core.formatting_checker import check_formatting
from app.core.keyword_matcher import match_keywords
from app.core.parser import parse_resume
from app.core.recommendations import generate_recommendations
from app.config import config
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

# ── Global CSS — dark theme, card polish, typography ─────────────────────────
st.markdown(
    """
    <style>
    /* ── Base & background ── */
    .stApp { background-color: #0f172a; }
    .block-container { padding-top: 2rem; padding-bottom: 3rem; max-width: 1100px; }

    /* ── Hide Streamlit default chrome ── */
    #MainMenu, footer, header { visibility: hidden; }

    /* ── Typography ── */
    html, body, [class*="css"] { font-family: 'Inter', 'Segoe UI', sans-serif; }
    h1, h2, h3 { color: #f1f5f9 !important; }
    p, li { color: #cbd5e1; }

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: #1e293b;
        border-radius: 12px;
        padding: 6px 8px;
        border: 1px solid #334155;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 8px 20px;
        color: #94a3b8;
        font-weight: 600;
        font-size: 14px;
        background: transparent;
        border: none;
    }
    .stTabs [aria-selected="true"] {
        background: #6366f1 !important;
        color: #fff !important;
    }
    .stTabs [data-baseweb="tab-border"] { display: none; }
    .stTabs [data-baseweb="tab-panel"] { padding-top: 24px; }

    /* ── Buttons ── */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%) !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        font-size: 15px !important;
        padding: 14px 0 !important;
        color: #fff !important;
        transition: opacity 0.2s ease !important;
    }
    .stButton > button[kind="primary"]:hover { opacity: 0.88 !important; }
    .stButton > button:not([kind="primary"]) {
        background: #1e293b !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
        color: #94a3b8 !important;
        font-weight: 600 !important;
    }
    .stButton > button:not([kind="primary"]):hover {
        border-color: #6366f1 !important;
        color: #e0e7ff !important;
    }

    /* ── Text inputs & text areas ── */
    .stTextArea textarea, .stTextInput input {
        background: #1e293b !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
        color: #f1f5f9 !important;
        font-size: 14px !important;
    }
    .stTextArea textarea:focus, .stTextInput input:focus {
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 2px #6366f122 !important;
    }

    /* ── File uploader ── */
    [data-testid="stFileUploader"] {
        background: #1e293b !important;
        border: 2px dashed #334155 !important;
        border-radius: 12px !important;
    }

    /* ── Select boxes ── */
    .stSelectbox [data-baseweb="select"] > div {
        background: #1e293b !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
        color: #f1f5f9 !important;
    }

    /* ── Expanders ── */
    .streamlit-expanderHeader {
        background: #1e293b !important;
        border: 1px solid #334155 !important;
        border-radius: 10px !important;
        color: #e2e8f0 !important;
        font-weight: 600 !important;
        font-size: 14px !important;
    }
    .streamlit-expanderContent {
        background: #1a2236 !important;
        border: 1px solid #334155 !important;
        border-top: none !important;
        border-radius: 0 0 10px 10px !important;
    }

    /* ── Radio buttons ── */
    .stRadio label { color: #cbd5e1 !important; font-size: 14px !important; }

    /* ── Alerts ── */
    .stSuccess { background: #14532d33 !important; border-color: #16a34a55 !important; }
    .stWarning { background: #78350f33 !important; border-color: #d9770655 !important; }
    .stError   { background: #7c1d1d33 !important; border-color: #dc262655 !important; }
    .stInfo    { background: #1e3a5f33 !important; border-color: #2563eb55 !important; }

    /* ── Divider ── */
    hr { border-color: #1e293b !important; }
    </style>
    """,
    unsafe_allow_html=True,
)


def _init_session_state() -> None:
    defaults = {
        # Seed from .env / config so keys & provider survive restarts
        "ai_provider":    config.AI_PROVIDER,
        "ollama_base_url": config.OLLAMA_BASE_URL,
        "ollama_model":   config.OLLAMA_MODEL,
        "openai_api_key": config.OPENAI_API_KEY,
        "openai_model":   config.OPENAI_MODEL,
        "groq_api_key":   config.GROQ_API_KEY,
        "groq_model":     config.GROQ_MODEL,
        "anthropic_api_key": config.ANTHROPIC_API_KEY,
        "anthropic_model":   config.ANTHROPIC_MODEL,
        "jd_text": "",
        "uploaded_file": None,
        "analysis_count": 0,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def main() -> None:
    _init_session_state()

    st.markdown(
        """
        <div style="
            display:flex; align-items:center; gap:16px;
            margin-bottom:28px;
        ">
            <div style="
                background:linear-gradient(135deg,#6366f1,#4f46e5);
                border-radius:14px; width:52px; height:52px;
                display:flex; align-items:center; justify-content:center;
                font-size:26px; flex-shrink:0;
            ">📄</div>
            <div>
                <div style="color:#f1f5f9;font-size:28px;font-weight:800;line-height:1.1;">
                    ATS Insight
                </div>
                <div style="color:#64748b;font-size:14px;margin-top:3px;">
                    Open-source resume ATS readiness analyzer
                    — rule-based scoring with optional local or cloud AI
                </div>
                <div style="margin-top:6px;font-size:13px;">
                    <a href="https://github.com/rayme11/ATS-Readiness-Checker"
                       target="_blank"
                       style="color:#6366f1;text-decoration:none;font-weight:600;">
                        ⭐ View source on GitHub
                    </a>
                    <span style="color:#334155;margin:0 8px;">·</span>
                    <a href="https://www.linkedin.com/in/rmaldonado"
                       target="_blank"
                       style="color:#6366f1;text-decoration:none;font-weight:600;">
                        👤 Author on LinkedIn
                    </a>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_analyze, tab_settings = st.tabs(["🔍 Analyze Resume", "⚙️ AI Settings"])

    with tab_settings:
        render_settings()

    with tab_analyze:
        analyze_clicked = render_upload()

        if analyze_clicked:
            count = st.session_state.get("analysis_count", 0)
            if count >= config.MAX_ANALYSES_PER_SESSION:
                st.error(
                    f"You've run {config.MAX_ANALYSES_PER_SESSION} analyses this session — "
                    "the limit helps keep the service free for everyone. "
                    "Refresh the page to start a new session.",
                    icon="🚫",
                )
            else:
                st.session_state["analysis_count"] = count + 1
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
        model = st.session_state.get("ollama_model", "llama3")
        with st.spinner(
            f"Loading model '{model}' and generating AI feedback… "
            f"(first run can take 30–120 s while Ollama loads weights)"
        ):
            ai_feedback = get_ai_feedback(
                resume=resume,
                scoring=scoring,
                job_description=jd_text,
                provider="ollama",
                ollama_base_url=st.session_state.get("ollama_base_url"),
                ollama_model=model,
            )
        if ai_feedback and ai_feedback.startswith("AI feedback unavailable:"):
            st.error(
                ai_feedback.replace("AI feedback unavailable: ", "") + "\n\n"
                "**Tips:**\n"
                "- Make sure Ollama is running: `ollama serve` in a terminal\n"
                "- Try again — the model may need a few seconds after loading\n"
                "- Switch to a smaller model (e.g. `llama3:8b`) in AI Settings",
                icon="🔴",
            )
            ai_feedback = None

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
                f"({st.session_state.get('groq_model', 'llama-3.1-8b-instant')})…"
            ):
                ai_feedback = get_ai_feedback(
                    resume=resume,
                    scoring=scoring,
                    job_description=jd_text,
                    provider="groq",
                    groq_api_key=api_key,
                    groq_model=st.session_state.get("groq_model", "llama-3.1-8b-instant"),
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
