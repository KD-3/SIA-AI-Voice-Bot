"""
Appointment Setting Service (Feature #4)

Responsibilities:
  - Query Firestore for sales reps in the merchant's area
  - Check Google Calendar free/busy for each rep
  - Cache candidate slots in Firestore (pending_slots collection)
  - Create confirmed Calendar events
  - Persist confirmed appointments in Firestore
  - Send SMS confirmation via Twilio
"""

import json
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
from loguru import logger

import firebase_admin
from firebase_admin import credentials, firestore as fs
from google.oauth2 import service_account
from googleapiclient.discovery import build
from twilio.rest import Client as TwilioClient

from config import settings


# ── Firebase singleton ────────────────────────────────────────────────────────

_db: Optional[object] = None


def _get_db():
    global _db
    if _db is None:
        if not firebase_admin._apps:
            cred = credentials.Certificate(settings.firebase_service_account_path)
            firebase_admin.initialize_app(cred, {"projectId": settings.firebase_project_id})
        _db = fs.client()
    return _db


# ── Google Calendar helper ────────────────────────────────────────────────────

def _get_calendar_service():
    """Build a Google Calendar API service using a service-account key file."""
    creds = service_account.Credentials.from_service_account_file(
        settings.google_calendar_service_account_path,
        scopes=["https://www.googleapis.com/auth/calendar"],
    )
    # If the service account uses domain-wide delegation, impersonate the delegate
    if settings.google_calendar_delegate_email:
        creds = creds.with_subject(settings.google_calendar_delegate_email)
    return build("calendar", "v3", credentials=creds, cache_discovery=False)


# ── AppointmentService ────────────────────────────────────────────────────────

