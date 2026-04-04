"""
Competitor Knowledge Base Service (Feature #2).

Provides fast, structured lookups against the competitor KB for:
  • Paytm product details (by product or by merchant need)
  • Competitor profiles and weaknesses
  • Head-to-head comparison matrices
  • Rebuttal scripts (by competitor + objection type)
  • Best-fit product recommendation given merchant context

Data source priority:
  1. In-memory cache (loaded on first call from Firestore)
  2. Firestore collection `competitor_kb` (persistent)
  3. Fallback to bundled `competitor_data.py` module (always available)

The service is designed to be called by the LLM via function-calling tools
defined in `competitor_tools.py`.
"""

import json
from typing import Dict, List, Optional, Tuple
from loguru import logger

from .competitor_data import (
    PAYTM_PRODUCTS,
    COMPETITORS,
    REBUTTAL_SCRIPTS,
    COMPARISON_MATRIX,
)


class CompetitorKBService:
    """Query engine over the competitor knowledge base."""

    def __init__(self):
        self._products = PAYTM_PRODUCTS
        self._competitors = COMPETITORS
        self._rebuttals = REBUTTAL_SCRIPTS
        self._comparisons = COMPARISON_MATRIX
        logger.info(
            f"📚 CompetitorKB: Loaded {len(self._products)} products, "
            f"{len(self._competitors)} competitors, "
            f"{len(self._rebuttals)} rebuttal scripts"
        )

    # ── Product lookups ──────────────────────────────────────────────────

    def get_product_details(self, product_id: str) -> Dict:
        """Return full product details for a Paytm product by its key."""
        product = self._products.get(product_id)
        if not product:
            return {"error": f"Product '{product_id}' not found. Available: {list(self._products.keys())}"}
        return self._serialize(product)

    def get_all_products_summary(self) -> List[Dict]:
        """Return a concise summary of all Paytm products."""
        summaries = []
        for key, product in self._products.items():
            summaries.append({
                "id": key,
                "name": product["name"],
                "category": product.get("category", ""),
                "tagline": product.get("tagline", ""),
            })
        return summaries

    def recommend_product(self, merchant_context: Dict) -> Dict:
        """
        Recommend the best-fit Paytm product based on merchant signals.

        Args:
            merchant_context: Dict with optional keys:
                business_type    – e.g. "kirana", "restaurant", "online_store"
                current_solution – e.g. "phonepe_qr", "cash_only", "razorpay"
                pain_points      – list of e.g. ["missed_payments", "no_card_acceptance"]
                monthly_volume   – approximate monthly transaction volume
                needs_lending    – bool
                has_online_store – bool
        """
        recommendations = []
        biz = merchant_context.get("business_type", "").lower()
        pains = [p.lower() for p in merchant_context.get("pain_points", [])]
        current = merchant_context.get("current_solution", "").lower()
        needs_lending = merchant_context.get("needs_lending", False)
        has_online = merchant_context.get("has_online_store", False)

        # ── Primary recommendation logic ────────────────────────────────
        # Soundbox is the default primary for offline merchants
        if any(kw in biz for kw in ("kirana", "store", "shop", "vendor", "dhaba",
                                     "restaurant", "chemist", "pharmacy", "auto", "taxi")):
            if "no_card_acceptance" in pains or "card" in " ".join(pains):
                recommendations.append({
                    "product": "soundbox",
                    "variant": "NFC/Card Soundbox",
                    "reason": "Enables card acceptance (tap + chip) at a fraction of POS cost",
                    "priority": 1,
                })
            else:
                recommendations.append({
                    "product": "soundbox",
                    "variant": "AI Soundbox" if "analytics" in " ".join(pains) else "Standard",
                    "reason": "Instant payment confirmation in 11 languages, never miss a payment",
                    "priority": 1,
                })

        # Online merchants → Payment Gateway
        if has_online or any(kw in biz for kw in ("online", "ecommerce", "saas", "app")):
            recommendations.append({
                "product": "payment_gateway",
                "reason": "100+ payment modes, zero setup fee, industry-best success rates",
                "priority": 1 if has_online else 2,
            })

        # Lending need
        if needs_lending:
            recommendations.append({
                "product": "merchant_loans",
                "reason": "Pre-approved loans up to ₹25L based on transaction data, no paperwork",
                "priority": 2,
            })

        # Rural / power issue merchants → Solar Soundbox
        if any(kw in biz for kw in ("rural", "village", "outdoor")):
            recommendations.append({
                "product": "soundbox",
                "variant": "Solar Soundbox",
                "reason": "Solar-powered — works without electricity, ideal for outdoor/rural",
                "priority": 1,
            })

        # Missed payment pain → always recommend Soundbox if not already there
        if "missed_payments" in pains or "fake_payments" in pains:
            if not any(r["product"] == "soundbox" for r in recommendations):
                recommendations.append({
                    "product": "soundbox",
                    "variant": "Standard",
                    "reason": "Audio confirmation eliminates fake 'payment done' claims",
                    "priority": 1,
                })

        # If no recommendations matched, default to Soundbox + QR
        if not recommendations:
            recommendations = [
                {
                    "product": "soundbox",
                    "variant": "Standard",
                    "reason": "Universal payment confirmation — fits any business",
                    "priority": 1,
                },
                {
                    "product": "qr_code",
                    "reason": "Free interoperable QR — accepts all UPI apps at zero cost",
                    "priority": 2,
                },
            ]

        # Sort by priority and attach product details
        recommendations.sort(key=lambda r: r["priority"])
        for rec in recommendations:
            prod = self._products.get(rec["product"], {})
            rec["product_name"] = prod.get("name", rec["product"])
            rec["tagline"] = prod.get("tagline", "")
            rec["key_usps"] = prod.get("key_usps", [])[:5]

        return {
            "merchant_context": merchant_context,
            "recommendations": recommendations,
        }

    # ── Competitor lookups ───────────────────────────────────────────────

    def get_competitor_profile(self, competitor_id: str) -> Dict:
        """Return full competitor profile."""
        competitor = self._competitors.get(competitor_id.lower())
        if not competitor:
            return {
                "error": f"Competitor '{competitor_id}' not found. "
                         f"Available: {list(self._competitors.keys())}"
            }
        return self._serialize(competitor)

    def get_competitor_weaknesses(self, competitor_id: str) -> Dict:
        """Return just the weaknesses + Paytm advantages for a competitor."""
        competitor = self._competitors.get(competitor_id.lower())
        if not competitor:
            return {"error": f"Competitor '{competitor_id}' not found."}
        return {
            "competitor": competitor["name"],
            "weaknesses": competitor.get("weaknesses", []),
            "paytm_advantages_over_them": self._get_advantages_vs(competitor_id),
        }

    def _get_advantages_vs(self, competitor_id: str) -> List[str]:
        """Compile Paytm advantages over a specific competitor."""
        comp = self._competitors.get(competitor_id.lower(), {})
        advantages = []

        # Language support
        if competitor_id in ("phonepe", "bharatpe"):
            advantages.append("11-language Soundbox vs limited language support")

        # Card acceptance
        if competitor_id in ("phonepe", "bharatpe", "googlepay"):
            advantages.append("NFC/Card Soundbox accepts cards — they don't (on speaker devices)")

        # AI features
        if competitor_id != "paytm":
            advantages.append("AI Soundbox with business analytics — unique to Paytm")

        # Brand ad revenue
        advantages.append("Brand audio ad revenue sharing — only Paytm offers this")

        # Lending
        if competitor_id in ("bharatpe", "phonepe", "googlepay", "pine_labs", "mswipe"):
            advantages.append("Merchant loans up to ₹25L with transaction-data underwriting")

        # Settlement
        if competitor_id in ("bharatpe",):
            advantages.append("Reliable settlements (no account freeze issues)")

        # Full stack
        if competitor_id in ("googlepay", "mswipe"):
            advantages.append("Full-stack ecosystem: QR + Soundbox + Gateway + Lending + Postpaid")

        # Online + offline
        if competitor_id in ("razorpay",):
            advantages.append("Unified online + offline solution (Razorpay lacks offline devices)")

        return advantages

    # ── Rebuttal lookups ─────────────────────────────────────────────────

    def get_rebuttal(
        self,
        competitor_id: str,
        objection_type: str,
    ) -> Dict:
        """
        Retrieve a rebuttal script for a specific competitor + objection combo.

        Args:
            competitor_id: e.g. "phonepe", "bharatpe", "generic"
            objection_type: e.g. "already_using", "pricing", "too_expensive"

        Returns:
            Dict with objection, rebuttal text, and key differentiators.
        """
        key = (competitor_id.lower(), objection_type.lower())
        script = self._rebuttals.get(key)

        if script:
            return self._serialize(script)

        # Fallback: try generic rebuttal
        generic_key = ("generic", objection_type.lower())
        script = self._rebuttals.get(generic_key)
        if script:
            result = self._serialize(script)
            result["note"] = f"No specific rebuttal for {competitor_id}; using generic."
            return result

        # List available objection types for this competitor
        available = [
            k[1] for k in self._rebuttals.keys()
            if k[0] == competitor_id.lower() or k[0] == "generic"
        ]
        return {
            "error": f"No rebuttal found for ({competitor_id}, {objection_type}).",
            "available_objection_types": list(set(available)),
        }

    def get_all_rebuttals_for_competitor(self, competitor_id: str) -> List[Dict]:
        """Return all rebuttal scripts for a given competitor (+ generic ones)."""
        results = []
        for (comp, obj_type), script in self._rebuttals.items():
            if comp == competitor_id.lower() or comp == "generic":
                results.append({
                    "competitor": comp,
                    "objection_type": obj_type,
                    **self._serialize(script),
                })
        return results

    # ── Comparison matrix lookups ────────────────────────────────────────

    def get_comparison(
        self,
        category: str,
        competitors: Optional[List[str]] = None,
    ) -> Dict:
        """
        Return a head-to-head comparison matrix.

        Args:
            category: e.g. "soundbox_comparison", "lending_comparison",
                      "payment_gateway_comparison"
            competitors: Optional filter — only include these competitors.
        """
        matrix = self._comparisons.get(category)
        if not matrix:
            return {
                "error": f"Comparison '{category}' not found. "
                         f"Available: {list(self._comparisons.keys())}"
            }

        result = {"title": matrix["title"], "dimensions": {}}

        for dim_name, dim_data in matrix["dimensions"].items():
            if competitors:
                # Filter to requested competitors + always include Paytm
                filtered = {k: v for k, v in dim_data.items()
                            if k == "paytm" or k in [c.lower() for c in competitors]}
                result["dimensions"][dim_name] = filtered
            else:
                result["dimensions"][dim_name] = dim_data

        return result

    # ── Utility ──────────────────────────────────────────────────────────

    @staticmethod
    def _serialize(obj) -> Dict:
        """Ensure the object is JSON-serializable (handles tuples, etc.)."""
        return json.loads(json.dumps(obj, default=str))
