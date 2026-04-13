"""
Results page — displays score, keyword analysis, warnings, recommendations, and LLM info.
"""

from typing import Optional

import streamlit as st

from app.models.scoring_models import FormattingResult, KeywordMatchResult, ScoringResult

# ── LLM suitability metadata ──────────────────────────────────────────────────
# Scores are out of 5 stars across dimensions relevant to resume analysis.
_LLM_PROFILES: dict[str, dict] = {
    "none": {
        "label": "Rule-based (No AI)",
        "icon": "🔵",
        "description": (
            "Deterministic heuristics: keyword frequency, section detection, "
            "formatting rules, and weighted scoring. Fast, private, reproducible. "
            "No interpretation of context or nuance."
        ),
        "scores": {
            "Resume Understanding": 3,
            "Keyword Analysis": 4,
            "Feedback Quality": 2,
            "Speed": 5,
            "Privacy": 5,
        },
        "best_for": "Quick structural checks, CI pipelines, privacy-sensitive use cases.",
        "limitations": "Cannot reason about soft skills, narrative, or job-fit nuance.",
    },
    "ollama": {
        "label": "Ollama — Local LLM",
        "icon": "🟢",
        "description": (
            "Runs a full LLM locally on your machine (llama3, mistral, etc.). "
            "No data leaves your computer. Quality depends heavily on the model "
            "size you pulled — llama3 8B is decent, 70B models are much stronger."
        ),
        "scores": {
            "Resume Understanding": 4,
            "Keyword Analysis": 4,
            "Feedback Quality": 4,
            "Speed": 3,
            "Privacy": 5,
        },
        "best_for": "Local privacy-first analysis with solid qualitative feedback.",
        "limitations": "Slower than cloud APIs; quality limited by your hardware and model size.",
    },
    "groq": {
        "label": "Groq — Free Tier Cloud",
        "icon": "🟡",
        "description": (
            "Ultra-fast cloud inference of open-weight models (Llama 3, Mixtral). "
            "Free developer tier — no credit card needed. "
            "Data is sent to Groq's servers but not used for training."
        ),
        "scores": {
            "Resume Understanding": 4,
            "Keyword Analysis": 4,
            "Feedback Quality": 4,
            "Speed": 5,
            "Privacy": 3,
        },
        "best_for": "Fast, high-quality feedback at zero cost. Great starting point.",
        "limitations": "Data leaves your machine; rate limited on free tier.",
    },
    "openai": {
        "label": "OpenAI GPT",
        "icon": "🟠",
        "description": (
            "GPT-4o / GPT-4o-mini via OpenAI API. Excellent at interpreting resume "
            "narratives, job-fit alignment, and generating actionable suggestions. "
            "Pay-per-use — gpt-4o-mini is very affordable (~$0.001 per analysis)."
        ),
        "scores": {
            "Resume Understanding": 5,
            "Keyword Analysis": 5,
            "Feedback Quality": 5,
            "Speed": 4,
            "Privacy": 3,
        },
        "best_for": "Highest quality feedback; best for career-critical applications.",
        "limitations": "Requires paid API key; data sent to OpenAI.",
    },
    "anthropic": {
        "label": "Anthropic Claude",
        "icon": "🟣",
        "description": (
            "Claude 3 Haiku / Sonnet / Opus. Particularly strong at structured "
            "document analysis, tone detection, and nuanced rewriting suggestions. "
            "Pay-per-use — Haiku is the most cost-efficient option."
        ),
        "scores": {
            "Resume Understanding": 5,
            "Keyword Analysis": 5,
            "Feedback Quality": 5,
            "Speed": 4,
            "Privacy": 3,
        },
        "best_for": "Excellent narrative rewriting and structured document reasoning.",
        "limitations": "Requires paid API key; no free tier; data sent to Anthropic.",
    },
}


def _star_bar(score: int, max_score: int = 5) -> str:
    """Return a filled/empty star string like ★★★★☆."""
    return "★" * score + "☆" * (max_score - score)


def _score_color(score: float) -> str:
    if score >= 80:
        return "#22c55e"   # green-500
    if score >= 60:
        return "#f59e0b"   # amber-500
    return "#ef4444"       # red-500


def _score_label(score: float) -> str:
    if score >= 80:
        return "Strong"
    if score >= 60:
        return "Decent"
    return "Needs work"


