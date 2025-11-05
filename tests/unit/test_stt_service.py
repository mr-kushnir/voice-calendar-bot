"""Unit tests for Speech-to-Text service"""
import pytest
import io
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path
from src.services.voice.stt_service import STTService


@pytest.fixture
def stt_service():
    """STTService fixture"""
    return STTService(api_key="test_api_key")


@pytest.mark.asyncio
async def test_transcribe_audio_file(stt_service):
    """Test transcribing audio file"""
    with patch('openai.AsyncOpenAI') as mock_openai:
        with patch('pathlib.Path.exists', return_value=True):
            with patch('builtins.open', create=True) as mock_open:
                mock_open.return_value.__enter__.return_value = io.BytesIO(b"fake audio")

                # Mock OpenAI client
                mock_client = AsyncMock()
                mock_openai.return_value = mock_client

                # Mock transcription response
                mock_response = Mock()
                mock_response.text = "что сегодня в календаре"
                mock_client.audio.transcriptions.create = AsyncMock(return_value=mock_response)

                # Reinitialize service with mocked client
                stt_service.client = mock_client

                # Test transcription
                result = await stt_service.transcribe("test_audio.ogg")

                assert result == "что сегодня в календаре"
                mock_client.audio.transcriptions.create.assert_called_once()


@pytest.mark.asyncio
async def test_transcribe_handles_invalid_file(stt_service):
    """Test transcribe handles invalid file"""
    with patch('pathlib.Path.exists', return_value=False):
        with pytest.raises(FileNotFoundError):
            await stt_service.transcribe("nonexistent.ogg")


@pytest.mark.asyncio
async def test_transcribe_api_error_handling(stt_service):
    """Test transcribe API error handling"""
    with patch('openai.AsyncOpenAI') as mock_openai:
        mock_client = AsyncMock()
        mock_openai.return_value = mock_client

        # Mock API error
        mock_client.audio.transcriptions.create = AsyncMock(
            side_effect=Exception("API Error")
        )

        stt_service.client = mock_client

        with pytest.raises(Exception):
            await stt_service.transcribe("test_audio.ogg")


@pytest.mark.asyncio
async def test_transcribe_with_bytes(stt_service):
    """Test transcribing from audio bytes"""
    with patch('openai.AsyncOpenAI') as mock_openai:
        mock_client = AsyncMock()
        mock_openai.return_value = mock_client

        mock_response = Mock()
        mock_response.text = "привет мир"
        mock_client.audio.transcriptions.create = AsyncMock(return_value=mock_response)

        stt_service.client = mock_client

        # Test with bytes
        audio_bytes = b"fake audio data"
        result = await stt_service.transcribe_bytes(audio_bytes, "audio.ogg")

        assert result == "привет мир"


@pytest.mark.asyncio
async def test_transcribe_with_language(stt_service):
    """Test transcribe with language parameter"""
    with patch('openai.AsyncOpenAI') as mock_openai:
        with patch('pathlib.Path.exists', return_value=True):
            with patch('builtins.open', create=True) as mock_open:
                mock_open.return_value.__enter__.return_value = io.BytesIO(b"fake audio")

                mock_client = AsyncMock()
                mock_openai.return_value = mock_client

                mock_response = Mock()
                mock_response.text = "когда встреча"
                mock_client.audio.transcriptions.create = AsyncMock(return_value=mock_response)

                stt_service.client = mock_client

                result = await stt_service.transcribe("test.ogg", language="ru")

                assert result == "когда встреча"
                # Verify language was passed
                call_kwargs = mock_client.audio.transcriptions.create.call_args[1]
                assert call_kwargs.get('language') == 'ru'


def test_stt_service_initialization():
    """Test STTService initialization"""
    service = STTService(api_key="test_key")
    assert service.api_key == "test_key"
    assert service.model == "whisper-1"


def test_stt_service_custom_model():
    """Test STTService with custom model"""
    service = STTService(api_key="test_key", model="custom-whisper")
    assert service.model == "custom-whisper"
