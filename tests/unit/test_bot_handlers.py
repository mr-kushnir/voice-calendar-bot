"""Unit tests for Telegram Bot Handlers"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
from telegram import Update, Voice, Message, User, Chat
from telegram.ext import ContextTypes
from src.bot.handlers import BotHandlers
from src.services.calendar.models import Event, Command, Intent


@pytest.fixture
def bot_handlers():
    """BotHandlers fixture"""
    return BotHandlers(
        stt_service=AsyncMock(),
        tts_service=AsyncMock(),
        nlp_service=AsyncMock(),
        calendar_aggregator=AsyncMock()
    )


@pytest.fixture
def mock_update():
    """Mock Telegram Update"""
    update = Mock(spec=Update)
    update.effective_user = Mock(spec=User)
    update.effective_user.first_name = "TestUser"
    update.effective_user.id = 12345
    update.message = Mock(spec=Message)
    update.message.chat = Mock(spec=Chat)
    update.message.chat.id = 12345
    return update


@pytest.fixture
def mock_context():
    """Mock Telegram Context"""
    context = Mock(spec=ContextTypes.DEFAULT_TYPE)
    context.bot = AsyncMock()
    return context


@pytest.mark.asyncio
async def test_start_command(bot_handlers, mock_update, mock_context):
    """Test /start command handler"""
    await bot_handlers.start_command(mock_update, mock_context)

    # Should send welcome message
    mock_update.message.reply_text.assert_called_once()
    call_args = mock_update.message.reply_text.call_args[0][0]
    assert "Привет" in call_args or "приветствую" in call_args.lower()


@pytest.mark.asyncio
async def test_help_command(bot_handlers, mock_update, mock_context):
    """Test /help command handler"""
    await bot_handlers.help_command(mock_update, mock_context)

    # Should send help message
    mock_update.message.reply_text.assert_called_once()
    call_args = mock_update.message.reply_text.call_args[0][0]
    assert "команд" in call_args.lower() or "помощь" in call_args.lower()


@pytest.mark.asyncio
async def test_voice_message_handler_get_today(bot_handlers, mock_update, mock_context):
    """Test voice message handler with 'get today' command"""
    # Mock voice message
    mock_update.message.voice = Mock(spec=Voice)
    mock_update.message.voice.file_id = "test_file_id"

    # Mock file download
    mock_file = AsyncMock()
    mock_file.download_to_drive = AsyncMock()
    mock_context.bot.get_file = AsyncMock(return_value=mock_file)

    # Mock STT result
    bot_handlers.stt_service.transcribe.return_value = "что сегодня в календаре"

    # Mock NLP result
    bot_handlers.nlp_service.parse.return_value = Command(
        intent=Intent.GET_TODAY,
        original_text="что сегодня в календаре",
        parameters={},
        confidence=0.95
    )

    # Mock calendar events
    now = datetime.now()
    bot_handlers.calendar_aggregator.get_today_events.return_value = [
        Event(
            id="1", title="Team Meeting",
            start=now.replace(hour=10, minute=0),
            end=now.replace(hour=11, minute=0),
            attendees=[], source="yandex", raw_data={}
        )
    ]

    # Mock TTS result
    bot_handlers.tts_service.synthesize.return_value = b"fake audio data"

    # Execute handler
    await bot_handlers.voice_message_handler(mock_update, mock_context)

    # Verify flow
    bot_handlers.stt_service.transcribe.assert_called_once()
    bot_handlers.nlp_service.parse.assert_called_once()
    bot_handlers.calendar_aggregator.get_today_events.assert_called_once()
    bot_handlers.tts_service.synthesize.assert_called_once()
    mock_update.message.reply_voice.assert_called_once()


@pytest.mark.asyncio
async def test_voice_message_handler_get_tomorrow(bot_handlers, mock_update, mock_context):
    """Test voice message handler with 'get tomorrow' command"""
    mock_update.message.voice = Mock(spec=Voice)
    mock_update.message.voice.file_id = "test_file_id"

    mock_file = AsyncMock()
    mock_file.download_to_drive = AsyncMock()
    mock_context.bot.get_file = AsyncMock(return_value=mock_file)

    bot_handlers.stt_service.transcribe.return_value = "что завтра"

    bot_handlers.nlp_service.parse.return_value = Command(
        intent=Intent.GET_TOMORROW,
        original_text="что завтра",
        parameters={},
        confidence=0.90
    )

    bot_handlers.calendar_aggregator.get_tomorrow_events.return_value = []
    bot_handlers.tts_service.synthesize.return_value = b"fake audio"

    await bot_handlers.voice_message_handler(mock_update, mock_context)

    bot_handlers.calendar_aggregator.get_tomorrow_events.assert_called_once()

    # Check that TTS was called with "no events" message
    tts_call_args = bot_handlers.tts_service.synthesize.call_args[0][0]
    assert "нет событий" in tts_call_args.lower() or "свободен" in tts_call_args.lower()


@pytest.mark.asyncio
async def test_voice_message_handler_get_upcoming(bot_handlers, mock_update, mock_context):
    """Test voice message handler with 'get upcoming' command"""
    mock_update.message.voice = Mock(spec=Voice)
    mock_update.message.voice.file_id = "test_file_id"

    mock_file = AsyncMock()
    mock_file.download_to_drive = AsyncMock()
    mock_context.bot.get_file = AsyncMock(return_value=mock_file)

    bot_handlers.stt_service.transcribe.return_value = "что в ближайшие 3 часа"

    bot_handlers.nlp_service.parse.return_value = Command(
        intent=Intent.GET_UPCOMING,
        original_text="что в ближайшие 3 часа",
        parameters={"hours": 3},
        confidence=0.85
    )

    now = datetime.now()
    bot_handlers.calendar_aggregator.get_upcoming_events.return_value = [
        Event(
            id="1", title="Call",
            start=now + timedelta(hours=1),
            end=now + timedelta(hours=2),
            attendees=[], source="yandex", raw_data={}
        )
    ]

    bot_handlers.tts_service.synthesize.return_value = b"fake audio"

    await bot_handlers.voice_message_handler(mock_update, mock_context)

    bot_handlers.calendar_aggregator.get_upcoming_events.assert_called_once_with(hours=3)


@pytest.mark.asyncio
async def test_voice_message_handler_find_meeting(bot_handlers, mock_update, mock_context):
    """Test voice message handler with 'find meeting' command"""
    mock_update.message.voice = Mock(spec=Voice)
    mock_update.message.voice.file_id = "test_file_id"

    mock_file = AsyncMock()
    mock_file.download_to_drive = AsyncMock()
    mock_context.bot.get_file = AsyncMock(return_value=mock_file)

    bot_handlers.stt_service.transcribe.return_value = "когда встреча с Иваном"

    bot_handlers.nlp_service.parse.return_value = Command(
        intent=Intent.FIND_MEETING,
        original_text="когда встреча с Иваном",
        parameters={"person": "Иван"},
        confidence=0.92
    )

    now = datetime.now()
    bot_handlers.calendar_aggregator.find_meetings_with_person.return_value = [
        Event(
            id="1", title="Meeting with Ivan",
            start=now + timedelta(days=1),
            end=now + timedelta(days=1, hours=1),
            attendees=["ivan@example.com"], source="yandex", raw_data={}
        )
    ]

    bot_handlers.tts_service.synthesize.return_value = b"fake audio"

    await bot_handlers.voice_message_handler(mock_update, mock_context)

    bot_handlers.calendar_aggregator.find_meetings_with_person.assert_called_once_with(person="Иван")


@pytest.mark.asyncio
async def test_voice_message_handler_unknown_intent(bot_handlers, mock_update, mock_context):
    """Test voice message handler with unknown intent"""
    mock_update.message.voice = Mock(spec=Voice)
    mock_update.message.voice.file_id = "test_file_id"

    mock_file = AsyncMock()
    mock_file.download_to_drive = AsyncMock()
    mock_context.bot.get_file = AsyncMock(return_value=mock_file)

    bot_handlers.stt_service.transcribe.return_value = "абракадабра"

    bot_handlers.nlp_service.parse.return_value = Command(
        intent=Intent.UNKNOWN,
        original_text="абракадабра",
        parameters={},
        confidence=0.1
    )

    bot_handlers.tts_service.synthesize.return_value = b"fake audio"

    await bot_handlers.voice_message_handler(mock_update, mock_context)

    # Should send "not understood" message
    tts_call_args = bot_handlers.tts_service.synthesize.call_args[0][0]
    assert "не понял" in tts_call_args.lower() or "не распознал" in tts_call_args.lower()


@pytest.mark.asyncio
async def test_voice_message_handler_stt_error(bot_handlers, mock_update, mock_context):
    """Test voice message handler with STT error"""
    mock_update.message.voice = Mock(spec=Voice)
    mock_update.message.voice.file_id = "test_file_id"

    mock_file = AsyncMock()
    mock_file.download_to_drive = AsyncMock()
    mock_context.bot.get_file = AsyncMock(return_value=mock_file)

    # STT fails
    bot_handlers.stt_service.transcribe.side_effect = Exception("STT API Error")

    await bot_handlers.voice_message_handler(mock_update, mock_context)

    # Should send error message (at least 2 calls: status + error)
    assert mock_update.message.reply_text.call_count >= 1
    # Check last call for error message
    error_msg = mock_update.message.reply_text.call_args[0][0]
    assert "ошибка" in error_msg.lower()


@pytest.mark.asyncio
async def test_voice_message_handler_calendar_error(bot_handlers, mock_update, mock_context):
    """Test voice message handler with calendar error"""
    mock_update.message.voice = Mock(spec=Voice)
    mock_update.message.voice.file_id = "test_file_id"

    mock_file = AsyncMock()
    mock_file.download_to_drive = AsyncMock()
    mock_context.bot.get_file = AsyncMock(return_value=mock_file)

    bot_handlers.stt_service.transcribe.return_value = "что сегодня"

    bot_handlers.nlp_service.parse.return_value = Command(
        intent=Intent.GET_TODAY,
        original_text="что сегодня",
        parameters={},
        confidence=0.95
    )

    # Calendar fails
    bot_handlers.calendar_aggregator.get_today_events.side_effect = Exception("Calendar Error")

    await bot_handlers.voice_message_handler(mock_update, mock_context)

    # Should send error message (at least 2 calls: status + error)
    assert mock_update.message.reply_text.call_count >= 1
    # Check last call for error message
    error_msg = mock_update.message.reply_text.call_args[0][0]
    assert "ошибка" in error_msg.lower()


@pytest.mark.asyncio
async def test_text_message_handler(bot_handlers, mock_update, mock_context):
    """Test text message handler"""
    mock_update.message.text = "что сегодня в календаре"

    bot_handlers.nlp_service.parse.return_value = Command(
        intent=Intent.GET_TODAY,
        original_text="что сегодня в календаре",
        parameters={},
        confidence=0.95
    )

    bot_handlers.calendar_aggregator.get_today_events.return_value = []

    await bot_handlers.text_message_handler(mock_update, mock_context)

    bot_handlers.nlp_service.parse.assert_called_once_with("что сегодня в календаре")
    mock_update.message.reply_text.assert_called()


def test_format_events_response(bot_handlers):
    """Test formatting events into text response"""
    now = datetime.now()
    events = [
        Event(
            id="1", title="Meeting 1",
            start=now.replace(hour=10, minute=0),
            end=now.replace(hour=11, minute=0),
            attendees=["alice@example.com"], source="yandex", raw_data={}
        ),
        Event(
            id="2", title="Meeting 2",
            start=now.replace(hour=14, minute=30),
            end=now.replace(hour=15, minute=0),
            attendees=[], source="google", raw_data={}
        )
    ]

    response = bot_handlers._format_events_response(events)

    assert "Meeting 1" in response
    assert "Meeting 2" in response
    assert "10:00" in response
    assert "14:30" in response


def test_format_events_response_empty(bot_handlers):
    """Test formatting empty events list"""
    response = bot_handlers._format_events_response([])

    assert "нет событий" in response.lower() or "свободен" in response.lower()
