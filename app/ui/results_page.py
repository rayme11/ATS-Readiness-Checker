"""
Results page — displays score, keyword analysis, warnings, and recommendations.
"""

from typing import Optional

import streamlit as st

from app.models.scoring_models import FormattingResult, KeywordMatchResult, ScoringResult


def _color(score: float) -> str:
    if score >= 80:
        return "green"
    if score >= 60:
        return "orange"
    return "red"


def render_results(
    scoring: ScoringResult,
    keyword_match: Optional[KeywordMatchResult],
    formatting: FormattingResult,
    ai_feedback: Optional[str] = None,
) -> None:
    st.header("📊 ATS Readiness Report")

    # ── Overall score ────────────────────────────────────────────────────────
    colour = _color(scoring.total_score)
    st.markdown(
        f"<h2 style='text-align:center; color:{colour};'>"
        f"Overall Score: {scoring.total_score} / 100"
        f"</h2>",
        unsafe_allow_html=True,
    )
    st.progress(int(scoring.total_score) / 100)

    # Score interpretation
    if scoring.total_score >= 80:
        st.success("Strong resume — well structured and likely to parse cleanly.")
    elif scoring.total_score >= 60:
        st.warning("Decent resume — a few targeted fixes could meaningfully raise your score.")
    else:
        st.error("Needs work — several issues may cause ATS problems or recruiter confusion.")

    st.divider()

    # ── Category breakdown ───────────────────────────────────────────────────
    st.subheader("Category Breakdown")
    cols = st.columns(len(scoring.categories))
    for col, cat in zip(cols, scoring.categories):
        with col:
            delta_color = "normal" if cat.score >= 60 else "inverse"
            st.metric(
                label=cat.name,
                value=f"{cat.score:.0f}",
                delta=f"weight {int(cat.weight * 100)}%",
                delta_color=delta_color,
            )

    st.divider()

    # ── Strengths & Weaknesses ───────────────────────────────────────────────
    col_s, col_w = st.columns(2)

    with col_s:
        st.subheader("✅ Strengths")
        if scoring.strengths:
            for s in scoring.strengths:
                st.markdown(f"- {s}")
        else:
            st.write("Nothing notable to flag as a strength yet.")

    with col_w:
        st.subheader("⚠️ Risks & Issues")
        if scoring.weaknesses:
            for w in scoring.weaknesses:
                st.markdown(f"- {w}")
        else:
            st.success("No major issues found — great shape!")

    st.divider()

    # ── Keyword analysis ─────────────────────────────────────────────────────
    if keyword_match and (keyword_match.matched_keywords or keyword_match.missing_keywords):
        st.subheader("🔑 Keyword Analysis")
        st.caption(f"Keyword match score: **{keyword_match.score:.0f} / 100**")

        col_m, col_miss = st.columns(2)

        with col_m:
            st.markdown(f"**Matched ({len(keyword_match.matched_keywords)})**")
            if keyword_match.matched_keywords:
                st.write(", ".join(keyword_match.matched_keywords[:30]))

        with col_miss:
            st.markdown(f"**Missing ({len(keyword_match.missing_keywords)})**")
            if keyword_match.critical_missing:
                st.markdown("*Required in JD:*")
                for k in keyword_match.critical_missing:
                    st.markdown(f"🔴 `{k}`")
            if keyword_match.missing_keywords:
                st.markdown("*Suggested additions:*")
                st.write(", ".join(keyword_match.missing_keywords[:15]))

        st.divider()

    # ── Formatting warnings ──────────────────────────────────────────────────
    if formatting.warnings:
        st.subheader("🛡️ ATS Formatting Warnings")
        for w in formatting.warnings:
            st.warning(w)
        st.divider()

    # ── Recommendations ──────────────────────────────────────────────────────
    st.subheader("💡 Top Recommendations")
    if scoring.recommendations:
        for i, rec in enumerate(scoring.recommendations, 1):
            st.markdown(f"**{i}.** {rec}")
    else:
        st.success(
            "Your resume looks solid! Keep tailoring it for each specific job application."
        )

    # ── AI feedback ──────────────────────────────────────────────────────────
    if ai_feedback:
        st.divider()
        provider = st.session_state.get("ai_provider", "none")
        label = {
            "ollama": f"🤖 AI Feedback (Ollama — {st.session_state.get('ollama_model', 'llama3')})",
            "openai": f"🤖 AI Feedback (OpenAI — {st.session_state.get('openai_model', 'gpt-4o-mini')})",
        }.get(provider, "🤖 AI Feedback")
        st.subheader(label)
        st.markdown(ai_feedback)
