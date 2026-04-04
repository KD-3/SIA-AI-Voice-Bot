"""Main application entry point - FastAPI server for voice agent."""

import asyncio
import base64
import json
import uuid
from typing import Dict
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import Response
from loguru import logger
import sys

from config import settings
from orchestrator import CallSession

# Configure logging
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> | <level>{message}</level>",
    level=settings.log_level
)

# FastAPI app
app = FastAPI(
    title="AI Voice Bot",
    description="Autonomous voice agent for lead conversion",
    version="0.1.0"
)

# Active call sessions
sessions: Dict[str, CallSession] = {}


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "AI Voice Bot",
        "version": "0.1.0",
        "active_sessions": len(sessions)
    }


@app.get("/health")
async def health():
    """Detailed health check."""
    return {
        "status": "healthy",
        "twilio_configured": bool(settings.twilio_account_sid),
        "openai_configured": bool(settings.openai_api_key),
        "deepgram_configured": bool(settings.deepgram_api_key),
        "elevenlabs_configured": bool(settings.elevenlabs_api_key),
    }


@app.post("/api/calls/inbound")
async def handle_inbound_call(request: Request):
    """
    Handle incoming call from Twilio.

    This webhook is called when someone calls your Twilio number.
    We respond with TwiML to connect the call to a Media Stream (WebSocket).
    """
    # Parse Twilio request
    form_data = await request.form()
    caller_id = form_data.get("From", "Unknown")
    to_number = form_data.get("To", "Unknown")

    # Generate session ID
    session_id = f"call_{uuid.uuid4().hex[:12]}"

    logger.info(f"📞 Incoming call: {caller_id} → {to_number} (Session: {session_id})")

    # Build WebSocket URL (will be wss:// in production with ngrok/production domain)
    ws_url = f"wss://{request.url.hostname}:{request.url.port}/ws/calls/{session_id}"
    if settings.app_env == "development":
        # In dev, use your ngrok URL
        ws_url = f"wss://YOUR_NGROK_SUBDOMAIN.ngrok.io/ws/calls/{session_id}"

    # Return TwiML to connect call to Media Stream
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say>Please wait while we connect you.</Say>
    <Connect>
        <Stream url="{ws_url}">
            <Parameter name="sessionId" value="{session_id}" />
            <Parameter name="callerId" value="{caller_id}" />
        </Stream>
    </Connect>
</Response>
"""

    return Response(content=twiml, media_type="application/xml")


@app.websocket("/ws/calls/{session_id}")
async def websocket_call_handler(websocket: WebSocket, session_id: str):
    """
    Handle WebSocket connection from Twilio Media Streams.

    This receives/sends real-time audio with bidirectional streaming.
    """
    await websocket.accept()
    logger.info(f"🔌 WebSocket connected: {session_id}")

    session: CallSession = None
    caller_id = "Unknown"

    try:
        # Listen for messages from Twilio
        while True:
            message = await websocket.receive_text()
            data = json.loads(message)

            event = data.get("event")

            if event == "start":
                # Call started - initialize session
                start_data = data.get("start", {})
                caller_id = start_data.get("customParameters", {}).get("callerId", "Unknown")

                logger.info(f"▶️  Call started: {session_id} from {caller_id}")

                # Create and initialize session
                session = CallSession(session_id, caller_id)
                sessions[session_id] = session
                await session.initialize()

            elif event == "media":
                # Audio data received from caller
                if session and session.is_active:
                    media = data.get("media", {})
                    payload = media.get("payload")

                    if payload:
                        # Decode audio (base64 μ-law)
                        audio_data = base64.b64decode(payload)

                        # Send to STT
                        await session.process_audio_in(audio_data)

                        # Check if we have audio to send back
                        audio_out = await session.get_audio_out()
                        if audio_out:
                            # Send audio back to Twilio
                            audio_b64 = base64.b64encode(audio_out).decode('utf-8')
                            await websocket.send_json({
                                "event": "media",
                                "streamSid": data.get("streamSid"),
                                "media": {
                                    "payload": audio_b64
                                }
                            })

            elif event == "stop":
                # Call ended
                logger.info(f"⏹️  Call stopped: {session_id}")

                if session:
                    duration = session.get_duration()
                    logger.info(f"📊 Call duration: {duration:.1f} seconds")

                    # Cleanup
                    await session.cleanup()
                    del sessions[session_id]

                break

    except WebSocketDisconnect:
        logger.info(f"🔌 WebSocket disconnected: {session_id}")

    except Exception as e:
        logger.error(f"❌ WebSocket error ({session_id}): {e}")

    finally:
        # Cleanup if session still exists
        if session_id in sessions:
            session = sessions[session_id]
            await session.cleanup()
            del sessions[session_id]

        logger.info(f"👋 Session ended: {session_id}")


@app.get("/api/sessions")
async def list_sessions():
    """List all active call sessions."""
    return {
        "active_sessions": len(sessions),
        "sessions": [
            {
                "session_id": s.session_id,
                "caller_id": s.caller_id,
                "started_at": s.started_at.isoformat(),
                "duration_seconds": s.get_duration()
            }
            for s in sessions.values()
        ]
    }


if __name__ == "__main__":
    import uvicorn

    logger.info("🚀 Starting AI Voice Bot server...")
    logger.info(f"📍 Environment: {settings.app_env}")
    logger.info(f"📞 Twilio number: {settings.twilio_phone_number}")

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.app_port,
        reload=settings.app_env == "development",
        log_level=settings.log_level.lower()
    )
