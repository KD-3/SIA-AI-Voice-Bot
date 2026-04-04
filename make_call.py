"""
Outbound call script - dials a number using the full AI pipeline.

Flow:
  Twilio dials out → picks up → sends TwiML URL pointing to our /api/calls/inbound webhook
  → FastAPI connects Twilio Media Stream via WebSocket
  → CallSession runs STT (Deepgram) → LLM (GPT-4o) → TTS (Sarvam AI)
  → Alex greets the callee and has a live conversation.

Requirements:
  - FastAPI server running:  cd voice && python main.py
  - ngrok tunnel running:    ngrok http 8000
  - NGROK_URL set in .env

Run from project root:
  source voice/venv/bin/activate
  python make_call.py
"""

import os
from dotenv import load_dotenv
from twilio.rest import Client

# Load .env from project root
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

ACCOUNT_SID  = os.getenv("TWILIO_ACCOUNT_SID")
AUTH_TOKEN   = os.getenv("TWILIO_AUTH_TOKEN")
FROM_NUMBER  = os.getenv("TWILIO_PHONE_NUMBER")
NGROK_URL    = os.getenv("NGROK_URL", "").rstrip("/")
TO_NUMBER    = "+919919837374"   # Kaustubh's number

def make_call():
    if not NGROK_URL:
        raise RuntimeError(
            "NGROK_URL is not set in .env. "
            "Start ngrok (`ngrok http 8000`) and add the URL to .env."
        )

    # Point Twilio at our existing inbound webhook — this triggers the full pipeline
    webhook_url = f"{NGROK_URL}/api/calls/inbound"

    client = Client(ACCOUNT_SID, AUTH_TOKEN)
    call = client.calls.create(
        to=TO_NUMBER,
        from_=FROM_NUMBER,
        url=webhook_url,          # Twilio fetches TwiML from here (STT→LLM→TTS)
        method="POST",
    )

    print(f"✅ Pipeline call initiated!")
    print(f"   SID     : {call.sid}")
    print(f"   From    : {FROM_NUMBER}")
    print(f"   To      : {TO_NUMBER}")
    print(f"   Webhook : {webhook_url}")
    print(f"   Status  : {call.status}")
    print()
    print("📊 Watch the server logs for real-time pipeline traces:")
    print("   STT (Deepgram) → LLM (GPT-4o) → TTS (Sarvam AI 'priya')")

if __name__ == "__main__":
    make_call()
