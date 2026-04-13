"""
Upload page — collect resume file and optional job description.
"""

import streamlit as st


def render_upload() -> bool:
    """
    Render the upload form.

    Returns True when the user clicks "Analyze Resume" with a valid file.
    """
    st.header("📄 Upload Your Resume")

    col_file, col_jd = st.columns(2)

    with col_file:
        st.subheader("Resume File")
        uploaded = st.file_uploader(
            "PDF, DOCX, or TXT",
            type=["pdf", "docx", "txt"],
            help="Your file is processed entirely on your machine — nothing is uploaded to any server.",
        )
        if uploaded is not None:
            st.session_state["uploaded_file"] = uploaded
            st.session_state["file_name"] = uploaded.name
            st.success(f"Loaded: **{uploaded.name}**")

    with col_jd:
        st.subheader("Job Description (optional)")
        jd_text = st.text_area(
            "Paste the full job description here",
            height=220,
            placeholder=(
                "Copy and paste the job posting here.\n\n"
                "Including a JD enables keyword matching and improves AI feedback."
            ),
            value=st.session_state.get("jd_text", ""),
        )
        st.session_state["jd_text"] = jd_text

    st.divider()

    # AI mode badge
    provider = st.session_state.get("ai_provider", "none")
    badge_map = {
        "none":      "🔵 Rule-based only",
        "ollama":    f"🟢 Ollama — {st.session_state.get('ollama_model', 'llama3')}",
        "groq":      f"🟡 Groq — {st.session_state.get('groq_model', 'llama3-8b-8192')}",
        "openai":    f"🟠 OpenAI — {st.session_state.get('openai_model', 'gpt-4o-mini')}",
        "anthropic": f"🟣 Anthropic — {st.session_state.get('anthropic_model', 'claude-3-haiku-20240307')}",
    }
    badge_label = badge_map.get(provider, f"🔵 Rule-based only")
    st.caption(f"AI mode: **{badge_label}** — change this in the **AI Settings** tab")

    file_ready = st.session_state.get("uploaded_file") is not None

    if not file_ready:
        st.info("⬆️  Upload a resume file above to enable analysis.")

    return st.button(
        "🔍 Analyze Resume",
        type="primary",
        disabled=not file_ready,
        use_container_width=True,
    )
