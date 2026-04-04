"""Text-to-Speech service using Sarvam AI (Indian voices)."""

from typing import Callable, Optional
from loguru import logger
import requests
import base64

from config import settings


class SarvamTTSService:
    """Manages text-to-speech with Sarvam AI for Indian English and Indic languages."""

    def __init__(self, on_audio: Callable[[bytes], None]):
        """
        Initialize Sarvam TTS service.

        Args:
            on_audio: Callback function(audio_chunk: bytes)
        """
        self.on_audio = on_audio
        self.api_key: Optional[str] = None
        self.api_url = "https://api.sarvam.ai/text-to-speech"

    def connect(self):
        """Initialize Sarvam AI client."""
        try:
            self.api_key = settings.sarvam_api_key
            if not self.api_key:
                raise ValueError("Sarvam API key not configured")
            logger.info("✅ TTS: Sarvam AI client initialized")
        except Exception as e:
            logger.error(f"❌ TTS: Failed to initialize Sarvam: {e}")
            raise

    async def synthesize_streaming(self, text: str):
        """
        Convert text to speech using Sarvam AI.

        Note: Sarvam doesn't support native streaming, so we get the full audio
        and send it in chunks.

        Args:
            text: Text to synthesize
        """
        if not self.api_key:
            logger.error("❌ TTS: Client not initialized")
            return

        if not text.strip():
            return

        try:
            logger.debug(f"🔊 TTS (Sarvam): Synthesizing: {text[:50]}...")

            # Prepare request
            headers = {
                "Content-Type": "application/json",
                "API-Subscription-Key": self.api_key
            }

            payload = {
                "inputs": [text],
                "target_language_code": "hi-IN",  # Hindi-English (Indian accent)
                "speaker": "meera",  # Female voice (options: meera, ar

kesh)
                "pitch": 0,
                "pace": 1.0,
                "loudness": 1.5,
                "speech_sample_rate": 8000,  # Match Twilio's 8kHz
                "enable_preprocessing": True,
                "model": "bulbul:v1"
            }

            # Make API call
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=10
            )

            if response.status_code != 200:
                logger.error(f"❌ TTS: Sarvam API error {response.status_code}: {response.text}")
                return

            # Parse response
            result = response.json()
            audio_base64 = result.get("audios", [None])[0]

            if not audio_base64:
                logger.error("❌ TTS: No audio in Sarvam response")
                return

            # Decode audio
            audio_bytes = base64.b64decode(audio_base64)

            # Send in chunks (simulate streaming for Twilio)
            chunk_size = 640  # 20ms chunks for 8kHz μ-law
            for i in range(0, len(audio_bytes), chunk_size):
                chunk = audio_bytes[i:i + chunk_size]
                self.on_audio(chunk)

            logger.debug(f"✅ TTS: Streamed {len(audio_bytes)} bytes in chunks")

        except Exception as e:
            logger.error(f"❌ TTS: Sarvam synthesis error: {e}")
            raise

    async def synthesize(self, text: str) -> bytes:
        """
        Convert text to speech and return complete audio.

        Args:
            text: Text to synthesize

        Returns:
            Complete audio bytes
        """
        if not self.api_key:
            logger.error("❌ TTS: Client not initialized")
            return b""

        if not text.strip():
            return b""

        try:
            logger.debug(f"🔊 TTS (Sarvam): Synthesizing (non-streaming): {text[:50]}...")

            headers = {
                "Content-Type": "application/json",
                "API-Subscription-Key": self.api_key
            }

            payload = {
                "inputs": [text],
                "target_language_code": "hi-IN",
                "speaker": "meera",
                "pitch": 0,
                "pace": 1.0,
                "loudness": 1.5,
                "speech_sample_rate": 8000,
                "enable_preprocessing": True,
                "model": "bulbul:v1"
            }

            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=10
            )

            if response.status_code != 200:
                logger.error(f"❌ TTS: Sarvam API error {response.status_code}")
                return b""

            result = response.json()
            audio_base64 = result.get("audios", [None])[0]

            if not audio_base64:
                return b""

            audio_bytes = base64.b64decode(audio_base64)
            logger.debug("✅ TTS: Synthesis complete")
            return audio_bytes

        except Exception as e:
            logger.error(f"❌ TTS: Sarvam synthesis error: {e}")
            return b""
