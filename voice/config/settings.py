"""Configuration settings for the voice agent."""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_env: str = "development"
    app_port: int = 8000
    log_level: str = "INFO"

    # Twilio
    twilio_account_sid: str
    twilio_auth_token: str
    twilio_phone_number: str

    # OpenAI
    openai_api_key: str

    # Deepgram
    deepgram_api_key: str

    # ElevenLabs
    elevenlabs_api_key: str
    elevenlabs_voice_id: str = "21m00Tcm4TlvDq8ikWAM"  # Rachel voice

    # Database
    database_url: str
    redis_url: str = "redis://localhost:6379/0"

    # Pinecone
    pinecone_api_key: Optional[str] = None
    pinecone_environment: str = "us-east-1"
    pinecone_index_name: str = "voice-bot-knowledge"

    # CRM (Optional)
    hubspot_api_key: Optional[str] = None
    salesforce_client_id: Optional[str] = None
    salesforce_client_secret: Optional[str] = None

    # Google Calendar (Optional)
    google_calendar_credentials_path: Optional[str] = None

    # SendGrid (Optional)
    sendgrid_api_key: Optional[str] = None
    sendgrid_from_email: Optional[str] = None

    # Security
    secret_key: str = "dev-secret-key-change-in-production"
    api_key: str = "dev-api-key-change-in-production"

    # Feature Flags
    enable_call_recording: bool = True
    enable_analytics: bool = True
    enable_crm_sync: bool = False

    # Conversation Settings
    max_conversation_duration_seconds: int = 600  # 10 minutes
    session_ttl_seconds: int = 86400  # 24 hours

    # AI Settings
    stt_model: str = "nova-2"
    stt_language: str = "en-US"
    llm_model: str = "gpt-4o-realtime-preview"
    tts_model: str = "eleven_turbo_v2_5"

    # Latency Targets (milliseconds)
    target_stt_latency_ms: int = 50
    target_llm_latency_ms: int = 150
    target_tts_latency_ms: int = 50
    target_total_latency_ms: int = 250

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
