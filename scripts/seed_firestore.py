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

# ── Field Engineers ───────────────────────────────────────────────────────────
# Separate hierarchy from sales reps. Zones use cardinal/central breakdown
# distinct from the North/South breakdown used for sales reps.
# Replace calendar_id values with real Google Calendar IDs before going live.

FIELD_ENGINEERS = [
    # ── Bengaluru ─────────────────────────────────────────────────────────────
    {
        "id": "fe_blr_central_01",
        "name": "Arjun Nair",
        "email": "arjun.nair@paytm-field.example.com",
        "phone": "+919700001001",
        "zone": "Central Bengaluru",
        "city": "Bengaluru",
        "calendar_id": "arjun.nair@paytm-field.example.com",
        "specialisation": ["Soundbox", "POS Terminal", "EDC Machine"],
        "active": True,
    },
    {
        "id": "fe_blr_central_02",
        "name": "Meena Krishnan",
        "email": "meena.krishnan@paytm-field.example.com",
        "phone": "+919700001002",
        "zone": "Central Bengaluru",
        "city": "Bengaluru",
        "calendar_id": "meena.krishnan@paytm-field.example.com",
        "specialisation": ["Soundbox", "POS Terminal"],
        "active": True,
    },
    {
        "id": "fe_blr_east_01",
        "name": "Sudarshan Rao",
        "email": "sudarshan.rao@paytm-field.example.com",
        "phone": "+919700001003",
        "zone": "East Bengaluru",
        "city": "Bengaluru",
        "calendar_id": "sudarshan.rao@paytm-field.example.com",
        "specialisation": ["Soundbox", "EDC Machine"],
        "active": True,
    },
    {
        "id": "fe_blr_west_01",
        "name": "Lakshmi Venkat",
        "email": "lakshmi.venkat@paytm-field.example.com",
        "phone": "+919700001004",
        "zone": "West Bengaluru",
        "city": "Bengaluru",
        "calendar_id": "lakshmi.venkat@paytm-field.example.com",
        "specialisation": ["Soundbox", "POS Terminal", "EDC Machine"],
        "active": True,
    },
    # ── Mumbai ────────────────────────────────────────────────────────────────
    {
        "id": "fe_mum_central_01",
        "name": "Rohit Sawant",
        "email": "rohit.sawant@paytm-field.example.com",
        "phone": "+919700002001",
        "zone": "Central Mumbai",
        "city": "Mumbai",
        "calendar_id": "rohit.sawant@paytm-field.example.com",
        "specialisation": ["Soundbox", "POS Terminal"],
        "active": True,
    },
    {
        "id": "fe_mum_east_01",
        "name": "Preeti Kulkarni",
        "email": "preeti.kulkarni@paytm-field.example.com",
        "phone": "+919700002002",
        "zone": "East Mumbai",
        "city": "Mumbai",
        "calendar_id": "preeti.kulkarni@paytm-field.example.com",
        "specialisation": ["Soundbox", "EDC Machine"],
        "active": True,
    },
    {
        "id": "fe_mum_west_01",
        "name": "Ganesh Patil",
        "email": "ganesh.patil@paytm-field.example.com",
        "phone": "+919700002003",
        "zone": "West Mumbai",
        "city": "Mumbai",
        "calendar_id": "ganesh.patil@paytm-field.example.com",
        "specialisation": ["Soundbox", "POS Terminal", "EDC Machine"],
        "active": True,
    },
    # ── Delhi ─────────────────────────────────────────────────────────────────
    {
        "id": "fe_del_central_01",
        "name": "Harpreet Kaur",
        "email": "harpreet.kaur@paytm-field.example.com",
        "phone": "+919700003001",
        "zone": "Central Delhi",
        "city": "Delhi",
        "calendar_id": "harpreet.kaur@paytm-field.example.com",
        "specialisation": ["Soundbox", "POS Terminal"],
        "active": True,
    },
    {
        "id": "fe_del_east_01",
        "name": "Deepak Sharma",
        "email": "deepak.sharma@paytm-field.example.com",
        "phone": "+919700003002",
        "zone": "East Delhi",
        "city": "Delhi",
        "calendar_id": "deepak.sharma@paytm-field.example.com",
        "specialisation": ["Soundbox", "EDC Machine"],
        "active": True,
    },
    {
        "id": "fe_del_west_01",
        "name": "Sunita Arora",
        "email": "sunita.arora@paytm-field.example.com",
        "phone": "+919700003003",
        "zone": "West Delhi",
        "city": "Delhi",
        "calendar_id": "sunita.arora@paytm-field.example.com",
        "specialisation": ["Soundbox", "POS Terminal", "EDC Machine"],
        "active": True,
    },
    # ── Hyderabad ─────────────────────────────────────────────────────────────
    {
        "id": "fe_hyd_central_01",
        "name": "Venkata Reddy",
        "email": "venkata.reddy@paytm-field.example.com",
        "phone": "+919700004001",
        "zone": "Central Hyderabad",
        "city": "Hyderabad",
        "calendar_id": "venkata.reddy@paytm-field.example.com",
        "specialisation": ["Soundbox", "POS Terminal", "EDC Machine"],
        "active": True,
    },
    {
        "id": "fe_hyd_east_01",
        "name": "Padma Lakshmi",
        "email": "padma.lakshmi@paytm-field.example.com",
        "phone": "+919700004002",
        "zone": "East Hyderabad",
        "city": "Hyderabad",
        "calendar_id": "padma.lakshmi@paytm-field.example.com",
        "specialisation": ["Soundbox", "EDC Machine"],
        "active": True,
    },
    # ── Chennai ───────────────────────────────────────────────────────────────
    {
        "id": "fe_chn_north_01",
        "name": "Kartik Subramanian",
        "email": "kartik.subramanian@paytm-field.example.com",
        "phone": "+919700005001",
        "zone": "North Chennai",
        "city": "Chennai",
        "calendar_id": "kartik.subramanian@paytm-field.example.com",
        "specialisation": ["Soundbox", "POS Terminal"],
        "active": True,
    },
    {
        "id": "fe_chn_south_01",
        "name": "Ananya Iyer",
        "email": "ananya.iyer@paytm-field.example.com",
        "phone": "+919700005002",
        "zone": "South Chennai",
        "city": "Chennai",
        "calendar_id": "ananya.iyer@paytm-field.example.com",
        "specialisation": ["Soundbox", "POS Terminal", "EDC Machine"],
        "active": True,
    },
    # ── Ahmedabad ─────────────────────────────────────────────────────────────
    {
        "id": "fe_ahm_central_01",
        "name": "Nikhil Shah",
        "email": "nikhil.shah@paytm-field.example.com",
        "phone": "+919700006001",
        "zone": "Central Ahmedabad",
        "city": "Ahmedabad",
        "calendar_id": "nikhil.shah@paytm-field.example.com",
        "specialisation": ["Soundbox", "POS Terminal", "EDC Machine"],
        "active": True,
    },
    {
        "id": "fe_ahm_east_01",
        "name": "Foram Patel",
        "email": "foram.patel@paytm-field.example.com",
        "phone": "+919700006002",
        "zone": "East Ahmedabad",
        "city": "Ahmedabad",
        "calendar_id": "foram.patel@paytm-field.example.com",
        "specialisation": ["Soundbox", "EDC Machine"],
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

    print(f"Seeding {len(SALES_REPS)} sales reps → 'sales_reps' collection...")
    batch = db.batch()
    for rep in SALES_REPS:
        rep_id = rep.pop("id")
        ref = db.collection("sales_reps").document(rep_id)
        batch.set(ref, rep)
        print(f"  ✓ {rep_id:35s}  {rep['name']:22s}  {rep['area']}")
    batch.commit()
    print(f"  → {len(SALES_REPS)} sales reps written.\n")

    print(f"Seeding {len(FIELD_ENGINEERS)} field engineers → 'field_engineers' collection...")
    batch2 = db.batch()
    for eng in FIELD_ENGINEERS:
        eng_id = eng.pop("id")
        ref = db.collection("field_engineers").document(eng_id)
        batch2.set(ref, eng)
        print(f"  ✓ {eng_id:35s}  {eng['name']:22s}  {eng['zone']}")
    batch2.commit()
    print(f"  → {len(FIELD_ENGINEERS)} field engineers written.\n")

    print("All done!")
    print(
        "\nNext steps:\n"
        "  1. Replace placeholder calendar_id values with real Google Calendar IDs\n"
        "     for BOTH sales_reps and field_engineers.\n"
        "  2. Share each person's calendar with your Google service account.\n"
        "  3. Set GOOGLE_CALENDAR_SERVICE_ACCOUNT_PATH and FIREBASE_SERVICE_ACCOUNT_PATH in .env.\n"
        "  4. Optionally set GOOGLE_CALENDAR_DELEGATE_EMAIL if using domain-wide delegation."
    )


if __name__ == "__main__":
    seed()
