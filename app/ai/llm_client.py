"""
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

from typing import Optional

import requests


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
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=3)
            return resp.status_code == 200
        except (requests.ConnectionError, requests.Timeout):
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

    def chat(self, prompt: str, system: Optional[str] = None) -> str:
        """Send a chat completion request and return the response text."""
        messages: list[dict] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {"model": self.model, "messages": messages, "stream": False}

        resp = requests.post(
            f"{self.base_url}/api/chat",
            json=payload,
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json()["message"]["content"]


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

        client = OpenAI(api_key=self.api_key)

        messages: list[dict] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=1500,
            temperature=0.4,
        )
        return response.choices[0].message.content


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

        client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.groq.com/openai/v1",
        )
        messages: list[dict] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=1500,
            temperature=0.4,
        )
        return response.choices[0].message.content


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

        client = Anthropic(api_key=self.api_key)
        kwargs: dict = {
            "model": self.model,
            "max_tokens": 1500,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            kwargs["system"] = system
        response = client.messages.create(**kwargs)
        return response.content[0].text


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
