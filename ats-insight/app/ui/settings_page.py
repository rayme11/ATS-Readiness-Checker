"""
AI Settings page — lets users switch between rule-based, Ollama, and OpenAI modes.
"""

import streamlit as st

from app.ai.llm_client import OllamaClient


def render_settings() -> None:
    st.header("⚙️ AI Settings")

    st.markdown(
        """
Configure how **ATS Insight** uses AI for deeper resume analysis.

| Mode | Cost | Requirements |
|---|---|---|
| **None (Rule-based only)** | Free | Nothing extra |
| **Ollama (Local AI)** | Free | [Ollama](https://ollama.ai) installed & running |
| **OpenAI (Your API Key)** | Pay-per-use | Your own [OpenAI key](https://platform.openai.com/api-keys) |
        """
    )

    st.divider()

    # Determine current selection index for the radio widget
    current = st.session_state.get("ai_provider", "none")
    idx = {"none": 0, "ollama": 1, "openai": 2}.get(current, 0)

    provider_choice = st.radio(
        "Select AI Provider",
        options=[
            "None (Rule-based only)",
            "Ollama — Free & Local",
            "OpenAI — Bring Your Own Key",
        ],
        index=idx,
        horizontal=True,
    )

    st.divider()

    # ── Ollama config ────────────────────────────────────────────────────────
    if provider_choice == "Ollama — Free & Local":
        st.session_state["ai_provider"] = "ollama"
        st.subheader("Ollama Configuration")

        col1, col2 = st.columns([3, 1])
        with col1:
            ollama_url = st.text_input(
                "Ollama Base URL",
                value=st.session_state.get("ollama_base_url", "http://localhost:11434"),
                help="The URL where your local Ollama server is running.",
            )
            st.session_state["ollama_base_url"] = ollama_url

        with col2:
            st.write("")
            st.write("")
            check = st.button("Test Connection", use_container_width=True)

        if check:
            with st.spinner("Connecting to Ollama…"):
                c = OllamaClient(base_url=ollama_url)
                if c.is_available():
                    models = c.list_models()
                    st.session_state["ollama_models"] = models
                    st.success(
                        f"✅ Ollama is running!  "
                        f"Available models: **{', '.join(models) or 'none pulled yet'}**"
                    )
                else:
                    st.error(
                        "❌ Cannot reach Ollama. "
                        "Make sure it's running (`ollama serve` in a terminal)."
                    )

        available_models = st.session_state.get(
            "ollama_models",
            ["llama3", "llama3.2", "mistral", "gemma2", "phi3"],
        )
        ollama_model = st.selectbox(
            "Model",
            options=available_models,
            index=0,
            help="Choose from locally pulled models. Run `ollama pull <model>` to add one.",
        )
        st.session_state["ollama_model"] = ollama_model

        with st.expander("How to get started with Ollama"):
            st.code(
                "# 1. Install Ollama\nbrew install ollama    # macOS\n"
                "# (or download from https://ollama.ai)\n\n"
                "# 2. Start the server (runs in background)\nollama serve\n\n"
                "# 3. Pull a model (one-time download, ~4 GB for llama3)\n"
                "ollama pull llama3\n\n"
                "# 4. Come back here and click 'Test Connection'",
                language="bash",
            )

    # ── OpenAI config ────────────────────────────────────────────────────────
    elif provider_choice == "OpenAI — Bring Your Own Key":
        st.session_state["ai_provider"] = "openai"
        st.subheader("OpenAI Configuration")

        st.warning(
            "🔒 Your API key is stored **in session memory only** "
            "and is never written to disk or sent anywhere except OpenAI.",
            icon="⚠️",
        )

        api_key = st.text_input(
            "OpenAI API Key",
            type="password",
            value=st.session_state.get("openai_api_key", ""),
            placeholder="sk-…",
            help="Get your key at https://platform.openai.com/api-keys",
        )
        if api_key:
            st.session_state["openai_api_key"] = api_key

        openai_model = st.selectbox(
            "Model",
            options=["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"],
            index=0,
            help="gpt-4o-mini is cheapest and works well for resume analysis.",
        )
        st.session_state["openai_model"] = openai_model

    # ── No AI ────────────────────────────────────────────────────────────────
    else:
        st.session_state["ai_provider"] = "none"
        st.info(
            "Running in **rule-based mode**. "
            "You'll still get a full score, keyword analysis, formatting checks, "
            "and recommendations — just no AI narrative feedback."
        )

    # ── Status footer ────────────────────────────────────────────────────────
    st.divider()
    _prov = st.session_state.get("ai_provider", "none")
    if _prov == "none":
        st.caption("Current AI mode: **Rule-based only** (no AI)")
    elif _prov == "ollama":
        st.caption(
            f"Current AI mode: **Ollama** — model `{st.session_state.get('ollama_model', 'llama3')}` "
            f"at `{st.session_state.get('ollama_base_url', 'http://localhost:11434')}`"
        )
    elif _prov == "openai":
        key_ok = "✓ Set" if st.session_state.get("openai_api_key") else "✗ Not set"
        st.caption(
            f"Current AI mode: **OpenAI** — model `{st.session_state.get('openai_model', 'gpt-4o-mini')}` "
            f"— API key: {key_ok}"
        )
