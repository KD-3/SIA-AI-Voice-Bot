# AI Voice Bot - Automated Lead Conversion System

An autonomous AI voice bot that handles inbound/outbound calls, qualifies leads, books appointments, and updates CRM - all without human intervention.

## Project Structure

```
.
├── api/                    # Backend API (FastAPI)
│   ├── routes/            # API endpoints
│   ├── services/          # Business logic
│   ├── models/            # Data models
│   └── middleware/        # Middleware & auth
│
├── voice/                  # Voice agent core (Pipecat)
│   ├── orchestrator/      # Main orchestration logic
│   ├── pipeline/          # STT/LLM/TTS streaming pipeline
│   ├── state_machine/     # Conversation state management
│   ├── integrations/      # External service integrations
│   └── utils/             # Utilities
│
├── web/                    # Dashboard (Next.js)
│   ├── app/               # Next.js 14 app router
│   ├── components/        # React components
│   └── lib/               # Utilities
│
├── shared/                 # Shared code between services
│   ├── types/             # TypeScript/Python types
│   └── constants/         # Constants
│
├── tests/                  # Test suites
└── docs/                   # Documentation

```

## Tech Stack

### Voice Agent Core
- **Orchestration**: Pipecat (Daily.co)
- **STT**: Deepgram Nova-2
- **LLM**: OpenAI GPT-4o Realtime API
- **TTS**: ElevenLabs Turbo v2.5
- **Telephony**: Twilio Media Streams

### Backend
- **API**: FastAPI (Python 3.12+)
- **Database**: PostgreSQL (Supabase)
- **Cache**: Redis (Upstash)
- **Vector DB**: Pinecone
- **Workers**: Celery

### Frontend
- **Framework**: Next.js 14
- **UI**: Tailwind CSS + shadcn/ui
- **Auth**: NextAuth

## Getting Started

### Prerequisites
- Python 3.12+
- Node.js 18+
- Redis (local or Upstash)
- PostgreSQL (local or Supabase)

### Environment Variables

Create a `.env` file in the root:

```bash
# Twilio
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890

# OpenAI
OPENAI_API_KEY=your_openai_api_key

# Deepgram
DEEPGRAM_API_KEY=your_deepgram_api_key

# ElevenLabs
ELEVENLABS_API_KEY=your_elevenlabs_api_key

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/aivoicebot
REDIS_URL=redis://localhost:6379

# Pinecone
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_ENVIRONMENT=us-east-1

# HubSpot (optional)
HUBSPOT_API_KEY=your_hubspot_api_key

# Google Calendar (optional)
GOOGLE_CALENDAR_CREDENTIALS=path/to/credentials.json
```

### Installation

#### Backend (Voice + API)
```bash
cd voice
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### Frontend
```bash
cd web
npm install
```

### Running Locally

#### 1. Start Redis (if local)
```bash
redis-server
```

#### 2. Start Voice Agent
```bash
cd voice
source venv/bin/activate
python main.py
```

#### 3. Start Backend API
```bash
cd api
uvicorn main:app --reload --port 8000
```

#### 4. Start Frontend
```bash
cd web
npm run dev
```

#### 5. Expose local server with ngrok (for Twilio webhooks)
```bash
ngrok http 8000
# Copy the HTTPS URL (e.g., https://abc123.ngrok.io)
# Update Twilio webhook URL to: https://abc123.ngrok.io/api/calls/inbound
```

## Development Phases

- [x] Phase 0: Research & Architecture
- [ ] **Phase 1: Foundation (Current)** - Weeks 1-2
  - [ ] Twilio integration
  - [ ] Pipecat setup
  - [ ] STT/LLM/TTS streaming pipeline
  - [ ] First successful AI call
- [ ] Phase 2: Conversation Intelligence - Weeks 3-4
- [ ] Phase 3: Qualification & Knowledge - Weeks 5-6
- [ ] Phase 4: Integrations (CRM/Calendar) - Weeks 7-8
- [ ] Phase 5: Dashboard - Weeks 9-10
- [ ] Phase 6: Compliance & Launch - Weeks 11-12

## Architecture

See [ARCHITECTURE.md](./ARCHITECTURE.md) for detailed system design and data flow.

## License

Private - Confidential

## Contact

Built by solo founder with Claude Code (Opus 4.6)
