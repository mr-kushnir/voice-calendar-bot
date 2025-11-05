"""Speech-to-Text service using OpenAI Whisper"""
from pathlib import Path
from typing import Optional
import io
from openai import AsyncOpenAI
from loguru import logger


class STTService:
    """Speech-to-Text service using OpenAI Whisper API"""

    def __init__(self, api_key: str, model: str = "whisper-1"):
        """
        Initialize STT service

        Args:
            api_key: OpenAI API key
            model: Whisper model to use (default: whisper-1)
        """
        self.api_key = api_key
        self.model = model
        self.client = AsyncOpenAI(api_key=api_key)

    async def transcribe(self, audio_path: str, language: Optional[str] = None) -> str:
        """
        Transcribe audio file to text

        Args:
            audio_path: Path to audio file
            language: Optional language code (e.g., 'ru', 'en')

        Returns:
            Transcribed text

        Raises:
            FileNotFoundError: If audio file doesn't exist
            Exception: If API call fails
        """
        audio_file_path = Path(audio_path)

        if not audio_file_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        try:
            with open(audio_file_path, "rb") as audio_file:
                logger.info(f"Transcribing audio file: {audio_path}")

                # Prepare transcription parameters
                transcription_params = {
                    "model": self.model,
                    "file": audio_file
                }

                if language:
                    transcription_params["language"] = language

                # Call Whisper API
                response = await self.client.audio.transcriptions.create(
                    **transcription_params
                )

                text = response.text
                logger.info(f"Transcription successful: {text[:50]}...")
                return text

        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise

    async def transcribe_bytes(
        self,
        audio_bytes: bytes,
        filename: str = "audio.ogg",
        language: Optional[str] = None
    ) -> str:
        """
        Transcribe audio from bytes

        Args:
            audio_bytes: Audio data as bytes
            filename: Filename for the audio (used for format detection)
            language: Optional language code

        Returns:
            Transcribed text

        Raises:
            Exception: If API call fails
        """
        try:
            logger.info(f"Transcribing audio from bytes (size: {len(audio_bytes)} bytes)")

            # Create file-like object from bytes
            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = filename

            # Prepare transcription parameters
            transcription_params = {
                "model": self.model,
                "file": audio_file
            }

            if language:
                transcription_params["language"] = language

            # Call Whisper API
            response = await self.client.audio.transcriptions.create(
                **transcription_params
            )

            text = response.text
            logger.info(f"Transcription successful: {text[:50]}...")
            return text

        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise

    async def close(self):
        """Close OpenAI client"""
        await self.client.close()
