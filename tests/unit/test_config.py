"""Unit tests for configuration management"""
import pytest
import os
from unittest.mock import patch
from src.config import Config


def test_config_loads_from_env():
    """Test configuration loads from environment variables"""
    with patch.dict(os.environ, {
        'TELEGRAM_BOT_TOKEN': 'test_bot_token',
        'OPENAI_API_KEY': 'test_openai_key',
        'ELEVENLABS_API_KEY': 'test_elevenlabs_key',
        'YANDEX_CALENDAR_LOGIN': 'test@example.com',
        'YANDEX_CALENDAR_PASSWORD': 'test_password',
        'YANDEX_CALENDAR_URL': 'https://caldav.yandex.ru',
        'YANDEX_TRACKER_TOKEN': 'test_tracker_token',
        'YANDEX_TRACKER_ORG_ID': 'test_org_id',
        'YANDEX_TRACKER_QUEUE': 'EXTEST'
    }):
        config = Config()

        assert config.telegram_bot_token == 'test_bot_token'
        assert config.openai_api_key == 'test_openai_key'
        assert config.elevenlabs_api_key == 'test_elevenlabs_key'
        assert config.yandex_calendar_login == 'test@example.com'
        assert config.yandex_calendar_password == 'test_password'


def test_config_validation():
    """Test configuration validation for required fields"""
    # Test that missing required field raises validation error
    with patch.dict(os.environ, {
        'OPENAI_API_KEY': 'test_openai_key',
        'ELEVENLABS_API_KEY': 'test_elevenlabs_key',
        'YANDEX_CALENDAR_LOGIN': 'test@example.com',
        'YANDEX_CALENDAR_PASSWORD': 'test_password'
        # Missing TELEGRAM_BOT_TOKEN
    }, clear=True):
        with patch('src.config.Config.Config.env_file', None):  # Prevent reading .env
            with pytest.raises(Exception):
                Config(_env_file=None)  # Explicitly prevent .env reading


def test_config_default_values():
    """Test configuration default values"""
    with patch.dict(os.environ, {
        'TELEGRAM_BOT_TOKEN': 'test_bot_token',
        'OPENAI_API_KEY': 'test_openai_key',
        'ELEVENLABS_API_KEY': 'test_elevenlabs_key',
        'YANDEX_CALENDAR_LOGIN': 'test@example.com',
        'YANDEX_CALENDAR_PASSWORD': 'test_password'
    }):
        config = Config()

        # Check defaults
        assert config.log_level == 'INFO'
        assert config.yandex_calendar_url == 'https://caldav.yandex.ru'
        assert config.test_agent_poll_interval == 60
        assert config.test_agent_coverage_threshold == 80


def test_config_optional_fields():
    """Test configuration with optional fields"""
    with patch.dict(os.environ, {
        'TELEGRAM_BOT_TOKEN': 'test_bot_token',
        'OPENAI_API_KEY': 'test_openai_key',
        'ELEVENLABS_API_KEY': 'test_elevenlabs_key',
        'ELEVENLABS_VOICE_ID': 'custom_voice',
        'YANDEX_CALENDAR_LOGIN': 'test@example.com',
        'YANDEX_CALENDAR_PASSWORD': 'test_password',
        'GOOGLE_CALENDAR_CREDENTIALS_PATH': 'custom_credentials.json'
    }):
        config = Config()

        assert config.elevenlabs_voice_id == 'custom_voice'
        assert config.google_calendar_credentials_path == 'custom_credentials.json'


def test_config_immutability():
    """Test that config is immutable after creation"""
    with patch.dict(os.environ, {
        'TELEGRAM_BOT_TOKEN': 'test_bot_token',
        'OPENAI_API_KEY': 'test_openai_key',
        'ELEVENLABS_API_KEY': 'test_elevenlabs_key',
        'YANDEX_CALENDAR_LOGIN': 'test@example.com',
        'YANDEX_CALENDAR_PASSWORD': 'test_password'
    }):
        config = Config()

        # Pydantic BaseSettings is frozen, so assignment should raise
        with pytest.raises(Exception):
            config.telegram_bot_token = 'new_token'