class AppointmentService:
    """
    Core service for Feature #4 – Appointment Setting.

    Usage (from CallSession):
        svc = AppointmentService()
        slots = await svc.find_available_slots("South Bengaluru", "demo")
        result = await svc.book_appointment(slot_id, lead_phone, ...)
    """

    SLOT_DURATION_MIN = 30        # minutes per slot
    SLOTS_TO_OFFER = 3            # max slots presented to merchant
    LOOK_AHEAD_DAYS = 5           # search window
    BUSINESS_START_HOUR = 10      # 10:00 IST
    BUSINESS_END_HOUR = 18        # 18:00 IST (6 PM)
    IST_OFFSET = timedelta(hours=5, minutes=30)

    def __init__(self):
        self.db = _get_db()
        self.cal = _get_calendar_service()
        self.twilio = TwilioClient(settings.twilio_account_sid, settings.twilio_auth_token)

    # ── Public API ────────────────────────────────────────────────────────────

    async def find_available_slots(
        self, area: str, appointment_type: str = "demo"
    ) -> Dict:
        """
        Find up to SLOTS_TO_OFFER available slots across all reps in the area.

        Returns:
            {
                "area": str,
                "appointment_type": str,
                "slots": [
                    {
                        "slot_id": str,
                        "rep_name": str,
                        "display": "Monday, 07 Apr at 11:00 AM IST",
                        "start_iso": str,
                        "end_iso": str,
                    }, ...
                ]
            }
        """
        reps = self._get_reps_by_area(area)
        if not reps:
            logger.warning(f"🗓 No sales reps found for area: {area}")
            return {"area": area, "appointment_type": appointment_type, "slots": []}

        all_slots: List[Dict] = []
        for rep in reps:
            rep_slots = self._get_free_slots(rep)
            all_slots.extend(rep_slots)
            if len(all_slots) >= self.SLOTS_TO_OFFER * 2:
                break  # Enough candidates, stop early

        # Sort by start time, deduplicate, take top N
        all_slots.sort(key=lambda s: s["start_iso"])
        top = all_slots[: self.SLOTS_TO_OFFER]

        # Persist as pending_slots so booking step can retrieve full metadata
        for slot in top:
            self.db.collection("pending_slots").document(slot["slot_id"]).set(slot)

        logger.info(f"🗓 Found {len(top)} slot(s) for {area} ({appointment_type})")
        return {"area": area, "appointment_type": appointment_type, "slots": top}

    async def book_appointment(
        self,
        slot_id: str,
        lead_phone: str,
        appointment_type: str,
        needs_document_collection: bool = False,
        lead_name: str = "Merchant",
    ) -> Dict:
        """
        Confirm the booking:
          1. Retrieve pending slot from Firestore
          2. Create Google Calendar event
          3. Persist appointment in Firestore
          4. Send SMS to merchant
          5. Return structured result for LLM to narrate

        Returns:
            {"success": bool, "rep_name": str, "readable_time": str, "sms_sent": bool, ...}
        """
        # 1. Retrieve pending slot
        slot_doc = self.db.collection("pending_slots").document(slot_id).get()
        if not slot_doc.exists:
            logger.error(f"❌ Pending slot not found: {slot_id}")
            return {"success": False, "error": "Slot not found or has expired. Please check slots again."}

        slot = slot_doc.to_dict()
        rep = self._get_rep_by_id(slot["rep_id"])
        if not rep:
            logger.error(f"❌ Rep not found: {slot['rep_id']}")
            return {"success": False, "error": "Sales rep not found."}

        # 2. Create Google Calendar event
        summary = f"Paytm Demo – {lead_name}"
        if appointment_type == "document_collection":
            summary = f"Paytm KYC Document Collection – {lead_name}"
        elif appointment_type == "demo_and_document_collection":
            summary = f"Paytm Demo + KYC – {lead_name}"

        description_lines = [f"Appointment type: {appointment_type}"]
        if needs_document_collection and appointment_type == "demo":
            description_lines.append(
                "Note: Merchant has also requested KYC document collection at this visit."
            )
        description_lines.append(f"Lead phone: {lead_phone}")

        event_body = {
            "summary": summary,
            "description": "\n".join(description_lines),
            "start": {"dateTime": slot["start_iso"], "timeZone": "Asia/Kolkata"},
            "end":   {"dateTime": slot["end_iso"],   "timeZone": "Asia/Kolkata"},
            "attendees": [{"email": rep["email"]}],
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "email", "minutes": 60},
                    {"method": "popup", "minutes": 15},
                ],
            },
        }

        try:
            created_event = self.cal.events().insert(
                calendarId=rep["calendar_id"],
                body=event_body,
                sendUpdates="all",
            ).execute()
            calendar_event_id = created_event.get("id", "")
            logger.info(f"📅 Calendar event created: {calendar_event_id}")
        except Exception as e:
            logger.error(f"❌ Google Calendar event creation failed: {e}")
            return {"success": False, "error": f"Calendar booking failed: {str(e)}"}

        # 3. Persist to Firestore appointments collection
        appt_data = {
            "lead_phone": lead_phone,
            "lead_name": lead_name,
            "rep_id": rep["id"],
            "rep_name": rep["name"],
            "rep_phone": rep["phone"],
            "area": rep["area"],
            "appointment_type": appointment_type,
            "needs_document_collection": needs_document_collection,
            "start_iso": slot["start_iso"],
            "end_iso": slot["end_iso"],
            "calendar_event_id": calendar_event_id,
            "status": "confirmed",
            "created_at": fs.SERVER_TIMESTAMP,
        }
        _, appt_ref = self.db.collection("appointments").add(appt_data)
        logger.info(f"✅ Appointment saved: {appt_ref.id}")

        # 4. Clean up pending slot
        self.db.collection("pending_slots").document(slot_id).delete()

        # 5. Send SMS
        sms_body = self._build_sms(slot, rep, appointment_type, needs_document_collection)
        sms_sent = self._send_sms(lead_phone, sms_body)

        # Human-readable confirmation time
        start_dt = datetime.fromisoformat(slot["start_iso"])
        ist_dt = start_dt + self.IST_OFFSET
        readable_time = ist_dt.strftime("%A, %d %B at %I:%M %p IST")

        return {
            "success": True,
            "appointment_id": appt_ref.id,
            "rep_name": rep["name"],
            "rep_phone": rep["phone"],
            "readable_time": readable_time,
            "sms_sent": sms_sent,
        }

    # ── Firestore helpers ─────────────────────────────────────────────────────

    def _get_reps_by_area(self, area: str) -> List[Dict]:
        """Return active sales reps whose area matches (case-insensitive)."""
        # Exact match first
        docs = (
            self.db.collection("sales_reps")
            .where("area", "==", area)
            .where("active", "==", True)
            .stream()
        )
        reps = [{"id": d.id, **d.to_dict()} for d in docs]

        # Fallback: partial match (e.g. "Bengaluru" matches "South Bengaluru")
        if not reps:
            all_docs = (
                self.db.collection("sales_reps")
                .where("active", "==", True)
                .stream()
            )
            area_lower = area.lower()
            reps = [
                {"id": d.id, **d.to_dict()}
                for d in all_docs
                if area_lower in d.to_dict().get("area", "").lower()
            ]

        return reps

    def _get_rep_by_id(self, rep_id: str) -> Optional[Dict]:
        doc = self.db.collection("sales_reps").document(rep_id).get()
        return {"id": doc.id, **doc.to_dict()} if doc.exists else None

    # ── Google Calendar free-slot finder ─────────────────────────────────────

    def _get_free_slots(self, rep: Dict) -> List[Dict]:
        """
        Return up to (SLOTS_TO_OFFER) free 30-min slots for a rep
        within the next LOOK_AHEAD_DAYS business hours.
        """
        now_utc = datetime.now(timezone.utc)
        look_end = now_utc + timedelta(days=self.LOOK_AHEAD_DAYS)

        # Query freebusy
        try:
            fb_result = self.cal.freebusy().query(body={
                "timeMin": now_utc.isoformat(),
                "timeMax": look_end.isoformat(),
                "timeZone": "Asia/Kolkata",
                "items": [{"id": rep["calendar_id"]}],
            }).execute()
            busy_periods = fb_result["calendars"].get(rep["calendar_id"], {}).get("busy", [])
        except Exception as e:
            logger.warning(f"⚠️  Freebusy query failed for rep {rep['id']}: {e}. Assuming free.")
            busy_periods = []

        slots: List[Dict] = []
        # Start from the next whole hour
        cursor = now_utc.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)

        while len(slots) < self.SLOTS_TO_OFFER and cursor < look_end:
            slot_end = cursor + timedelta(minutes=self.SLOT_DURATION_MIN)

            # Convert to IST for business-hours check
            ist_cursor = cursor + self.IST_OFFSET
            hour = ist_cursor.hour
            weekday = ist_cursor.weekday()  # 0=Mon … 6=Sun

            is_business = (
                weekday <= 5  # Mon–Sat
                and self.BUSINESS_START_HOUR <= hour < self.BUSINESS_END_HOUR
            )

            if is_business and not self._overlaps_busy(cursor, slot_end, busy_periods):
                slot_id = f"{rep['id']}_{cursor.strftime('%Y%m%dT%H%M%SZ')}"
                slots.append({
                    "slot_id": slot_id,
                    "rep_id": rep["id"],
                    "rep_name": rep["name"],
                    "area": rep["area"],
                    "start_iso": cursor.isoformat(),
                    "end_iso": slot_end.isoformat(),
                    "display": ist_cursor.strftime("%A, %d %b at %I:%M %p IST"),
                })

            cursor += timedelta(minutes=self.SLOT_DURATION_MIN)

        return slots

    @staticmethod
    def _overlaps_busy(start: datetime, end: datetime, busy: List[Dict]) -> bool:
        for period in busy:
            b_start = datetime.fromisoformat(period["start"].replace("Z", "+00:00"))
            b_end = datetime.fromisoformat(period["end"].replace("Z", "+00:00"))
            if start < b_end and end > b_start:
                return True
        return False

    # ── SMS helpers ───────────────────────────────────────────────────────────

    def _build_sms(
        self,
        slot: Dict,
        rep: Dict,
        appointment_type: str,
        needs_document_collection: bool,
    ) -> str:
        start_dt = datetime.fromisoformat(slot["start_iso"])
        ist_str = (start_dt + self.IST_OFFSET).strftime("%d %b %Y, %I:%M %p IST")

        type_label = {
            "demo": "Product Demo",
            "document_collection": "KYC Document Collection",
            "demo_and_document_collection": "Product Demo + KYC Document Collection",
        }.get(appointment_type, appointment_type)

        lines = [
            f"Your Paytm appointment is confirmed!",
            f"Type: {type_label}",
            f"Date: {ist_str}",
            f"Sales Rep: {rep['name']} ({rep['phone']})",
            f"Area: {rep['area']}",
        ]
        if needs_document_collection and appointment_type == "demo":
            lines.append("Please keep your KYC documents ready for collection.")
        lines.append("For queries, call Paytm Support: 0120-4456-456")
        return "\n".join(lines)

    def _send_sms(self, to_phone: str, body: str) -> bool:
        try:
            self.twilio.messages.create(
                body=body,
                from_=settings.twilio_phone_number,
                to=to_phone,
            )
            logger.info(f"📱 SMS confirmation sent to {to_phone}")
            return True
        except Exception as e:
            logger.error(f"❌ SMS send failed to {to_phone}: {e}")
            return False
