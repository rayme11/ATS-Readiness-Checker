import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    """
    Application configuration loaded from environment variables.

    Defaults are designed for a fully local, zero-cost setup:
      - AI is off by default (AI_PROVIDER=none)
      - Ollama base URL points to the default local server
      - OpenAI key is intentionally empty; users supply it via the UI
    """

    # ── AI provider ─────────────────────────────────────────────────────────
    # "none"   → rule-based analysis only, no LLM calls
    # "ollama" → free local inference via Ollama
    # "openai" → user-supplied OpenAI API key
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "none")

    # ── Ollama (local, free) ─────────────────────────────────────────────────
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3")

    # ── OpenAI (bring-your-own-key) ──────────────────────────────────────────
    # Never hard-code keys here; always inject via .env or the Settings UI.
    # Note: a ChatGPT Plus subscription is NOT the same as an API key.
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # ── Groq (bring-your-own-key, free developer tier available) ─────────────
    # Free tier: https://console.groq.com  — no credit card required.
    # Works for both local and hosted deployments.
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

    # ── Anthropic Claude (bring-your-own-key, pay-per-use) ────────────────────
    # Note: a Claude.ai Pro subscription is NOT the same as an API key.
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-3-haiku-20240307")

    # ── Deployment mode ──────────────────────────────────────────────────────
    # Streamlit Community Cloud sets HOME=/home/appuser.
    # Set HOSTED=true in any other cloud environment to get the same behaviour.
    IS_HOSTED: bool = (
        os.getenv("STREAMLIT_SHARING_MODE") == "streamlit"
        or os.getenv("HOME", "") == "/home/appuser"
        or os.getenv("HOSTED", "").lower() in ("true", "1", "yes")
    )

    # ── Abuse prevention ─────────────────────────────────────────────────────
    MAX_FILE_BYTES: int = int(os.getenv("MAX_FILE_BYTES", str(5 * 1024 * 1024)))  # 5 MB
    MAX_JD_CHARS: int = int(os.getenv("MAX_JD_CHARS", "15000"))
    MAX_ANALYSES_PER_SESSION: int = int(os.getenv("MAX_ANALYSES_PER_SESSION", "20"))


config = Config()
