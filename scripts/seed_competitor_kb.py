"""
Seed script – populates Firestore with the competitor knowledge base (Feature #2).

Usage:
    export FIREBASE_SERVICE_ACCOUNT_PATH=/path/to/serviceAccount.json
    python scripts/seed_competitor_kb.py

Collections created / overwritten:
    competitor_kb/paytm_products   – sub-collection with one doc per product
    competitor_kb/competitors      – sub-collection with one doc per competitor
    competitor_kb/rebuttals        – sub-collection with one doc per (competitor, objection)
    competitor_kb/comparisons      – sub-collection with one doc per comparison matrix
"""

import os
import sys

# Allow running from repo root without installing the package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "voice"))

import firebase_admin
from firebase_admin import credentials, firestore

from knowledge.competitor_data import (
    PAYTM_PRODUCTS,
    COMPETITORS,
    REBUTTAL_SCRIPTS,
    COMPARISON_MATRIX,
)

# ── Config ────────────────────────────────────────────────────────────────────

SERVICE_ACCOUNT_PATH = os.getenv(
    "FIREBASE_SERVICE_ACCOUNT_PATH", "serviceAccount.json"
)
PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "paytm-hackathon-1")

COLLECTION = "competitor_kb"


def seed():
    if not os.path.exists(SERVICE_ACCOUNT_PATH):
        print(
            f"ERROR: Service account file not found at '{SERVICE_ACCOUNT_PATH}'.\n"
            "Set FIREBASE_SERVICE_ACCOUNT_PATH to the correct path and retry."
        )
        sys.exit(1)

    # Initialise Firebase (skip if already initialised by another script)
    try:
        firebase_admin.get_app()
    except ValueError:
        cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
        firebase_admin.initialize_app(cred, {"projectId": PROJECT_ID})

    db = firestore.client()
    batch = db.batch()
    doc_count = 0

    # ── 1. Paytm Products ────────────────────────────────────────────────
    print("\n📦 Seeding Paytm Products...")
    for product_id, product_data in PAYTM_PRODUCTS.items():
        ref = db.collection(COLLECTION).document("paytm_products") \
                .collection("items").document(product_id)
        batch.set(ref, product_data)
        doc_count += 1
        print(f"  ✓ {product_id:25s}  {product_data['name']}")

    # ── 2. Competitor Profiles ───────────────────────────────────────────
    print("\n🕵️  Seeding Competitor Profiles...")
    for comp_id, comp_data in COMPETITORS.items():
        ref = db.collection(COLLECTION).document("competitors") \
                .collection("items").document(comp_id)
        batch.set(ref, comp_data)
        doc_count += 1
        print(f"  ✓ {comp_id:25s}  {comp_data['name']}")

    # ── 3. Rebuttal Scripts ──────────────────────────────────────────────
    print("\n🛡️  Seeding Rebuttal Scripts...")
    for (comp_id, objection_type), script_data in REBUTTAL_SCRIPTS.items():
        doc_id = f"{comp_id}__{objection_type}"
        ref = db.collection(COLLECTION).document("rebuttals") \
                .collection("items").document(doc_id)
        data = {
            "competitor_id": comp_id,
            "objection_type": objection_type,
            **script_data,
        }
        batch.set(ref, data)
        doc_count += 1
        print(f"  ✓ {doc_id:40s}  {script_data.get('objection', '')[:50]}")

    # ── 4. Comparison Matrices ───────────────────────────────────────────
    print("\n📊 Seeding Comparison Matrices...")
    for matrix_id, matrix_data in COMPARISON_MATRIX.items():
        ref = db.collection(COLLECTION).document("comparisons") \
                .collection("items").document(matrix_id)
        batch.set(ref, matrix_data)
        doc_count += 1
        print(f"  ✓ {matrix_id:40s}  {matrix_data['title']}")

    # ── Commit ───────────────────────────────────────────────────────────
    batch.commit()
    print(f"\n✅ Done. {doc_count} documents written to Firestore collection '{COLLECTION}'.")
    print(
        "\nThe competitor KB is now available for the AI SDR.\n"
        "The in-memory fallback (competitor_data.py) is always available even without Firestore."
    )


if __name__ == "__main__":
    seed()
