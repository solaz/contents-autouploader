"""TTS (Text-to-Speech) generator supporting multiple providers."""

from abc import ABC, abstractmethod
from pathlib import Path

from src.config import Settings, settings
from src.models.script import Script, ScriptSection
from src.utils.helpers import ensure_dir, sanitize_filename


class TTSProvider(ABC):
    """Abstract base class for TTS providers."""

    @abstractmethod
    def synthesize(self, text: str, output_path: Path) -> float:
        """Synthesize speech from text.

        Returns the duration of the audio in seconds.
        """
        pass


class ElevenLabsTTS(TTSProvider):
    """ElevenLabs TTS provider."""

    def __init__(self, config: Settings):
        self.config = config
        self.tts_config = config.tts.elevenlabs

        from elevenlabs import ElevenLabs

        self.client = ElevenLabs(api_key=config.elevenlabs_api_key)

    def synthesize(self, text: str, output_path: Path) -> float:
        """Synthesize speech using ElevenLabs."""
        from elevenlabs import save

        audio = self.client.text_to_speech.convert(
            voice_id=self.tts_config.voice_id,
            text=text,
            model_id=self.tts_config.model_id,
            voice_settings={
                "stability": self.tts_config.stability,
                "similarity_boost": self.tts_config.similarity_boost,
            },
        )

        # Save audio file
        save(audio, str(output_path))

        # Get duration
        return self._get_audio_duration(output_path)

    def _get_audio_duration(self, audio_path: Path) -> float:
        """Get the duration of an audio file."""
        try:
            from mutagen.mp3 import MP3

            audio = MP3(str(audio_path))
            return audio.info.length
        except ImportError:
            # Fallback: estimate based on file size
            # Rough estimate: 16kbps mono = 2KB/sec
            file_size = audio_path.stat().st_size
            return file_size / 2000


class GoogleTTS(TTSProvider):
    """Google Cloud TTS provider."""

    def __init__(self, config: Settings):
        self.config = config
        self.tts_config = config.tts.google

        from google.cloud import texttospeech

        self.client = texttospeech.TextToSpeechClient()
        self.texttospeech = texttospeech

    def synthesize(self, text: str, output_path: Path) -> float:
        """Synthesize speech using Google Cloud TTS."""
        synthesis_input = self.texttospeech.SynthesisInput(text=text)

        voice = self.texttospeech.VoiceSelectionParams(
            language_code=self.tts_config.language_code,
            name=self.tts_config.voice_name,
        )

        audio_config = self.texttospeech.AudioConfig(
            audio_encoding=self.texttospeech.AudioEncoding.MP3,
            speaking_rate=self.tts_config.speaking_rate,
            pitch=self.tts_config.pitch,
        )

        response = self.client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config,
        )

        # Save audio file
        with open(output_path, "wb") as f:
            f.write(response.audio_content)

        return self._get_audio_duration(output_path)

    def _get_audio_duration(self, audio_path: Path) -> float:
        """Get the duration of an audio file."""
        try:
            from mutagen.mp3 import MP3

            audio = MP3(str(audio_path))
            return audio.info.length
        except ImportError:
            file_size = audio_path.stat().st_size
            return file_size / 2000


class OpenAITTS(TTSProvider):
    """OpenAI TTS provider."""

    def __init__(self, config: Settings):
        self.config = config
        self.tts_config = config.tts.openai

        import openai

        self.client = openai.OpenAI(api_key=config.openai_api_key)

    def synthesize(self, text: str, output_path: Path) -> float:
        """Synthesize speech using OpenAI TTS."""
        response = self.client.audio.speech.create(
            model=self.tts_config.model,
            voice=self.tts_config.voice,
            input=text,
            speed=self.tts_config.speed,
        )

        # Save audio file
        response.stream_to_file(str(output_path))

        return self._get_audio_duration(output_path)

    def _get_audio_duration(self, audio_path: Path) -> float:
        """Get the duration of an audio file."""
        try:
            from mutagen.mp3 import MP3

            audio = MP3(str(audio_path))
            return audio.info.length
        except ImportError:
            file_size = audio_path.stat().st_size
            return file_size / 2000


