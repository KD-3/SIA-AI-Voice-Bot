"""
Exotel integration – outbound calls + media streaming WebSocket.

Flow:
  POST /api/calls/exotel/outbound
      → calls Exotel REST API (From=ExoPhone, To=merchant)
      → Exotel dials merchant; on answer calls our /answer webhook

  POST /api/calls/exotel/answer   (Exotel webhook)
      → returns ExoML <Connect><Stream url="wss://…/ws/exotel/{session_id}"/>

  WS   /ws/exotel/{session_id}    (Exotel media stream)
      → receives μ-law audio → STT → LLM (+tools) → TTS → sends audio back

  POST /api/calls/exotel/status   (optional status callback)
"""

import asyncio
import base64
import json
import uuid
from typing import Dict, Optional

import httpx
from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import Response
from loguru import logger

from config import settings
from orchestrator import CallSession


router = APIRouter(tags=["exotel"])

# Active Exotel sessions (separate from Twilio sessions in main.py)
exo_sessions: Dict[str, CallSession] = {}

# lead_data held here until the WebSocket start event fires
_pending_lead_data: Dict[str, dict] = {}


# ── Exotel REST client ────────────────────────────────────────────────────────

class ExotelClient:
    """Thin async wrapper around Exotel's Calls/connect REST API."""

    _BASE = "https://api.exotel.com/v1/Accounts/{sid}/Calls/connect.json"

    def __init__(self):
        self.sid   = settings.exotel_account_sid
        self.key   = settings.exotel_api_key
        self.token = settings.exotel_api_token
        self.phone = settings.exotel_phone_number

    async def make_outbound_call(
        self, to_phone: str, answer_url: str, status_url: str
    ) -> dict:
        """
        Dial `to_phone` from our ExoPhone.

        Exotel connects the call then hits `answer_url` to get ExoML,
        and sends lifecycle events to `status_url`.
        """
        url = self._BASE.format(sid=self.sid)
        data = {
            "From": self.phone,
            "To": to_phone,
            "Url": answer_url,
            "StatusCallback": status_url,
            "CallType": "trans",       # transactional (not promotional)
            "TimeLimit": "600",        # max 10 min
            "Record": "false",
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, data=data, auth=(self.key, self.token))
            resp.raise_for_status()
            return resp.json()


# ── HTTP routes ───────────────────────────────────────────────────────────────

@router.post("/api/calls/exotel/outbound")
async def initiate_outbound_call(request: Request):
    """
    Admin/system endpoint — trigger an outbound call to a merchant.

    Request JSON:
        {
            "to_phone": "+919876543210",   // E.164 or Indian format
            "lead_data": {                 // optional, passed to CallSession
                "lead_name": "Ramesh",
                "lead_area": "South Bengaluru",
                "needs_document_collection": false
            }
        }
    """
    body = await request.json()
    to_phone: str  = body.get("to_phone", "").strip()
    lead_data: dict = body.get("lead_data", {})

    if not to_phone:
        return {"error": "to_phone is required"}

    session_id = f"exo_{uuid.uuid4().hex[:12]}"
    _pending_lead_data[session_id] = lead_data

    # Prefer the runtime ngrok URL; fall back to request host (for production)
    base = (
        f"https://{settings.ngrok_url}"
        if settings.ngrok_url
        else str(request.base_url).rstrip("/")
    )
    answer_url = f"{base}/api/calls/exotel/answer?session_id={session_id}"
    status_url = f"{base}/api/calls/exotel/status"

    logger.info(
        f"📞 Initiating Exotel outbound call | to={to_phone} | session={session_id}"
    )
    logger.info(f"   Answer URL: {answer_url}")

    try:
        result  = await ExotelClient().make_outbound_call(to_phone, answer_url, status_url)
        call_sid = result.get("Call", {}).get("Sid", "")
        logger.info(f"✅ Exotel call created | CallSid={call_sid}")
        return {"session_id": session_id, "call_sid": call_sid, "status": "initiated"}
    except Exception as e:
        logger.error(f"❌ Exotel outbound call failed: {e}")
        _pending_lead_data.pop(session_id, None)
        return {"error": str(e)}


