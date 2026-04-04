"""Call session manager - orchestrates STT, LLM, TTS, and Appointment Setting."""

import asyncio
import json
from typing import Dict, Optional
from loguru import logger
from datetime import datetime

from pipeline import (
    STTService,
    LLMService,
    SarvamTTSService,
    AppointmentService,
    APPOINTMENT_TOOLS,
    CompetitorKBService,
    COMPETITOR_KB_TOOLS,
)


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

        # ── Detected competitor context (updated during conversation) ────────
        self.detected_competitor: str = lead.get("current_competitor", "")

        # ── Audio buffers ────────────────────────────────────────────────────
        self.audio_out_queue: asyncio.Queue = asyncio.Queue()
        self.current_transcript: str = ""
        self.is_ai_speaking: bool = False

        # ── Services (set during initialize) ────────────────────────────────
        self.stt_service: Optional[STTService] = None
        self.llm_service: Optional[LLMService] = None
        self.tts_service: Optional[SarvamTTSService] = None
        self.appointment_service: Optional[AppointmentService] = None
        self.competitor_kb: Optional[CompetitorKBService] = None

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

            # Competitor KB service (Feature #2)
            self.competitor_kb = CompetitorKBService()

            # Merge all tool definitions: Appointment (#4) + Competitor KB (#2)
            all_tools = APPOINTMENT_TOOLS + COMPETITOR_KB_TOOLS

            # LLM (GPT-4o) — wired with all tools + handler
            self.llm_service = LLMService(
                on_response=self._on_llm_response,
                on_function_call=self._handle_function_call,
                tools=all_tools,
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
        competitor_line = (
            f"- Known competitor in use: {self.detected_competitor}"
            if self.detected_competitor
            else "- No competitor info yet — detect from conversation."
        )

        return f"""You are Priya, a friendly and persuasive Paytm AI sales assistant.

ROLE: You qualify merchant intent, identify the best Paytm product for them, handle competitor objections using data from the knowledge base, and set appointments for demos or document collection.

SESSION CONTEXT:
- Caller: {self.caller_id}
- Merchant name: {self.lead_name}
{area_line}
{docs_line}
{competitor_line}
- Current time: {self.started_at.strftime('%A, %d %B %Y at %I:%M %p IST')}

═══════════════════════════════════════════════════════════════
KNOWLEDGE BASE TOOLS (Feature #2 — Competitor Intelligence)
═══════════════════════════════════════════════════════════════

1. recommend_product_for_merchant
   WHEN: After learning the merchant's business type and pain points (usually after 1-2 discovery questions).
   WHY: Get a data-driven product recommendation instead of guessing.

2. lookup_paytm_product
   WHEN: You need specific pricing, features, or USPs to pitch or answer a question.
   WHY: Never make up pricing or features — always look up from the KB.

3. get_competitor_intel
   WHEN: The merchant mentions they use or were approached by a competitor (PhonePe, BharatPe, Razorpay, Pine Labs, Google Pay, Mswipe).
   WHY: Get their weaknesses and Paytm's specific advantages to use in your pitch.

4. get_objection_rebuttal
   WHEN: The merchant raises an objection (pricing, already using competitor, don't need it, etc.).
   WHY: Get a proven, tested rebuttal script with key talking points.
   IMPORTANT: Adapt the rebuttal to sound natural in conversation — don't read it verbatim.

5. get_comparison_matrix
   WHEN: The merchant is explicitly comparing options or asks "why Paytm over X?".
   WHY: Get a structured side-by-side comparison to present.

KB USAGE RULES:
- ALWAYS use lookup_paytm_product before quoting any pricing or feature details.
- ALWAYS use get_competitor_intel when a competitor is mentioned.
- When a merchant objects, ALWAYS call get_objection_rebuttal BEFORE responding.
- Use the rebuttal as inspiration — adapt it to fit the conversation naturally.
- Never say "according to our database" — present information as your own knowledge.
- Focus on 2-3 key differentiators per response, not all of them.

SELLING APPROACH:
1. DISCOVER: Ask about their business, current payment setup, and pain points.
2. RECOMMEND: Use recommend_product_for_merchant to find the best fit.
3. PITCH: Use lookup_paytm_product to deliver a tailored pitch.
4. HANDLE OBJECTIONS: Use get_objection_rebuttal for any pushback.
5. CLOSE: If interested, move to appointment booking.

═══════════════════════════════════════════════════════════════
APPOINTMENT TOOLS (Feature #4)
═══════════════════════════════════════════════════════════════

6. check_appointment_slots — call when the merchant agrees to a demo or KYC visit.
7. book_appointment — call ONLY AFTER the merchant confirms a specific slot.

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

═══════════════════════════════════════════════════════════════
DEVICE DELIVERY & ACTIVATION TOOLS (Feature #4 Extension)
═══════════════════════════════════════════════════════════════

8. confirm_device_delivery
   WHEN: Merchant has agreed to the product AND confirmed KYC documents are ready/submitted.
   WHY: Log the delivery, inform the merchant of their expected delivery date (3 business days).
   AFTER CALLING: ALWAYS ask — "Would you also like one of our field engineers to visit and help you set up the device when it arrives?"

9. check_activation_slots
   WHEN: Merchant says yes to activation help.
   WHY: Find available field engineer slots in the merchant's zone.
   NOTE: Field engineers use zones (e.g. "Central Bengaluru", "East Mumbai") — different from sales rep areas. Ask the merchant to confirm their zone if unsure.

10. book_activation_appointment
    WHEN: Merchant explicitly confirms a specific activation slot.
    WHY: Book the field engineer and send SMS confirmation.

DEVICE DELIVERY + ACTIVATION FLOW:
1. Merchant agrees to product + KYC confirmed → call confirm_device_delivery(product_name, area).
2. Narrate: "Your [product] will be delivered by [delivery_date]. I've also sent you an SMS with the details."
3. Immediately follow up: "Would you like one of our field engineers to come and help you activate the device?"
4. If yes → call check_activation_slots(zone) — use or ask for their zone.
5. Present slots: "I have [slot 1], [slot 2], or [slot 3] — which works best for you?"
6. Merchant confirms → call book_activation_appointment(slot_id, product_name).
7. Confirm: "Done! Your activation appointment with [engineer_name] is set for [readable_time]. I've sent the details to your phone."
8. If merchant declines activation help — acknowledge and close the conversation warmly.

═══════════════════════════════════════════════════════════════
GENERAL INSTRUCTIONS
═══════════════════════════════════════════════════════════════
- Be warm and conversational, not robotic.
- Keep responses concise (1-3 sentences for voice).
- Never make up slot times — always use check_appointment_slots first.
- Never make up pricing or features — always use lookup_paytm_product.
- If the merchant's area is not known, ask: "Which area are you based in? For example, South Bengaluru or North Mumbai?"
- Recommend digital KYC over physical document collection whenever possible.
- If a merchant uses a competitor, acknowledge it positively before differentiating.

TONE: Friendly, confident, knowledgeable — like a great sales consultant who genuinely wants to help.
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

    # ── Function call handler (Features #2 + #4) ──────────────────────────────

    async def _handle_function_call(self, function_name: str, args: Dict) -> str:
        """
        Dispatches LLM tool calls to AppointmentService or CompetitorKBService.

        Returns:
            JSON string to feed back to the LLM as the tool result.
        """
        # ── Feature #4: Appointment tools ────────────────────────────────
        if function_name == "check_appointment_slots":
            if not self.appointment_service:
                return json.dumps({"error": "Appointment service not initialised."})

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
            if not self.appointment_service:
                return json.dumps({"error": "Appointment service not initialised."})

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

        # ── Feature #4 extension: Device delivery + activation ───────────
        if function_name == "confirm_device_delivery":
            if not self.appointment_service:
                return json.dumps({"error": "Appointment service not initialised."})

            result = await self.appointment_service.confirm_device_delivery(
                lead_phone=self.caller_id,
                product_name=args.get("product_name", "Paytm Device"),
                lead_name=self.lead_name,
                area=args.get("area", self.lead_area or ""),
            )
            logger.info(
                f"📦 Delivery confirmed for session {self.session_id}: "
                f"date={result.get('delivery_date')}"
            )
            return json.dumps(result)

        if function_name == "check_activation_slots":
            if not self.appointment_service:
                return json.dumps({"error": "Appointment service not initialised."})

            zone = args.get("zone", "")
            if not zone:
                return json.dumps({
                    "error": "Zone is required. Ask the merchant which zone they are in, e.g. Central Bengaluru or East Mumbai."
                })

            result = await self.appointment_service.find_activation_slots(zone)
            logger.info(
                f"🔧 Activation slots for zone {zone}: {len(result.get('slots', []))} option(s)"
            )
            return json.dumps(result)

        if function_name == "book_activation_appointment":
            if not self.appointment_service:
                return json.dumps({"error": "Appointment service not initialised."})

            slot_id = args.get("slot_id", "")
            if not slot_id:
                return json.dumps({"error": "slot_id is required."})

            result = await self.appointment_service.book_activation_appointment(
                slot_id=slot_id,
                lead_phone=self.caller_id,
                product_name=args.get("product_name", "Paytm Device"),
                lead_name=self.lead_name,
            )
            logger.info(
                f"🔧 Activation booking for session {self.session_id}: "
                f"success={result.get('success')}"
            )
            return json.dumps(result)

        # ── Feature #2: Competitor KB tools ──────────────────────────────
        if not self.competitor_kb:
            if function_name in (
                "lookup_paytm_product", "recommend_product_for_merchant",
                "get_competitor_intel", "get_objection_rebuttal",
                "get_comparison_matrix",
            ):
                return json.dumps({"error": "Competitor KB not initialised."})

        if function_name == "lookup_paytm_product":
            product_id = args.get("product_id", "")
            result = self.competitor_kb.get_product_details(product_id)
            logger.info(f"📦 KB lookup: product={product_id}")
            return json.dumps(result)

        if function_name == "recommend_product_for_merchant":
            result = self.competitor_kb.recommend_product(args)
            recs = result.get("recommendations", [])
            logger.info(
                f"🎯 KB recommendation: {len(recs)} product(s) for "
                f"biz_type={args.get('business_type', '?')}"
            )
            return json.dumps(result)

        if function_name == "get_competitor_intel":
            competitor_id = args.get("competitor_id", "")
            include_full = args.get("include_full_profile", False)

            # Track detected competitor for context
            if competitor_id and not self.detected_competitor:
                self.detected_competitor = competitor_id

            if include_full:
                result = self.competitor_kb.get_competitor_profile(competitor_id)
            else:
                result = self.competitor_kb.get_competitor_weaknesses(competitor_id)
            logger.info(f"🕵️ KB competitor intel: {competitor_id}")
            return json.dumps(result)

        if function_name == "get_objection_rebuttal":
            competitor_id = args.get("competitor_id", "generic")
            objection_type = args.get("objection_type", "")
            result = self.competitor_kb.get_rebuttal(competitor_id, objection_type)
            logger.info(f"🛡️ KB rebuttal: ({competitor_id}, {objection_type})")
            return json.dumps(result)

        if function_name == "get_comparison_matrix":
            category = args.get("category", "")
            competitors = args.get("competitors", None)
            result = self.competitor_kb.get_comparison(category, competitors)
            logger.info(f"📊 KB comparison: {category}")
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
