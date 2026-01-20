"""Utility functions and helpers."""

import re
from datetime import datetime
from pathlib import Path


def ensure_dir(path: Path | str) -> Path:
    """Ensure a directory exists, creating it if necessary."""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_timestamp() -> str:
    """Get current timestamp in a filename-safe format."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def sanitize_filename(filename: str, max_length: int = 100) -> str:
    """Sanitize a string to be used as a filename."""
    # Remove or replace invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', "", filename)
    # Replace spaces with underscores
    sanitized = re.sub(r"\s+", "_", sanitized)
    # Remove leading/trailing dots and spaces
    sanitized = sanitized.strip(". ")
    # Truncate if too long
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    return sanitized or "unnamed"


def format_duration(seconds: float) -> str:
    """Format duration in seconds to MM:SS format."""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"


def estimate_speech_duration(text: str, words_per_minute: int = 150) -> float:
    """Estimate speech duration for given text based on word count."""
    # Korean character count (roughly 2 characters per syllable, 4 syllables per second)
    korean_chars = len(re.findall(r"[가-힣]", text))
    # English word count
    english_words = len(re.findall(r"[a-zA-Z]+", text))

    # Estimate: Korean ~4 syllables/second, English ~2.5 words/second
    korean_duration = korean_chars / 8  # 2 chars/syllable, 4 syllables/second
    english_duration = english_words / 2.5

    return korean_duration + english_duration
