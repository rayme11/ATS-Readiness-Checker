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

    # ── Workflow explainer ────────────────────────────────────────────────────
    st.caption("HOW IT WORKS")
    step_cols = st.columns([4, 1, 4, 1, 4, 1, 4])
    steps = [
        ("1", "⬆️ Upload Resume", "PDF, DOCX, or TXT — required"),
        ("2", "📋 Paste Job Description", "Optional · unlocks keyword matching"),
        ("3", "🔍 Click Analyze", "Get score, gaps & recommendations"),
        ("4", "🤖 AI Feedback", "Optional · configure in ⚙️ AI Settings"),
    ]
    for i, (num, title, desc) in enumerate(steps):
        with step_cols[i * 2]:
            st.markdown(
                f"**{num}. {title}**  \n"
                f"<span style='color:#64748b;font-size:12px;'>{desc}</span>",
                unsafe_allow_html=True,
            )
        if i < 3:
            with step_cols[i * 2 + 1]:
                st.markdown(
                    "<div style='text-align:center;padding-top:4px;color:#475569;"
                    "font-size:18px;'>→</div>",
                    unsafe_allow_html=True,
                )
    st.divider()

    # ── Privacy / local mode callout ──────────────────────────────────────────
    with st.expander("🔒 Privacy & AI modes — what stays on your machine?", expanded=False):
        st.markdown(
            """
| Mode | Where AI runs | Internet needed? | API key needed? |
|---|---|---|---|
| 🔵 **Rule-based only** *(default)* | No AI — pure rule engine | ❌ Never | ❌ No |
| 🟢 **Ollama** | **Your own Mac/PC** | ❌ Never | ❌ No |
| 🟡 **Groq** | Groq cloud servers | ✅ Yes | ✅ Free key |
| 🟠 **OpenAI** | OpenAI cloud servers | ✅ Yes | ✅ Paid key |
| 🟣 **Anthropic** | Anthropic cloud servers | ✅ Yes | ✅ Paid key |

**Want to stay 100% local?** Choose **Rule-based only** (no AI) or install **Ollama** and pick it in the ⚙️ AI Settings tab — your resume never leaves your machine either way.

> Your resume file is **never uploaded to any external server** — even in cloud AI modes the text is sent only to the AI provider you choose, not stored anywhere else.
            """
        )

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
        "none":      "🔵 Rule-based only  ·  100% local, no AI",
        "ollama":    f"🟢 Ollama — {st.session_state.get('ollama_model', 'llama3')}  ·  100% local AI",
        "groq":      f"🟡 Groq — {st.session_state.get('groq_model', 'llama-3.1-8b-instant')}  ·  Cloud AI",
        "openai":    f"🟠 OpenAI — {st.session_state.get('openai_model', 'gpt-4o-mini')}  ·  Cloud AI",
        "anthropic": f"🟣 Anthropic — {st.session_state.get('anthropic_model', 'claude-3-haiku-20240307')}  ·  Cloud AI",
    }
    badge_label = badge_map.get(provider, "🔵 Rule-based only  ·  100% local, no AI")
    st.caption(f"AI mode: **{badge_label}** — change this in the **⚙️ AI Settings** tab")

    file_ready = st.session_state.get("uploaded_file") is not None

    if not file_ready:
        st.info("⬆️  Upload a resume file above to enable analysis.")

    return st.button(
        "🔍 Analyze Resume",
        type="primary",
        disabled=not file_ready,
        use_container_width=True,
    )
