"""Main application entry point - FastAPI server for voice agent."""

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
from exotel import router as exotel_router, get_active_sessions as get_exo_sessions

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

# Include Exotel router
app.include_router(exotel_router)

# Active call sessions (Twilio inbound)
sessions: Dict[str, CallSession] = {}


@app.on_event("startup")
async def startup_event():
    """Start ngrok tunnel on startup (if enabled)."""
    if settings.enable_ngrok:
        try:
            import ssl, urllib.request
            from pyngrok import ngrok, conf, installer

            # macOS Python 3.13 ships without system CA certs linked;
            # patch urllib to skip verification only for the one-time
            # ngrok binary download (dev machine only).
            _no_verify_ctx = ssl.create_default_context()
            _no_verify_ctx.check_hostname = False
            _no_verify_ctx.verify_mode = ssl.CERT_NONE
            urllib.request.install_opener(
                urllib.request.build_opener(
                    urllib.request.HTTPSHandler(context=_no_verify_ctx)
                )
            )

            pyngrok_cfg = conf.get_default()
            if settings.ngrok_auth_token:
                pyngrok_cfg.auth_token = settings.ngrok_auth_token

            # Download binary if not already present
            import os
            if not os.path.isfile(pyngrok_cfg.ngrok_path):
                installer.install_ngrok(pyngrok_cfg.ngrok_path)

            # Restore default opener after download
            urllib.request.install_opener(urllib.request.build_opener())

            # Reuse existing tunnel if server auto-reloaded
            existing = ngrok.get_tunnels()
            if existing:
                tunnel = existing[0]
            else:
                tunnel = ngrok.connect(settings.app_port, "http")
            # Store just the hostname (strip scheme prefix)
            settings.ngrok_url = tunnel.public_url.replace("https://", "").replace("http://", "")
            logger.info(f"🌐 ngrok tunnel active: https://{settings.ngrok_url}")
        except Exception as e:
            logger.error(f"❌ ngrok startup failed: {e}")


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
        "exotel_configured": bool(settings.exotel_account_sid),
        "openai_configured": bool(settings.openai_api_key),
        "deepgram_configured": bool(settings.deepgram_api_key),
        "elevenlabs_configured": bool(getattr(settings, "elevenlabs_api_key", "")),
        "ngrok_url": settings.ngrok_url or None,
    }


@app.post("/api/calls/twilio/outbound")
async def initiate_twilio_outbound(request: Request):
    """
    Trigger an outbound call via Twilio.
    Body: {"to_phone": "+91…", "lead_name": "…", "lead_area": "…"}
    """
    from urllib.parse import urlencode
    import httpx
    body = await request.json()
    to_phone: str  = body.get("to_phone", "").strip()
    lead_name: str  = body.get("lead_name", "")
    lead_area: str  = body.get("lead_area", "")

    if not to_phone:
        return {"error": "to_phone is required"}

    session_id = f"call_{uuid.uuid4().hex[:12]}"

    base = (
        f"https://{settings.ngrok_url}"
        if settings.ngrok_url
        else str(request.base_url).rstrip("/")
    )
    params      = urlencode({"session_id": session_id, "lead_name": lead_name, "lead_area": lead_area})
    answer_url  = f"{base}/api/calls/twilio/answer?{params}"
    status_url  = f"{base}/api/calls/twilio/status"

    logger.info(f"📞 Twilio outbound | to={to_phone} | session={session_id}")

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"https://api.twilio.com/2010-04-01/Accounts/{settings.twilio_account_sid}/Calls.json",
                data={
                    "To":   to_phone,
                    "From": settings.twilio_phone_number,
                    "Url":  answer_url,
                    "StatusCallback": status_url,
                    "TimeLimit": "600",
                },
                auth=(settings.twilio_account_sid, settings.twilio_auth_token),
            )
            resp.raise_for_status()
            call_sid = resp.json().get("sid", "")
            logger.info(f"✅ Twilio call created | CallSid={call_sid}")
            return {"session_id": session_id, "call_sid": call_sid, "status": "initiated"}
    except httpx.HTTPStatusError as e:
        body = e.response.text[:500] if e.response else ""
        logger.error(f"❌ Twilio outbound failed: {e} | body={body}")
        return {"error": str(e), "detail": body}
    except Exception as e:
        logger.error(f"❌ Twilio outbound failed: {e}")
        return {"error": str(e)}


@app.post("/api/calls/twilio/answer")
async def handle_twilio_answer(
    request: Request,
    session_id: str = "",
    lead_name: str = "",
    lead_area: str = "",
):
    """
    Twilio calls this when the merchant picks up.
    Returns TwiML to connect the call to our media-stream WebSocket.
    """
    ws_host = settings.ngrok_url or request.url.hostname
    ws_url  = f"wss://{ws_host}/ws/calls/{session_id}"

    logger.info(f"📲 Twilio outbound answered | session={session_id} | stream={ws_url}")

    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Connect>
        <Stream url="{ws_url}">
            <Parameter name="sessionId" value="{session_id}" />
            <Parameter name="leadName"  value="{lead_name}" />
            <Parameter name="leadArea"  value="{lead_area}" />
        </Stream>
    </Connect>
</Response>"""
    return Response(content=twiml, media_type="application/xml")


@app.post("/api/calls/twilio/status")
async def handle_twilio_status(request: Request):
    """Receive Twilio call lifecycle events."""
    form_data = await request.form()
    logger.info(
        f"📊 Twilio status | CallSid={form_data.get('CallSid','')} | "
        f"Status={form_data.get('CallStatus','')} | Duration={form_data.get('CallDuration','0')}s"
    )
    return Response(content="", status_code=204)


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

    # Build WebSocket URL — prefer ngrok tunnel (dev), fall back to request host (prod)
    ws_host = settings.ngrok_url or request.url.hostname
    ws_url = f"wss://{ws_host}/ws/calls/{session_id}"

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
                params    = start_data.get("customParameters", {})
                caller_id = params.get("callerId", "Unknown")

                # Outbound calls pass lead context via Stream parameters
                lead_data = {}
                if params.get("leadName"):
                    lead_data["lead_name"] = params["leadName"]
                if params.get("leadArea"):
                    lead_data["lead_area"] = params["leadArea"]

                logger.info(f"▶️  Call started: {session_id} from {caller_id}")

                # Create and initialize session
                session = CallSession(session_id, caller_id, lead_data=lead_data or None)
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
    """List all active call sessions (Twilio + Exotel)."""
    twilio_list = [
        {
            "session_id": s.session_id,
            "caller_id": s.caller_id,
            "provider": "twilio",
            "started_at": s.started_at.isoformat(),
            "duration_seconds": s.get_duration(),
        }
        for s in sessions.values()
    ]
    exotel_list = get_exo_sessions()
    all_sessions = twilio_list + exotel_list
    return {
        "active_sessions": len(all_sessions),
        "sessions": all_sessions,
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
