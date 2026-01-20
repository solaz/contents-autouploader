"""Tests for utility functions."""

import pytest
from pathlib import Path
import tempfile

from src.utils.helpers import (
    ensure_dir,
    get_timestamp,
    sanitize_filename,
    format_duration,
    estimate_speech_duration,
)


class TestHelpers:
    """Tests for helper functions."""

    def test_ensure_dir_creates_directory(self):
        """Test that ensure_dir creates a directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            new_dir = Path(tmpdir) / "test" / "nested" / "dir"
            result = ensure_dir(new_dir)
            assert result.exists()
            assert result.is_dir()

    def test_ensure_dir_with_existing_directory(self):
        """Test that ensure_dir works with existing directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = ensure_dir(tmpdir)
            assert result.exists()

    def test_get_timestamp_format(self):
        """Test timestamp format."""
        timestamp = get_timestamp()
        # Should be in format YYYYMMDD_HHMMSS
        assert len(timestamp) == 15
        assert "_" in timestamp

    def test_sanitize_filename_basic(self):
        """Test basic filename sanitization."""
        result = sanitize_filename("Hello World")
        assert result == "Hello_World"

    def test_sanitize_filename_special_chars(self):
        """Test sanitization of special characters."""
        result = sanitize_filename('Test<>:"/\\|?*File')
        assert "<" not in result
        assert ">" not in result
        assert ":" not in result

    def test_sanitize_filename_truncation(self):
        """Test filename truncation."""
        long_name = "a" * 200
        result = sanitize_filename(long_name, max_length=50)
        assert len(result) == 50

    def test_sanitize_filename_empty(self):
        """Test sanitization of empty or invalid strings."""
        result = sanitize_filename("...")
        assert result == "unnamed"

    def test_format_duration(self):
        """Test duration formatting."""
        assert format_duration(0) == "00:00"
        assert format_duration(65) == "01:05"
        assert format_duration(3661) == "61:01"

    def test_estimate_speech_duration_korean(self):
        """Test speech duration estimation for Korean text."""
        # Korean text
        korean_text = "안녕하세요 오늘은 좋은 날씨입니다"
        duration = estimate_speech_duration(korean_text)
        assert duration > 0

    def test_estimate_speech_duration_english(self):
        """Test speech duration estimation for English text."""
        english_text = "Hello this is a test sentence for duration estimation"
        duration = estimate_speech_duration(english_text)
        assert duration > 0

    def test_estimate_speech_duration_mixed(self):
        """Test speech duration estimation for mixed text."""
        mixed_text = "안녕하세요 Hello 반갑습니다 World"
        duration = estimate_speech_duration(mixed_text)
        assert duration > 0
