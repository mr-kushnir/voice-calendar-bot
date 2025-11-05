"""Unit tests for Main Bot Application"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from src.main import BotApplication, create_bot_application


@pytest.fixture
def mock_config():
    """Mock configuration"""
    config = Mock()
    config.telegram_bot_token = "test_token"
    config.openai_api_key = "test_openai_key"
    config.elevenlabs_api_key = "test_elevenlabs_key"
    config.yandex_calendar_login = "test@example.com"
    config.yandex_calendar_password = "test_password"
    config.yandex_calendar_url = "https://caldav.yandex.ru"
    return config


def test_bot_application_initialization(mock_config):
    """Test BotApplication initialization"""
    with patch('src.main.STTService'), \
         patch('src.main.TTSService'), \
         patch('src.main.NLPService'), \
         patch('src.main.YandexCalendarProvider'), \
         patch('src.main.CalendarAggregator'), \
         patch('src.main.BotHandlers'):

        app = BotApplication(mock_config)

        assert app.config == mock_config
        assert app.stt_service is not None
        assert app.tts_service is not None
        assert app.nlp_service is not None
        assert app.calendar_aggregator is not None
        assert app.handlers is not None


def test_bot_application_services_initialized(mock_config):
    """Test that all services are properly initialized"""
    with patch('src.main.STTService') as MockSTT, \
         patch('src.main.TTSService') as MockTTS, \
         patch('src.main.NLPService') as MockNLP, \
         patch('src.main.YandexCalendarProvider') as MockYandex, \
         patch('src.main.CalendarAggregator') as MockAgg, \
         patch('src.main.BotHandlers') as MockHandlers:

        app = BotApplication(mock_config)

        # Verify services were initialized with correct parameters
        MockSTT.assert_called_once_with(api_key="test_openai_key")
        MockTTS.assert_called_once_with(api_key="test_elevenlabs_key")
        MockNLP.assert_called_once_with(api_key="test_openai_key")
        MockYandex.assert_called_once_with(
            login="test@example.com",
            password="test_password",
            caldav_url="https://caldav.yandex.ru"
        )
        MockAgg.assert_called_once()
        MockHandlers.assert_called_once()


@patch('src.main.Application')
def test_create_telegram_app(mock_telegram_app, mock_config):
    """Test Telegram application creation"""
    with patch('src.main.STTService'), \
         patch('src.main.TTSService'), \
         patch('src.main.NLPService'), \
         patch('src.main.YandexCalendarProvider'), \
         patch('src.main.CalendarAggregator'), \
         patch('src.main.BotHandlers'):

        app = BotApplication(mock_config)
        telegram_app = app.create_telegram_app()

        # Verify Application.builder() was called with token
        mock_telegram_app.builder.assert_called_once()


@patch('src.main.Application')
def test_setup_handlers(mock_telegram_app, mock_config):
    """Test handlers are registered"""
    with patch('src.main.STTService'), \
         patch('src.main.TTSService'), \
         patch('src.main.NLPService'), \
         patch('src.main.YandexCalendarProvider'), \
         patch('src.main.CalendarAggregator'), \
         patch('src.main.BotHandlers'):

        # Mock the application instance
        mock_app_instance = MagicMock()
        mock_telegram_app.builder.return_value.token.return_value.build.return_value = mock_app_instance

        app = BotApplication(mock_config)
        telegram_app = app.create_telegram_app()
        app.setup_handlers(telegram_app)

        # Verify handlers were added
        assert mock_app_instance.add_handler.called


def test_create_bot_application_success(mock_config):
    """Test successful bot application creation"""
    with patch('src.main.Config', return_value=mock_config), \
         patch('src.main.STTService'), \
         patch('src.main.TTSService'), \
         patch('src.main.NLPService'), \
         patch('src.main.YandexCalendarProvider'), \
         patch('src.main.CalendarAggregator'), \
         patch('src.main.BotHandlers'):

        bot_app = create_bot_application()

        assert isinstance(bot_app, BotApplication)
        assert bot_app.config == mock_config


def test_create_bot_application_missing_config():
    """Test bot application creation with missing config"""
    with patch('src.main.Config', side_effect=ValueError("Missing API key")):
        with pytest.raises(ValueError, match="Missing API key"):
            create_bot_application()


@pytest.mark.asyncio
async def test_calendar_provider_added_to_aggregator(mock_config):
    """Test that Yandex calendar is added to aggregator"""
    with patch('src.main.STTService'), \
         patch('src.main.TTSService'), \
         patch('src.main.NLPService'), \
         patch('src.main.YandexCalendarProvider') as MockYandex, \
         patch('src.main.CalendarAggregator') as MockAgg, \
         patch('src.main.BotHandlers'):

        mock_yandex_instance = Mock()
        MockYandex.return_value = mock_yandex_instance

        mock_agg_instance = Mock()
        MockAgg.return_value = mock_agg_instance

        app = BotApplication(mock_config)

        # Verify calendar provider was added to aggregator
        mock_agg_instance.add_provider.assert_called_once_with("yandex", mock_yandex_instance)


@patch('src.main.Application')
def test_command_handlers_registered(mock_telegram_app, mock_config):
    """Test that command handlers are registered"""
    with patch('src.main.STTService'), \
         patch('src.main.TTSService'), \
         patch('src.main.NLPService'), \
         patch('src.main.YandexCalendarProvider'), \
         patch('src.main.CalendarAggregator'), \
         patch('src.main.BotHandlers') as MockHandlers:

        # Mock handlers
        mock_handlers_instance = Mock()
        mock_handlers_instance.start_command = Mock()
        mock_handlers_instance.help_command = Mock()
        mock_handlers_instance.voice_message_handler = Mock()
        mock_handlers_instance.text_message_handler = Mock()
        MockHandlers.return_value = mock_handlers_instance

        # Mock application
        mock_app_instance = MagicMock()
        mock_telegram_app.builder.return_value.token.return_value.build.return_value = mock_app_instance

        app = BotApplication(mock_config)
        telegram_app = app.create_telegram_app()
        app.setup_handlers(telegram_app)

        # Verify handlers were registered
        assert mock_app_instance.add_handler.call_count >= 3  # start, help, voice


def test_bot_application_has_all_services(mock_config):
    """Test that bot application has all required services"""
    with patch('src.main.STTService') as MockSTT, \
         patch('src.main.TTSService') as MockTTS, \
         patch('src.main.NLPService') as MockNLP, \
         patch('src.main.YandexCalendarProvider') as MockYandex, \
         patch('src.main.CalendarAggregator') as MockAgg, \
         patch('src.main.BotHandlers') as MockHandlers:

        # Setup mocks
        mock_stt = Mock()
        mock_tts = Mock()
        mock_nlp = Mock()
        mock_yandex = Mock()
        mock_agg = Mock()
        mock_handlers = Mock()

        MockSTT.return_value = mock_stt
        MockTTS.return_value = mock_tts
        MockNLP.return_value = mock_nlp
        MockYandex.return_value = mock_yandex
        MockAgg.return_value = mock_agg
        MockHandlers.return_value = mock_handlers

        app = BotApplication(mock_config)

        # Verify all services are set
        assert app.stt_service == mock_stt
        assert app.tts_service == mock_tts
        assert app.nlp_service == mock_nlp
        assert app.yandex_calendar == mock_yandex
        assert app.calendar_aggregator == mock_agg
        assert app.handlers == mock_handlers
