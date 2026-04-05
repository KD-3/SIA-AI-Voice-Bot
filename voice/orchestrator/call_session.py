"""Call session manager - orchestrates STT, LLM, and TTS."""

import asyncio
import base64
from typing import Optional
from loguru import logger
from datetime import datetime

from pipeline import STTService, LLMService, ElevenLabsTTSService


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
        self.should_stop_speaking = False
        self.current_tts_task = None
        self.tts_sentence_queue = asyncio.Queue()
        self.tts_worker_task = None
        self.current_llm_task = None

        # Services
        self.stt_service: Optional[STTService] = None
        self.llm_service: Optional[LLMService] = None
        self.tts_service: Optional[ElevenLabsTTSService] = None

        # State
        self.is_active = False
        self.loop: Optional[asyncio.AbstractEventLoop] = None

        # Transcript & Post-call data
        self.transcript: list[dict] = []  # [{"role": "user"|"assistant", "text": ...}]
        self.call_summary: Optional[dict] = None  # populated after call ends

        logger.info(f"📞 Session {session_id}: Created for {caller_id}")

    async def initialize(self):
        """Initialize all pipeline services."""
        try:
            # Store the event loop for thread-safe task scheduling
            self.loop = asyncio.get_running_loop()
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

            # Initialize TTS (ElevenLabs) with interruption callback
            self.tts_service = ElevenLabsTTSService(
                on_audio=self._on_tts_audio,
                should_stop_callback=lambda: self.should_stop_speaking
            )
            self.tts_service.connect()

            self.is_active = True
            logger.info(f"✅ Session {self.session_id}: Pipeline ready")

            # Start TTS worker task
            self.tts_worker_task = self.loop.create_task(self._tts_worker())

            # Send initial greeting (non-blocking)
            asyncio.run_coroutine_threadsafe(
                self._send_greeting(),
                self.loop
            )

        except Exception as e:
            logger.error(f"❌ Session {self.session_id}: Initialization failed: {e}")
            raise

    def _create_system_prompt(self) -> str:
        """Create system prompt for the AI agent."""
        return f"""You are Sia, a calm, smooth, and empathetic AI voice agent by Paytm.

ROLE: You reach out to potential customers to pitch Paytm's merchant devices (like Soundbox, EDC, POS), explain their USPs, and how they are better than the competition. Your ultimate goal is to convince the person to buy a device and schedule an appointment date and time for a human sales agent to call them and finalize the setup.

CURRENT CONTEXT:
- Caller: {self.caller_id}
- Time: {self.started_at.strftime('%A, %B %d at %I:%M %p')}

INSTRUCTIONS:
1. Be exceptionally calm, empathetic, and professional with a smooth conversational tone.
2. Listen actively to their business needs, objections, or concerns.
3. Pitch the right Paytm product and articulate clearly why it's better than competitors (e.g., faster settlements, instant reliable audio alerts, lower network downtime).
4. Do not be pushy. Try to convince them empathetically.
5. Emphasize that the next step is just scheduling a quick follow-up call with a dedicated human expert. Ask for a suitable date and time for this call.
6. MANDATORY DATA COLLECTION: Once they agree to a follow-up, you MUST politely collect and confirm the following details one by one (do not ask for all at once):
   - The best date and time for the human agent's call.
   - The decision maker's name.
   - An alternate contact number (if different from the one they are calling from).
7. Keep responses concise (1-2 sentences max) so it feels like a real two-way conversation.
8. Never hallucinate information you don't have.

CONVERSATION FLOW:
1. Greet the customer warmly and ask about their business.
2. Share a quick detail about how a Paytm device can help them.
3. Listen to their response and needs.
4. Explain the USP of the relevant device against competition.
5. Propose scheduling an appointment for a human expert to call them back.
6. Slowly but conversationally collect the required details (Date/Time, Name, Best Number).
7. Confirm the scheduling details and warmly end the call.
"""

    async def _send_greeting(self):
        """Send initial greeting to caller."""
        greeting = (
            "Hi there! This is SIA calling from Paytm. "
            "How is your business doing today?"
        )
        logger.info(f"👋 Session {self.session_id}: Sending greeting")
        await self._speak(greeting)

    def _on_transcript(self, transcript: str, is_final: bool):
        """
        Handle transcript from STT (called from Deepgram's background thread).
        """
        if self.loop and self.loop.is_running():
            # Thread-safe handoff to the asyncio event loop
            self.loop.call_soon_threadsafe(
                self._handle_transcript_threadsafe, transcript, is_final
            )
        else:
            logger.error(f"❌ Session {self.session_id}: Event loop not available")

    def _handle_transcript_threadsafe(self, transcript: str, is_final: bool):
        """Synchronously executed within the event loop to manage strictly ordered task execution."""
        if is_final:
            # INTERRUPT: Cancel the previous generation task instantly to stop stale data
            if self.current_llm_task and not self.current_llm_task.done():
                self.current_llm_task.cancel()
                logger.info(f"🛑 Session {self.session_id}: Hard-cancelled previous LLM processing task")

            self.current_llm_task = asyncio.create_task(self._async_on_transcript(transcript, is_final))
        else:
            asyncio.create_task(self._async_on_transcript(transcript, is_final))

    async def _async_on_transcript(self, transcript: str, is_final: bool):
        """Async implementation of transcript handling running on the main event loop."""
        if not is_final:
            # Interim result - accumulate
            self.current_transcript = transcript
            return

        # Capture user utterance in transcript log
        self.transcript.append({"role": "user", "text": transcript})

        # Final transcript received
        logger.info(f"👤 User: {transcript}")

        # If AI is currently speaking, this is an interruption
        if self.is_ai_speaking:
            logger.warning(f"🛑 Session {self.session_id}: User interrupted AI")

            # Cancel current TTS task
            if self.current_tts_task and not self.current_tts_task.done():
                self.current_tts_task.cancel()
                logger.info(f"❌ Session {self.session_id}: Cancelled TTS task")

            # Stop current speech
            self.should_stop_speaking = True
            self.is_ai_speaking = False

            # Clear sentence queue
            while not self.tts_sentence_queue.empty():
                try:
                    self.tts_sentence_queue.get_nowait()
                except:
                    break

            # Clear the audio queue
            while not self.audio_out_queue.empty():
                try:
                    self.audio_out_queue.get_nowait()
                except:
                    break
            
            # Notify main loop to clear the Twilio media buffer
            self.audio_out_queue.put_nowait(b"CLEAR")

        # Generate response from LLM
        await self._process_user_input(transcript)

        # Clear transcript buffer
        self.current_transcript = ""

    async def _process_user_input(self, user_input: str):
        """
        Process user input through LLM with streaming.

        Args:
            user_input: User's message
        """
        try:
            # We are generating a new response, so re-enable speaking!
            self.should_stop_speaking = False

            # Generate streaming response (will call _on_llm_response for each sentence)
            await self.llm_service.generate_response_streaming(user_input)
        except asyncio.CancelledError:
            logger.info(f"🛑 Session {self.session_id}: LLM processing safely cancelled by interruption")
        except Exception as e:
            logger.error(f"❌ Session {self.session_id}: Error processing input: {e}")

    def _on_llm_response(self, response: str):
        """
        Handle response from LLM.

        Args:
            response: LLM's response text
        """
        logger.info(f"🤖 Assistant: {response}")

        # Capture assistant response in transcript log
        self.transcript.append({"role": "assistant", "text": response})

        # Send to sequential TTS queue (thread-safe)
        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.tts_sentence_queue.put_nowait, response)
        else:
            logger.error(f"❌ Session {self.session_id}: Cannot speak, no event loop")

    async def _tts_worker(self):
        """Background task to synthesize and speak sentences strictly sequentially."""
        while self.is_active:
            try:
                # Wait for next sentence
                sentence = await self.tts_sentence_queue.get()
                
                # Speak it if we haven't been interrupted
                if not self.should_stop_speaking:
                    await self._speak(sentence)
                
                self.tts_sentence_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ TTS worker error: {e}")

    async def _speak(self, text: str):
        """
        Convert text to speech and send to caller.

        Args:
            text: Text to speak
        """
        try:
            self.is_ai_speaking = True
            self.should_stop_speaking = False

            # Run TTS in thread executor (it uses blocking requests.post)
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(
                None,  # Use default thread pool
                self.tts_service.synthesize_streaming,
                text
            )

            # Only mark as done if we weren't interrupted
            if not self.should_stop_speaking:
                self.is_ai_speaking = False
            else:
                logger.info(f"🛑 Session {self.session_id}: Speech interrupted")

        except Exception as e:
            logger.error(f"❌ Session {self.session_id}: TTS error: {e}")
            self.is_ai_speaking = False
            self.should_stop_speaking = False

    def _on_tts_audio(self, audio_chunk: bytes):
        """
        Handle audio chunk from TTS.

        Args:
            audio_chunk: Raw audio bytes
        """
        # Don't add audio if we've been interrupted
        if not self.should_stop_speaking:
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

        if self.tts_worker_task:
            self.tts_worker_task.cancel()

        # Disconnect services
        if self.stt_service:
            await self.stt_service.disconnect()

        # Generate post-call summary
        try:
            await self._generate_summary()
        except Exception as e:
            logger.error(f"❌ Summary generation failed: {e}")

        logger.info(f"👋 Session {self.session_id}: Cleaned up")

    async def _generate_summary(self):
        """Use GPT to generate a structured post-call summary."""
        if not self.transcript:
            return

        from openai import AsyncOpenAI
        from config.settings import settings
        import json

        client = AsyncOpenAI(api_key=settings.openai_api_key)

        # Build a plain text version of the transcript for GPT
        transcript_text = "\n".join(
            f"{t['role'].upper()}: {t['text']}" for t in self.transcript
        )

        prompt = f"""You are a CRM analyst. Analyze the following sales call transcript between an AI agent (Sia from Paytm) and a merchant prospect.

Transcript:
{transcript_text}

Respond ONLY with valid JSON in the following format:
{{
  "summary": "<2-3 sentence summary of the call>",
  "lead_rating": <integer 1 to 5, where 5 is highly interested>,
  "sentiment": "<Positive|Neutral|Negative>",
  "key_highlights": ["<highlight 1>", "<highlight 2>"],
  "next_actions": ["<action 1>", "<action 2>"]
}}"""

        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            response_format={"type": "json_object"}
        )

        summary_json = json.loads(response.choices[0].message.content)
        self.call_summary = {
            **summary_json,
            "transcript": self.transcript,
            "duration_seconds": int(self.get_duration()),
            "caller_id": self.caller_id,
            "session_id": self.session_id,
        }
        logger.info(f"📋 Session {self.session_id}: Summary generated — Rating {summary_json.get('lead_rating')}/5")

    def get_duration(self) -> float:
        """Get call duration in seconds."""
        return (datetime.now() - self.started_at).total_seconds()