class LocalTTS(TTSProvider):
    """Local TTS provider using pyttsx3."""

    def __init__(self, config: Settings):
        self.config = config
        self.tts_config = config.tts.local

        import pyttsx3
        
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty("rate", self.tts_config.rate)
            self.engine.setProperty("volume", self.tts_config.volume)
            if self.tts_config.voice_id:
                self.engine.setProperty("voice", self.tts_config.voice_id)
        except Exception as e:
            print(f"Warning: Failed to initialize Local TTS: {e}")
            self.engine = None

    def synthesize(self, text: str, output_path: Path) -> float:
        """Synthesize speech using local TTS."""
        if self.engine is None:
            raise RuntimeError("Local TTS engine is not initialized.")
            
        output_path = output_path.with_suffix(".wav")
        self.engine.save_to_file(text, str(output_path))
        self.engine.runAndWait()

        return self._get_audio_duration(output_path)

    def _get_audio_duration(self, audio_path: Path) -> float:
        """Get duration of a WAV audio file."""
        import wave
        
        try:
            with wave.open(str(audio_path), "rb") as wav_file:
                frames = wav_file.getnframes()
                rate = wav_file.getframerate()
                return frames / float(rate)
        except Exception:
            # Fallback to mutagen if wave fails (though unlikely for wav)
            return super()._get_audio_duration(audio_path)


class TTSGenerator:
    """Generator for creating audio from script text."""

    def __init__(self, config: Settings | None = None, provider: str | None = None):
        self.config = config or settings()
        self.provider_name = provider or self.config.tts.provider
        self.provider = self._get_provider(self.provider_name)

    def _get_output_extension(self) -> str:
        """Get the output file extension for the current provider."""
        if self.provider_name == "local":
            return ".wav"
        return ".mp3"

    def _get_provider(self, provider_name: str) -> TTSProvider:
        """Get the appropriate TTS provider."""
        if provider_name == "elevenlabs":
            return ElevenLabsTTS(self.config)
        elif provider_name == "google":
            return GoogleTTS(self.config)
        elif provider_name == "openai":
            return OpenAITTS(self.config)
        elif provider_name == "local":
            return LocalTTS(self.config)
        else:
            raise ValueError(f"Unknown TTS provider: {provider_name}")

    def generate_for_section(
        self,
        section: ScriptSection,
        output_dir: Path | str | None = None,
    ) -> tuple[Path, float]:
        """Generate audio for a single section.

        Returns tuple of (audio_path, duration_seconds).
        """
        if output_dir is None:
            output_dir = ensure_dir(Path(self.config.output.base_dir) / "audio")
        else:
            output_dir = ensure_dir(Path(output_dir))

        output_path = output_dir / f"section_{section.section_id:03d}{self._get_output_extension()}"
        duration = self.provider.synthesize(section.content, output_path)

        return output_path, duration

    def generate_for_script(
        self,
        script: Script,
        output_dir: Path | str | None = None,
    ) -> list[tuple[int, Path, float]]:
        """Generate audio for all sections in a script.

        Returns list of tuples: (section_id, audio_path, duration_seconds).
        """
        if output_dir is None:
            output_dir = ensure_dir(
                Path(self.config.output.base_dir) / "audio" / sanitize_filename(script.title)
            )
        else:
            output_dir = ensure_dir(Path(output_dir))

        results = []
        for section in script.sections:
            audio_path, duration = self.generate_for_section(section, output_dir)
            results.append((section.section_id, audio_path, duration))
            # Update section with actual duration
            section.estimated_duration_sec = duration

        return results

    def generate_full_audio(
        self,
        script: Script,
        output_path: Path | str | None = None,
    ) -> tuple[Path, float]:
        """Generate a single audio file for the entire script.

        Returns tuple of (audio_path, total_duration_seconds).
        """
        if output_path is None:
            output_dir = ensure_dir(Path(self.config.output.base_dir) / "audio")
            output_path = output_dir / (
                f"{sanitize_filename(script.title)}_full{self._get_output_extension()}"
            )
        else:
            output_path = Path(output_path)
            ensure_dir(output_path.parent)
            if self.provider_name == "local" and output_path.suffix != ".wav":
                output_path = output_path.with_suffix(".wav")

        full_text = script.to_full_text()
        duration = self.provider.synthesize(full_text, output_path)

        return output_path, duration
