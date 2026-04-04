"""Call session manager - orchestrates STT, LLM, and TTS."""

import asyncio
import base64
from typing import Optional
from loguru import logger
from datetime import datetime

from pipeline import STTService, LLMService, TTSService


class CallSession:
    """
    Manages a single call session with streaming audio pipeline.

    Flow: Audio In → STT → LLM → TTS → Audio Out
    """

    def __init__(self, session_id: str, caller_id: str):
        """
        Initialize call session.

        Args:
            session_id: Unique session identifier
            caller_id: Caller's phone number
        """
        self.session_id = session_id
        self.caller_id = caller_id
        self.started_at = datetime.now()

        # Audio buffers
        self.audio_out_queue = asyncio.Queue()
        self.current_transcript = ""
        self.is_ai_speaking = False

        # Services
        self.stt_service: Optional[STTService] = None
        self.llm_service: Optional[LLMService] = None
        self.tts_service: Optional[TTSService] = None

        # State
        self.is_active = False

        logger.info(f"📞 Session {session_id}: Created for {caller_id}")

    async def initialize(self):
        """Initialize all pipeline services."""
        try:
            logger.info(f"🚀 Session {self.session_id}: Initializing pipeline...")

            # Initialize STT (Deepgram)
            self.stt_service = STTService(on_transcript=self._on_transcript)
            await self.stt_service.connect()

            # Initialize LLM (GPT-4o)
            self.llm_service = LLMService(on_response=self._on_llm_response)
            self.llm_service.connect()

            # Set system prompt
            system_prompt = self._create_system_prompt()
            self.llm_service.set_system_prompt(system_prompt)

            # Initialize TTS (ElevenLabs)
            self.tts_service = TTSService(on_audio=self._on_tts_audio)
            self.tts_service.connect()

            self.is_active = True
            logger.info(f"✅ Session {self.session_id}: Pipeline ready")

            # Send initial greeting
            await self._send_greeting()

        except Exception as e:
            logger.error(f"❌ Session {self.session_id}: Initialization failed: {e}")
            raise

    def _create_system_prompt(self) -> str:
        """Create system prompt for the AI agent."""
        return f"""You are Alex, a friendly and professional AI sales assistant.

ROLE: You help qualify inbound leads and book appointments with the sales team.

CURRENT CONTEXT:
- Caller: {self.caller_id}
- Time: {self.started_at.strftime('%A, %B %d at %I:%M %p')}

INSTRUCTIONS:
1. Be warm and conversational (not robotic)
2. Listen actively and ask clarifying questions
3. Keep responses concise (1-2 sentences max)
4. Never hallucinate information you don't have
5. If unsure, say "Let me check on that and get back to you"

CONVERSATION FLOW:
1. Greet the caller warmly
2. Ask how you can help them today
3. Listen to their needs
4. Ask relevant follow-up questions
5. Provide helpful information
6. Offer to book a meeting with the sales team if appropriate

TONE: Friendly, professional, helpful (like a great SDR)
"""

    async def _send_greeting(self):
        """Send initial greeting to caller."""
        greeting = (
            "Hi! I'm Alex, an AI assistant. "
            "Thanks for calling! How can I help you today?"
        )
        logger.info(f"👋 Session {self.session_id}: Sending greeting")
        await self._speak(greeting)

    def _on_transcript(self, transcript: str, is_final: bool):
        """
        Handle transcript from STT.

        Args:
            transcript: Transcribed text
            is_final: Whether this is the final transcript
        """
        if not is_final:
            # Interim result - accumulate
            self.current_transcript = transcript
            return

        # Final transcript received
        logger.info(f"👤 User: {transcript}")

        # If AI is currently speaking, this is an interruption
        if self.is_ai_speaking:
            logger.warning(f"⚠️  Session {self.session_id}: User interrupted AI")
            # TODO: Implement interruption handling (cancel TTS)
            self.is_ai_speaking = False

        # Generate response from LLM
        asyncio.create_task(self._process_user_input(transcript))

        # Clear transcript buffer
        self.current_transcript = ""

    async def _process_user_input(self, user_input: str):
        """
        Process user input through LLM.

        Args:
            user_input: User's message
        """
        try:
            # Generate response (will call _on_llm_response)
            await self.llm_service.generate_response(user_input)
        except Exception as e:
            logger.error(f"❌ Session {self.session_id}: Error processing input: {e}")

    def _on_llm_response(self, response: str):
        """
        Handle response from LLM.

        Args:
            response: LLM's response text
        """
        logger.info(f"🤖 Assistant: {response}")

        # Convert text to speech
        asyncio.create_task(self._speak(response))

    async def _speak(self, text: str):
        """
        Convert text to speech and send to caller.

        Args:
            text: Text to speak
        """
        try:
            self.is_ai_speaking = True

            # Generate speech (will call _on_tts_audio for each chunk)
            await self.tts_service.synthesize_streaming(text)

            self.is_ai_speaking = False

        except Exception as e:
            logger.error(f"❌ Session {self.session_id}: TTS error: {e}")
            self.is_ai_speaking = False

    def _on_tts_audio(self, audio_chunk: bytes):
        """
        Handle audio chunk from TTS.

        Args:
            audio_chunk: Raw audio bytes
        """
        # Add to output queue to be sent to Twilio
        self.audio_out_queue.put_nowait(audio_chunk)

    async def process_audio_in(self, audio_data: bytes):
        """
        Process incoming audio from caller.

        Args:
            audio_data: Raw audio bytes from Twilio (μ-law, 8kHz)
        """
        if not self.is_active or not self.stt_service:
            return

        # Send audio to STT for transcription
        await self.stt_service.send_audio(audio_data)

    async def get_audio_out(self) -> Optional[bytes]:
        """
        Get next audio chunk to send to caller.

        Returns:
            Audio bytes or None if queue is empty
        """
        try:
            # Non-blocking get
            return self.audio_out_queue.get_nowait()
        except asyncio.QueueEmpty:
            return None

    async def cleanup(self):
        """Clean up session resources."""
        logger.info(f"🧹 Session {self.session_id}: Cleaning up...")

        self.is_active = False

        # Disconnect services
        if self.stt_service:
            await self.stt_service.disconnect()

        logger.info(f"👋 Session {self.session_id}: Cleaned up")

    def get_duration(self) -> float:
        """Get call duration in seconds."""
        return (datetime.now() - self.started_at).total_seconds()
