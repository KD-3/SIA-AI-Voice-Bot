"""Speech-to-Text service using Deepgram."""

import asyncio
from typing import Callable, Optional
from loguru import logger
from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    LiveTranscriptionEvents,
    LiveOptions,
)

from config import settings


class STTService:
    """Manages real-time speech-to-text streaming with Deepgram."""

    def __init__(self, on_transcript: Callable[[str, bool], None]):
        """
        Initialize STT service.

        Args:
            on_transcript: Callback function(transcript: str, is_final: bool)
        """
        self.on_transcript = on_transcript
        self.client: Optional[DeepgramClient] = None
        self.connection = None
        self.is_connected = False

    async def connect(self):
        """Establish connection to Deepgram streaming API."""
        try:
            # Configure Deepgram client
            config = DeepgramClientOptions(
                api_key=settings.deepgram_api_key,
                options={"keepalive": "true"}
            )
            self.client = DeepgramClient("", config)

            # Configure streaming options
            options = LiveOptions(
                model=settings.stt_model,
                language=settings.stt_language,
                encoding="mulaw",  # Twilio uses μ-law encoding
                sample_rate=8000,  # Twilio sample rate
                channels=1,
                punctuate=True,
                interim_results=True,  # Get partial transcripts
                endpointing=300,  # Detect end of speech after 300ms silence
                vad_events=True,  # Voice Activity Detection events
                smart_format=True,
            )

            # Create live transcription connection
            self.connection = self.client.listen.live.v("1")

            # Register event handlers
            self.connection.on(LiveTranscriptionEvents.Transcript, self._on_message)
            self.connection.on(LiveTranscriptionEvents.Error, self._on_error)
            self.connection.on(LiveTranscriptionEvents.Close, self._on_close)

            # Start connection
            if self.connection.start(options):
                self.is_connected = True
                logger.info("✅ STT: Connected to Deepgram")
            else:
                logger.error("❌ STT: Failed to connect to Deepgram")
                raise Exception("Failed to start Deepgram connection")

        except Exception as e:
            logger.error(f"❌ STT: Connection error: {e}")
            raise

    async def send_audio(self, audio_data: bytes):
        """
        Send audio data to Deepgram for transcription.

        Args:
            audio_data: Raw audio bytes (μ-law encoded, 8kHz)
        """
        if not self.is_connected or not self.connection:
            logger.warning("⚠️  STT: Not connected, skipping audio")
            return

        try:
            self.connection.send(audio_data)
        except Exception as e:
            logger.error(f"❌ STT: Error sending audio: {e}")

    def _on_message(self, *args, **kwargs):
        """Handle incoming transcript from Deepgram."""
        try:
            result = kwargs.get("result")
            if not result:
                return

            # Extract transcript
            transcript = result.channel.alternatives[0].transcript
            is_final = result.is_final

            if transcript.strip():
                # Log transcript
                final_indicator = "✓" if is_final else "..."
                logger.debug(f"🎤 STT {final_indicator}: {transcript}")

                # Call user callback
                self.on_transcript(transcript, is_final)

        except Exception as e:
            logger.error(f"❌ STT: Error processing transcript: {e}")

    def _on_error(self, *args, **kwargs):
        """Handle Deepgram errors."""
        error = kwargs.get("error")
        logger.error(f"❌ STT: Deepgram error: {error}")

    def _on_close(self, *args, **kwargs):
        """Handle connection close."""
        self.is_connected = False
        logger.info("🔌 STT: Deepgram connection closed")

    async def disconnect(self):
        """Close connection to Deepgram."""
        if self.connection:
            try:
                self.connection.finish()
                logger.info("👋 STT: Disconnected from Deepgram")
            except Exception as e:
                logger.error(f"❌ STT: Error disconnecting: {e}")
            finally:
                self.is_connected = False
