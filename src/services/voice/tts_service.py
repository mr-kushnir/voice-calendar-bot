"""Text-to-Speech service using ElevenLabs"""
from typing import Optional
try:
    from elevenlabs.client import ElevenLabs
except ImportError:
    # Fallback for older version
    from elevenlabs import generate, set_api_key
from loguru import logger
import asyncio


class TTSService:
    """Text-to-Speech service using ElevenLabs API"""

    def __init__(self, api_key: str, voice_id: Optional[str] = None):
        """
        Initialize TTS service

        Args:
            api_key: ElevenLabs API key
            voice_id: Voice ID to use (default: Rachel voice)
        """
        self.api_key = api_key
        self.voice_id = voice_id or "21m00Tcm4TlvDq8ikWAM"  # Rachel voice

        # Try new API first
        try:
            self.client = ElevenLabs(api_key=api_key)
            self.use_new_api = True
        except (NameError, ImportError):
            set_api_key(api_key)
            self.use_new_api = False

    async def synthesize(
        self,
        text: str,
        voice_id: Optional[str] = None,
        model: str = "eleven_multilingual_v2"
    ) -> bytes:
        """
        Synthesize speech from text

        Args:
            text: Text to convert to speech
            voice_id: Optional voice ID (overrides default)
            model: Model to use (default: eleven_multilingual_v2)

        Returns:
            Audio data as bytes (MP3 format)

        Raises:
            ValueError: If text is empty
            Exception: If API call fails
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        voice = voice_id or self.voice_id

        try:
            logger.info(f"Synthesizing speech: {text[:50]}... (voice: {voice})")

            loop = asyncio.get_event_loop()

            if self.use_new_api:
                # New API (v1.0+)
                audio_data = await loop.run_in_executor(
                    None,
                    lambda: self.client.generate(
                        text=text,
                        voice=voice,
                        model=model
                    )
                )
            else:
                # Old API (v0.x)
                audio_data = await loop.run_in_executor(
                    None,
                    lambda: generate(
                        text=text,
                        voice=voice,
                        model=model
                    )
                )

            # Convert generator to bytes
            if hasattr(audio_data, '__iter__') and not isinstance(audio_data, bytes):
                audio_bytes = b''.join(audio_data)
            else:
                audio_bytes = audio_data

            logger.info(f"Synthesis successful (size: {len(audio_bytes)} bytes)")
            return audio_bytes

        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            raise
