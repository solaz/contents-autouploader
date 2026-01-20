"""AI service abstraction layer for Claude, OpenAI, and Ollama."""

import json
from abc import ABC, abstractmethod

import anthropic
import openai

from src.config import Settings, settings


def _parse_json_response(response: str) -> dict:
    """Parse JSON content from a model response."""
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        cleaned = response.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned[3:].lstrip()
            if cleaned.startswith("json"):
                cleaned = cleaned[4:].lstrip()
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3].rstrip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            start = response.find("{")
            end = response.rfind("}") + 1
            if start != -1 and end > start:
                return json.loads(response[start:end])
            raise ValueError(f"Could not parse JSON from response: {response[:200]}...")


class AIService(ABC):
    """Abstract base class for AI services."""

    @abstractmethod
    def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        """Generate text from the AI model."""
        pass

    @abstractmethod
    def generate_json(
        self, prompt: str, system_prompt: str | None = None
    ) -> dict:
        """Generate JSON response from the AI model."""
        pass


class ClaudeService(AIService):
    """Claude AI service implementation."""

    def __init__(self, config: Settings | None = None):
        self.config = config or settings()
        self.client = anthropic.Anthropic(api_key=self.config.anthropic_api_key)
        self.model = self.config.ai.claude.model
        self.max_tokens = self.config.ai.claude.max_tokens

    def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        """Generate text using Claude."""
        messages = [{"role": "user", "content": prompt}]

        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system_prompt or "",
            messages=messages,
        )

        return response.content[0].text

    def generate_json(
        self, prompt: str, system_prompt: str | None = None
    ) -> dict:
        """Generate JSON response using Claude."""
        json_prompt = f"""{prompt}

IMPORTANT: Respond with valid JSON only. Do not include any text before or after the JSON."""

        response = self.generate(json_prompt, system_prompt)

        return _parse_json_response(response)


class OpenAIService(AIService):
    """OpenAI service implementation."""

    def __init__(self, config: Settings | None = None):
        self.config = config or settings()
        self.client = openai.OpenAI(api_key=self.config.openai_api_key)
        self.model = self.config.ai.openai.model
        self.max_tokens = self.config.ai.openai.max_tokens

    def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        """Generate text using OpenAI."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=messages,
        )

        return response.choices[0].message.content or ""

    def generate_json(
        self, prompt: str, system_prompt: str | None = None
    ) -> dict:
        """Generate JSON response using OpenAI."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        json_prompt = f"""{prompt}

IMPORTANT: Respond with valid JSON only. Do not include any text before or after the JSON."""
        messages.append({"role": "user", "content": json_prompt})

        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=messages,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content or "{}"
        return json.loads(content)


class OllamaService(AIService):
    """Ollama service implementation using OpenAI-compatible API."""

    def __init__(self, config: Settings | None = None):
        self.config = config or settings()
        self.client = openai.OpenAI(
            base_url=self.config.ai.ollama.base_url,
            api_key="ollama",  # Ollama는 API 키가 필요 없지만 클라이언트 요구사항 충족용
        )
        self.model = self.config.ai.ollama.model
        self.max_tokens = self.config.ai.ollama.max_tokens

    def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        """Generate text using Ollama."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=messages,
            )
        except openai.APIConnectionError:
            raise ConnectionError(
                f"Ollama 서버에 연결할 수 없습니다. ({self.client.base_url}) 'ollama serve'가 실행 중인지 확인해주세요."
            )

        return response.choices[0].message.content or ""

    def generate_json(
        self, prompt: str, system_prompt: str | None = None
    ) -> dict:
        """Generate JSON response using Ollama."""
        json_prompt = f"""{prompt}

IMPORTANT: Respond with valid JSON only. Do not include any text before or after the JSON."""
        response = self.generate(json_prompt, system_prompt)
        return _parse_json_response(response)


def get_ai_service(provider: str | None = None, config: Settings | None = None) -> AIService:
    """Factory function to get the appropriate AI service."""
    config = config or settings()
    provider = provider or config.ai.provider

    if provider == "claude":
        return ClaudeService(config)
    elif provider == "openai":
        return OpenAIService(config)
    elif provider == "ollama":
        return OllamaService(config)
    else:
        raise ValueError(f"Unknown AI provider: {provider}")
