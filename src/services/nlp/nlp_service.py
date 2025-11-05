"""NLP Command Parser using GPT-4"""
from typing import Optional
import json
from openai import AsyncOpenAI
from loguru import logger

from src.services.calendar.models import Command, Intent


class NLPService:
    """NLP service for parsing voice commands using GPT-4"""

    SYSTEM_PROMPT = """Ты - ассистент для парсинга голосовых команд для календаря.
Анализируй текст и определи намерение (intent) пользователя.

Доступные интенты:
- get_today: запрос событий на сегодня (например: "что сегодня", "что в календаре сегодня")
- get_tomorrow: запрос событий на завтра (например: "что завтра", "что завтра в календаре")
- get_upcoming: запрос ближайших событий (например: "что в ближайшие 3 часа", "ближайшие встречи")
  params: {"hours": N} - количество часов
- find_meeting: поиск встречи с человеком (например: "когда встреча с Иваном", "когда встречаюсь с Петром")
  params: {"person": "имя"} - имя человека
- create_event: создание события (например: "создай встречу", "напомни о звонке")
  params: {"title": "название", "time": "время"} - опционально
- unknown: неизвестная команда

Ответь ТОЛЬКО в формате JSON:
{"intent": "название_интента", "params": {}}

Примеры:
Пользователь: "что сегодня в календаре"
Ответ: {"intent": "get_today", "params": {}}

Пользователь: "что в ближайшие 5 часов"
Ответ: {"intent": "get_upcoming", "params": {"hours": 5}}

Пользователь: "когда встреча с Сергеем"
Ответ: {"intent": "find_meeting", "params": {"person": "Сергей"}}
"""

    def __init__(self, api_key: str, model: str = "gpt-4"):
        """
        Initialize NLP service

        Args:
            api_key: OpenAI API key
            model: GPT model to use (default: gpt-4)
        """
        self.api_key = api_key
        self.model = model
        self.client = AsyncOpenAI(api_key=api_key)

    async def parse(self, text: str) -> Command:
        """
        Parse text command to structured Command

        Args:
            text: Text to parse

        Returns:
            Command object with intent and params

        Raises:
            ValueError: If text is empty
            Exception: If API call fails
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        try:
            logger.info(f"Parsing command: {text}")

            # Call GPT-4 for intent classification
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": text}
                ],
                temperature=0.0,  # Deterministic for classification
                max_tokens=150
            )

            # Parse GPT response
            gpt_response = response.choices[0].message.content.strip()
            logger.debug(f"GPT response: {gpt_response}")

            # Parse JSON response
            try:
                parsed = json.loads(gpt_response)
                intent_str = parsed.get("intent", "unknown")
                params = parsed.get("params", {})

                # Convert string intent to Intent enum
                try:
                    intent = Intent[intent_str.upper()]
                except KeyError:
                    logger.warning(f"Unknown intent: {intent_str}, using UNKNOWN")
                    intent = Intent.UNKNOWN

                command = Command(
                    intent=intent,
                    original_text=text,
                    parameters=params,
                    confidence=0.9  # High confidence for successful parse
                )

                logger.info(f"Parsed command: intent={intent.value}, params={params}")
                return command

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse GPT response as JSON: {e}")
                # Fallback to UNKNOWN intent
                return Command(
                    intent=Intent.UNKNOWN,
                    original_text=text,
                    parameters={},
                    confidence=0.0  # Low confidence for failed parse
                )

        except Exception as e:
            logger.error(f"NLP parsing failed: {e}")
            raise

    async def close(self):
        """Close OpenAI client"""
        await self.client.close()
