"""Unit tests for Text-to-Speech service"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.services.voice.tts_service import TTSService


@pytest.fixture
def tts_service():
    """TTSService fixture"""
    return TTSService(api_key="test_api_key", voice_id="test_voice")


@pytest.mark.asyncio
async def test_synthesize_speech(tts_service):
    """Test synthesizing speech from text"""
    # Mock the client.generate method
    tts_service.client = Mock()
    tts_service.client.generate = Mock(return_value=b"fake audio data")
    tts_service.use_new_api = True

    # Test synthesis
    result = await tts_service.synthesize("Привет мир")

    assert result == b"fake audio data"
    tts_service.client.generate.assert_called_once()


@pytest.mark.asyncio
async def test_synthesize_with_custom_voice(tts_service):
    """Test synthesis with custom voice"""
    tts_service.client = Mock()
    tts_service.client.generate = Mock(return_value=b"audio with custom voice")
    tts_service.use_new_api = True

    result = await tts_service.synthesize("Тест", voice_id="custom_voice_id")

    assert result == b"audio with custom voice"
    # Verify custom voice was used
    call_kwargs = tts_service.client.generate.call_args[1]
    assert call_kwargs.get('voice') == 'custom_voice_id'


@pytest.mark.asyncio
async def test_synthesize_api_error(tts_service):
    """Test synthesis handles API errors"""
    tts_service.client = Mock()
    tts_service.client.generate = Mock(side_effect=Exception("API Error"))
    tts_service.use_new_api = True

    with pytest.raises(Exception):
        await tts_service.synthesize("Тест")


@pytest.mark.asyncio
async def test_synthesize_empty_text(tts_service):
    """Test synthesis with empty text"""
    with pytest.raises(ValueError):
        await tts_service.synthesize("")


@pytest.mark.asyncio
async def test_synthesize_long_text(tts_service):
    """Test synthesis with long text"""
    tts_service.client = Mock()
    tts_service.client.generate = Mock(return_value=b"long audio")
    tts_service.use_new_api = True

    long_text = "А" * 5000  # Very long text
    result = await tts_service.synthesize(long_text)

    assert result == b"long audio"


def test_tts_service_initialization():
    """Test TTSService initialization"""
    service = TTSService(api_key="key123", voice_id="voice456")
    assert service.api_key == "key123"
    assert service.voice_id == "voice456"


def test_tts_service_default_voice():
    """Test TTSService with default voice"""
    service = TTSService(api_key="key123")
    assert service.voice_id is not None  # Should have a default voice


@pytest.mark.asyncio
async def test_synthesize_with_model_parameter(tts_service):
    """Test synthesis with model parameter"""
    tts_service.client = Mock()
    tts_service.client.generate = Mock(return_value=b"audio data")
    tts_service.use_new_api = True

    result = await tts_service.synthesize("Текст", model="eleven_multilingual_v2")

    assert result == b"audio data"
    # Verify model was passed
    call_kwargs = tts_service.client.generate.call_args[1]
    assert call_kwargs.get('model') == 'eleven_multilingual_v2'
