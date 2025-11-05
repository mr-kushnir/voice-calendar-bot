"""Configuration management using Pydantic Settings"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Config(BaseSettings):
    """Application configuration loaded from environment variables"""

    # Telegram Bot
    telegram_bot_token: str = Field(..., description="Telegram Bot Token")
    log_level: str = Field(default="INFO", description="Logging level")

    # OpenAI
    openai_api_key: str = Field(..., description="OpenAI API Key")

    # ElevenLabs
    elevenlabs_api_key: str = Field(..., description="ElevenLabs API Key")
    elevenlabs_voice_id: Optional[str] = Field(default="21m00Tcm4TlvDq8ikWAM", description="ElevenLabs Voice ID")

    # Yandex Calendar
    yandex_calendar_login: str = Field(..., description="Yandex Calendar Login")
    yandex_calendar_password: str = Field(..., description="Yandex Calendar Password")
    yandex_calendar_url: str = Field(default="https://caldav.yandex.ru", description="Yandex CalDAV URL")

    # Google Calendar
    google_calendar_credentials_path: str = Field(default="credentials.json", description="Google Calendar Credentials Path")
    google_calendar_token_path: str = Field(default="token.json", description="Google Calendar Token Path")
    google_calendar_ics_url: Optional[str] = Field(default=None, description="Google Calendar ICS URL")

    # Yandex Tracker
    yandex_tracker_token: Optional[str] = Field(default=None, description="Yandex Tracker OAuth Token")
    yandex_tracker_org_id: Optional[str] = Field(default=None, description="Yandex Tracker Organization ID")
    yandex_tracker_queue: str = Field(default="VOICEBOT", description="Yandex Tracker Queue")

    # Test Agent
    test_agent_poll_interval: int = Field(default=60, description="Test Agent Poll Interval (seconds)")
    test_agent_coverage_threshold: int = Field(default=80, description="Test Agent Coverage Threshold (%)")

    class Config:
        """Pydantic configuration"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        frozen = True  # Make config immutable
        extra = "ignore"  # Ignore extra fields from .env


# Singleton instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get configuration singleton"""
    global _config
    if _config is None:
        _config = Config()
    return _config
