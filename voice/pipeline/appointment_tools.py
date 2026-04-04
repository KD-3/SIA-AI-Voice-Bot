"""OpenAI function-calling tool definitions for appointment setting (Feature #4)."""

APPOINTMENT_TOOLS = [
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
