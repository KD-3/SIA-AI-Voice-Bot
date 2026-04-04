"""OpenAI function-calling tool definitions for appointment setting (Feature #4)."""

APPOINTMENT_TOOLS = [
    # ── Device delivery + activation (Feature #4 extension) ──────────────────
    {
        "type": "function",
        "function": {
            "name": "confirm_device_delivery",
            "description": (
                "Call this when the merchant has agreed to take the product AND has "
                "confirmed their KYC documents are ready or submitted. "
                "This triggers the delivery process and sends an SMS with the expected "
                "delivery date (3 business days from today, Mon–Sat). "
                "After calling, ALWAYS ask: 'Would you like one of our field engineers "
                "to visit and help you set up the device when it arrives?'"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "product_name": {
                        "type": "string",
                        "description": (
                            "Name of the Paytm product/device being delivered, "
                            "e.g. 'Paytm Soundbox', 'Paytm POS Terminal', 'Paytm EDC Machine'."
                        )
                    },
                    "area": {
                        "type": "string",
                        "description": "Merchant's area of operation (used for delivery routing)."
                    }
                },
                "required": ["product_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_activation_slots",
            "description": (
                "Check available activation appointment slots for field engineers "
                "in the merchant's zone. Call this ONLY after the merchant says yes "
                "to needing help with device setup/activation. "
                "Field engineers operate in different zones than sales reps "
                "(e.g. 'Central Bengaluru', 'East Mumbai')."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "zone": {
                        "type": "string",
                        "description": (
                            "Merchant's zone for field engineer dispatch, "
                            "e.g. 'Central Bengaluru', 'East Mumbai', 'West Delhi'. "
                            "Infer from the merchant's area or ask if unsure."
                        )
                    }
                },
                "required": ["zone"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "book_activation_appointment",
            "description": (
                "Book the device activation appointment with a field engineer. "
                "Call ONLY after the merchant has explicitly confirmed a specific slot "
                "from the options presented by check_activation_slots."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "slot_id": {
                        "type": "string",
                        "description": "Slot ID from the check_activation_slots result."
                    },
                    "product_name": {
                        "type": "string",
                        "description": "Name of the product being activated."
                    }
                },
                "required": ["slot_id", "product_name"]
            }
        }
    },
    # ── Sales rep appointments (demo / KYC doc collection) ────────────────────
    {
        "type": "function",
        "function": {
            "name": "check_appointment_slots",
            "description": (
                "Check available appointment slots for sales reps in the merchant's area. "
                "Call this as soon as the merchant agrees to a product demo or has previously "
                "requested document collection. Extract the area from the conversation context."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "area": {
                        "type": "string",
                        "description": (
                            "Merchant's area of operation, e.g. 'South Bengaluru', "
                            "'North Mumbai', 'South Delhi'. Infer from conversation."
                        )
                    },
                    "appointment_type": {
                        "type": "string",
                        "enum": ["demo", "document_collection", "demo_and_document_collection"],
                        "description": (
                            "Type of appointment: 'demo' for product demo only, "
                            "'document_collection' for KYC doc pickup only, "
                            "'demo_and_document_collection' if merchant wants both."
                        )
                    }
                },
                "required": ["area", "appointment_type"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "book_appointment",
            "description": (
                "Book the appointment slot that the merchant has explicitly confirmed. "
                "Only call this AFTER the merchant has verbally agreed to a specific slot "
                "from the options you presented."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "slot_id": {
                        "type": "string",
                        "description": "The slot_id from the check_appointment_slots result."
                    },
                    "appointment_type": {
                        "type": "string",
                        "enum": ["demo", "document_collection", "demo_and_document_collection"],
                        "description": "Type of appointment being booked."
                    },
                    "needs_document_collection": {
                        "type": "boolean",
                        "description": (
                            "True if document collection should also happen at this visit "
                            "(even if primary type is demo). Set based on full conversation context."
                        )
                    }
                },
                "required": ["slot_id", "appointment_type", "needs_document_collection"]
            }
        }
    }
]