@router.post("/api/calls/exotel/answer")
async def handle_answer(request: Request, session_id: str = ""):
    """
    Exotel calls this webhook when the merchant picks up.
    We respond with ExoML instructing Exotel to open a media stream to our WebSocket.
    """
    form_data  = await request.form()
    call_sid   = form_data.get("CallSid", "")
    # "To" = number Exotel dialled (our merchant); "From" = our ExoPhone
    merchant_phone = form_data.get("To", form_data.get("Called", "Unknown"))

    if not session_id:
        session_id = f"exo_{uuid.uuid4().hex[:12]}"

    # Use ngrok hostname for WSS (required — Exotel can't reach localhost)
    ws_host = settings.ngrok_url or request.url.hostname
    ws_url  = f"wss://{ws_host}/ws/exotel/{session_id}"

    logger.info(
        f"📲 Merchant answered | session={session_id} | "
        f"CallSid={call_sid} | merchant={merchant_phone}"
    )
    logger.info(f"   Stream URL: {ws_url}")

    exoml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Connect>
        <Stream url="{ws_url}">
            <Parameter name="sessionId"     value="{session_id}" />
            <Parameter name="callSid"       value="{call_sid}" />
            <Parameter name="merchantPhone" value="{merchant_phone}" />
        </Stream>
    </Connect>
</Response>"""

    return Response(content=exoml, media_type="application/xml")


@router.post("/api/calls/exotel/status")
async def handle_status_callback(request: Request):
    """Receive Exotel call lifecycle events (ringing, answered, completed, failed…)."""
    form_data = await request.form()
    call_sid  = form_data.get("CallSid", "")
    status    = form_data.get("CallStatus", form_data.get("Status", "unknown"))
    duration  = form_data.get("Duration", "0")
    direction = form_data.get("Direction", "")

    logger.info(
        f"📊 Exotel status | CallSid={call_sid} | "
        f"status={status} | duration={duration}s | direction={direction}"
    )
    return {"ok": True}


# ── WebSocket media stream handler ────────────────────────────────────────────

@router.websocket("/ws/exotel/{session_id}")
async def exotel_websocket(websocket: WebSocket, session_id: str):
    """
    Handle Exotel Media Streaming WebSocket.

    Exotel's message format mirrors Twilio's:
      {"event": "start",  "start":  {"streamSid": "…", "customParameters": {…}}}
      {"event": "media",  "media":  {"payload": "<base64 μ-law audio>"}}
      {"event": "stop",   "stop":   {"callSid": "…"}}

    We pipe audio through the existing CallSession pipeline (STT → LLM → TTS).
    """
    await websocket.accept()
    logger.info(f"🔌 Exotel WebSocket connected: {session_id}")

    session: Optional[CallSession] = None
    stream_sid = ""

    try:
        while True:
            raw = await websocket.receive_text()
            data  = json.loads(raw)
            event = data.get("event")

            # ── Call started ──────────────────────────────────────────────
            if event == "start":
                start_data     = data.get("start", {})
                stream_sid     = data.get("streamSid", start_data.get("streamSid", ""))
                params         = start_data.get("customParameters", {})
                merchant_phone = params.get("merchantPhone", "Unknown")

                logger.info(
                    f"▶️  Exotel stream started | session={session_id} | "
                    f"merchant={merchant_phone} | streamSid={stream_sid}"
                )

                # Attach lead_data if the outbound route stored it
                lead_data = _pending_lead_data.pop(session_id, {})
                if not lead_data.get("lead_phone"):
                    lead_data["lead_phone"] = merchant_phone

                session = CallSession(session_id, merchant_phone, lead_data=lead_data)
                exo_sessions[session_id] = session
                await session.initialize()

            # ── Audio chunk received ──────────────────────────────────────
            elif event == "media":
                if session and session.is_active:
                    payload = data.get("media", {}).get("payload")
                    if payload:
                        audio_in = base64.b64decode(payload)
                        await session.process_audio_in(audio_in)

                        audio_out = await session.get_audio_out()
                        if audio_out:
                            await websocket.send_json({
                                "event": "media",
                                "streamSid": stream_sid,
                                "media": {
                                    "payload": base64.b64encode(audio_out).decode("utf-8")
                                }
                            })

            # ── Call ended ────────────────────────────────────────────────
            elif event == "stop":
                logger.info(f"⏹️  Exotel stream stopped: {session_id}")
                if session:
                    logger.info(f"📊 Duration: {session.get_duration():.1f}s")
                    await session.cleanup()
                    exo_sessions.pop(session_id, None)
                break

    except WebSocketDisconnect:
        logger.info(f"🔌 Exotel WebSocket disconnected: {session_id}")
    except Exception as e:
        logger.error(f"❌ Exotel WebSocket error ({session_id}): {e}")
    finally:
        if session_id in exo_sessions:
            await exo_sessions[session_id].cleanup()
            exo_sessions.pop(session_id, None)
        logger.info(f"👋 Exotel session ended: {session_id}")


def get_active_sessions() -> Dict[str, CallSession]:
    """Expose active Exotel sessions for the /api/sessions endpoint."""
    return exo_sessions
