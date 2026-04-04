"""Text-to-Speech service using ElevenLabs."""

from typing import Callable, Optional
from loguru import logger
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs

from config import settings


class TTSService:
    """Manages real-time text-to-speech streaming with ElevenLabs."""

    def __init__(self, on_audio: Callable[[bytes], None]):
        """
        Initialize TTS service.

        Args:
            on_audio: Callback function(audio_chunk: bytes)
        """
        self.on_audio = on_audio
        self.client: Optional[ElevenLabs] = None

    def connect(self):
        """Initialize ElevenLabs client."""
        try:
            self.client = ElevenLabs(api_key=settings.elevenlabs_api_key)
            logger.info("✅ TTS: ElevenLabs client initialized")
        except Exception as e:
            logger.error(f"❌ TTS: Failed to initialize: {e}")
            raise

    async def synthesize_streaming(self, text: str):
        """
        Convert text to speech and stream audio chunks.

        Args:
            text: Text to synthesize
        """
        if not self.client:
            logger.error("❌ TTS: Client not initialized")
            return

        if not text.strip():
            return

        try:
            logger.debug(f"🔊 TTS: Synthesizing: {text[:50]}...")

            # Configure voice settings for optimal streaming
            voice_settings = VoiceSettings(
                stability=0.5,
                similarity_boost=0.75,
                style=0.5,
                use_speaker_boost=True
            )

            # Stream audio from ElevenLabs
            audio_stream = self.client.text_to_speech.convert_as_stream(
                voice_id=settings.elevenlabs_voice_id,
                text=text,
                model_id=settings.tts_model,
                voice_settings=voice_settings,
                optimize_streaming_latency=4,  # 0-4, higher = lower latency
                output_format="ulaw_8000",  # Match Twilio's format
            )

            # Stream audio chunks to callback
            chunk_count = 0
            for audio_chunk in audio_stream:
                if audio_chunk:
                    self.on_audio(audio_chunk)
                    chunk_count += 1

            logger.debug(f"✅ TTS: Streamed {chunk_count} audio chunks")

        except Exception as e:
            logger.error(f"❌ TTS: Synthesis error: {e}")
            raise

    async def synthesize(self, text: str) -> bytes:
        """
        Convert text to speech and return complete audio.

        Args:
            text: Text to synthesize

        Returns:
            Complete audio bytes
        """
        if not self.client:
            logger.error("❌ TTS: Client not initialized")
            return b""

        if not text.strip():
            return b""

        try:
            logger.debug(f"🔊 TTS: Synthesizing (non-streaming): {text[:50]}...")

            voice_settings = VoiceSettings(
                stability=0.5,
                similarity_boost=0.75,
                style=0.5,
                use_speaker_boost=True
            )

            # Get complete audio
            audio = self.client.text_to_speech.convert(
                voice_id=settings.elevenlabs_voice_id,
                text=text,
                model_id=settings.tts_model,
                voice_settings=voice_settings,
                output_format="ulaw_8000",
            )

            logger.debug("✅ TTS: Synthesis complete")
            return audio

        except Exception as e:
            logger.error(f"❌ TTS: Synthesis error: {e}")
            return b""
