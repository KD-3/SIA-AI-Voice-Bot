"""ElevenLabs TTS service with true streaming support."""

import requests
import subprocess
import threading
from typing import Callable, Optional
from loguru import logger
from config import settings


class ElevenLabsTTSService:
    """
    ElevenLabs text-to-speech service with streaming support.

    Supports real-time audio generation for natural-sounding voices.
    """

    def __init__(self, on_audio: Callable[[bytes], None], should_stop_callback: Optional[Callable[[], bool]] = None):
        """
        Initialize ElevenLabs TTS service.

        Args:
            on_audio: Callback function(audio_chunk: bytes) for each audio chunk
            should_stop_callback: Optional callback that returns True if TTS should stop
        """
        self.on_audio = on_audio
        self.should_stop_callback = should_stop_callback
        self.api_key = settings.elevenlabs_api_key
        self.voice_id = "pNInz6obpgDQGcFmaJgB"  # Adam (free tier)
        self.is_connected = False

    def connect(self):
        """Initialize TTS service (validate API key)."""
        if not self.api_key:
            raise ValueError("ElevenLabs API key not configured")

        self.is_connected = True
        logger.info(f"✅ TTS: ElevenLabs connected (voice: {self.voice_id})")

    def synthesize_streaming(self, text: str):
        """
        Synthesize text to speech with true chunk-by-chunk streaming.

        Uses ffmpeg in pipe mode to convert MP3→μ-law as data arrives.

        Args:
            text: Text to synthesize
        """
        if not text or not text.strip():
            logger.warning("⚠️  TTS: Empty text, skipping synthesis")
            return

        try:
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}/stream"

            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.api_key
            }

            data = {
                "text": text,
                "model_id": "eleven_turbo_v2_5",  # Lowest latency model
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75,
                    "optimize_streaming_latency": 4,  # Max optimization
                }
            }

            logger.info(f"🔊 TTS: Synthesizing: '{text[:30]}...'")

            # Start ffmpeg process for streaming conversion
            ffmpeg_process = subprocess.Popen([
                'ffmpeg',
                '-i', 'pipe:0',  # Read MP3 from stdin
                '-f', 'mulaw',  # Output format: μ-law
                '-ar', '8000',  # Sample rate: 8kHz
                '-ac', '1',  # Mono
                '-loglevel', 'error',
                'pipe:1'  # Write μ-law to stdout
            ], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # Thread to read ffmpeg output and send audio chunks
            chunks_sent = 0
            stop_flag = threading.Event()

            def read_and_send_audio():
                nonlocal chunks_sent
                try:
                    while not stop_flag.is_set():
                        # Read 160 bytes (20ms at 8kHz μ-law)
                        chunk = ffmpeg_process.stdout.read(160)
                        if not chunk:
                            break

                        # Check if we should stop
                        if self.should_stop_callback and self.should_stop_callback():
                            logger.info(f"🛑 TTS: Stopped after {chunks_sent} chunks (interrupted)")
                            stop_flag.set()
                            break

                        if len(chunk) == 160:
                            self.on_audio(chunk)
                            chunks_sent += 1
                except Exception as e:
                    logger.error(f"❌ TTS: Error reading audio: {e}")
                finally:
                    stop_flag.set()

            # Start audio reading thread
            audio_thread = threading.Thread(target=read_and_send_audio, daemon=True)
            audio_thread.start()

            # Stream MP3 from ElevenLabs to ffmpeg stdin
            response = requests.post(url, headers=headers, json=data, stream=True)

            if response.status_code != 200:
                error_msg = response.text
                logger.error(f"❌ TTS: ElevenLabs API error ({response.status_code}): {error_msg}")
                ffmpeg_process.stdin.close()
                ffmpeg_process.kill()
                stop_flag.set()
                return

            # Stream MP3 chunks to ffmpeg
            for mp3_chunk in response.iter_content(chunk_size=4096):
                if stop_flag.is_set():
                    break
                if mp3_chunk:
                    try:
                        ffmpeg_process.stdin.write(mp3_chunk)
                        ffmpeg_process.stdin.flush()
                    except BrokenPipeError:
                        break

            # Close ffmpeg stdin to signal end of input
            ffmpeg_process.stdin.close()

            # Wait for audio thread to finish
            audio_thread.join(timeout=2.0)

            # Clean up ffmpeg process
            ffmpeg_process.wait(timeout=1.0)

            if not stop_flag.is_set():
                logger.debug(f"✅ TTS: Sent {chunks_sent} chunks")

        except Exception as e:
            logger.error(f"❌ TTS: Synthesis error: {e}")

    def synthesize(self, text: str) -> bytes:
        """
        Synthesize text to speech (non-streaming).

        Args:
            text: Text to synthesize

        Returns:
            Audio bytes in μ-law format
        """
        if not text or not text.strip():
            return b""

        try:
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"

            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.api_key
            }

            data = {
                "text": text,
                "model_id": "eleven_turbo_v2_5",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75
                }
            }

            response = requests.post(url, headers=headers, json=data)

            if response.status_code != 200:
                logger.error(f"❌ TTS: API error ({response.status_code}): {response.text}")
                return b""

            # Convert MP3 to μ-law
            mp3_data = response.content
            process = subprocess.run([
                'ffmpeg',
                '-i', 'pipe:0',
                '-f', 'mulaw',
                '-ar', '8000',
                '-ac', '1',
                '-loglevel', 'error',
                'pipe:1'
            ], input=mp3_data, capture_output=True)

            return process.stdout

        except Exception as e:
            logger.error(f"❌ TTS: Synthesis error: {e}")
            return b""

    def disconnect(self):
        """Clean up TTS resources."""
        self.is_connected = False
        logger.info("👋 TTS: ElevenLabs disconnected")
