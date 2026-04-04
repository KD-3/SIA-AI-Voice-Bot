"""
Seed script – populates Firestore with placeholder sales rep data for Feature #4.

Usage:
    export FIREBASE_SERVICE_ACCOUNT_PATH=/path/to/serviceAccount.json
    python scripts/seed_firestore.py

Collections created / overwritten:
    sales_reps   – one document per rep, keyed by rep_id
"""

import os
import sys

# Allow running from repo root without installing the package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "voice"))

import firebase_admin
from firebase_admin import credentials, firestore

# ── Config ────────────────────────────────────────────────────────────────────

SERVICE_ACCOUNT_PATH = os.getenv(
    "FIREBASE_SERVICE_ACCOUNT_PATH", "serviceAccount.json"
)
PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "paytm-hackathon-1")

# ── Placeholder sales rep data ────────────────────────────────────────────────
# Each rep has a Google Calendar ID (their work email on Google Workspace).
# Replace calendar_id values with real calendars before going live.

SALES_REPS = [
    # ── Bengaluru ─────────────────────────────────────────────────────────────
    {
        "id": "rep_blr_south_01",
        "name": "Ravi Kumar",
        "email": "ravi.kumar@paytm-sales.example.com",
        "phone": "+919876543210",
        "area": "South Bengaluru",
        "city": "Bengaluru",
        "calendar_id": "ravi.kumar@paytm-sales.example.com",
        "active": True,
    },
    {
        "id": "rep_blr_south_02",
        "name": "Priya Sharma",
        "email": "priya.sharma@paytm-sales.example.com",
        "phone": "+919876543211",
        "area": "South Bengaluru",
        "city": "Bengaluru",
        "calendar_id": "priya.sharma@paytm-sales.example.com",
        "active": True,
    },
    {
        "id": "rep_blr_north_01",
        "name": "Amit Patel",
        "email": "amit.patel@paytm-sales.example.com",
        "phone": "+919876543212",
        "area": "North Bengaluru",
        "city": "Bengaluru",
        "calendar_id": "amit.patel@paytm-sales.example.com",
        "active": True,
    },
    {
        "id": "rep_blr_north_02",
        "name": "Sneha Reddy",
        "email": "sneha.reddy@paytm-sales.example.com",
        "phone": "+919876543213",
        "area": "North Bengaluru",
        "city": "Bengaluru",
        "calendar_id": "sneha.reddy@paytm-sales.example.com",
        "active": True,
    },
    # ── Mumbai ────────────────────────────────────────────────────────────────
    {
        "id": "rep_mum_south_01",
        "name": "Rahul Mehta",
        "email": "rahul.mehta@paytm-sales.example.com",
        "phone": "+919876543220",
        "area": "South Mumbai",
        "city": "Mumbai",
        "calendar_id": "rahul.mehta@paytm-sales.example.com",
        "active": True,
    },
    {
        "id": "rep_mum_south_02",
        "name": "Kavita Joshi",
        "email": "kavita.joshi@paytm-sales.example.com",
        "phone": "+919876543221",
        "area": "South Mumbai",
        "city": "Mumbai",
        "calendar_id": "kavita.joshi@paytm-sales.example.com",
        "active": True,
    },
    {
        "id": "rep_mum_north_01",
        "name": "Suresh Iyer",
        "email": "suresh.iyer@paytm-sales.example.com",
        "phone": "+919876543222",
        "area": "North Mumbai",
        "city": "Mumbai",
        "calendar_id": "suresh.iyer@paytm-sales.example.com",
        "active": True,
    },
    {
        "id": "rep_mum_north_02",
        "name": "Neha Gupta",
        "email": "neha.gupta@paytm-sales.example.com",
        "phone": "+919876543223",
        "area": "North Mumbai",
        "city": "Mumbai",
        "calendar_id": "neha.gupta@paytm-sales.example.com",
        "active": True,
    },
    # ── Delhi ─────────────────────────────────────────────────────────────────
    {
        "id": "rep_del_south_01",
        "name": "Vikram Singh",
        "email": "vikram.singh@paytm-sales.example.com",
        "phone": "+919876543230",
        "area": "South Delhi",
        "city": "Delhi",
        "calendar_id": "vikram.singh@paytm-sales.example.com",
        "active": True,
    },
    {
        "id": "rep_del_south_02",
        "name": "Pooja Verma",
        "email": "pooja.verma@paytm-sales.example.com",
        "phone": "+919876543231",
        "area": "South Delhi",
        "city": "Delhi",
        "calendar_id": "pooja.verma@paytm-sales.example.com",
        "active": True,
    },
    {
        "id": "rep_del_north_01",
        "name": "Rajesh Khanna",
        "email": "rajesh.khanna@paytm-sales.example.com",
        "phone": "+919876543232",
        "area": "North Delhi",
        "city": "Delhi",
        "calendar_id": "rajesh.khanna@paytm-sales.example.com",
        "active": True,
    },
    {
        "id": "rep_del_north_02",
        "name": "Anita Bose",
        "email": "anita.bose@paytm-sales.example.com",
        "phone": "+919876543233",
        "area": "North Delhi",
        "city": "Delhi",
        "calendar_id": "anita.bose@paytm-sales.example.com",
        "active": True,
    },
    # ── Hyderabad ─────────────────────────────────────────────────────────────
    {
        "id": "rep_hyd_01",
        "name": "Kiran Rao",
        "email": "kiran.rao@paytm-sales.example.com",
        "phone": "+919876543240",
        "area": "Hyderabad",
        "city": "Hyderabad",
        "calendar_id": "kiran.rao@paytm-sales.example.com",
        "active": True,
    },
    {
        "id": "rep_hyd_02",
        "name": "Divya Nair",
        "email": "divya.nair@paytm-sales.example.com",
        "phone": "+919876543241",
        "area": "Hyderabad",
        "city": "Hyderabad",
        "calendar_id": "divya.nair@paytm-sales.example.com",
        "active": True,
    },
    # ── Pune ──────────────────────────────────────────────────────────────────
    {
        "id": "rep_pun_01",
        "name": "Sanjay Desai",
        "email": "sanjay.desai@paytm-sales.example.com",
        "phone": "+919876543250",
        "area": "Pune",
        "city": "Pune",
        "calendar_id": "sanjay.desai@paytm-sales.example.com",
        "active": True,
    },
]


