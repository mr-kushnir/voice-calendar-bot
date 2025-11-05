"""Telegram Bot Handlers"""
from typing import List
import os
import tempfile
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from loguru import logger

from src.services.voice.stt_service import STTService
from src.services.voice.tts_service import TTSService
from src.services.nlp.nlp_service import NLPService
from src.services.calendar.aggregator import CalendarAggregator
from src.services.calendar.models import Event, Intent


class BotHandlers:
    """Telegram bot handlers for voice calendar"""

    def __init__(
        self,
        stt_service: STTService,
        tts_service: TTSService,
        nlp_service: NLPService,
        calendar_aggregator: CalendarAggregator
    ):
        """
        Initialize bot handlers

        Args:
            stt_service: Speech-to-text service
            tts_service: Text-to-speech service
            nlp_service: NLP command parser
            calendar_aggregator: Calendar aggregator
        """
        self.stt_service = stt_service
        self.tts_service = tts_service
        self.nlp_service = nlp_service
        self.calendar_aggregator = calendar_aggregator

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle /start command

        Args:
            update: Telegram update
            context: Telegram context
        """
        user = update.effective_user
        welcome_message = f"""Привет, {user.first_name}! 👋

Я голосовой календарь-бот. Отправьте мне голосовое сообщение с командой, и я помогу вам с календарем.

Доступные команды:
• "Что сегодня в календаре?" - события на сегодня
• "Что завтра?" - события на завтра
• "Что в ближайшие 3 часа?" - ближайшие события
• "Когда встреча с Иваном?" - найти встречу с человеком

Отправьте голосовое сообщение или используйте /help для подробной справки."""

        await update.message.reply_text(welcome_message)
        logger.info(f"User {user.id} started bot")

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle /help command

        Args:
            update: Telegram update
            context: Telegram context
        """
        help_message = """📖 Справка по командам

Я понимаю голосовые команды на русском языке:

🗓 Запросы событий:
• "Что сегодня?" / "Что сегодня в календаре?"
• "Что завтра?"
• "Что в ближайшие N часов?" (например, "в ближайшие 3 часа")

👤 Поиск встреч:
• "Когда встреча с [имя]?" (например, "когда встреча с Иваном")
• "Когда встречаюсь с [имя]?"

📝 Формат ответа:
Я отвечу голосовым сообщением со списком ваших событий.

💡 Советы:
• Говорите четко и не спешите
• Используйте простые формулировки
• Я работаю с Яндекс.Календарем и Google Calendar

Для начала используйте /start"""

        await update.message.reply_text(help_message)
        logger.info(f"User {update.effective_user.id} requested help")

    async def voice_message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle voice messages

        Args:
            update: Telegram update
            context: Telegram context
        """
        user_id = update.effective_user.id
        logger.info(f"Received voice message from user {user_id}")

        try:
            # Download voice message
            voice = update.message.voice
            voice_file = await context.bot.get_file(voice.file_id)

            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as temp_file:
                temp_path = temp_file.name
                await voice_file.download_to_drive(temp_path)

            logger.info(f"Voice file downloaded: {temp_path}")

            # Step 1: Speech-to-Text
            await update.message.reply_text("🎤 Распознаю голосовое сообщение...")
            text = await self.stt_service.transcribe(temp_path, language="ru")
            logger.info(f"Transcribed text: {text}")

            # Clean up temp file
            os.unlink(temp_path)

            # Step 2: Parse command with NLP
            command = await self.nlp_service.parse(text)
            logger.info(f"Parsed command: intent={command.intent.value}, confidence={command.confidence}")

            # Step 3: Execute command
            response_text = await self._execute_command(command)

            # Step 4: Synthesize speech
            await update.message.reply_text("🔊 Генерирую ответ...")
            audio_data = await self.tts_service.synthesize(response_text)

            # Step 5: Send voice response
            await update.message.reply_voice(voice=audio_data)
            logger.info(f"Voice response sent to user {user_id}")

        except Exception as e:
            logger.error(f"Error processing voice message: {e}")
            await update.message.reply_text(
                "❌ Произошла ошибка при обработке голосового сообщения. Попробуйте еще раз."
            )

    async def text_message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle text messages (optional)

        Args:
            update: Telegram update
            context: Telegram context
        """
        user_id = update.effective_user.id
        text = update.message.text
        logger.info(f"Received text message from user {user_id}: {text}")

        try:
            # Parse command
            command = await self.nlp_service.parse(text)
            logger.info(f"Parsed command: intent={command.intent.value}")

            # Execute command
            response_text = await self._execute_command(command)

            # Send text response
            await update.message.reply_text(response_text)

        except Exception as e:
            logger.error(f"Error processing text message: {e}")
            await update.message.reply_text(
                "❌ Произошла ошибка при обработке сообщения. Попробуйте еще раз."
            )

    async def _execute_command(self, command) -> str:
        """
        Execute parsed command

        Args:
            command: Parsed command object

        Returns:
            Response text

        Raises:
            Exception: If command execution fails
        """
        try:
            if command.intent == Intent.GET_TODAY:
                events = await self.calendar_aggregator.get_today_events()
                return self._format_events_response(events, "на сегодня")

            elif command.intent == Intent.GET_TOMORROW:
                events = await self.calendar_aggregator.get_tomorrow_events()
                return self._format_events_response(events, "на завтра")

            elif command.intent == Intent.GET_UPCOMING:
                hours = command.parameters.get("hours", 24)
                events = await self.calendar_aggregator.get_upcoming_events(hours=hours)
                return self._format_events_response(events, f"в ближайшие {hours} часов")

            elif command.intent == Intent.FIND_MEETING:
                person = command.parameters.get("person", "")
                events = await self.calendar_aggregator.find_meetings_with_person(person=person)
                if events:
                    return self._format_events_response(events, f"встречи с {person}")
                else:
                    return f"Встреч с {person} не найдено."

            elif command.intent == Intent.UNKNOWN:
                return "Извините, я не понял вашу команду. Попробуйте сказать: 'Что сегодня в календаре?'"

            else:
                return "Эта команда пока не поддерживается."

        except Exception as e:
            logger.error(f"Error executing command: {e}")
            raise

    def _format_events_response(self, events: List[Event], context: str = "") -> str:
        """
        Format events into text response

        Args:
            events: List of events
            context: Context string (e.g., "на сегодня")

        Returns:
            Formatted response text
        """
        if not events:
            if context:
                return f"У вас нет событий {context}. Вы свободны!"
            else:
                return "У вас нет событий. Вы свободны!"

        response = f"У вас {len(events)} событий {context}:\n\n" if context else f"Найдено событий: {len(events)}\n\n"

        for i, event in enumerate(events, 1):
            start_time = event.start.strftime("%H:%M")
            end_time = event.end.strftime("%H:%M")
            response += f"{i}. {event.title}\n"
            response += f"   Время: {start_time} - {end_time}\n"

            if event.attendees:
                response += f"   Участники: {len(event.attendees)}\n"

            if event.location:
                response += f"   Место: {event.location}\n"

            response += "\n"

        return response.strip()
