"""Configuration settings for the voice agent."""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings:
    """Application settings loaded from environment variables."""

    # Application
    app_env: str = os.getenv("APP_ENV", "development")
    app_port: int = int(os.getenv("APP_PORT", "8000"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    # Twilio
    twilio_account_sid: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    twilio_auth_token: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    twilio_phone_number: str = os.getenv("TWILIO_PHONE_NUMBER", "")

    # OpenAI
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")

    # Deepgram
    deepgram_api_key: str = os.getenv("DEEPGRAM_API_KEY", "")

    # Sarvam AI (Indian TTS)
    sarvam_api_key: str = os.getenv("SARVAM_API_KEY", "")
    sarvam_speaker: str = os.getenv("SARVAM_SPEAKER", "priya")  # priya (female) or arkesh (male)

    # Database
    database_url: str = os.getenv("DATABASE_URL", "")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Pinecone
    pinecone_api_key: str = os.getenv("PINECONE_API_KEY", "")
    pinecone_environment: str = os.getenv("PINECONE_ENVIRONMENT", "us-east-1")
    pinecone_index_name: str = os.getenv("PINECONE_INDEX_NAME", "voice-bot-knowledge")

    # CRM (Optional)
    hubspot_api_key: str = os.getenv("HUBSPOT_API_KEY", "")
    salesforce_client_id: str = os.getenv("SALESFORCE_CLIENT_ID", "")
    salesforce_client_secret: str = os.getenv("SALESFORCE_CLIENT_SECRET", "")

    # Firebase / Firestore (Feature #4 – Appointment Setting)
    firebase_service_account_path: str = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH", "")
    firebase_project_id: str = os.getenv("FIREBASE_PROJECT_ID", "paytm-hackathon-1")

    # Google Calendar (Feature #4 – Appointment Setting)
    google_calendar_credentials_path: str = os.getenv("GOOGLE_CALENDAR_CREDENTIALS_PATH", "")
    google_calendar_service_account_path: str = os.getenv("GOOGLE_CALENDAR_SERVICE_ACCOUNT_PATH", "")
    google_calendar_delegate_email: str = os.getenv("GOOGLE_CALENDAR_DELEGATE_EMAIL", "")

    # SendGrid (Optional)
    sendgrid_api_key: str = os.getenv("SENDGRID_API_KEY", "")
    sendgrid_from_email: str = os.getenv("SENDGRID_FROM_EMAIL", "")

    # Security
    secret_key: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    api_key: str = os.getenv("API_KEY", "dev-api-key-change-in-production")

    # Feature Flags
    enable_call_recording: bool = os.getenv("ENABLE_CALL_RECORDING", "true").lower() == "true"
    enable_analytics: bool = os.getenv("ENABLE_ANALYTICS", "true").lower() == "true"
    enable_crm_sync: bool = os.getenv("ENABLE_CRM_SYNC", "false").lower() == "true"

    # Conversation Settings
    max_conversation_duration_seconds: int = int(os.getenv("MAX_CONVERSATION_DURATION_SECONDS", "600"))  # 10 minutes
    session_ttl_seconds: int = int(os.getenv("SESSION_TTL_SECONDS", "86400"))  # 24 hours

    # AI Settings
    stt_model: str = os.getenv("STT_MODEL", "nova-2")
    stt_language: str = os.getenv("STT_LANGUAGE", "en-US")
    llm_model: str = os.getenv("LLM_MODEL", "gpt-4o-realtime-preview")
    tts_model: str = os.getenv("TTS_MODEL", "bulbul:v3")

    # Latency Targets (milliseconds)
    target_stt_latency_ms: int = int(os.getenv("TARGET_STT_LATENCY_MS", "50"))
    target_llm_latency_ms: int = int(os.getenv("TARGET_LLM_LATENCY_MS", "150"))
    target_tts_latency_ms: int = int(os.getenv("TARGET_TTS_LATENCY_MS", "50"))
    target_total_latency_ms: int = int(os.getenv("TARGET_TOTAL_LATENCY_MS", "250"))


# Global settings instance
settings = Settings()
