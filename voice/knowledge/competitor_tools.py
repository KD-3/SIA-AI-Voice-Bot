"""
OpenAI function-calling tool definitions for Competitor KB (Feature #2).

These tools let the LLM query the competitor knowledge base mid-conversation to:
  • Look up Paytm product details
  • Recommend the best product for the merchant
  • Get competitor weaknesses
  • Retrieve rebuttal scripts for specific objections
  • Get head-to-head comparison data
"""

COMPETITOR_KB_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "lookup_paytm_product",
            "description": (
                "Get detailed information about a specific Paytm product "
                "including features, pricing, variants, key USPs, and ideal merchant profiles. "
                "Call this when the merchant asks about a product or you need details to pitch."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {
                        "type": "string",
                        "enum": [
                            "soundbox",
                            "qr_code",
                            "payment_gateway",
                            "merchant_loans",
                            "paytm_postpaid",
                            "digital_kyc",
                        ],
                        "description": (
                            "The Paytm product to look up. Options: "
                            "'soundbox' (payment confirmation device), "
                            "'qr_code' (all-in-one QR), "
                            "'payment_gateway' (online payments), "
                            "'merchant_loans' (business lending), "
                            "'paytm_postpaid' (buy now pay later for customers), "
                            "'digital_kyc' (onboarding verification)."
                        ),
                    }
                },
                "required": ["product_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "recommend_product_for_merchant",
            "description": (
                "Get a smart product recommendation based on what you've learned about "
                "the merchant during the conversation. Call this after gathering initial "
                "context about their business type, pain points, and current solutions."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "business_type": {
                        "type": "string",
                        "description": (
                            "The merchant's business type, inferred from conversation. "
                            "Examples: 'kirana', 'restaurant', 'chemist', 'online_store', "
                            "'street_vendor', 'auto_driver', 'salon', 'clinic'."
                        ),
                    },
                    "current_solution": {
                        "type": "string",
                        "description": (
                            "What the merchant currently uses for payments. "
                            "Examples: 'phonepe_qr', 'bharatpe_speaker', 'cash_only', "
                            "'razorpay', 'pine_labs_pos', 'googlepay', 'none'."
                        ),
                    },
                    "pain_points": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "Merchant's pain points gathered from conversation. "
                            "Examples: 'missed_payments', 'no_card_acceptance', "
                            "'slow_settlement', 'no_analytics', 'fake_payments', "
                            "'poor_support', 'need_loan', 'high_mdr'."
                        ),
                    },
                    "needs_lending": {
                        "type": "boolean",
                        "description": "True if the merchant has expressed interest in a business loan.",
                    },
                    "has_online_store": {
                        "type": "boolean",
                        "description": "True if the merchant sells online (website, app, or social media).",
                    },
                },
                "required": ["business_type"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_competitor_intel",
            "description": (
                "Get intelligence about a competitor including their weaknesses "
                "and Paytm's advantages over them. Call this when a merchant "
                "mentions using or being approached by a competitor."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "competitor_id": {
                        "type": "string",
                        "enum": [
                            "phonepe",
                            "bharatpe",
                            "razorpay",
                            "pine_labs",
                            "mswipe",
                            "googlepay",
                        ],
                        "description": (
                            "The competitor to look up. Map merchant mentions: "
                            "'PhonePe' → 'phonepe', "
                            "'BharatPe' → 'bharatpe', "
                            "'Razorpay' → 'razorpay', "
                            "'Pine Labs' → 'pine_labs', "
                            "'Mswipe' → 'mswipe', "
                            "'Google Pay/GPay' → 'googlepay'."
                        ),
                    },
                    "include_full_profile": {
                        "type": "boolean",
                        "description": (
                            "If true, return the full competitor profile including their "
                            "products for a detailed comparison. If false, return only "
                            "weaknesses and Paytm advantages (faster, more focused)."
                        ),
                    },
                },
                "required": ["competitor_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_objection_rebuttal",
            "description": (
                "Get a tailored rebuttal script when a merchant raises an objection. "
                "Call this any time the merchant pushes back — on pricing, on switching, "
                "on not needing the product, etc. Returns a proven rebuttal with key talking points."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "competitor_id": {
                        "type": "string",
                        "enum": [
                            "phonepe",
                            "bharatpe",
                            "razorpay",
                            "pine_labs",
                            "mswipe",
                            "googlepay",
                            "generic",
                        ],
                        "description": (
                            "The competitor context for the objection. Use 'generic' for "
                            "objections not tied to a specific competitor (e.g. 'too expensive', "
                            "'don't need it', 'will think about it')."
                        ),
                    },
                    "objection_type": {
                        "type": "string",
                        "enum": [
                            "already_using",
                            "pricing",
                            "approached_by_them",
                            "trust_issues",
                            "too_expensive",
                            "dont_need_it",
                            "will_think_about_it",
                            "competitor_cheaper",
                            "bad_experience",
                        ],
                        "description": (
                            "The type of objection raised. "
                            "'already_using' — merchant says they use a competitor. "
                            "'pricing' — merchant objects on price. "
                            "'approached_by_them' — a competitor just pitched the merchant. "
                            "'trust_issues' — merchant has trust concerns about payment platforms. "
                            "'too_expensive' — merchant says it costs too much. "
                            "'dont_need_it' — merchant says they don't need it. "
                            "'will_think_about_it' — merchant wants to delay decision. "
                            "'competitor_cheaper' — merchant says another offer is cheaper. "
                            "'bad_experience' — merchant had a bad past experience with Paytm."
                        ),
                    },
                },
                "required": ["competitor_id", "objection_type"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_comparison_matrix",
            "description": (
                "Get a side-by-side comparison table between Paytm and competitors "
                "for a specific product category. Useful when the merchant is comparing options."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "enum": [
                            "soundbox_comparison",
                            "lending_comparison",
                            "payment_gateway_comparison",
                        ],
                        "description": (
                            "The comparison category. "
                            "'soundbox_comparison' — speaker/device comparison. "
                            "'lending_comparison' — merchant loan comparison. "
                            "'payment_gateway_comparison' — online gateway comparison."
                        ),
                    },
                    "competitors": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "Optional: filter to specific competitors. "
                            "E.g. ['phonepe', 'bharatpe'] to compare only those two against Paytm. "
                            "Leave empty to compare all."
                        ),
                    },
                },
                "required": ["category"],
            },
        },
    },
]