def render_results(
    scoring: ScoringResult,
    keyword_match: Optional[KeywordMatchResult],
    formatting: FormattingResult,
    ai_feedback: Optional[str] = None,
) -> None:

    provider = st.session_state.get("ai_provider", "none")
    color = _score_color(scoring.total_score)
    label = _score_label(scoring.total_score)

    # ── Hero score banner ────────────────────────────────────────────────────
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            border-radius: 16px;
            padding: 36px 40px;
            margin-bottom: 24px;
            display: flex;
            align-items: center;
            gap: 40px;
        ">
            <div style="text-align:center; min-width:140px;">
                <div style="
                    font-size: 64px;
                    font-weight: 800;
                    color: {color};
                    line-height: 1;
                ">{int(scoring.total_score)}</div>
                <div style="color:#94a3b8; font-size:15px; margin-top:4px;">out of 100</div>
            </div>
            <div style="flex:1;">
                <div style="color:#f1f5f9; font-size:26px; font-weight:700; margin-bottom:6px;">
                    ATS Readiness Report
                </div>
                <div style="
                    display:inline-block;
                    background:{color}22;
                    color:{color};
                    border:1px solid {color}55;
                    border-radius:20px;
                    padding:3px 14px;
                    font-size:14px;
                    font-weight:600;
                    margin-bottom:12px;
                ">{label}</div>
                <div style="
                    background:#1e293b;
                    border-radius:8px;
                    height:10px;
                    width:100%;
                    overflow:hidden;
                ">
                    <div style="
                        background:{color};
                        height:100%;
                        width:{int(scoring.total_score)}%;
                        border-radius:8px;
                        transition:width 0.6s ease;
                    "></div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Category cards ───────────────────────────────────────────────────────
    st.markdown("### 📊 Category Breakdown")
    cols = st.columns(len(scoring.categories))
    for col, cat in zip(cols, scoring.categories):
        cat_color = _score_color(cat.score)
        with col:
            st.markdown(
                f"""
                <div style="
                    background:#1e293b;
                    border:1px solid #334155;
                    border-top:3px solid {cat_color};
                    border-radius:12px;
                    padding:18px 16px;
                    text-align:center;
                    height:100%;
                ">
                    <div style="font-size:26px; font-weight:800; color:{cat_color};">
                        {int(cat.score)}
                    </div>
                    <div style="color:#f1f5f9; font-size:13px; font-weight:600; margin:4px 0;">
                        {cat.name}
                    </div>
                    <div style="color:#64748b; font-size:11px;">
                        weight {int(cat.weight * 100)}%
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Strengths & Weaknesses ───────────────────────────────────────────────
    col_s, col_w = st.columns(2)

    with col_s:
        st.markdown(
            """<div style="
                background:#14532d22;
                border:1px solid #16a34a55;
                border-radius:12px;
                padding:20px;
            "><div style="color:#4ade80; font-size:16px; font-weight:700; margin-bottom:12px;">
                ✅ Strengths
            </div>""",
            unsafe_allow_html=True,
        )
        if scoring.strengths:
            for s in scoring.strengths:
                st.markdown(f"- {s}")
        else:
            st.markdown("*Nothing notable to flag as a strength yet.*")
        st.markdown("</div>", unsafe_allow_html=True)

    with col_w:
        st.markdown(
            """<div style="
                background:#7c1d1d22;
                border:1px solid #dc262655;
                border-radius:12px;
                padding:20px;
            "><div style="color:#f87171; font-size:16px; font-weight:700; margin-bottom:12px;">
                ⚠️ Risks & Issues
            </div>""",
            unsafe_allow_html=True,
        )
        if scoring.weaknesses:
            for w in scoring.weaknesses:
                st.markdown(f"- {w}")
        else:
            st.markdown("*No major issues found — great shape!*")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Keyword analysis ─────────────────────────────────────────────────────
    if keyword_match and (keyword_match.matched_keywords or keyword_match.missing_keywords):
        kw_color = _score_color(keyword_match.score)
        st.markdown(
            f"""
            <div style="
                background:#1e293b;
                border:1px solid #334155;
                border-radius:12px;
                padding:20px 24px;
                margin-bottom:16px;
            ">
                <div style="display:flex; align-items:center; gap:12px; margin-bottom:14px;">
                    <span style="font-size:18px;">🔑</span>
                    <span style="color:#f1f5f9; font-size:17px; font-weight:700;">
                        Keyword Match Analysis
                    </span>
                    <span style="
                        margin-left:auto;
                        background:{kw_color}22;
                        color:{kw_color};
                        border:1px solid {kw_color}55;
                        border-radius:20px;
                        padding:3px 14px;
                        font-size:13px;
                        font-weight:700;
                    ">{keyword_match.score:.0f} / 100</span>
                </div>
            """,
            unsafe_allow_html=True,
        )
        col_m, col_miss = st.columns(2)
        with col_m:
            st.markdown(
                f"**✅ Matched ({len(keyword_match.matched_keywords)})**"
            )
            if keyword_match.matched_keywords:
                chips = " ".join(
                    f'<span style="background:#166534; color:#4ade80; border-radius:20px;'
                    f' padding:2px 10px; font-size:12px; margin:2px; display:inline-block;">'
                    f'{k}</span>'
                    for k in keyword_match.matched_keywords[:30]
                )
                st.markdown(chips, unsafe_allow_html=True)
        with col_miss:
            st.markdown(
                f"**❌ Missing ({len(keyword_match.missing_keywords)})**"
            )
            if keyword_match.critical_missing:
                st.markdown("*🔴 Critical / required:*")
                chips = " ".join(
                    f'<span style="background:#7c1d1d; color:#fca5a5; border-radius:20px;'
                    f' padding:2px 10px; font-size:12px; margin:2px; display:inline-block;">'
                    f'{k}</span>'
                    for k in keyword_match.critical_missing
                )
                st.markdown(chips, unsafe_allow_html=True)
            if keyword_match.missing_keywords:
                st.markdown("*Suggested additions:*")
                chips = " ".join(
                    f'<span style="background:#1e293b; color:#94a3b8; border:1px solid #334155;'
                    f' border-radius:20px; padding:2px 10px; font-size:12px; margin:2px;'
                    f' display:inline-block;">{k}</span>'
                    for k in keyword_match.missing_keywords[:15]
                )
                st.markdown(chips, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Formatting warnings ──────────────────────────────────────────────────
    if formatting.warnings:
        st.markdown("### 🛡️ ATS Formatting Warnings")
        for w in formatting.warnings:
            st.warning(w)
        st.markdown("<br>", unsafe_allow_html=True)

    # ── Recommendations ──────────────────────────────────────────────────────
    st.markdown("### 💡 Top Recommendations")
    if scoring.recommendations:
        for i, rec in enumerate(scoring.recommendations, 1):
            st.markdown(
                f"""<div style="
                    background:#1e293b;
                    border-left:3px solid #6366f1;
                    border-radius:0 10px 10px 0;
                    padding:12px 16px;
                    margin-bottom:8px;
                    color:#e2e8f0;
                    font-size:14px;
                "><span style="color:#818cf8; font-weight:700; margin-right:8px;">
                    {i}.
                </span>{rec}</div>""",
                unsafe_allow_html=True,
            )
    else:
        st.success("Your resume looks solid! Keep tailoring it for each specific job application.")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── LLM panel ────────────────────────────────────────────────────────────
    _render_llm_panel(provider)

    # ── AI feedback ──────────────────────────────────────────────────────────
    if ai_feedback:
        profile = _LLM_PROFILES.get(provider, _LLM_PROFILES["none"])
        model_str = _active_model_label(provider)
        st.markdown(
            f"""
            <div style="
                background: linear-gradient(135deg, #1e1b4b 0%, #172554 100%);
                border:1px solid #4338ca55;
                border-radius:14px;
                padding:24px 28px;
                margin-top:8px;
            ">
                <div style="display:flex; align-items:center; gap:10px; margin-bottom:16px;">
                    <span style="font-size:22px;">{profile['icon']}</span>
                    <span style="color:#e0e7ff; font-size:18px; font-weight:700;">
                        AI Feedback
                    </span>
                    <span style="
                        margin-left:auto;
                        background:#312e8155;
                        color:#a5b4fc;
                        border:1px solid #4338ca66;
                        border-radius:20px;
                        padding:3px 12px;
                        font-size:12px;
                    ">{model_str}</span>
                </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(ai_feedback)
        st.markdown("</div>", unsafe_allow_html=True)


def _active_model_label(provider: str) -> str:
    """Return a human-readable 'Provider — model' string."""
    if provider == "ollama":
        return f"Ollama — {st.session_state.get('ollama_model', 'llama3')}"
    if provider == "openai":
        return f"OpenAI — {st.session_state.get('openai_model', 'gpt-4o-mini')}"
    if provider == "groq":
        return f"Groq — {st.session_state.get('groq_model', 'llama-3.1-8b-instant')}"
    if provider == "anthropic":
        return f"Anthropic — {st.session_state.get('anthropic_model', 'claude-3-haiku-20240307')}"
    return "Rule-based"


def _render_llm_panel(provider: str) -> None:
    """Render an info card explaining the active LLM and scoring it for this task."""
    profile = _LLM_PROFILES.get(provider, _LLM_PROFILES["none"])

    with st.expander(
        f"{profile['icon']} AI Engine: **{profile['label']}** — how well does it fit this task?",
        expanded=False,
    ):
        col_desc, col_scores = st.columns([3, 2])

        with col_desc:
            st.markdown(
                f"""
                <div style="color:#cbd5e1; font-size:14px; line-height:1.7;">
                    {profile['description']}
                </div>
                <div style="margin-top:14px;">
                    <div style="color:#4ade80; font-size:13px; font-weight:600;">
                        ✅ Best for
                    </div>
                    <div style="color:#94a3b8; font-size:13px; margin-top:3px;">
                        {profile['best_for']}
                    </div>
                </div>
                <div style="margin-top:10px;">
                    <div style="color:#f87171; font-size:13px; font-weight:600;">
                        ⚠️ Limitations
                    </div>
                    <div style="color:#94a3b8; font-size:13px; margin-top:3px;">
                        {profile['limitations']}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col_scores:
            st.markdown(
                "<div style='color:#94a3b8; font-size:12px; font-weight:600; "
                "text-transform:uppercase; letter-spacing:0.08em; margin-bottom:10px;'>"
                "Task Suitability Scores</div>",
                unsafe_allow_html=True,
            )
            for dim, score in profile["scores"].items():
                star_color = "#f59e0b" if score >= 4 else "#64748b"
                st.markdown(
                    f"""
                    <div style="display:flex; align-items:center; margin-bottom:8px; gap:10px;">
                        <div style="color:#cbd5e1; font-size:13px; min-width:160px;">{dim}</div>
                        <div style="color:{star_color}; font-size:16px; letter-spacing:2px;">
                            {_star_bar(score)}
                        </div>
                        <div style="color:#64748b; font-size:12px;">{score}/5</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        # Compare all providers
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            "<div style='color:#94a3b8; font-size:12px; font-weight:600; "
            "text-transform:uppercase; letter-spacing:0.08em; margin-bottom:10px;'>"
            "Compare All Providers</div>",
            unsafe_allow_html=True,
        )
        dim_keys = list(next(iter(_LLM_PROFILES.values()))["scores"].keys())
        header_cols = st.columns([2] + [1] * len(dim_keys))
        header_cols[0].markdown(
            "<div style='color:#64748b; font-size:12px;'>Provider</div>",
            unsafe_allow_html=True,
        )
        for i, dk in enumerate(dim_keys):
            header_cols[i + 1].markdown(
                f"<div style='color:#64748b; font-size:11px; text-align:center;'>{dk}</div>",
                unsafe_allow_html=True,
            )
        for prov_key, prov_data in _LLM_PROFILES.items():
            row_cols = st.columns([2] + [1] * len(dim_keys))
            is_active = prov_key == provider
            name_style = (
                "color:#818cf8; font-weight:700;" if is_active else "color:#94a3b8;"
            )
            active_badge = " ◀" if is_active else ""
            row_cols[0].markdown(
                f"<div style='font-size:13px; {name_style}'>"
                f"{prov_data['icon']} {prov_data['label']}{active_badge}</div>",
                unsafe_allow_html=True,
            )
            for i, dk in enumerate(dim_keys):
                s = prov_data["scores"][dk]
                sc = "#f59e0b" if s >= 4 else "#475569"
                row_cols[i + 1].markdown(
                    f"<div style='text-align:center; color:{sc}; font-size:14px;'>"
                    f"{'★' * s}{'☆' * (5 - s)}</div>",
                    unsafe_allow_html=True,
                )
