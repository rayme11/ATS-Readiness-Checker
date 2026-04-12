"""
LLM client abstraction layer.

Two backends are supported:

  OllamaClient  – free, runs 100 % locally, no API key required.
                  Requires Ollama (https://ollama.ai) to be running.

  OpenAIClient  – uses the user's own OpenAI API key.
                  The key is NEVER persisted to disk by this module.

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


def get_llm_client(provider: str, **kwargs) -> Optional[OllamaClient | OpenAIClient]:
    """
    Factory that returns the appropriate LLM client.

    provider: "ollama" | "openai" | "none" / anything else → None
    kwargs for ollama: ollama_base_url, ollama_model
    kwargs for openai: openai_api_key, openai_model
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
    return None
