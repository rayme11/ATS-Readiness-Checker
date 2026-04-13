"""

LLM client abstraction layer.

Four backends are supported:

  OllamaClient    – free, runs 100 % locally, no API key required.
                    Requires Ollama (https://ollama.ai) to be running.
                    ⚠️  Not available to visitors of a hosted web app unless
                    Ollama also runs on the server.

  OpenAIClient    – uses the user's own OpenAI API key (pay-per-use).
                    Note: a ChatGPT Plus subscription is NOT the same as an
                    API key — billing is completely separate.

  GroqClient      – uses the user's own Groq API key.
                    Groq offers a genuine FREE developer tier (no credit card).
                    API is OpenAI-compatible so the openai SDK is reused.
                    Works for both local AND hosted deployments.

  AnthropicClient – uses the user's own Anthropic API key (pay-per-use).
                    Note: a Claude.ai Pro subscription is NOT the same as an
                    API key — billing is completely separate.

Security invariant: API keys are NEVER persisted to disk by this module.
They are accepted at construction time, used in-memory, and discarded.

Use get_llm_client() to obtain the right client based on provider name.
"""

import logging
import time
from typing import Optional

import requests

logger = logging.getLogger(__name__)


class OllamaClient:
    """HTTP client for a locally running Ollama server."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama3",
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model

    def is_available(self) -> bool:
        """Return True if Ollama is reachable at base_url."""
        logger.info("[Ollama] Checking availability at %s", self.base_url)
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=3)
            if resp.status_code == 200:
                logger.info("[Ollama] Server is reachable")
                return True
            logger.warning("[Ollama] Unexpected status %s", resp.status_code)
            return False
        except requests.ConnectionError:
            logger.warning("[Ollama] Connection refused — is `ollama serve` running?")
            return False
        except requests.Timeout:
            logger.warning("[Ollama] Connection timed out after 3 s")
            return False

    def list_models(self) -> list[str]:
        """Return names of models pulled into Ollama."""
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                return [m["name"] for m in data.get("models", [])]
        except Exception:
            pass
        return []

    # Models can take a long time to load on first use (weights loaded into RAM/VRAM).
    # 300 s covers even large 13B+ models on modest hardware.
    _CHAT_TIMEOUT = 300

    def _warm_model(self) -> None:
        """
        Send a minimal /api/generate request to ensure the model is loaded
        before the real (longer) prompt arrives.  This avoids the main request
        sitting idle while Ollama loads weights, which can silently exhaust the
        read timeout before a single token is generated.
        """
        try:
            logger.info("[Ollama] Warming model '%s'…", self.model)
            t0 = time.perf_counter()
            resp = requests.post(
                f"{self.base_url}/api/generate",
                json={"model": self.model, "prompt": "hi", "stream": False},
                timeout=self._CHAT_TIMEOUT,
            )
            elapsed = time.perf_counter() - t0
            if resp.status_code == 200:
                logger.info("[Ollama] Model warm after %.1fs", elapsed)
            else:
                logger.warning("[Ollama] Warm ping returned status %s", resp.status_code)
        except Exception as exc:
            logger.warning("[Ollama] Warm ping failed (non-fatal): %s", exc)

    def chat(self, prompt: str, system: Optional[str] = None) -> str:
        """Send a chat completion request and return the response text."""
        logger.info(
            "[Ollama] → POST %s/api/chat  model=%s  prompt_chars=%d",
            self.base_url, self.model, len(prompt),
        )
        # Ensure the model is loaded; this is a no-op if already resident.
        self._warm_model()

        messages: list[dict] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {"model": self.model, "messages": messages, "stream": False}

        t0 = time.perf_counter()
        try:
            resp = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=self._CHAT_TIMEOUT,
            )
        except requests.Timeout:
            raise RuntimeError(
                f"Ollama timed out after {self._CHAT_TIMEOUT}s. "
                "The model may still be loading — try again in a few seconds, "
                "or pull a smaller model (e.g. `ollama pull llama3:8b`)."
            )
        except requests.ConnectionError:
            raise RuntimeError(
                "Cannot reach Ollama. Make sure the server is running: `ollama serve`"
            )
        elapsed = time.perf_counter() - t0
        resp.raise_for_status()
        result = resp.json()["message"]["content"]
        logger.info(
            "[Ollama] ← response received  elapsed=%.1fs  response_chars=%d",
            elapsed, len(result),
        )
        return result


class OpenAIClient:
    """
    Thin wrapper around the official openai SDK.

    The api_key must be provided at construction time; it is used only
    for the duration of this object's lifetime and is never written to disk.
    """

    def __init__(self, api_key: str, model: str = "gpt-4o-mini") -> None:
        if not api_key:
            raise ValueError("OpenAI API key must not be empty.")
        self.api_key = api_key
        self.model = model

    def chat(self, prompt: str, system: Optional[str] = None) -> str:
        """Send a chat completion request and return the response text."""
        from openai import OpenAI  # lazy import keeps startup fast

        logger.info("[OpenAI] → request  model=%s  prompt_chars=%d", self.model, len(prompt))
        client = OpenAI(api_key=self.api_key)

        messages: list[dict] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        t0 = time.perf_counter()
        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=1500,
            temperature=0.4,
        )
        elapsed = time.perf_counter() - t0
        usage = response.usage
        result = response.choices[0].message.content
        logger.info(
            "[OpenAI] ← response  elapsed=%.1fs  prompt_tokens=%s  completion_tokens=%s  response_chars=%d",
            elapsed,
            usage.prompt_tokens if usage else "?",
            usage.completion_tokens if usage else "?",
            len(result) if result else 0,
        )
        return result


class GroqClient:
    """
    Client for Groq's cloud inference API.

    Groq offers a free developer tier — no credit card required.
    Get a key at: https://console.groq.com

    Uses Groq's OpenAI-compatible endpoint so the openai SDK is reused.
    Works for both local and hosted deployments of this app.
    The api_key is NEVER persisted to disk by this module.
    """

    def __init__(self, api_key: str, model: str = "llama3-8b-8192") -> None:
        if not api_key:
            raise ValueError("Groq API key must not be empty.")
        self.api_key = api_key
        self.model = model

    def chat(self, prompt: str, system: Optional[str] = None) -> str:
        """Send a chat completion request and return the response text."""
        from openai import OpenAI  # reuse openai SDK — Groq is OpenAI-compatible

        logger.info("[Groq] → request  model=%s  prompt_chars=%d", self.model, len(prompt))
        client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.groq.com/openai/v1",
        )
        messages: list[dict] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        t0 = time.perf_counter()
        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=1500,
            temperature=0.4,
        )
        elapsed = time.perf_counter() - t0
        usage = response.usage
        if not response.choices:
            logger.warning("[Groq] ← empty response  elapsed=%.1fs", elapsed)
            return ""
        content = response.choices[0].message.content
        logger.info(
            "[Groq] ← response  elapsed=%.1fs  prompt_tokens=%s  completion_tokens=%s  response_chars=%d",
            elapsed,
            usage.prompt_tokens if usage else "?",
            usage.completion_tokens if usage else "?",
            len(content) if isinstance(content, str) else 0,
        )
        return content if isinstance(content, str) else ""


class AnthropicClient:
    """
    Client for Anthropic's Claude API.

    Requires the 'anthropic' package: pip install anthropic
    Get a key at: https://console.anthropic.com

    Note: a Claude.ai Pro subscription is NOT the same as an API key.
    The api_key is NEVER persisted to disk by this module.
    """

    def __init__(self, api_key: str, model: str = "claude-3-haiku-20240307") -> None:
        if not api_key:
            raise ValueError("Anthropic API key must not be empty.")
        self.api_key = api_key
        self.model = model

    def chat(self, prompt: str, system: Optional[str] = None) -> str:
        """Send a chat completion request and return the response text."""
        from anthropic import Anthropic  # lazy import — anthropic package optional

        logger.info("[Anthropic] → request  model=%s  prompt_chars=%d", self.model, len(prompt))
        client = Anthropic(api_key=self.api_key)
        kwargs: dict = {
            "model": self.model,
            "max_tokens": 1500,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            kwargs["system"] = system
        t0 = time.perf_counter()
        response = client.messages.create(**kwargs)
        elapsed = time.perf_counter() - t0
        usage = getattr(response, "usage", None)
        result = response.content[0].text
        logger.info(
            "[Anthropic] ← response  elapsed=%.1fs  input_tokens=%s  output_tokens=%s  response_chars=%d",
            elapsed,
            getattr(usage, "input_tokens", "?") if usage else "?",
            getattr(usage, "output_tokens", "?") if usage else "?",
            len(result),
        )
        return result


def get_llm_client(
    provider: str, **kwargs
) -> Optional[OllamaClient | OpenAIClient | GroqClient | AnthropicClient]:
    """
    Factory that returns the appropriate LLM client.

    provider: "ollama" | "openai" | "groq" | "anthropic" | "none" / anything → None
    kwargs for ollama:    ollama_base_url, ollama_model
    kwargs for openai:    openai_api_key, openai_model
    kwargs for groq:      groq_api_key, groq_model
    kwargs for anthropic: anthropic_api_key, anthropic_model
    """
    if provider == "ollama":
        return OllamaClient(
            base_url=kwargs.get("ollama_base_url", "http://localhost:11434"),
            model=kwargs.get("ollama_model", "llama3"),
        )
    if provider == "openai":
        api_key = kwargs.get("openai_api_key", "")
        if not api_key:
            return None
        return OpenAIClient(
            api_key=api_key,
            model=kwargs.get("openai_model", "gpt-4o-mini"),
        )
    if provider == "groq":
        api_key = kwargs.get("groq_api_key", "")
        if not api_key:
            return None
        return GroqClient(
            api_key=api_key,
            model=kwargs.get("groq_model", "llama3-8b-8192"),
        )
    if provider == "anthropic":
        api_key = kwargs.get("anthropic_api_key", "")
        if not api_key:
            return None
        return AnthropicClient(
            api_key=api_key,
            model=kwargs.get("anthropic_model", "claude-3-haiku-20240307"),
        )
    return None
