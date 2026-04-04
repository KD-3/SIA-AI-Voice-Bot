# Setup Guide - Phase 1: Foundation

This guide walks you through setting up your development environment and making your first AI phone call.

## Prerequisites

- Python 3.12+ installed
- A Twilio account (free trial works)
- OpenAI API key
- Deepgram API key
- ElevenLabs API key
- ngrok installed (for local development)

## Step 1: Get API Keys

### Twilio
1. Sign up at https://www.twilio.com/try-twilio
2. Go to Console Dashboard
3. Copy your **Account SID** and **Auth Token**
4. Buy a phone number: Console → Phone Numbers → Buy a number
   - Choose a number with Voice capabilities
   - Cost: ~$1/month + $0.013/min for calls

### OpenAI
1. Go to https://platform.openai.com/api-keys
2. Create new secret key
3. Copy the key (starts with `sk-proj-...`)
4. Add credits to your account (Settings → Billing)
   - GPT-4o costs: ~$0.03/min of conversation

### Deepgram
1. Sign up at https://console.deepgram.com/signup
2. Create a new API key
3. Free tier includes: 12,000 minutes/year (~33 min/day)
4. Paid: $0.0015/min after free tier

### ElevenLabs
1. Sign up at https://elevenlabs.io
2. Go to Profile → API Key
3. Copy your API key
4. Free tier: 10,000 characters/month
5. Paid: $22/month for 30,000 chars (Creator plan)

## Step 2: Install Dependencies

```bash
cd voice

# Create virtual environment
python3.12 -m venv venv

# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

## Step 3: Configure Environment

Create `.env` file in the root directory:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```bash
# Twilio
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890

# OpenAI
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Deepgram
DEEPGRAM_API_KEY=your_deepgram_key

# ElevenLabs
ELEVENLABS_API_KEY=your_elevenlabs_key

# Database (for now, just use dummy values)
DATABASE_URL=postgresql://localhost:5432/aivoicebot
REDIS_URL=redis://localhost:6379/0
```

## Step 4: Start the Server

```bash
cd voice
source venv/bin/activate
python main.py
```

You should see:
```
🚀 Starting AI Voice Bot server...
📍 Environment: development
📞 Twilio number: +1234567890
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

## Step 5: Expose Local Server with ngrok

In a new terminal:

```bash
ngrok http 8000
```

You'll see:
```
Forwarding  https://abc123xyz.ngrok.io -> http://localhost:8000
```

Copy the HTTPS URL (e.g., `https://abc123xyz.ngrok.io`)

**Important**: Update `voice/main.py` line 72 with your ngrok subdomain:
```python
ws_url = f"wss://abc123xyz.ngrok.io/ws/calls/{session_id}"
```

## Step 6: Configure Twilio Webhook

1. Go to Twilio Console → Phone Numbers → Manage → Active Numbers
2. Click on your phone number
3. Scroll to "Voice Configuration"
4. Set **A CALL COMES IN** to:
   - Webhook
   - `https://abc123xyz.ngrok.io/api/calls/inbound`
   - HTTP POST
5. Click **Save**

## Step 7: Make Your First Call! 🎉

1. Call your Twilio number from your phone
2. You should hear: "Please wait while we connect you."
3. Then the AI will greet you: "Hi! I'm Alex, an AI assistant. Thanks for calling! How can I help you today?"
4. Talk to the AI!

## Step 8: Monitor Logs

Watch the terminal running `main.py`. You should see:

```
📞 Incoming call: +15551234567 → +15559876543 (Session: call_abc123)
🔌 WebSocket connected: call_abc123
▶️  Call started: call_abc123 from +15551234567
🚀 Session call_abc123: Initializing pipeline...
✅ STT: Connected to Deepgram
✅ LLM: OpenAI client initialized
✅ TTS: ElevenLabs client initialized
✅ Session call_abc123: Pipeline ready
👋 Session call_abc123: Sending greeting
🔊 TTS: Synthesizing: Hi! I'm Alex, an AI assistant...
🎤 STT ✓: hello can you hear me
👤 User: hello can you hear me
🤖 LLM: Generating response to: hello can you hear me...
🤖 Assistant: Yes, I can hear you perfectly! How can I help you today?
🔊 TTS: Synthesizing: Yes, I can hear you perfectly!...
```

## Troubleshooting

### "Connection refused" when calling
- Check that `main.py` is running
- Check that ngrok is running
- Verify ngrok URL in Twilio webhook matches your ngrok URL

### "Unauthorized" errors
- Double-check your API keys in `.env`
- Make sure no extra spaces or quotes around keys
- Restart `main.py` after changing `.env`

### Audio quality issues
- Twilio uses μ-law encoding at 8kHz (phone quality)
- This is expected - not high-fidelity
- Latency should be <1 second for natural conversation

### "No module named 'pipecat'" error
```bash
# Make sure you're in the virtual environment
source venv/bin/activate
pip install -r requirements.txt
```

### Deepgram connection errors
- Check that your API key is correct
- Free tier has rate limits - wait a minute and try again
- Check Deepgram Console for API status

### ElevenLabs errors
- Check API key
- Free tier is limited - might need to wait or upgrade
- Try a different voice_id if synthesis fails

## Next Steps

Once you have a successful call:

1. ✅ You've completed Phase 1: Foundation!
2. Next: Phase 2 - Improve conversational quality
   - Add interruption handling
   - Optimize latency (<300ms)
   - Improve conversation flow

## Cost Estimate (Phase 1 Testing)

For ~10 test calls (2-3 minutes each):

| Service | Usage | Cost |
|---------|-------|------|
| Twilio | 30 min | $0.39 |
| Deepgram | 30 min | FREE (under 33 min/day) |
| OpenAI GPT-4o | 30 min | ~$0.90 |
| ElevenLabs | ~5,000 chars | FREE (under 10k/month) |
| **Total** | | **~$1.30** |

Very affordable for testing! 🎉

## Help & Support

If you get stuck:
1. Check the logs in the terminal
2. Review the ARCHITECTURE.md for how components connect
3. Test each API key separately with curl
4. Check Twilio debugger: Console → Monitor → Logs → Errors