def seed():
    if not os.path.exists(SERVICE_ACCOUNT_PATH):
        print(
            f"ERROR: Service account file not found at '{SERVICE_ACCOUNT_PATH}'.\n"
            "Set FIREBASE_SERVICE_ACCOUNT_PATH to the correct path and retry."
        )
        sys.exit(1)

    cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
    firebase_admin.initialize_app(cred, {"projectId": PROJECT_ID})
    db = firestore.client()

    print(f"Seeding {len(SALES_REPS)} sales reps into project '{PROJECT_ID}'...")

    batch = db.batch()
    for rep in SALES_REPS:
        rep_id = rep.pop("id")
        ref = db.collection("sales_reps").document(rep_id)
        batch.set(ref, rep)
        print(f"  ✓ {rep_id:30s}  {rep['name']:20s}  {rep['area']}")

    batch.commit()
    print(f"\nDone. {len(SALES_REPS)} reps written to Firestore collection 'sales_reps'.")
    print(
        "\nNext steps:\n"
        "  1. Replace placeholder calendar_id values with real Google Calendar IDs.\n"
        "  2. Share each rep's calendar with your Google service account.\n"
        "  3. Set GOOGLE_CALENDAR_SERVICE_ACCOUNT_PATH and FIREBASE_SERVICE_ACCOUNT_PATH in .env.\n"
        "  4. Optionally set GOOGLE_CALENDAR_DELEGATE_EMAIL if using domain-wide delegation."
    )


if __name__ == "__main__":
    seed()
