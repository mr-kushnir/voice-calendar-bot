"""Unit tests for NLP Command Parser"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.services.nlp.nlp_service import NLPService
from src.services.calendar.models import Intent, Command


@pytest.fixture
def nlp_service():
    """NLPService fixture"""
    return NLPService(api_key="test_api_key")


@pytest.mark.asyncio
async def test_parse_get_today_command(nlp_service):
    """Test parsing 'what's today' command"""
    with patch('openai.AsyncOpenAI') as mock_openai:
        mock_client = AsyncMock()
        mock_openai.return_value = mock_client

        # Mock GPT-4 response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '{"intent": "get_today", "params": {}}'
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        nlp_service.client = mock_client

        # Test parsing
        result = await nlp_service.parse("что сегодня в календаре")

        assert result.intent == Intent.GET_TODAY
        assert result.original_text == "что сегодня в календаре"


@pytest.mark.asyncio
async def test_parse_get_tomorrow_command(nlp_service):
    """Test parsing 'what's tomorrow' command"""
    with patch('openai.AsyncOpenAI') as mock_openai:
        mock_client = AsyncMock()
        mock_openai.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '{"intent": "get_tomorrow", "params": {}}'
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        nlp_service.client = mock_client

        result = await nlp_service.parse("что завтра")

        assert result.intent == Intent.GET_TOMORROW
        assert result.original_text == "что завтра"


@pytest.mark.asyncio
async def test_parse_get_upcoming_command(nlp_service):
    """Test parsing 'upcoming events' command"""
    with patch('openai.AsyncOpenAI') as mock_openai:
        mock_client = AsyncMock()
        mock_openai.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '{"intent": "get_upcoming", "params": {"hours": 3}}'
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        nlp_service.client = mock_client

        result = await nlp_service.parse("что в ближайшие 3 часа")

        assert result.intent == Intent.GET_UPCOMING
        assert result.parameters.get("hours") == 3


@pytest.mark.asyncio
async def test_parse_find_meeting_command(nlp_service):
    """Test parsing 'find meeting' command"""
    with patch('openai.AsyncOpenAI') as mock_openai:
        mock_client = AsyncMock()
        mock_openai.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '{"intent": "find_meeting", "params": {"person": "Иван"}}'
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        nlp_service.client = mock_client

        result = await nlp_service.parse("когда встреча с Иваном")

        assert result.intent == Intent.FIND_MEETING
        assert result.parameters.get("person") == "Иван"


@pytest.mark.asyncio
async def test_parse_unknown_command(nlp_service):
    """Test parsing unknown command"""
    with patch('openai.AsyncOpenAI') as mock_openai:
        mock_client = AsyncMock()
        mock_openai.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '{"intent": "unknown", "params": {}}'
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        nlp_service.client = mock_client

        result = await nlp_service.parse("абракадабра")

        assert result.intent == Intent.UNKNOWN


@pytest.mark.asyncio
async def test_parse_empty_text(nlp_service):
    """Test parsing empty text"""
    with pytest.raises(ValueError, match="Text cannot be empty"):
        await nlp_service.parse("")


@pytest.mark.asyncio
async def test_parse_api_error(nlp_service):
    """Test parsing handles API errors"""
    with patch('openai.AsyncOpenAI') as mock_openai:
        mock_client = AsyncMock()
        mock_openai.return_value = mock_client

        mock_client.chat.completions.create = AsyncMock(
            side_effect=Exception("API Error")
        )

        nlp_service.client = mock_client

        with pytest.raises(Exception, match="API Error"):
            await nlp_service.parse("тестовая команда")


@pytest.mark.asyncio
async def test_parse_invalid_json_response(nlp_service):
    """Test parsing handles invalid JSON from GPT"""
    with patch('openai.AsyncOpenAI') as mock_openai:
        mock_client = AsyncMock()
        mock_openai.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = 'invalid json'
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        nlp_service.client = mock_client

        # Should fallback to UNKNOWN intent
        result = await nlp_service.parse("тестовая команда")
        assert result.intent == Intent.UNKNOWN


def test_nlp_service_initialization():
    """Test NLPService initialization"""
    service = NLPService(api_key="test_key")
    assert service.api_key == "test_key"
    assert service.model == "gpt-4"


def test_nlp_service_custom_model():
    """Test NLPService with custom model"""
    service = NLPService(api_key="test_key", model="gpt-4-turbo")
    assert service.model == "gpt-4-turbo"
