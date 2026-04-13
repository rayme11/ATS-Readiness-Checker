"""
AI Settings page — lets users switch between rule-based and cloud AI modes.
On hosted deployments (IS_HOSTED=True) Ollama is hidden; it requires a local server.
"""

import streamlit as st

from app.ai.llm_client import OllamaClient
from app.config import config


def render_settings() -> None:
    st.header("⚙️ AI Settings")

    if config.IS_HOSTED:
        st.markdown(
            """
Configure how **ATS Insight** uses AI for deeper resume analysis.

| Mode | Cost | Requirements |
|---|---|---|
| **None (Rule-based)** | Free | Nothing extra |
| **Groq (Free Tier)** | Free | Free key from [console.groq.com](https://console.groq.com) |
| **OpenAI** | Pay-per-use | Your own [OpenAI key](https://platform.openai.com/api-keys) |
| **Anthropic Claude** | Pay-per-use | Your own [Anthropic key](https://console.anthropic.com) |

> 🔒 **Security:** Keys you enter here are stored **in your browser session only** — never
> written to disk, never logged, cleared when you close or refresh the tab.
            """
        )
    else:
        st.markdown(
            """
Configure how **ATS Insight** uses AI for deeper resume analysis.

| Mode | Cost | Local run | Hosted / online | Requirements |
|---|---|---|---|---|
| **None (Rule-based)** | Free | ✅ | ✅ | Nothing extra |
| **Ollama (Local AI)** | Free | ✅ | ❌ local only | [Ollama](https://ollama.ai) installed & running |
| **Groq (Free Tier)** | Free | ✅ | ✅ | Free key from [console.groq.com](https://console.groq.com) |
| **OpenAI** | Pay-per-use | ✅ | ✅ | Your own [OpenAI key](https://platform.openai.com/api-keys) |
| **Anthropic Claude** | Pay-per-use | ✅ | ✅ | Your own [Anthropic key](https://console.anthropic.com) |

> 🔒 **Security:** Keys you enter here are stored **in your browser session only** — never
> written to disk, never logged, cleared when you close or refresh the tab.
            """
        )

    st.divider()

    # Determine current selection index for the radio widget
    current = st.session_state.get("ai_provider", "none")

    # Ollama requires a local server — not available when hosted in the cloud
    if config.IS_HOSTED:
        if current == "ollama":
            current = "none"  # reset to rule-based if previously set to local AI
            st.session_state["ai_provider"] = "none"
        provider_options = [
            "None (Rule-based only)",
            "Groq — Free Tier (Bring Your Own Key)",
            "OpenAI — Bring Your Own Key",
            "Anthropic Claude — Bring Your Own Key",
        ]
        idx = {"none": 0, "groq": 1, "openai": 2, "anthropic": 3}.get(current, 0)
    else:
        provider_options = [
            "None (Rule-based only)",
            "Ollama — Free & Local",
            "Groq — Free Tier (Bring Your Own Key)",
            "OpenAI — Bring Your Own Key",
            "Anthropic Claude — Bring Your Own Key",
        ]
        idx = {"none": 0, "ollama": 1, "groq": 2, "openai": 3, "anthropic": 4}.get(current, 0)

    provider_choice = st.radio(
        "Select AI Provider",
        options=provider_options,
        index=idx,
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
            "and is never written to disk or sent anywhere except OpenAI.  \n"
            "💡 To persist across restarts, add `OPENAI_API_KEY=sk-…` to your `.env` file.",
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
    # ── Groq config ──────────────────────────────────────────────────────────
    elif provider_choice == "Groq — Free Tier (Bring Your Own Key)":
        st.session_state["ai_provider"] = "groq"
        st.subheader("Groq Configuration")

        st.success(
            "🆓 Groq has a **free developer tier** — no credit card required.  \n"
            "Sign up and get your key at [console.groq.com](https://console.groq.com)"
        )
        st.warning(
            "🔒 Your key is stored **in session memory only** — "
            "never written to disk or sent anywhere except Groq's API.  \n"
            "💡 To persist across restarts, add `GROQ_API_KEY=gsk_…` and `AI_PROVIDER=groq` to your `.env` file.",
            icon="⚠️",
        )

        groq_key = st.text_input(
            "Groq API Key",
            type="password",
            value=st.session_state.get("groq_api_key", ""),
            placeholder="gsk_…",
            help="Get your free key at https://console.groq.com",
        )
        if groq_key:
            st.session_state["groq_api_key"] = groq_key

        groq_model = st.selectbox(
            "Model",
            options=[
                "llama-3.1-8b-instant",
                "llama-3.3-70b-versatile",
                "llama-3.1-70b-versatile",
                "gemma2-9b-it",
            ],
            index=0,
            help="All models are available on the Groq free developer tier.",
        )
        st.session_state["groq_model"] = groq_model

        with st.expander("ℹ️ About Groq free tier"):
            st.markdown(
                "- **No credit card** required to sign up\n"
                "- Rate limits apply (~30 req/min on free tier) — more than enough for resume analysis\n"
                "- Works with both local and hosted deployments of this app\n"
                "- See [console.groq.com](https://console.groq.com) for current model list and limits"
            )

    # ── Anthropic config ──────────────────────────────────────────────────────
    elif provider_choice == "Anthropic Claude — Bring Your Own Key":
        st.session_state["ai_provider"] = "anthropic"
        st.subheader("Anthropic Claude Configuration")

        st.warning(
            "💳 Anthropic's API is **pay-per-use** — there is no free tier.  \n"
            "⚠️ A **Claude.ai Pro** subscription does **not** include API access — "
            "API billing is separate at [console.anthropic.com](https://console.anthropic.com).",
            icon="⚠️",
        )
        st.info(
            "🔒 Your key is stored **in session memory only** — "
            "never written to disk or sent anywhere except Anthropic's API.",
            icon="ℹ️",
        )

        anthropic_key = st.text_input(
            "Anthropic API Key",
            type="password",
            value=st.session_state.get("anthropic_api_key", ""),
            placeholder="sk-ant-…",
            help="Get your key at https://console.anthropic.com",
        )
        if anthropic_key:
            st.session_state["anthropic_api_key"] = anthropic_key

        anthropic_model = st.selectbox(
            "Model",
            options=[
                "claude-3-haiku-20240307",
                "claude-3-5-sonnet-20241022",
                "claude-3-opus-20240229",
            ],
            index=0,
            help="claude-3-haiku is cheapest and fastest for resume analysis.",
        )
        st.session_state["anthropic_model"] = anthropic_model

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
    elif _prov == "groq":
        key_ok = "✓ Set" if st.session_state.get("groq_api_key") else "✗ Not set"
        st.caption(
            f"Current AI mode: **Groq** — model `{st.session_state.get('groq_model', 'llama-3.1-8b-instant')}` "
            f"— API key: {key_ok}"
        )
    elif _prov == "anthropic":
        key_ok = "✓ Set" if st.session_state.get("anthropic_api_key") else "✗ Not set"
        st.caption(
            f"Current AI mode: **Anthropic Claude** — "
            f"model `{st.session_state.get('anthropic_model', 'claude-3-haiku-20240307')}` "
            f"— API key: {key_ok}"
        )
