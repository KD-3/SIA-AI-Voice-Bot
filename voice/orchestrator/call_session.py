"""Call session manager - orchestrates STT, LLM, TTS, and Appointment Setting."""

import asyncio
import json
from typing import Dict, Optional
from loguru import logger
from datetime import datetime

from pipeline import STTService, LLMService, SarvamTTSService, AppointmentService, APPOINTMENT_TOOLS


class CallSession:
    """
    Manages a single call session with streaming audio pipeline.

    Flow: Audio In → STT → LLM (+ tool calls) → TTS → Audio Out

    Feature #4 additions
    --------------------
    - Accepts optional `lead_data` dict from upstream (features #1-#3) carrying:
        lead_name, lead_area, needs_document_collection, lead_phone
    - Wires AppointmentService as the LLM function-call handler so the bot can
      check slots and book appointments mid-conversation.
    """

    def __init__(
        self,
        session_id: str,
        caller_id: str,
        lead_data: Optional[Dict] = None,
    ):
        """
        Args:
            session_id: Unique session identifier
            caller_id:  Caller's phone number (E.164 format)
            lead_data:  Optional enrichment from CRM/DB (features #1-#3).
                        Keys used here:
                          lead_name               – merchant's name
                          lead_area               – e.g. "South Bengaluru"
                          needs_document_collection – bool from qualification step
        """
        self.session_id = session_id
        self.caller_id = caller_id
        self.started_at = datetime.now()

        # ── Lead enrichment (populated by features #1-#3, defaulted here) ──
        lead = lead_data or {}
        self.lead_name: str = lead.get("lead_name", "Merchant")
        self.lead_area: str = lead.get("lead_area", "")   # LLM will extract if blank
        self.needs_document_collection: bool = lead.get("needs_document_collection", False)

        # ── Audio buffers ────────────────────────────────────────────────────
        self.audio_out_queue: asyncio.Queue = asyncio.Queue()
        self.current_transcript: str = ""
        self.is_ai_speaking: bool = False

        # ── Services (set during initialize) ────────────────────────────────
        self.stt_service: Optional[STTService] = None
        self.llm_service: Optional[LLMService] = None
        self.tts_service: Optional[SarvamTTSService] = None
        self.appointment_service: Optional[AppointmentService] = None

        self.is_active: bool = False

        logger.info(
            f"📞 Session {session_id}: Created for {caller_id} "
            f"| area={self.lead_area or 'unknown'} "
            f"| docs_needed={self.needs_document_collection}"
        )

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    async def initialize(self):
        """Initialize all pipeline services."""
        try:
            logger.info(f"🚀 Session {self.session_id}: Initializing pipeline...")

            # STT (Deepgram)
            self.stt_service = STTService(on_transcript=self._on_transcript)
            await self.stt_service.connect()

            # Appointment service
            self.appointment_service = AppointmentService()

            # LLM (GPT-4o) — wired with appointment tools + handler
            self.llm_service = LLMService(
                on_response=self._on_llm_response,
                on_function_call=self._handle_function_call,
                tools=APPOINTMENT_TOOLS,
            )
            self.llm_service.connect()
            self.llm_service.set_system_prompt(self._create_system_prompt())

            # TTS (Sarvam AI)
            self.tts_service = SarvamTTSService(on_audio=self._on_tts_audio)
            self.tts_service.connect()

            self.is_active = True
            logger.info(f"✅ Session {self.session_id}: Pipeline ready")

            await self._send_greeting()

        except Exception as e:
            logger.error(f"❌ Session {self.session_id}: Initialization failed: {e}")
            raise

    async def cleanup(self):
        """Clean up session resources."""
        logger.info(f"🧹 Session {self.session_id}: Cleaning up...")
        self.is_active = False
        if self.stt_service:
            await self.stt_service.disconnect()
        logger.info(f"👋 Session {self.session_id}: Cleaned up")

    # ── System prompt ─────────────────────────────────────────────────────────

    def _create_system_prompt(self) -> str:
        area_line = f"- Merchant's area: {self.lead_area}" if self.lead_area else \
                    "- Merchant's area: Unknown (extract from conversation)"
        docs_line = (
            "- The merchant has previously requested KYC document collection — "
            "mention this while setting the appointment."
            if self.needs_document_collection
            else "- No prior document collection request."
        )
        return f"""You are Priya, a friendly Paytm AI sales assistant.

ROLE: You help merchants understand Paytm products and set appointments for demos or document collection.

SESSION CONTEXT:
- Caller: {self.caller_id}
- Merchant name: {self.lead_name}
{area_line}
{docs_line}
- Current time: {self.started_at.strftime('%A, %d %B %Y at %I:%M %p IST')}

TOOLS AVAILABLE:
1. check_appointment_slots — call this as soon as the merchant agrees to a demo or KYC visit.
2. book_appointment — call this only AFTER the merchant has explicitly confirmed a specific slot.

APPOINTMENT FLOW:
1. When the merchant agrees to a demo (or KYC visit), call check_appointment_slots with their area and appointment_type.
2. Present the returned slots naturally: "I have a few options for you — [slot 1], [slot 2], or [slot 3]. Which works best?"
3. Once they choose, confirm: "Great! Let me book [chosen slot] for you."
4. Call book_appointment with the chosen slot_id.
5. Relay the result: "Done! Your appointment with [rep_name] is confirmed for [readable_time]. I've also sent you an SMS confirmation."
6. If needs_document_collection is true AND appointment_type is "demo", set needs_document_collection=true in the booking so the rep knows to bring collection materials.

DOCUMENT COLLECTION NOTE:
If the merchant earlier asked for document collection, mention it while confirming the slot:
"I'll also let [rep_name] know to collect your KYC documents during the visit."

GENERAL INSTRUCTIONS:
- Be warm and conversational, not robotic.
- Keep responses concise (1-3 sentences for voice).
- Never make up slot times — always use check_appointment_slots first.
- If the merchant's area is not known, ask: "Which area are you based in? For example, South Bengaluru or North Mumbai?"
- Recommend digital KYC over physical document collection whenever possible.

TONE: Friendly, professional, helpful — like a great sales assistant at a top fintech company.
"""

    # ── Greeting ──────────────────────────────────────────────────────────────

    async def _send_greeting(self):
        name_part = f", {self.lead_name}" if self.lead_name and self.lead_name != "Merchant" else ""
        greeting = (
            f"Hello{name_part}! I'm Priya from Paytm. "
            "How can I help you today?"
        )
        logger.info(f"👋 Session {self.session_id}: Sending greeting")
        await self._speak(greeting)

    # ── Audio pipeline callbacks ──────────────────────────────────────────────

    def _on_transcript(self, transcript: str, is_final: bool):
        if not is_final:
            self.current_transcript = transcript
            return

        logger.info(f"👤 User: {transcript}")

        if self.is_ai_speaking:
            logger.warning(f"⚠️  Session {self.session_id}: User interrupted AI")
            self.is_ai_speaking = False

        asyncio.create_task(self._process_user_input(transcript))
        self.current_transcript = ""

    async def _process_user_input(self, user_input: str):
        try:
            # Use tool-aware generation for all turns
            await self.llm_service.generate_response_with_tools(user_input)
        except Exception as e:
            logger.error(f"❌ Session {self.session_id}: Error processing input: {e}")

    def _on_llm_response(self, response: str):
        logger.info(f"🤖 Assistant: {response}")
        asyncio.create_task(self._speak(response))

    async def _speak(self, text: str):
        try:
            self.is_ai_speaking = True
            await self.tts_service.synthesize_streaming(text)
            self.is_ai_speaking = False
        except Exception as e:
            logger.error(f"❌ Session {self.session_id}: TTS error: {e}")
            self.is_ai_speaking = False

    def _on_tts_audio(self, audio_chunk: bytes):
        self.audio_out_queue.put_nowait(audio_chunk)

    # ── Function call handler (Feature #4) ───────────────────────────────────

    async def _handle_function_call(self, function_name: str, args: Dict) -> str:
        """
        Dispatches LLM tool calls to AppointmentService.

        Returns:
            JSON string to feed back to the LLM as the tool result.
        """
        if not self.appointment_service:
            return json.dumps({"error": "Appointment service not initialised."})

        if function_name == "check_appointment_slots":
            area = args.get("area", self.lead_area or "")
            appt_type = args.get("appointment_type", "demo")

            if not area:
                return json.dumps({
                    "error": "Area is required. Ask the merchant which area they operate in."
                })

            # Cache area for potential follow-up booking
            if not self.lead_area:
                self.lead_area = area

            result = await self.appointment_service.find_available_slots(area, appt_type)
            logger.info(
                f"🗓 Slots found for {area}: {len(result.get('slots', []))} option(s)"
            )
            return json.dumps(result)

        if function_name == "book_appointment":
            slot_id = args.get("slot_id", "")
            appt_type = args.get("appointment_type", "demo")
            needs_docs = args.get("needs_document_collection", self.needs_document_collection)

            if not slot_id:
                return json.dumps({"error": "slot_id is required."})

            result = await self.appointment_service.book_appointment(
                slot_id=slot_id,
                lead_phone=self.caller_id,
                appointment_type=appt_type,
                needs_document_collection=needs_docs,
                lead_name=self.lead_name,
            )
            logger.info(
                f"📅 Booking result for session {self.session_id}: "
                f"success={result.get('success')}"
            )
            return json.dumps(result)

        return json.dumps({"error": f"Unknown function: {function_name}"})

    # ── Audio I/O ─────────────────────────────────────────────────────────────

    async def process_audio_in(self, audio_data: bytes):
        if not self.is_active or not self.stt_service:
            return
        await self.stt_service.send_audio(audio_data)

    async def get_audio_out(self) -> Optional[bytes]:
        try:
            return self.audio_out_queue.get_nowait()
        except asyncio.QueueEmpty:
            return None

    def get_duration(self) -> float:
        return (datetime.now() - self.started_at).total_seconds()
