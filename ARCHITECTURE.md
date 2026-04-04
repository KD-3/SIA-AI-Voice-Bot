# AI Voice Bot Architecture - Complete System Design

## Table of Contents
1. [System Overview](#system-overview)
2. [End-to-End Call Flow](#end-to-end-call-flow)
3. [Architecture Diagram](#architecture-diagram)
4. [Component Details](#component-details)
5. [Data Flow](#data-flow)
6. [Technology Stack](#technology-stack)
7. [Implementation Phases](#implementation-phases)

---

## System Overview

**Goal**: Autonomous AI voice bot that handles inbound/outbound calls, qualifies leads, books appointments, and updates CRM - all without human intervention.

**Key Capabilities**:
- Real-time voice conversation with <300ms latency
- Full-duplex (can be interrupted naturally)
- Context-aware (remembers conversation history + CRM data)
- Autonomous actions (book meetings, send emails, update CRM)
- TCPA compliant (consent tracking, call recording disclosure)

---

## End-to-End Call Flow

### **Inbound Lead Call Journey**

```
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 1: CALL INITIATION (0-5 seconds)                        │
└─────────────────────────────────────────────────────────────────┘

1. Lead calls company phone number (Twilio number)
   ↓
2. Twilio receives call → triggers webhook to our backend
   ↓
3. Backend creates session:
   - Generate unique session_id
   - Look up caller_id in CRM (if exists, pull contact data)
   - Initialize conversation state machine
   - Start call recording
   ↓
4. Twilio connects call to Media Streams (bidirectional audio)
   ↓
5. Backend announces: "This call may be recorded for quality purposes"
   ↓
6. AI Voice Agent starts greeting

┌─────────────────────────────────────────────────────────────────┐
│  PHASE 2: GREETING & CONTEXT LOADING (5-15 seconds)            │
└─────────────────────────────────────────────────────────────────┘

7. AI speaks (via ElevenLabs TTS):
   "Hi! I'm Alex, an AI assistant from [Company].
    I noticed you [called about X / filled out a form about Y].
    Do you have a minute to chat?"

   [PARALLEL]: While speaking, backend loads:
   - Customer history from CRM
   - Company knowledge base
   - Qualification script template
   - Available meeting slots from calendar

8. User responds (captured by Deepgram STT in real-time)
   ↓
9. Conversation state → "QUALIFYING"

┌─────────────────────────────────────────────────────────────────┐
│  PHASE 3: QUALIFICATION (1-3 minutes)                           │
└─────────────────────────────────────────────────────────────────┘

10. AI asks discovery questions (BANT framework):
    - Budget: "What's your budget range for this?"
    - Authority: "Are you the decision maker?"
    - Need: "What problem are you trying to solve?"
    - Timeline: "When are you looking to get started?"

11. For each user response:
    - Deepgram STT → transcribes in real-time chunks
    - GPT-4o Realtime API → processes audio + generates response
    - Response validated against knowledge base (RAG)
    - ElevenLabs TTS → speaks response
    - All in <300ms (streaming pipeline)

12. AI detects interruptions:
    - Voice Activity Detection (VAD) detects user started speaking
    - Immediately stops TTS mid-sentence
    - Listens to user's full interruption
    - Responds naturally

13. Backend calculates lead score in real-time:
    - Budget match: 0-25 points
    - Authority: 0-25 points
    - Need fit: 0-25 points
    - Timeline urgency: 0-25 points
    - Total: 0-100 (60+ = qualified)

14. Conversation memory:
    - Every exchange stored in session state
    - Vector embeddings created for semantic search
    - Context passed to next LLM call

┌─────────────────────────────────────────────────────────────────┐
│  PHASE 4: PITCH & OBJECTION HANDLING (1-2 minutes)             │
└─────────────────────────────────────────────────────────────────┘

15. If lead_score >= 60:
    AI delivers tailored pitch:
    - References their stated needs
    - Highlights relevant features from knowledge base
    - Provides social proof / case studies

16. If lead raises objections:
    - Detect objection type (price, timing, features, trust)
    - Retrieve objection handling script from knowledge base
    - Respond with empathy + information
    - Re-qualify if needed

17. If lead_score < 60:
    AI politely disqualifies:
    "Thanks for your interest. Based on what you shared,
     I think [alternative solution] might be a better fit.
     Can I send you some information?"
    → Send nurture email, end call

┌─────────────────────────────────────────────────────────────────┐
│  PHASE 5: APPOINTMENT BOOKING (30-60 seconds)                  │
└─────────────────────────────────────────────────────────────────┘

18. For qualified leads, AI proposes meeting:
    "I'd love to have [Sales Rep Name] walk you through a
     personalized demo. Let me check the calendar..."

19. Backend queries Google Calendar API:
    - Find next 3 available slots
    - Filter by business hours + rep availability
    - Return options to AI

20. AI presents choices:
    "Are you free Tuesday at 2pm, Wednesday at 10am,
     or Thursday at 3pm?"

21. User selects time → AI confirms:
    "Perfect! I'm booking Tuesday April 8th at 2pm for you."

22. Backend executes booking workflow:
    ✓ Create Google Calendar event
    ✓ Send calendar invite (.ics) to lead's email
    ✓ Send confirmation email (SendGrid) with:
      - Meeting details
      - Zoom/Meet link
      - What to prepare
    ✓ Send SMS confirmation (Twilio SMS)
    ✓ Schedule SMS reminder for 1 hour before meeting

┌─────────────────────────────────────────────────────────────────┐
│  PHASE 6: CRM UPDATE & FOLLOW-UP (background, async)           │
└─────────────────────────────────────────────────────────────────┘

23. Backend updates CRM (HubSpot/Salesforce):
    ✓ Create or update contact record
    ✓ Log call activity with:
      - Full transcript
      - Call duration
      - Lead score
      - Call outcome (booked, not interested, callback)
      - Sentiment analysis
    ✓ Create opportunity/deal
    ✓ Set deal stage to "Meeting Scheduled"
    ✓ Assign to sales rep
    ✓ Create follow-up task for rep

24. AI closes call:
    "Great! You'll receive a confirmation email and calendar
     invite shortly. Looking forward to speaking with you Tuesday.
     Have a great day!"

25. Post-call processing:
    ✓ Save full call recording to S3
    ✓ Generate conversation summary (GPT-4)
    ✓ Extract key insights (pain points, budget, objections)
    ✓ Store in vector database for future reference
    ✓ Trigger analytics pipeline
    ✓ Update conversion dashboards

┌─────────────────────────────────────────────────────────────────┐
│  PHASE 7: AUTOMATED FOLLOW-UP (hours/days after call)          │
└─────────────────────────────────────────────────────────────────┘

26. T+1 hour before meeting:
    → Send SMS reminder: "Your meeting with [Rep] is in 1 hour!"

27. If no-show detected:
    → Trigger re-engagement sequence:
      - Email: "We missed you! Want to reschedule?"
      - SMS: "Tap here to reschedule in 30 seconds"

28. If meeting happened:
    → Send post-meeting email:
      - Recap of discussion
      - Next steps
      - Resources shared
      - Proposal/quote (if applicable)
```

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                 CLIENT LAYER                                     │
│                                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                     │
│  │   PSTN       │    │   WebRTC     │    │   Mobile     │                     │
│  │  (Phone)     │    │   (Browser)  │    │   (App)      │                     │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘                     │
│         │                    │                    │                             │
└─────────┼────────────────────┼────────────────────┼─────────────────────────────┘
          │                    │                    │
          ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            TELEPHONY LAYER                                       │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐  │
│  │                          TWILIO                                          │  │
│  │                                                                          │  │
│  │  • Programmable Voice (call routing)                                    │  │
│  │  • Media Streams (bidirectional audio: WebSocket)                       │  │
│  │  • SMS (appointment confirmations, reminders)                           │  │
│  │  • Call Recording                                                       │  │
│  └───────────────────────────────┬──────────────────────────────────────┘  │
└───────────────────────────────────┼──────────────────────────────────────────┘
                                    │
                                    │ WebSocket (audio stream)
                                    │ Webhook (call events)
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         ORCHESTRATION LAYER (CORE)                               │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐  │
│  │                   PIPECAT FRAMEWORK (Python)                             │  │
│  │                                                                          │  │
│  │  ┌────────────────────────────────────────────────────────────────┐    │  │
│  │  │  Session Manager                                                │    │  │
│  │  │  • Create/destroy sessions                                      │    │  │
│  │  │  • Track active calls                                          │    │  │
│  │  │  • Manage conversation state                                   │    │  │
│  │  └────────────────────────────────────────────────────────────────┘    │  │
│  │                                                                          │  │
│  │  ┌────────────────────────────────────────────────────────────────┐    │  │
│  │  │  Conversation State Machine                                    │    │  │
│  │  │                                                                 │    │  │
│  │  │  IDLE → GREETING → QUALIFYING → PITCHING →                     │    │  │
│  │  │  BOOKING → CONFIRMING → CLOSING → ENDED                        │    │  │
│  │  │                                                                 │    │  │
│  │  │  • Handles state transitions                                   │    │  │
│  │  │  • Manages conversation flow                                   │    │  │
│  │  │  • Triggers appropriate actions per state                      │    │  │
│  │  └────────────────────────────────────────────────────────────────┘    │  │
│  │                                                                          │  │
│  │  ┌────────────────────────────────────────────────────────────────┐    │  │
│  │  │  Audio Pipeline Manager (STREAMING)                            │    │  │
│  │  │                                                                 │    │  │
│  │  │  Audio In (WebSocket) ──→ STT (streaming chunks) ──→           │    │  │
│  │  │  LLM (streaming tokens) ──→ TTS (streaming audio) ──→          │    │  │
│  │  │  Audio Out (WebSocket)                                         │    │  │
│  │  │                                                                 │    │  │
│  │  │  • All components stream simultaneously                        │    │  │
│  │  │  • Target latency: <250ms end-to-end                          │    │  │
│  │  └────────────────────────────────────────────────────────────────┘    │  │
│  │                                                                          │  │
│  │  ┌────────────────────────────────────────────────────────────────┐    │  │
│  │  │  Interruption Handler                                          │    │  │
│  │  │                                                                 │    │  │
│  │  │  • Voice Activity Detection (VAD)                              │    │  │
│  │  │  • Detect user speech during AI speaking                       │    │  │
│  │  │  • Cancel TTS immediately                                      │    │  │
│  │  │  • Buffer partial user input                                   │    │  │
│  │  │  • Resume conversation naturally                               │    │  │
│  │  └────────────────────────────────────────────────────────────────┘    │  │
│  │                                                                          │  │
│  │  ┌────────────────────────────────────────────────────────────────┐    │  │
│  │  │  Context Manager                                               │    │  │
│  │  │                                                                 │    │  │
│  │  │  • Maintain conversation history (in-memory + Redis)           │    │  │
│  │  │  • Load CRM context before call                                │    │  │
│  │  │  • Pass context window to LLM (last N exchanges)               │    │  │
│  │  │  • Store conversation embeddings in vector DB                  │    │  │
│  │  └────────────────────────────────────────────────────────────────┘    │  │
│  └─────────────────────────────────────────────────────────────────────────┘  │
└────────────┬──────────────┬──────────────┬──────────────┬─────────────────────┘
             │              │              │              │
        ┌────▼────┐    ┌───▼────┐    ┌───▼────┐    ┌───▼────┐
        │   STT   │    │  LLM   │    │  TTS   │    │ Backend│
        │ Layer   │    │ Layer  │    │ Layer  │    │   API  │
        └────┬────┘    └───┬────┘    └───┬────┘    └───┬────┘
             │              │              │              │
┌────────────┼──────────────┼──────────────┼──────────────┼─────────────────────┐
│            ▼              ▼              ▼              ▼                      │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │                       AI PROCESSING LAYER                               │  │
│  │                                                                          │  │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐    │  │
│  │  │  DEEPGRAM        │  │  GPT-4o          │  │  ELEVENLABS      │    │  │
│  │  │  Nova-2          │  │  Realtime API    │  │  Turbo v2.5      │    │  │
│  │  │                  │  │                  │  │                  │    │  │
│  │  │  Streaming STT   │  │  Audio-to-Audio  │  │  Streaming TTS   │    │  │
│  │  │  • Real-time     │  │  • <300ms        │  │  • Natural voice │    │  │
│  │  │  • 95%+ accuracy │  │  • Emotion aware │  │  • 29+ languages │    │  │
│  │  │  • Multilingual  │  │  • Context aware │  │  • Low latency   │    │  │
│  │  └──────────────────┘  └──────────────────┘  └──────────────────┘    │  │
│  │                                                                          │  │
│  │  ┌──────────────────────────────────────────────────────────────────┐  │  │
│  │  │  LangGraph Policy & Guardrails Layer                             │  │  │
│  │  │                                                                   │  │  │
│  │  │  Before LLM speaks:                                              │  │  │
│  │  │  ✓ Validate response against knowledge base                      │  │  │
│  │  │  ✓ Check for hallucinations                                      │  │  │
│  │  │  ✓ Enforce brand voice                                           │  │  │
│  │  │  ✓ Prevent off-topic responses                                   │  │  │
│  │  │  ✓ TCPA compliance checks                                        │  │  │
│  │  │  ✓ Flag low-confidence responses → escalate                      │  │  │
│  │  └──────────────────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────┬───────────────────────────────────────┘
                                       │
┌──────────────────────────────────────▼───────────────────────────────────────┐
│                         KNOWLEDGE & DATA LAYER                                │
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Knowledge Base (RAG)                                                │   │
│  │                                                                      │   │
│  │  ┌────────────────┐              ┌────────────────┐                │   │
│  │  │  PINECONE      │◄─────────────│  OPENAI        │                │   │
│  │  │  Vector DB     │  Embeddings  │  Embeddings    │                │   │
│  │  │                │              │  API           │                │   │
│  │  │  • Company FAQs│              └────────────────┘                │   │
│  │  │  • Product docs│                                                 │   │
│  │  │  • Case studies│                                                 │   │
│  │  │  • Objection   │                                                 │   │
│  │  │    handling    │                                                 │   │
│  │  │  • Past convos │                                                 │   │
│  │  └────────────────┘                                                 │   │
│  │                                                                      │   │
│  │  Query: "What's our pricing for enterprise?"                        │   │
│  │  → Embed query → Search vectors → Return top 3 matches →            │   │
│  │  → Inject into LLM context                                          │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Session Store (Redis)                                              │   │
│  │                                                                      │   │
│  │  Key: session:{session_id}                                          │   │
│  │  Value: {                                                           │   │
│  │    caller_id, contact_id, state, conversation_history,             │   │
│  │    lead_score, context, metadata                                   │   │
│  │  }                                                                  │   │
│  │  TTL: 24 hours                                                      │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Persistent Database (PostgreSQL)                                   │   │
│  │                                                                      │   │
│  │  Tables:                                                            │   │
│  │  • calls (session_id, caller_id, duration, outcome, score, ...)    │   │
│  │  • transcripts (session_id, full_transcript, speaker_labels, ...)  │   │
│  │  • contacts (contact_id, name, email, phone, crm_id, ...)          │   │
│  │  • appointments (appt_id, contact_id, calendar_event_id, ...)      │   │
│  │  • consent_records (contact_id, consent_type, granted_at, ...)     │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────┬───────────────────────────────────────┘
                                        │
┌───────────────────────────────────────▼───────────────────────────────────────┐
│                         INTEGRATION LAYER                                      │
│                                                                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │  SALESFORCE  │  │   HUBSPOT    │  │    GOOGLE    │  │   SENDGRID   │    │
│  │     CRM      │  │     CRM      │  │   CALENDAR   │  │    EMAIL     │    │
│  │              │  │              │  │              │  │              │    │
│  │  REST API    │  │  REST API    │  │  Calendar    │  │  SMTP API    │    │
│  │              │  │              │  │  API         │  │              │    │
│  │  Actions:    │  │  Actions:    │  │              │  │  Actions:    │    │
│  │  • Create    │  │  • Create    │  │  • Find      │  │  • Send      │    │
│  │    contact   │  │    contact   │  │    slots     │  │    confirm   │    │
│  │  • Update    │  │  • Update    │  │  • Create    │  │  • Send      │    │
│  │    contact   │  │    deal      │  │    event     │  │    reminder  │    │
│  │  • Create    │  │  • Log       │  │  • Send      │  │  • Send      │    │
│  │    oppty     │  │    activity  │  │    invite    │  │    nurture   │    │
│  │  • Log call  │  │  • Create    │  │              │  │              │    │
│  │  • Assign    │  │    task      │  │              │  │              │    │
│  │    to rep    │  │              │  │              │  │              │    │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
│                                                                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                       │
│  │   TWILIO     │  │    STRIPE    │  │    SLACK     │                       │
│  │     SMS      │  │   BILLING    │  │   WEBHOOK    │                       │
│  │              │  │              │  │              │                       │
│  │  Actions:    │  │  Actions:    │  │  Actions:    │                       │
│  │  • Send      │  │  • Track     │  │  • Alert on  │                       │
│  │    confirm   │  │    usage     │  │    high-     │                       │
│  │  • Send      │  │  • Invoice   │  │    value     │                       │
│  │    reminder  │  │  • Meter     │  │    lead      │                       │
│  │              │  │    minutes   │  │  • Alert on  │                       │
│  │              │  │              │  │    error     │                       │
│  └──────────────┘  └──────────────┘  └──────────────┘                       │
└────────────────────────────────────────────────────────────────────────────────┘
                                        │
┌───────────────────────────────────────▼───────────────────────────────────────┐
│                         BACKEND API LAYER (FastAPI)                            │
│                                                                                │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │  REST API Endpoints                                                      │ │
│  │                                                                          │ │
│  │  POST   /api/calls/inbound           # Handle inbound call webhook      │ │
│  │  POST   /api/calls/outbound          # Initiate outbound call           │ │
│  │  GET    /api/calls/{session_id}      # Get call details                 │ │
│  │  WS     /api/calls/{session_id}/ws   # WebSocket for audio stream       │ │
│  │                                                                          │ │
│  │  POST   /api/transcripts             # Store transcript                 │ │
│  │  GET    /api/transcripts/{session_id}# Get transcript                   │ │
│  │                                                                          │ │
│  │  POST   /api/appointments            # Book appointment                 │ │
│  │  GET    /api/appointments/{appt_id}  # Get appointment                  │ │
│  │  PATCH  /api/appointments/{appt_id}  # Update appointment               │ │
│  │                                                                          │ │
│  │  POST   /api/contacts                # Create/update contact            │ │
│  │  GET    /api/contacts/{contact_id}   # Get contact details              │ │
│  │                                                                          │ │
│  │  POST   /api/knowledge               # Upload knowledge docs            │ │
│  │  GET    /api/knowledge/search        # Search knowledge base            │ │
│  │                                                                          │ │
│  │  GET    /api/analytics/dashboard     # Get dashboard metrics            │ │
│  │  GET    /api/analytics/calls         # Call analytics                   │ │
│  └──────────────────────────────────────────────────────────────────────────┘ │
│                                                                                │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │  Background Workers (Celery)                                            │ │
│  │                                                                          │ │
│  │  • process_call_recording()      # Transcribe + analyze recording       │ │
│  │  • sync_to_crm()                 # Sync contact/deal data               │ │
│  │  • send_follow_up_email()        # Automated email sequences            │ │
│  │  • send_sms_reminder()           # Appointment reminders                │ │
│  │  • generate_conversation_summary()                                      │ │
│  │  • update_analytics()            # Update conversion metrics            │ │
│  │  • cleanup_expired_sessions()    # Remove old Redis sessions            │ │
│  └──────────────────────────────────────────────────────────────────────────┘ │
│                                                                                │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │  Middleware & Cross-Cutting Concerns                                    │ │
│  │                                                                          │ │
│  │  • Authentication (API keys, JWT)                                       │ │
│  │  • Rate Limiting (per customer, per endpoint)                           │ │
│  │  • Request Logging (Datadog, CloudWatch)                                │ │
│  │  • Error Handling (Sentry)                                              │ │
│  │  • CORS (for dashboard frontend)                                        │ │
│  │  • Health Checks (/health, /ready)                                      │ │
│  └──────────────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────────────┘
                                        │
┌───────────────────────────────────────▼───────────────────────────────────────┐
│                         FRONTEND LAYER (Next.js)                               │
│                                                                                │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │  Dashboard Application                                                   │ │
│  │                                                                          │ │
│  │  Routes:                                                                │ │
│  │  /login                   # Authentication                              │ │
│  │  /dashboard               # Overview metrics                            │ │
│  │  /calls                   # Call log list                               │ │
│  │  /calls/:id               # Call detail + transcript                    │ │
│  │  /appointments            # Appointments calendar                       │ │
│  │  /analytics               # Conversion funnel, charts                   │ │
│  │  /settings                # Configure greeting, scripts, integrations   │ │
│  │  /knowledge               # Manage knowledge base documents             │ │
│  │  /onboarding              # Setup wizard (CRM, calendar, phone)         │ │
│  │                                                                          │ │
│  │  Components:                                                            │ │
│  │  • CallPlayer (audio playback with transcript sync)                     │ │
│  │  • ConversationTimeline (visual flow of call stages)                    │ │
│  │  • SentimentChart (emotion analysis over time)                          │ │
│  │  • ConversionFunnel (lead → qualified → booked)                         │ │
│  │  • LeadScoreCard (BANT scoring visualization)                           │ │
│  └──────────────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────────────┘
                                        │
┌───────────────────────────────────────▼───────────────────────────────────────┐
│                    MONITORING & OBSERVABILITY LAYER                            │
│                                                                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   SENTRY     │  │   DATADOG    │  │   POSTHOG    │  │   AWS        │    │
│  │              │  │              │  │              │  │   CLOUDWATCH │    │
│  │  Error       │  │  APM         │  │  Product     │  │              │    │
│  │  Tracking    │  │  Metrics     │  │  Analytics   │  │  Logs        │    │
│  │              │  │  Traces      │  │  Events      │  │  Alarms      │    │
│  │  • API errors│  │  • Latency   │  │  • User flow │  │  • API logs  │    │
│  │  • LLM fails │  │  • STT time  │  │  • Feature   │  │  • Error     │    │
│  │  • TTS fails │  │  • LLM time  │  │    usage     │  │    logs      │    │
│  │  • CRM sync  │  │  • TTS time  │  │  • Funnels   │  │  • Lambda    │    │
│  │    errors    │  │  • End-to-end│  │              │  │    logs      │    │
│  │              │  │    latency   │  │              │  │              │    │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
│                                                                                │
│  Key Metrics:                                                                 │
│  • Call volume (per hour/day/week)                                           │
│  • Average call duration                                                      │
│  • Conversion rate (calls → qualified → booked)                              │
│  • Lead score distribution                                                    │
│  • Average latency per component                                             │
│  • Error rates (by type)                                                      │
│  • Customer satisfaction (from post-call survey)                             │
└────────────────────────────────────────────────────────────────────────────────┘
```

---

## Component Details

### 1. **Telephony Layer (Twilio)**

**Purpose**: Handle all telephony operations - inbound/outbound calls, audio routing, SMS

**Key Components**:
- **Programmable Voice**: Routes calls to our backend
- **Media Streams**: Bidirectional audio WebSocket (8kHz μ-law audio)
- **Call Recording**: Store raw call audio
- **SMS API**: Send confirmations and reminders

**WebSocket Message Format**:
```json
{
  "event": "media",
  "sequenceNumber": "1234",
  "media": {
    "track": "inbound",
    "chunk": "1234",
    "timestamp": "1234567890",
    "payload": "base64_encoded_audio"
  },
  "streamSid": "MZ..."
}
```

**Integration Flow**:
```python
# 1. User calls → Twilio receives
# 2. Twilio sends webhook to POST /api/calls/inbound
# 3. Backend responds with TwiML:
<Response>
  <Start>
    <Stream url="wss://api.yourapp.com/calls/{session_id}/ws" />
  </Start>
  <Say>Please hold while we connect you...</Say>
</Response>
# 4. Twilio opens WebSocket, streams audio bidirectionally
```

---

### 2. **Orchestration Layer (Pipecat)**

**Purpose**: Core brain that orchestrates the entire conversation

**Key Responsibilities**:
1. Session management (create, track, destroy)
2. State machine (IDLE → GREETING → QUALIFYING → PITCHING → BOOKING → CLOSING)
3. Audio pipeline coordination (STT ↔ LLM ↔ TTS)
4. Interruption detection and handling
5. Context management (conversation history + CRM data)
6. Action execution (book appointment, update CRM)

**State Machine**:
```python
class ConversationState(Enum):
    IDLE = "idle"
    GREETING = "greeting"
    QUALIFYING = "qualifying"
    PITCHING = "pitching"
    OBJECTION_HANDLING = "objection_handling"
    BOOKING = "booking"
    CONFIRMING = "confirming"
    CLOSING = "closing"
    ENDED = "ended"
    ESCALATED = "escalated"

# Transitions:
# IDLE → GREETING (call starts)
# GREETING → QUALIFYING (user agrees to chat)
# QUALIFYING → PITCHING (lead_score >= 60)
# QUALIFYING → CLOSING (lead_score < 60, disqualify)
# PITCHING → OBJECTION_HANDLING (user raises objection)
# PITCHING → BOOKING (user interested)
# BOOKING → CONFIRMING (time slot selected)
# CONFIRMING → CLOSING (appointment confirmed)
# * → ESCALATED (user requests human, AI confidence low)
```

**Streaming Pipeline**:
```
Audio In (WebSocket from Twilio)
    ↓
[Buffer: 20ms chunks]
    ↓
Deepgram STT (streaming mode)
    ↓ (transcribed text chunks in real-time)
GPT-4o Realtime API (streaming audio-to-audio)
    ↓ (audio tokens generated in real-time)
ElevenLabs TTS (streaming mode)
    ↓ (audio bytes in real-time)
[Buffer: assemble chunks]
    ↓
Audio Out (WebSocket to Twilio)

Total latency: 50ms (STT) + 150ms (LLM) + 50ms (TTS) = 250ms
```

---

### 3. **AI Processing Layer**

#### **Speech-to-Text (Deepgram Nova-2)**

**Why Deepgram**:
- Best streaming latency in market (<50ms)
- 95%+ accuracy
- Speaker diarization (detect who's speaking)
- Custom vocabulary support

**Configuration**:
```python
deepgram_options = {
    "model": "nova-2",
    "language": "en-US",
    "punctuate": True,
    "diarize": True,
    "interim_results": True,  # Get partial transcripts
    "endpointing": 300,  # Detect end of speech after 300ms silence
    "vad_events": True,  # Voice Activity Detection events
}
```

#### **Language Model (GPT-4o Realtime API)**

**Why GPT-4o Realtime**:
- Native audio-to-audio (preserves tone, emotion)
- Sub-300ms latency
- Can detect sarcasm, urgency, hesitation in voice
- Streaming output

**System Prompt Structure**:
```python
system_prompt = f"""
You are Alex, an AI sales assistant for {company_name}.

ROLE: Friendly, professional SDR who qualifies leads and books appointments.

CONTEXT:
- Customer: {customer_name} (email: {email}, phone: {phone})
- Previous interactions: {crm_history}
- Current conversation so far: {conversation_history}

QUALIFICATION CRITERIA (BANT):
- Budget: ${min_budget}+
- Authority: Decision maker or influencer
- Need: {product_fit_criteria}
- Timeline: Looking to start within 3 months

INSTRUCTIONS:
1. Greet warmly, confirm why they called/filled form
2. Ask discovery questions naturally (don't interrogate)
3. Listen actively, detect objections
4. If qualified (score >= 60), pitch value prop
5. Handle objections with empathy
6. Propose meeting with {sales_rep_name}
7. Book appointment, confirm details
8. NEVER hallucinate pricing, features, or availability
9. If unsure, say "Let me check on that and get back to you"
10. If user asks for human, immediately transfer

TONE: Conversational, empathetic, professional (not robotic)
"""
```

**Function Calling** (for actions):
```python
tools = [
    {
        "name": "search_knowledge_base",
        "description": "Search company knowledge base for information",
        "parameters": {"query": "string"}
    },
    {
        "name": "calculate_lead_score",
        "description": "Calculate lead score based on BANT criteria",
        "parameters": {"budget": "int", "authority": "bool", "need": "string", "timeline": "string"}
    },
    {
        "name": "find_available_slots",
        "description": "Find available meeting slots",
        "parameters": {"rep_name": "string", "num_slots": "int"}
    },
    {
        "name": "book_appointment",
        "description": "Book meeting at specified time",
        "parameters": {"datetime": "string", "duration_mins": "int"}
    },
    {
        "name": "escalate_to_human",
        "description": "Transfer call to human agent",
        "parameters": {"reason": "string"}
    }
]
```

#### **Text-to-Speech (ElevenLabs Turbo v2.5)**

**Why ElevenLabs**:
- Most natural-sounding voice (indistinguishable from human in blind tests)
- Low latency streaming (<50ms first byte)
- Emotional range (can sound excited, empathetic, professional)
- 29+ languages

**Configuration**:
```python
elevenlabs_options = {
    "voice_id": "21m00Tcm4TlvDq8ikWAM",  # Rachel (professional female)
    "model_id": "eleven_turbo_v2_5",
    "optimize_streaming_latency": 4,  # 0-4, higher = lower latency
    "stability": 0.5,  # 0-1, how stable/consistent voice is
    "similarity_boost": 0.75,  # 0-1, how similar to original voice
    "style": 0.5,  # 0-1, how much style/emotion
    "use_speaker_boost": True,  # Enhance clarity
}
```

---

### 4. **Knowledge & Data Layer**

#### **Vector Database (Pinecone + RAG)**

**Purpose**: Store and retrieve company knowledge semantically

**Document Types**:
- Product documentation
- FAQs
- Case studies
- Pricing information
- Objection handling scripts
- Past successful conversations

**RAG Flow**:
```python
# 1. User asks: "What's your pricing for enterprise?"
# 2. Embed question using OpenAI Embeddings
embedding = openai.Embedding.create(
    model="text-embedding-3-small",
    input="What's your pricing for enterprise?"
)

# 3. Query Pinecone for similar vectors
results = pinecone_index.query(
    vector=embedding,
    top_k=3,
    include_metadata=True
)

# 4. Inject results into LLM context
context = "\n\n".join([r.metadata['text'] for r in results])
system_prompt += f"\n\nRELEVANT INFORMATION:\n{context}"

# 5. LLM generates response grounded in retrieved knowledge
```

#### **Session Store (Redis)**

**Purpose**: Fast in-memory storage for active call sessions

**Schema**:
```python
session_key = f"session:{session_id}"
session_data = {
    "session_id": "sess_abc123",
    "caller_id": "+15551234567",
    "contact_id": "contact_xyz789",
    "state": "QUALIFYING",
    "conversation_history": [
        {"speaker": "ai", "text": "Hi! I'm Alex...", "timestamp": "..."},
        {"speaker": "user", "text": "Hi, I'm calling about...", "timestamp": "..."},
    ],
    "lead_score": {
        "budget": 20,
        "authority": 25,
        "need": 15,
        "timeline": 10,
        "total": 70
    },
    "context": {
        "crm_data": {...},
        "extracted_info": {
            "budget_range": "$10k-50k",
            "role": "VP of Sales",
            "pain_points": ["manual lead follow-up", "low conversion rate"],
            "timeline": "next quarter"
        }
    },
    "metadata": {
        "started_at": "2026-04-04T10:30:00Z",
        "last_activity": "2026-04-04T10:32:15Z"
    }
}

redis.setex(session_key, 86400, json.dumps(session_data))  # 24h TTL
```

#### **Persistent Database (PostgreSQL)**

**Schema**:
```sql
CREATE TABLE calls (
    session_id UUID PRIMARY KEY,
    contact_id UUID REFERENCES contacts(id),
    caller_id VARCHAR(20),
    direction VARCHAR(10), -- 'inbound' or 'outbound'
    started_at TIMESTAMP NOT NULL,
    ended_at TIMESTAMP,
    duration_seconds INT,
    state VARCHAR(50),
    outcome VARCHAR(50), -- 'booked', 'disqualified', 'callback', 'no_answer'
    lead_score INT,
    recording_url TEXT,
    transcript_id UUID,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE transcripts (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES calls(session_id),
    full_transcript JSONB, -- array of {speaker, text, timestamp}
    summary TEXT,
    extracted_entities JSONB, -- {budget, timeline, pain_points, ...}
    sentiment_scores JSONB, -- {overall, by_phase, ...}
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE contacts (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(20),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    company VARCHAR(255),
    crm_id VARCHAR(255), -- Salesforce/HubSpot ID
    crm_type VARCHAR(50), -- 'salesforce', 'hubspot'
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE appointments (
    id UUID PRIMARY KEY,
    contact_id UUID REFERENCES contacts(id),
    session_id UUID REFERENCES calls(session_id),
    scheduled_at TIMESTAMP NOT NULL,
    duration_minutes INT DEFAULT 30,
    calendar_event_id VARCHAR(255), -- Google Calendar event ID
    sales_rep_email VARCHAR(255),
    status VARCHAR(50), -- 'scheduled', 'completed', 'no_show', 'cancelled'
    meeting_link TEXT, -- Zoom/Meet URL
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE consent_records (
    id UUID PRIMARY KEY,
    contact_id UUID REFERENCES contacts(id),
    consent_type VARCHAR(50), -- 'call', 'sms', 'email'
    granted BOOLEAN,
    granted_at TIMESTAMP,
    expires_at TIMESTAMP,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

### 5. **Integration Layer**

#### **CRM Integration (Salesforce/HubSpot)**

**Bidirectional Sync**:

**Before Call (Read)**:
```python
# Look up contact by phone number
contact = hubspot.contacts.search_by_phone(caller_id)
if contact:
    # Load context
    crm_data = {
        "name": contact.properties.firstname + " " + contact.properties.lastname,
        "email": contact.properties.email,
        "company": contact.properties.company,
        "lifecycle_stage": contact.properties.lifecyclestage,
        "last_contact": contact.properties.lastmodifieddate,
        "notes": contact.properties.notes,
        "deals": hubspot.deals.get_by_contact(contact.id)
    }
```

**After Call (Write)**:
```python
# Create or update contact
contact = hubspot.contacts.create_or_update(
    email=email,
    properties={
        "firstname": first_name,
        "lastname": last_name,
        "phone": phone,
        "company": company,
        "lead_source": "ai_voice_bot",
        "lead_score": lead_score,
        "last_call_date": datetime.now(),
        "last_call_outcome": outcome,
        "notes": conversation_summary
    }
)

# Create deal
deal = hubspot.deals.create(
    properties={
        "dealname": f"{company} - AI Voice Bot Lead",
        "dealstage": "appointmentscheduled" if outcome == "booked" else "qualifiedtobuy",
        "amount": estimated_deal_size,
        "closedate": datetime.now() + timedelta(days=30),
        "pipeline": "default"
    },
    associations=[{"to": {"id": contact.id}, "types": [{"associationTypeId": 3}]}]
)

# Log activity
hubspot.engagements.create(
    engagement={
        "type": "CALL",
        "timestamp": call_started_at
    },
    associations={
        "contactIds": [contact.id],
        "dealIds": [deal.id]
    },
    metadata={
        "toNumber": caller_id,
        "fromNumber": twilio_number,
        "status": "COMPLETED",
        "durationMilliseconds": duration_ms,
        "recordingUrl": recording_url,
        "body": conversation_summary
    }
)

# Create follow-up task for sales rep
hubspot.tasks.create(
    properties={
        "subject": f"Follow up with {first_name} {last_name} - AI Voice Bot Qualified Lead",
        "status": "NOT_STARTED",
        "tasktype": "CALL",
        "priority": "HIGH",
        "hs_timestamp": (datetime.now() + timedelta(hours=2)).timestamp() * 1000
    },
    associations=[{"to": {"id": contact.id}, "types": [{"associationTypeId": 3}]}]
)
```

#### **Calendar Integration (Google Calendar)**

**Find Available Slots**:
```python
def find_available_slots(rep_email, num_slots=3, duration_mins=30):
    # Get calendar free/busy info
    now = datetime.now()
    time_min = now.replace(hour=9, minute=0)  # Business hours start
    time_max = (now + timedelta(days=14)).replace(hour=17, minute=0)  # 2 weeks out

    freebusy = google_calendar.freebusy().query(
        body={
            "timeMin": time_min.isoformat(),
            "timeMax": time_max.isoformat(),
            "items": [{"id": rep_email}]
        }
    ).execute()

    busy_slots = freebusy['calendars'][rep_email]['busy']

    # Find free slots
    available_slots = []
    current_time = time_min
    while len(available_slots) < num_slots and current_time < time_max:
        # Skip weekends
        if current_time.weekday() >= 5:
            current_time += timedelta(days=1)
            continue

        # Check if slot is free
        slot_end = current_time + timedelta(minutes=duration_mins)
        is_free = not any(
            overlap(current_time, slot_end, busy['start'], busy['end'])
            for busy in busy_slots
        )

        if is_free:
            available_slots.append(current_time)
            current_time += timedelta(hours=1)  # Next slot
        else:
            current_time += timedelta(minutes=15)  # Try 15 min later

    return available_slots
```

**Book Appointment**:
```python
def book_appointment(contact, rep_email, scheduled_at, duration_mins=30):
    # Create calendar event
    event = google_calendar.events().insert(
        calendarId=rep_email,
        conferenceDataVersion=1,
        body={
            "summary": f"Demo Call - {contact.first_name} {contact.last_name}",
            "description": f"""
                AI Voice Bot Qualified Lead

                Lead Score: {contact.lead_score}/100
                Company: {contact.company}
                Pain Points: {', '.join(contact.pain_points)}
                Budget: {contact.budget_range}
                Timeline: {contact.timeline}

                Call Recording: {contact.recording_url}
                Full Transcript: {app_url}/calls/{contact.session_id}
            """,
            "start": {
                "dateTime": scheduled_at.isoformat(),
                "timeZone": "America/New_York"
            },
            "end": {
                "dateTime": (scheduled_at + timedelta(minutes=duration_mins)).isoformat(),
                "timeZone": "America/New_York"
            },
            "attendees": [
                {"email": rep_email},
                {"email": contact.email}
            ],
            "conferenceData": {
                "createRequest": {
                    "requestId": str(uuid.uuid4()),
                    "conferenceSolutionKey": {"type": "hangoutsMeet"}
                }
            },
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "email", "minutes": 60},
                    {"method": "popup", "minutes": 10}
                ]
            }
        }
    ).execute()

    return event
```

---

## Data Flow (Sequence Diagram)

```
User          Twilio        Backend       Pipecat      Deepgram    GPT-4o      ElevenLabs    CRM
 │              │              │             │             │           │            │           │
 │──Call────────▶              │             │             │           │            │           │
 │              │──Webhook────▶              │             │           │            │           │
 │              │              │──Create─────▶             │           │            │           │
 │              │              │  Session    │             │           │            │           │
 │              │              │             │             │           │            │           │
 │              │              │──Load CRM───┼─────────────┼───────────┼────────────┼──────────▶
 │              │              │  Context    │             │           │            │           │
 │              │              │◀────────────┼─────────────┼───────────┼────────────┼───────────┤
 │              │              │             │             │           │            │           │
 │              │◀─TwiML (Stream URL)────────┤             │           │            │           │
 │              │              │             │             │           │            │           │
 │              │──WebSocket Open────────────▶             │           │            │           │
 │              │              │             │             │           │            │           │
 │              │──Audio Chunk────────────────┼────────────▶           │            │           │
 │              │              │             │  Transcribe │           │            │           │
 │              │              │             │◀────────────┤           │            │           │
 │              │              │             │  "Hi, I'm  │           │            │           │
 │              │              │             │   calling   │           │            │           │
 │              │              │             │   about..." │           │            │           │
 │              │              │             │             │           │            │           │
 │              │              │             │──Generate───▶           │            │           │
 │              │              │             │  Response   │           │            │           │
 │              │              │             │◀────────────┤           │            │           │
 │              │              │             │  "Great!    │           │            │           │
 │              │              │             │   Tell me..." │         │            │           │
 │              │              │             │             │           │            │           │
 │              │              │             │──Synthesize─┼───────────┼───────────▶           │
 │              │              │             │  Speech     │           │            │           │
 │              │              │             │◀────────────┼───────────┼────────────┤           │
 │              │              │             │  Audio      │           │            │           │
 │              │◀─Audio Chunk────────────────┤             │           │            │           │
 │◀─Hears AI───┤              │             │             │           │            │           │
 │              │              │             │             │           │            │           │
 │  (Conversation continues... 1-3 minutes)  │             │           │            │           │
 │              │              │             │             │           │            │           │
 │              │              │             │──Calculate──┤           │            │           │
 │              │              │             │  Lead Score │           │            │           │
 │              │              │             │  (75/100)   │           │            │           │
 │              │              │             │             │           │            │           │
 │              │              │             │──Find───────┤           │            │           │
 │              │              │             │  Calendar   │           │            │           │
 │              │              │             │  Slots      │           │            │           │
 │              │              │             │◀────────────┤           │            │           │
 │              │              │             │  [Tue 2pm,  │           │            │           │
 │              │              │             │   Thu 10am] │           │            │           │
 │              │              │             │             │           │            │           │
 │ (AI presents times, user selects)        │             │           │            │           │
 │              │              │             │             │           │            │           │
 │              │              │             │──Book───────┤           │            │           │
 │              │              │             │  Appt       │           │            │           │
 │              │              │             │◀────────────┤           │            │           │
 │              │              │             │  Confirmed  │           │            │           │
 │              │              │             │             │           │            │           │
 │              │              │──Update CRM─┼─────────────┼───────────┼────────────┼──────────▶
 │              │              │  (create    │             │           │            │  • Contact│
 │              │              │   contact,  │             │           │            │  • Deal   │
 │              │              │   deal,     │             │           │            │  • Task   │
 │              │              │   task)     │             │           │            │           │
 │              │              │             │             │           │            │           │
 │              │              │──Send───────┤             │           │            │           │
 │              │              │  Email +    │             │           │            │           │
 │              │              │  SMS        │             │           │            │           │
 │              │              │             │             │           │            │           │
 │◀─Goodbye─────┤              │             │             │           │            │           │
 │              │──Hangup─────▶              │             │           │            │           │
 │              │              │──End────────▶             │           │            │           │
 │              │              │  Session    │             │           │            │           │
 │              │              │             │             │           │            │           │
 │              │              │──Process────┤             │           │            │           │
 │              │              │  Recording  │             │           │            │           │
 │              │              │  (async)    │             │           │            │           │
```

---

## Technology Stack Summary

| Layer | Component | Technology | Cost |
|-------|-----------|------------|------|
| **Telephony** | Call Routing | Twilio Programmable Voice | $0.013/min |
| | Audio Streaming | Twilio Media Streams | Included |
| | SMS | Twilio SMS | $0.0079/msg |
| **Orchestration** | Framework | Pipecat (open-source) | Free |
| | Runtime | Python 3.12+ | Free |
| **AI - STT** | Speech-to-Text | Deepgram Nova-2 | $0.0015/min |
| **AI - LLM** | Conversation | GPT-4o Realtime API | $0.02-0.04/min |
| **AI - TTS** | Text-to-Speech | ElevenLabs Turbo v2.5 | $0.003/min |
| **Knowledge** | Vector DB | Pinecone | $70/mo (starter) |
| | Embeddings | OpenAI text-embedding-3-small | $0.00002/1k tokens |
| **Data** | Session Store | Redis (Upstash) | $0-10/mo |
| | Database | PostgreSQL (Supabase) | $0-25/mo |
| **Backend** | API | FastAPI | Free |
| | Workers | Celery + Redis | Free (hosting cost) |
| | Hosting | Railway/Render | $20-50/mo |
| **Frontend** | Dashboard | Next.js 14 | Free |
| | Hosting | Vercel | $0-20/mo |
| **Integrations** | CRM | HubSpot/Salesforce APIs | Free (API calls) |
| | Calendar | Google Calendar API | Free |
| | Email | SendGrid | $20/mo |
| **Monitoring** | Errors | Sentry | $0 (free tier) |
| | Analytics | PostHog | $0 (free tier) |
| **Total Variable** | | | **~$0.05-0.07/min** |
| **Total Fixed** | | | **~$150-200/mo** |

---

## Implementation Phases

### **Phase 1: Foundation (Weeks 1-2)**
- [ ] Set up Twilio account + phone number
- [ ] Initialize Pipecat project structure
- [ ] Integrate Deepgram STT (streaming)
- [ ] Integrate GPT-4o Realtime API
- [ ] Integrate ElevenLabs TTS (streaming)
- [ ] Build basic conversation loop (hello → response → goodbye)
- [ ] **Milestone**: Make first successful AI phone call

### **Phase 2: Conversation Intelligence (Weeks 3-4)**
- [ ] Implement full-duplex interruption handling
- [ ] Optimize streaming pipeline (<300ms latency)
- [ ] Build conversation state machine
- [ ] Add VAD (Voice Activity Detection)
- [ ] Implement conversation memory (Redis)
- [ ] **Milestone**: 10 consecutive natural conversations with smooth interruptions

### **Phase 3: Qualification & Knowledge (Weeks 5-6)**
- [ ] Implement BANT qualification framework
- [ ] Build lead scoring algorithm
- [ ] Set up Pinecone vector database
- [ ] Implement RAG (knowledge base search)
- [ ] Add LangGraph guardrails
- [ ] **Milestone**: AI correctly qualifies 80%+ of test leads

### **Phase 4: Integrations (Weeks 7-8)**
- [ ] HubSpot CRM integration (read + write)
- [ ] Google Calendar integration (find slots + book)
- [ ] SendGrid email integration (confirmations)
- [ ] Twilio SMS integration (reminders)
- [ ] PostgreSQL database setup
- [ ] **Milestone**: End-to-end flow without manual intervention

### **Phase 5: Dashboard (Weeks 9-10)**
- [ ] Next.js dashboard scaffolding
- [ ] Authentication (NextAuth)
- [ ] Call log view
- [ ] Call detail page with transcript
- [ ] Analytics dashboard
- [ ] Settings page (customize greeting, scripts)
- [ ] **Milestone**: Customer can self-service entire setup

### **Phase 6: Compliance & Launch (Weeks 11-12)**
- [ ] TCPA compliance (consent tracking, DNC)
- [ ] Call recording disclosure
- [ ] Stripe billing integration
- [ ] Error monitoring (Sentry)
- [ ] Load testing (50 concurrent calls)
- [ ] Beta customer onboarding
- [ ] **Milestone**: Production-ready, first paying customers

---

**Next Step**: Shall we start building Phase 1? I can create the project structure and start with the Twilio + Pipecat integration.
