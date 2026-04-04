"""
Competitor Knowledge Base – structured data for the AI SDR.

This module contains comprehensive intelligence on:
  • Paytm's own product catalog (features, pricing, USPs)
  • Competitor offerings (PhonePe, BharatPe, Razorpay, Pine Labs, etc.)
  • Head-to-head comparison matrices
  • Rebuttal scripts keyed by competitor + objection type
  • Common merchant objections and proven responses

The data is designed to be:
  1. Seeded into Firestore (collection: competitor_kb) for persistent storage
  2. Loaded at session start by CompetitorKBService for fast lookups
  3. Injected into the LLM context via function-calling tools
"""

# ─────────────────────────────────────────────────────────────────────────────
# PAYTM PRODUCT CATALOG
# ─────────────────────────────────────────────────────────────────────────────

PAYTM_PRODUCTS = {
    "soundbox": {
        "id": "paytm_soundbox",
        "name": "Paytm Soundbox",
        "category": "payment_device",
        "tagline": "India's #1 payment confirmation device — now AI-powered",
        "description": (
            "Instant audio+visual payment confirmation in 11 languages. "
            "Accepts UPI from any app, cards (NFC tap + chip), wallets. "
            "AI Soundbox variant includes an integrated AI assistant for "
            "real-time business insights, payment history, and performance tracking."
        ),
        "variants": [
            {
                "name": "Paytm Soundbox (Standard)",
                "price": "₹99/month rental OR ₹999 one-time (lifetime)",
                "features": [
                    "Instant audio confirmation in 11 languages",
                    "Accepts all UPI apps",
                    "4G connectivity — no Wi-Fi needed",
                    "Long battery life (up to 10 days)",
                    "Pre-activated, zero setup",
                ],
            },
            {
                "name": "Paytm AI Soundbox",
                "price": "₹125/month rental",
                "features": [
                    "Everything in Standard, plus:",
                    "Dual display — one for merchant, one for customer",
                    "Built-in AI assistant (voice-based business insights)",
                    "Performance tracking and payment analytics",
                    "Brand audio ads — earn extra revenue per transaction",
                    "Android-based — future firmware updates OTA",
                ],
            },
            {
                "name": "Paytm NFC/Card Soundbox",
                "price": "₹149/month rental",
                "features": [
                    "Everything in Standard, plus:",
                    "NFC tap-to-pay for credit/debit cards",
                    "Chip card insertion slot",
                    "EMV-compliant for secure card transactions",
                ],
            },
            {
                "name": "Paytm Solar Soundbox",
                "price": "₹99/month rental",
                "features": [
                    "Everything in Standard, plus:",
                    "Solar-powered — eco-friendly, uninterrupted operation",
                    "Ideal for outdoor vendors and rural merchants",
                    "No electricity dependency",
                ],
            },
        ],
        "key_usps": [
            "Largest merchant device install base in India",
            "Zero MDR on UPI transactions",
            "Works with ALL UPI apps — not locked to Paytm",
            "11-language audio support covers 95%+ of Indian merchants",
            "AI variant gives free business analytics — competitors charge extra",
            "Brand audio ads = additional passive income for merchants",
            "Pre-activated delivery — plug and earn in 5 minutes",
        ],
        "ideal_for": [
            "Kirana/general stores",
            "Street food vendors",
            "Chemists/pharmacies",
            "Small restaurants/dhabas",
            "Auto/taxi drivers",
            "Rural merchants with poor connectivity",
        ],
    },

    "qr_code": {
        "id": "paytm_qr",
        "name": "Paytm All-in-One QR",
        "category": "payment_acceptance",
        "tagline": "One QR. Every payment app. Zero cost.",
        "description": (
            "Interoperable QR code that accepts payments from any UPI app "
            "(Google Pay, PhonePe, BHIM, etc.) plus Paytm Wallet. "
            "Dynamic QR available for enterprise/GST-compliant businesses."
        ),
        "pricing": "FREE — zero setup, zero MDR on UPI",
        "features": [
            "Accepts ALL UPI apps — not restricted",
            "Static QR (free) or Dynamic QR (per-order amount pre-set)",
            "Instant settlement available (T+0 for eligible merchants)",
            "GST-compliant invoicing with Dynamic QR",
            "Works offline — customer scans, you get paid",
        ],
        "key_usps": [
            "Completely free to set up and use",
            "Interoperable — accepts all UPI apps, not just Paytm",
            "Dynamic QR prevents wrong-amount payments",
            "Instant settlement option for cash-flow-critical businesses",
        ],
    },

    "payment_gateway": {
        "id": "paytm_pg",
        "name": "Paytm Payment Gateway",
        "category": "online_payments",
        "tagline": "100+ payment modes. One integration. Industry-best success rates.",
        "description": (
            "Full-stack online payment gateway supporting UPI, cards, net banking, "
            "wallets, EMI, PayLater. 100% digital onboarding. "
            "Developer-friendly APIs and plugins for Shopify, WooCommerce, Magento."
        ),
        "pricing": {
            "setup_fee": "₹0",
            "annual_maintenance": "₹0",
            "upi_mdr": "0%",
            "cards_mdr": "1.5% – 2.5% (volume-based)",
            "netbanking_mdr": "1.5% – 2.0%",
            "enterprise_custom": "Custom pricing for > ₹10L/month volume",
        },
        "features": [
            "100+ payment sources",
            "Intelligent payment routing for highest success rates",
            "Seamless checkout (< 3 clicks)",
            "One-click checkout for returning customers",
            "Subscription/recurring payments (auto-pay)",
            "Split payments and marketplace support",
            "Developer SDKs: Android, iOS, Flutter, React Native",
            "Plugins: Shopify, WooCommerce, Magento, OpenCart",
            "PCI DSS Level 1 compliant",
            "Real-time analytics dashboard",
        ],
        "key_usps": [
            "Zero setup + zero AMC — lowest cost of entry",
            "Industry-best payment success rates via intelligent routing",
            "Fastest onboarding — go live in < 15 minutes",
            "One integration supports online + offline",
        ],
    },

    "merchant_loans": {
        "id": "paytm_loans",
        "name": "Paytm Merchant Loans",
        "category": "lending",
        "tagline": "Instant loans based on your transaction history — no paperwork.",
        "description": (
            "Pre-approved merchant loans from ₹50,000 to ₹25,00,000 based on "
            "Paytm transaction data. Partnered with major banks and NBFCs. "
            "100% digital disbursal, no physical documentation needed."
        ),
        "pricing": {
            "interest_rate": "Starting from 12% p.a.",
            "processing_fee": "1-2% of loan amount",
            "prepayment_penalty": "None (flexible repayment)",
        },
        "features": [
            "Pre-approved offers based on transaction history",
            "Loan amounts: ₹50,000 to ₹25,00,000",
            "Tenure: 3 to 36 months",
            "100% digital — no branch visit, no paperwork",
            "Disbursal in < 24 hours to your bank account",
            "Auto-deduction from Paytm collections (optional)",
            "CIBIL score not the only factor — transaction data matters more",
            "Repeat loans with improved terms for good repayment",
        ],
        "key_usps": [
            "Transaction-data underwriting = higher approval rates vs traditional banks",
            "No collateral required",
            "No paperwork — KYC already done if you're a Paytm merchant",
            "Flexible repayment — deduct from daily collections or EMI",
            "Pre-approved offers → no rejection anxiety",
        ],
    },

    "paytm_postpaid": {
        "id": "paytm_postpaid",
        "name": "Paytm Postpaid (Buy Now, Pay Later)",
        "category": "consumer_finance",
        "tagline": "Let your customers buy now, pay next month — you get paid instantly.",
        "description": (
            "Consumer BNPL that your customers can use at your store. "
            "Merchant gets full payment instantly; customer pays Paytm next month."
        ),
        "pricing": "Zero cost to merchant — Paytm charges the customer",
        "features": [
            "Increases basket size — customers spend 30-40% more",
            "Merchant gets full amount instantly",
            "Customer repays Paytm — zero risk for merchant",
            "Available at both online and offline merchants",
        ],
    },

    "digital_kyc": {
        "id": "paytm_dkyc",
        "name": "Paytm Digital KYC",
        "category": "onboarding",
        "tagline": "Go live in minutes with Aadhaar-based digital verification.",
        "description": (
            "100% digital merchant onboarding using Aadhaar OTP, PAN verification, "
            "and video KYC. No document collection visit needed."
        ),
        "features": [
            "Aadhaar OTP-based verification",
            "PAN verification with Name matching",
            "Video KYC option for full compliance",
            "GSTIN auto-fetch and validation",
            "Bank account verification via penny drop",
            "Complete in < 10 minutes from your phone",
        ],
        "key_usps": [
            "No waiting for a field agent — instant onboarding",
            "Fully RBI-compliant",
            "Works from any smartphone",
            "Skip the paperwork — go digital",
        ],
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# COMPETITOR PROFILES
# ─────────────────────────────────────────────────────────────────────────────

COMPETITORS = {
    "phonepe": {
        "id": "phonepe",
        "name": "PhonePe",
        "parent_company": "Walmart/Flipkart (via PhonePe Pvt Ltd, Singapore HQ)",
        "market_position": "Largest UPI app by consumer volume",
        "merchant_products": {
            "qr": {
                "name": "PhonePe QR",
                "pricing": "Free",
                "features": [
                    "UPI payments via PhonePe and other UPI apps",
                    "Basic transaction dashboard",
                ],
            },
            "soundbox": {
                "name": "PhonePe SmartSpeaker",
                "pricing": "₹99-149/month rental (limited availability)",
                "features": [
                    "Audio payment confirmation",
                    "Limited language support (fewer than Paytm)",
                    "UPI-only — NO card acceptance",
                ],
            },
            "payment_gateway": {
                "name": "PhonePe Payment Gateway",
                "pricing": "2-3% MDR on cards, 0% UPI",
                "features": [
                    "UPI, Cards, Netbanking, Wallets",
                    "Decent checkout experience",
                    "Good for mobile-first businesses",
                ],
            },
            "lending": {
                "name": "PhonePe Lending (via partners)",
                "pricing": "Varies by NBFC partner",
                "features": [
                    "Personal loans via NBFC partnerships",
                    "Limited merchant-specific lending",
                    "Less data-driven underwriting than Paytm",
                ],
            },
        },
        "weaknesses": [
            "SmartSpeaker has limited language support (vs Paytm's 11)",
            "No card/NFC acceptance on their speaker device",
            "Merchant lending is not as data-driven (less transaction data for underwriting)",
            "Payment gateway onboarding slower than Paytm (> 1 day)",
            "Customer support complaints — slow ticket resolution",
            "No equivalent to Paytm's AI Soundbox features",
            "No brand audio ad revenue sharing for merchants",
            "Dynamic QR not as mature as Paytm's enterprise offering",
        ],
        "strengths": [
            "Largest consumer UPI user base — customers already have the app",
            "Strong brand recognition",
            "Good mobile-first checkout experience",
            "Backed by Walmart — deep pockets",
        ],
    },

    "bharatpe": {
        "id": "bharatpe",
        "name": "BharatPe",
        "parent_company": "Resilient Innovations Pvt Ltd",
        "market_position": "Strong in kirana/offline merchant segment",
        "merchant_products": {
            "qr": {
                "name": "BharatPe QR",
                "pricing": "Free (interoperable UPI QR)",
                "features": [
                    "Accepts all UPI apps",
                    "Zero MDR",
                    "Basic merchant dashboard",
                ],
            },
            "soundbox": {
                "name": "BharatPe Speaker",
                "pricing": "₹99-130/month rental",
                "features": [
                    "Audio payment confirmation",
                    "Hindi + English (limited language support)",
                    "UPI-only, no card acceptance",
                ],
            },
            "pos": {
                "name": "BharatSwipe (POS)",
                "pricing": "₹500 deposit, 1.5-2% MDR on cards",
                "features": [
                    "Card acceptance (swipe + chip)",
                    "UPI + card in one device",
                ],
            },
            "lending": {
                "name": "BharatPe Loans",
                "pricing": "Starting from 1.5%/month",
                "features": [
                    "Small merchant loans up to ₹10 lakhs",
                    "Quick disbursal",
                    "Based on QR transaction volume",
                ],
            },
        },
        "weaknesses": [
            "Corporate governance issues — eroded merchant trust (Ashneer Grover controversy)",
            "Settlement delays / account freezes — frequent merchant complaints",
            "Customer support is notoriously poor",
            "Speaker has only 2-language support vs Paytm's 11",
            "No AI features, no business analytics on their speaker",
            "Lending limited to ₹10L (Paytm offers up to ₹25L)",
            "No payment gateway for online businesses",
            "POS device (BharatSwipe) has reliability issues",
            "No digital KYC onboarding — requires field agent visit",
            "Recent leadership instability impacts service continuity",
        ],
        "strengths": [
            "Strong kirana store penetration in Tier-2/3 cities",
            "Interoperable QR was a pioneer move",
            "12% club (peer-to-peer lending) attracts merchants who want returns",
        ],
    },

    "razorpay": {
        "id": "razorpay",
        "name": "Razorpay",
        "parent_company": "Razorpay Software Pvt Ltd",
        "market_position": "Leading online payment gateway for startups/SMBs",
        "merchant_products": {
            "payment_gateway": {
                "name": "Razorpay Payment Gateway",
                "pricing": "2% standard, custom for enterprise",
                "features": [
                    "100+ payment methods",
                    "Excellent API documentation",
                    "Subscription billing (auto-pay)",
                    "Marketplace/split payments",
                    "Shopify, WooCommerce plugins",
                    "Smart collect (virtual accounts)",
                ],
            },
            "pos": {
                "name": "Razorpay POS",
                "pricing": "Device cost + 1.5-2% MDR",
                "features": [
                    "Card + UPI in-store payments",
                    "Integrated billing",
                ],
            },
            "payroll": {
                "name": "RazorpayX Payroll",
                "pricing": "From ₹100/employee/month",
                "features": [
                    "Automated payroll and compliance",
                    "TDS/PF/ESI automation",
                ],
            },
            "lending": {
                "name": "Razorpay Capital",
                "pricing": "Custom (NBFC partnerships)",
                "features": [
                    "Working capital loans",
                    "Based on gateway transaction volume",
                    "Instant collection via gateway deductions",
                ],
            },
        },
        "weaknesses": [
            "Primarily online-focused — weak offline/kirana merchant presence",
            "No Soundbox/speaker device — cannot serve street vendors",
            "Complex pricing — hidden fees for instant settlement (1-2%)",
            "Higher MDR than Paytm for cards (2% vs 1.5%)",
            "Onboarding requires tech knowledge — not suitable for small merchants",
            "No UPI QR for offline merchants",
            "Customer support prioritizes enterprise clients — SMBs wait longer",
            "No consumer-facing app — depends on other UPI apps for payments",
        ],
        "strengths": [
            "Best-in-class API and developer experience",
            "Excellent for e-commerce, SaaS, and subscription businesses",
            "RazorpayX banking suite (current accounts, payroll)",
            "Strong brand with tech startups",
        ],
    },

    "pine_labs": {
        "id": "pine_labs",
        "name": "Pine Labs",
        "parent_company": "Pine Labs Pvt Ltd (backed by Mastercard, Sequoia)",
        "market_position": "Enterprise POS and omnichannel payment leader",
        "merchant_products": {
            "pos": {
                "name": "Pine Labs POS Terminal",
                "pricing": "Device lease/purchase + 1.5-2.5% MDR",
                "features": [
                    "Android Smart POS",
                    "Card (swipe/chip/NFC) + UPI",
                    "EMI at POS (consumer finance)",
                    "Multi-acquirer capability",
                    "Integrated billing and inventory",
                ],
            },
            "payment_gateway": {
                "name": "Plural by Pine Labs (Online Gateway)",
                "pricing": "Custom enterprise pricing",
                "features": [
                    "Online payments",
                    "Omnichannel: link offline POS data with online",
                    "Checkout optimization",
                ],
            },
            "lending": {
                "name": "Pine Labs EMI (Consumer finance at POS)",
                "pricing": "Varies by brand/bank partnership",
                "features": [
                    "Brand EMIs and no-cost EMIs at point of sale",
                    "Consumer lending, not merchant lending",
                ],
            },
        },
        "weaknesses": [
            "Expensive hardware — POS devices cost ₹5,000-15,000+",
            "Enterprise-focused — not suitable for small merchants or street vendors",
            "No consumer app — zero consumer ecosystem",
            "High MDR on card transactions",
            "No Soundbox/speaker — large POS only",
            "No merchant lending (only consumer EMI at POS)",
            "Slow onboarding — requires hardware deployment team visit",
            "Monthly rental + MDR makes it expensive for small volumes",
            "Limited UPI support compared to Paytm/PhonePe",
        ],
        "strengths": [
            "Best-in-class enterprise POS hardware",
            "Strong with large retailers (Big Bazaar, Reliance, etc.)",
            "EMI at POS drives up ticket sizes",
            "Omnichannel capability (online + offline unified)",
            "Backed by Mastercard — global credibility",
        ],
    },

    "mswipe": {
        "id": "mswipe",
        "name": "Mswipe",
        "parent_company": "Mswipe Technologies Pvt Ltd",
        "market_position": "Niche POS provider for SMB retailers",
        "merchant_products": {
            "pos": {
                "name": "Mswipe POS Terminal",
                "pricing": "₹3,000-8,000 + 1.5-2% MDR",
                "features": [
                    "Android-based Smart POS",
                    "Card + UPI acceptance",
                    "Billing and inventory management",
                    "EMI options",
                ],
            },
        },
        "weaknesses": [
            "Very limited market share",
            "No consumer app or ecosystem",
            "No Soundbox/speaker product",
            "No merchant lending",
            "Customer support limited to business hours",
            "Hardware reliability complaints",
            "No payment gateway for online",
        ],
        "strengths": [
            "Affordable Android POS for small retailers",
            "Good EMI integration with banks",
        ],
    },

    "googlepay": {
        "id": "googlepay",
        "name": "Google Pay (for Merchants)",
        "parent_company": "Google (Alphabet Inc)",
        "market_position": "Strong consumer UPI app, limited merchant services",
        "merchant_products": {
            "qr": {
                "name": "Google Pay Business QR",
                "pricing": "Free",
                "features": [
                    "UPI payments",
                    "Spot codes for nearby discovery",
                    "Google Maps integration",
                ],
            },
        },
        "weaknesses": [
            "No Soundbox or payment confirmation device",
            "No POS terminal",
            "No payment gateway",
            "No merchant lending or financial services",
            "No dedicated merchant support team in India",
            "Cannot accept card payments",
            "Limited to UPI only",
            "No offline payments capability without internet",
            "Cannot scale with business — purely basic QR",
        ],
        "strengths": [
            "Massive consumer user base",
            "Strong brand (Google)",
            "Google Maps/Search integration for merchant discovery",
            "Free and simple to set up",
        ],
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# REBUTTAL SCRIPTS – Keyed by (competitor, objection_type)
# ─────────────────────────────────────────────────────────────────────────────

REBUTTAL_SCRIPTS = {
    # ── PhonePe rebuttals ────────────────────────────────────────────────
    ("phonepe", "already_using"): {
        "objection": "I'm already using PhonePe for payments.",
        "rebuttal": (
            "That's great — PhonePe is excellent for consumers! "
            "But here's the thing: as a merchant, you need more than just UPI collection. "
            "Our Soundbox confirms payments in 11 languages with audio AND visual display. "
            "PhonePe's SmartSpeaker only supports a few languages and can't accept cards. "
            "Plus, our AI Soundbox gives you free business analytics — daily sales summaries, "
            "peak hour insights — that PhonePe simply doesn't offer. "
            "And the best part? Your customers can still pay you with PhonePe through our QR!"
        ),
        "key_differentiators": [
            "11 languages vs limited",
            "Card/NFC acceptance",
            "AI business analytics",
            "Brand audio ad revenue",
            "Accepts PhonePe payments too (interoperable)",
        ],
    },
    ("phonepe", "pricing"): {
        "objection": "PhonePe doesn't charge me anything, why should I pay for Paytm?",
        "rebuttal": (
            "Great question! PhonePe QR is free, and so is ours. Zero cost for UPI. "
            "The Soundbox is just ₹99/month — less than ₹4 per day. "
            "For that, you get instant audio confirmation so you never miss a payment, "
            "you don't have to keep checking your phone. Think about it — how many times "
            "has a customer said 'payment done' but it didn't come? The Soundbox eliminates "
            "that completely. It pays for itself by preventing even one missed payment a month."
        ),
        "key_differentiators": [
            "₹99/month = ₹3.3/day",
            "Prevents missed/fake payments",
            "No phone checking needed",
            "Time savings = money",
        ],
    },
    ("phonepe", "approached_by_them"): {
        "objection": "PhonePe sales team just visited and offered me their speaker.",
        "rebuttal": (
            "I'm glad they're interested in your business — that shows you're a valuable merchant! "
            "Before you decide, let me share what makes our Soundbox different. "
            "PhonePe's speaker only confirms UPI payments and supports fewer languages. "
            "Ours confirms UPI from ANY app PLUS cards (tap-to-pay and chip insert). "
            "That means you can accept credit card payments too — increasing your ticket size. "
            "Our AI Soundbox even tells you your daily sales summary and peak hours. "
            "And you actually earn money from brand audio ads on our device. "
            "Would you like a quick demo to see the difference?"
        ),
        "key_differentiators": [
            "Card acceptance = higher ticket size",
            "AI analytics included",
            "Brand ad revenue",
            "More language support",
        ],
    },

    # ── BharatPe rebuttals ───────────────────────────────────────────────
    ("bharatpe", "already_using"): {
        "objection": "I have a BharatPe QR / speaker already.",
        "rebuttal": (
            "BharatPe was one of the first with interoperable QR — solid choice at the time. "
            "But many merchants have been having issues with BharatPe lately — settlement delays, "
            "account freezes, and very poor customer support. If you've experienced any of those, "
            "you'll love the difference. Paytm has a dedicated merchant helpdesk (0120-4440440), "
            "we settle instantly (T+0 for eligible merchants), and our Soundbox speaks 11 languages "
            "while BharatPe's only does 2. Plus, we offer merchant loans up to ₹25 lakhs — "
            "BharatPe caps at ₹10 lakhs. Want me to set up a side-by-side demo?"
        ),
        "key_differentiators": [
            "Better customer support vs BharatPe's issues",
            "Instant settlement (T+0)",
            "11 vs 2 languages",
            "Loans up to ₹25L vs 10L",
            "No governance controversy",
        ],
    },
    ("bharatpe", "trust_issues"): {
        "objection": "I've heard bad things about payment companies freezing accounts.",
        "rebuttal": (
            "I completely understand your concern — trust is everything in business. "
            "That's actually one of the key reasons merchants are switching to Paytm. "
            "We've been in the market for over a decade, regulated by RBI, and we've never had "
            "the governance issues some competitors have faced. Your settlements are guaranteed — "
            "we even offer same-day settlement. And if you ever have an issue, "
            "our dedicated merchant helpdesk is just a call away at 0120-4440440. "
            "No ticket runaround, no closed-without-resolution complaints."
        ),
        "key_differentiators": [
            "10+ years in market",
            "RBI regulated",
            "Guaranteed settlements",
            "Dedicated helpdesk",
        ],
    },

    # ── Razorpay rebuttals ───────────────────────────────────────────────
    ("razorpay", "already_using"): {
        "objection": "I use Razorpay for my online payments.",
        "rebuttal": (
            "Razorpay is excellent for online — great APIs, great developer experience. "
            "But if you also have an offline presence, you need a unified solution. "
            "Paytm gives you online gateway PLUS Soundbox for in-store — all in one merchant account. "
            "One dashboard for online + offline sales. One settlement cycle. "
            "And our payment gateway has ZERO setup fee and ZERO AMC — "
            "Razorpay charges for instant settlement (1-2%). "
            "We're also better for UPI with zero MDR. "
            "Would you like to see how a unified online-offline setup would work for you?"
        ),
        "key_differentiators": [
            "Unified online + offline",
            "Zero setup + zero AMC",
            "Free instant settlement (vs Razorpay's 1-2% charge)",
            "Soundbox for offline — Razorpay has nothing",
            "Single dashboard",
        ],
    },
    ("razorpay", "pricing"): {
        "objection": "Razorpay's pricing seems more transparent.",
        "rebuttal": (
            "Razorpay's standard rate is 2% — ours is competitive at 1.5-2.5% with "
            "volume-based discounts. But here's what they don't highlight: "
            "instant settlement costs 1-2% extra on Razorpay. We offer it free for eligible merchants. "
            "Also, UPI via Paytm gateway is zero MDR — Razorpay charges platform fees on some plans. "
            "When you factor in total cost of ownership including settlement speed, "
            "Paytm is typically cheaper for most merchant profiles."
        ),
        "key_differentiators": [
            "Competitive MDR with volume discounts",
            "Free instant settlement",
            "Zero UPI MDR",
            "Total cost typically lower",
        ],
    },

    # ── Pine Labs rebuttals ──────────────────────────────────────────────
    ("pine_labs", "already_using"): {
        "objection": "I already have a Pine Labs POS machine.",
        "rebuttal": (
            "Pine Labs makes great enterprise POS terminals — no question. "
            "But those devices are expensive (₹5,000-15,000+ upfront) and come with higher MDR. "
            "For the vast majority of your daily transactions (which are UPI-based), "
            "you're paying for a Ferrari to drive to the neighborhood kirana. "
            "Our Soundbox at ₹99/month handles UPI instantly, and our NFC Soundbox even accepts "
            "card taps at a fraction of the cost. You could keep Pine Labs for high-value card "
            "transactions and use Paytm for everything else — saving significantly on monthly costs."
        ),
        "key_differentiators": [
            "₹99/month vs ₹5,000-15,000 upfront",
            "Lower MDR on UPI (0%)",
            "NFC Soundbox as affordable card alternative",
            "Can complement Pine Labs for UPI",
        ],
    },

    # ── Google Pay rebuttals ─────────────────────────────────────────────
    ("googlepay", "already_using"): {
        "objection": "My customers already pay me through Google Pay.",
        "rebuttal": (
            "Perfect — and they can keep doing that! Paytm's QR and Soundbox both accept "
            "Google Pay payments because they're interoperable UPI. The difference is, "
            "with Google Pay alone, you have to keep checking your phone for confirmation. "
            "With our Soundbox, you get instant audio + visual confirmation — no phone needed. "
            "Plus, Google Pay doesn't offer merchant loans, analytics, or any business tools. "
            "Think of Paytm as the business upgrade — your customers still use whatever UPI app they want."
        ),
        "key_differentiators": [
            "Accepts Google Pay (and all UPI apps)",
            "Audio confirmation — no phone checking",
            "Merchant loans and business tools",
            "Analytics and insights",
        ],
    },

    # ── Generic objection rebuttals ──────────────────────────────────────
    ("generic", "too_expensive"): {
        "objection": "It's too expensive / I can't afford the monthly charge.",
        "rebuttal": (
            "I totally understand — every rupee matters. Let me put it this way: "
            "₹99 per month is about ₹3.3 per day. If the Soundbox prevents even ONE "
            "fake 'payment done' claim per month, it's already paid for itself. "
            "Most merchants tell us they were losing ₹500-2,000 per month from missed "
            "or disputed payments before getting the Soundbox. "
            "And if you sign up today, I can check if there are any special offers for your area."
        ),
    },
    ("generic", "dont_need_it"): {
        "objection": "I don't need any of this, my business runs fine.",
        "rebuttal": (
            "That's wonderful to hear — a well-running business is something to be proud of! "
            "I'm not suggesting anything is wrong. But imagine if you could also see which hours "
            "bring the most sales, get a daily summary of your collections, and even qualify "
            "for a business loan when you need it — all automatically. "
            "Think of it as giving your business superpowers, not fixing a problem. "
            "May I ask — do you accept card payments currently? Many of your customers "
            "might prefer tap-to-pay, especially the younger generation."
        ),
    },
    ("generic", "will_think_about_it"): {
        "objection": "Let me think about it / I'll decide later.",
        "rebuttal": (
            "Absolutely — take your time. But I'd love to share one thing before we go: "
            "we're currently running a special promotion in your area, and spots are limited. "
            "How about I schedule a quick 10-minute demo with our local representative? "
            "You can see the Soundbox in action at your own shop, ask all your questions, "
            "and there's absolutely no obligation. If it's not for you, no worries at all. "
            "Would tomorrow or the day after work better for a quick visit?"
        ),
    },
    ("generic", "competitor_cheaper"): {
        "objection": "Another company is offering me a better deal.",
        "rebuttal": (
            "I appreciate you being transparent — that helps me help you better! "
            "May I know which company? I'd love to do a quick comparison so you can make "
            "an informed decision. Often, the headline price looks similar, but the total "
            "value is very different. For example, we include AI business analytics, "
            "11-language support, card acceptance, and brand ad revenue in our Soundbox — "
            "things that others charge separately for or don't offer at all. "
            "Let's do a quick feature comparison together?"
        ),
    },
    ("generic", "bad_experience"): {
        "objection": "I had a bad experience with Paytm before.",
        "rebuttal": (
            "I'm really sorry to hear that — and I appreciate you telling me. "
            "Can you share what happened? I want to make sure it gets addressed. "
            "We've made significant improvements in the last year — our new AI Soundbox, "
            "faster settlements, and a dedicated merchant helpdesk at 0120-4440440. "
            "Many merchants who previously had issues have come back and seen a "
            "completely different experience. Would you be open to giving us another chance "
            "with a risk-free trial?"
        ),
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# HEAD-TO-HEAD COMPARISON MATRICES
# ─────────────────────────────────────────────────────────────────────────────

COMPARISON_MATRIX = {
    "soundbox_comparison": {
        "title": "Soundbox / Speaker Device Comparison",
        "dimensions": {
            "device": {
                "paytm": "Soundbox (Standard / AI / NFC / Solar)",
                "phonepe": "SmartSpeaker",
                "bharatpe": "BharatPe Speaker",
                "razorpay": "❌ None",
                "pine_labs": "❌ None (POS only)",
                "googlepay": "❌ None",
            },
            "languages": {
                "paytm": "11 Indian languages",
                "phonepe": "4-5 languages",
                "bharatpe": "2 languages (Hindi + English)",
                "razorpay": "N/A",
                "pine_labs": "N/A",
                "googlepay": "N/A",
            },
            "card_acceptance": {
                "paytm": "✅ NFC + Chip (NFC Soundbox variant)",
                "phonepe": "❌ UPI only",
                "bharatpe": "❌ UPI only (speaker) / ✅ BharatSwipe (separate POS)",
                "razorpay": "N/A",
                "pine_labs": "✅ (but ₹5,000+ POS device)",
                "googlepay": "N/A",
            },
            "ai_analytics": {
                "paytm": "✅ AI Soundbox — daily summaries, peak hours, voice assistant",
                "phonepe": "❌",
                "bharatpe": "❌",
                "razorpay": "N/A",
                "pine_labs": "Basic POS reports only",
                "googlepay": "N/A",
            },
            "monthly_cost": {
                "paytm": "₹99-149/month (or ₹999 lifetime)",
                "phonepe": "₹99-149/month",
                "bharatpe": "₹99-130/month",
                "razorpay": "N/A",
                "pine_labs": "₹500-1,000/month (POS rental)",
                "googlepay": "N/A",
            },
            "brand_ad_revenue": {
                "paytm": "✅ Earn from brand audio ads",
                "phonepe": "❌",
                "bharatpe": "❌",
                "razorpay": "N/A",
                "pine_labs": "❌",
                "googlepay": "N/A",
            },
            "4g_connectivity": {
                "paytm": "✅ Built-in 4G SIM",
                "phonepe": "✅ Some models",
                "bharatpe": "Bluetooth to phone",
                "razorpay": "N/A",
                "pine_labs": "✅ (POS has SIM)",
                "googlepay": "N/A",
            },
        },
    },

    "lending_comparison": {
        "title": "Merchant Lending Comparison",
        "dimensions": {
            "max_loan_amount": {
                "paytm": "₹25,00,000",
                "phonepe": "Varies (NBFC dependent)",
                "bharatpe": "₹10,00,000",
                "razorpay": "Custom (working capital only)",
                "pine_labs": "❌ No merchant lending",
                "googlepay": "❌ No lending",
            },
            "underwriting_method": {
                "paytm": "Transaction data + CIBIL (data-driven, higher approval)",
                "phonepe": "NBFC partner criteria (less data-driven)",
                "bharatpe": "QR transaction volume",
                "razorpay": "Gateway transaction volume",
                "pine_labs": "N/A",
                "googlepay": "N/A",
            },
            "disbursal_speed": {
                "paytm": "< 24 hours",
                "phonepe": "2-5 days (NBFC dependent)",
                "bharatpe": "1-3 days",
                "razorpay": "1-3 days",
                "pine_labs": "N/A",
                "googlepay": "N/A",
            },
            "digital_process": {
                "paytm": "✅ 100% digital — no paperwork",
                "phonepe": "Partial (may need documents)",
                "bharatpe": "Partial",
                "razorpay": "✅ Digital",
                "pine_labs": "N/A",
                "googlepay": "N/A",
            },
        },
    },

    "payment_gateway_comparison": {
        "title": "Online Payment Gateway Comparison",
        "dimensions": {
            "setup_fee": {
                "paytm": "₹0",
                "phonepe": "₹0",
                "bharatpe": "N/A",
                "razorpay": "₹0",
                "pine_labs": "Custom (enterprise)",
            },
            "upi_mdr": {
                "paytm": "0%",
                "phonepe": "0%",
                "bharatpe": "N/A",
                "razorpay": "0% (but platform fee on some plans)",
                "pine_labs": "0% (via Plural)",
            },
            "card_mdr": {
                "paytm": "1.5-2.5%",
                "phonepe": "2-3%",
                "bharatpe": "N/A",
                "razorpay": "2% (standard)",
                "pine_labs": "2-2.5%",
            },
            "instant_settlement": {
                "paytm": "✅ Free for eligible merchants",
                "phonepe": "Available (charges apply)",
                "bharatpe": "N/A",
                "razorpay": "1-2% extra charge",
                "pine_labs": "Custom terms",
            },
            "go_live_time": {
                "paytm": "< 15 minutes (100% digital)",
                "phonepe": "1-2 days",
                "bharatpe": "N/A",
                "razorpay": "Same day (with documents)",
                "pine_labs": "3-7 days (enterprise process)",
            },
        },
    },
}
