"""Configuration management for the content pipeline."""

from pathlib import Path
from typing import Literal

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AIClaudeSettings(BaseSettings):
    """Claude AI settings."""

    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 8192


class AIOpenAISettings(BaseSettings):
    """OpenAI settings."""

    model: str = "gpt-4o"
    max_tokens: int = 8192


class AIOllamaSettings(BaseSettings):
    """Ollama AI settings for local development."""

    base_url: str = "http://localhost:11434/v1"
    model: str = "llama3.2"
    max_tokens: int = 8192


class AISettings(BaseSettings):
    """AI service settings."""

    provider: Literal["claude", "openai", "ollama"] = "claude"
    claude: AIClaudeSettings = Field(default_factory=AIClaudeSettings)
    openai: AIOpenAISettings = Field(default_factory=AIOpenAISettings)
    ollama: AIOllamaSettings = Field(default_factory=AIOllamaSettings)


class ScriptSettings(BaseSettings):
    """Script generation settings."""

    default_duration: int = 10
    default_tone: str = "친근하고 설득력 있는"
    language: str = "ko"


class PresentationSettings(BaseSettings):
    """Presentation settings."""

    width: int = 1920
    height: int = 1080
    title_font_size: int = 44
    body_font_size: int = 28
    background_color: str = "#FFFFFF"
    title_color: str = "#1a1a2e"
    body_color: str = "#333333"
    accent_color: str = "#4a90d9"


class ElevenLabsSettings(BaseSettings):
    """ElevenLabs TTS settings."""

    voice_id: str = "pNInz6obpgDQGcFmaJgB"
    model_id: str = "eleven_multilingual_v2"
    stability: float = 0.5
    similarity_boost: float = 0.75


class GoogleTTSSettings(BaseSettings):
    """Google Cloud TTS settings."""

    language_code: str = "ko-KR"
    voice_name: str = "ko-KR-Neural2-C"
    speaking_rate: float = 1.0
    pitch: float = 0.0


class OpenAITTSSettings(BaseSettings):
    """OpenAI TTS settings."""

    model: str = "tts-1-hd"
    voice: str = "alloy"
    speed: float = 1.0


class LocalTTSSettings(BaseSettings):
    """Local TTS settings using pyttsx3 for development."""

    rate: int = 150  # Words per minute
    volume: float = 1.0  # 0.0 to 1.0
    voice_id: str | None = None  # System voice ID (None for default)


class TTSSettings(BaseSettings):
    """TTS settings."""

    provider: Literal["elevenlabs", "google", "openai", "local"] = "openai"
    elevenlabs: ElevenLabsSettings = Field(default_factory=ElevenLabsSettings)
    google: GoogleTTSSettings = Field(default_factory=GoogleTTSSettings)
    openai: OpenAITTSSettings = Field(default_factory=OpenAITTSSettings)
    local: LocalTTSSettings = Field(default_factory=LocalTTSSettings)


class VideoSettings(BaseSettings):
    """Video generation settings."""

    format: str = "mp4"
    width: int = 1920
    height: int = 1080
    fps: int = 30
    codec: str = "libx264"
    audio_codec: str = "aac"
    bitrate: str = "8000k"
    transition_duration: float = 0.5


class YouTubeSettings(BaseSettings):
    """YouTube upload settings."""

    privacy_status: Literal["public", "private", "unlisted"] = "private"
    category_id: str = "27"
    default_tags: list[str] = Field(default_factory=lambda: ["교육", "강의", "자기계발"])


class OutputSettings(BaseSettings):
    """Output settings."""

    base_dir: str = "output"
    keep_intermediate: bool = True


class Settings(BaseSettings):
    """Main application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # API Keys (from environment)
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    elevenlabs_api_key: str = ""
    google_application_credentials: str = ""
    youtube_client_id: str = ""
    youtube_client_secret: str = ""

    # Sub-settings
    ai: AISettings = Field(default_factory=AISettings)
    script: ScriptSettings = Field(default_factory=ScriptSettings)
    presentation: PresentationSettings = Field(default_factory=PresentationSettings)
    tts: TTSSettings = Field(default_factory=TTSSettings)
    video: VideoSettings = Field(default_factory=VideoSettings)
    youtube: YouTubeSettings = Field(default_factory=YouTubeSettings)
    output: OutputSettings = Field(default_factory=OutputSettings)

    @classmethod
    def from_yaml(cls, config_path: Path | str) -> "Settings":
        """Load settings from YAML file and environment."""
        config_path = Path(config_path)

        if config_path.exists():
            with open(config_path) as f:
                yaml_config = yaml.safe_load(f) or {}
        else:
            yaml_config = {}

        return cls(**yaml_config)


def get_settings(config_path: Path | str | None = None) -> Settings:
    """Get application settings."""
    if config_path is None:
        # Look for config in default locations
        possible_paths = [
            Path("config/config.yaml"),
            Path("config.yaml"),
            Path.home() / ".config" / "contents-autouploader" / "config.yaml",
        ]
        for path in possible_paths:
            if path.exists():
                config_path = path
                break

    if config_path:
        return Settings.from_yaml(config_path)
    return Settings()


# Global settings instance
_settings: Settings | None = None


def init_settings(config_path: Path | str | None = None) -> Settings:
    """Initialize global settings."""
    global _settings
    _settings = get_settings(config_path)
    return _settings


def settings() -> Settings:
    """Get global settings instance."""
    global _settings
    if _settings is None:
        _settings = get_settings()
    return _settings
