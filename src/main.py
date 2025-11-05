"""Main Bot Application"""
import asyncio
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from loguru import logger

from src.config import Config
from src.services.voice.stt_service import STTService
from src.services.voice.tts_service import TTSService
from src.services.nlp.nlp_service import NLPService
from src.services.calendar.yandex_calendar import YandexCalendarProvider
from src.services.calendar.google_calendar import GoogleCalendarProvider
from src.services.calendar.aggregator import CalendarAggregator
from src.bot.handlers import BotHandlers


class BotApplication:
    """Main bot application that initializes and runs all components"""

    def __init__(self, config: Config):
        """
        Initialize bot application

        Args:
            config: Configuration object
        """
        self.config = config
        logger.info("Initializing Voice Calendar Bot...")

        # Initialize services
        logger.info("Initializing STT service (Whisper)...")
        self.stt_service = STTService(api_key=config.openai_api_key)

        logger.info("Initializing TTS service (ElevenLabs)...")
        self.tts_service = TTSService(api_key=config.elevenlabs_api_key)

        logger.info("Initializing NLP service (GPT-4)...")
        self.nlp_service = NLPService(api_key=config.openai_api_key)

        # Initialize calendar providers
        logger.info("Initializing Yandex Calendar provider...")
        self.yandex_calendar = YandexCalendarProvider(
            login=config.yandex_calendar_login,
            password=config.yandex_calendar_password,
            caldav_url=config.yandex_calendar_url
        )

        # Initialize calendar aggregator
        logger.info("Initializing Calendar Aggregator...")
        self.calendar_aggregator = CalendarAggregator()
        self.calendar_aggregator.add_provider("yandex", self.yandex_calendar)

        # Add Google Calendar provider if ICS URL is configured
        if config.google_calendar_ics_url:
            logger.info("Initializing Google Calendar provider...")
            self.google_calendar = GoogleCalendarProvider(
                ics_url=config.google_calendar_ics_url
            )
            self.calendar_aggregator.add_provider("google", self.google_calendar)
        else:
            logger.info("Google Calendar ICS URL not configured, skipping...")

        # Initialize bot handlers
        logger.info("Initializing Bot Handlers...")
        self.handlers = BotHandlers(
            stt_service=self.stt_service,
            tts_service=self.tts_service,
            nlp_service=self.nlp_service,
            calendar_aggregator=self.calendar_aggregator
        )

        logger.info("✅ All services initialized successfully!")

    def create_telegram_app(self) -> Application:
        """
        Create Telegram application

        Returns:
            Telegram Application instance
        """
        logger.info("Creating Telegram application...")

        # Build application
        application = (
            Application.builder()
            .token(self.config.telegram_bot_token)
            .build()
        )

        logger.info("✅ Telegram application created")
        return application

    def setup_handlers(self, application: Application):
        """
        Setup bot handlers

        Args:
            application: Telegram Application instance
        """
        logger.info("Setting up bot handlers...")

        # Command handlers
        application.add_handler(
            CommandHandler("start", self.handlers.start_command)
        )
        application.add_handler(
            CommandHandler("help", self.handlers.help_command)
        )

        # Voice message handler
        application.add_handler(
            MessageHandler(
                filters.VOICE,
                self.handlers.voice_message_handler
            )
        )

        # Text message handler (optional)
        application.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                self.handlers.text_message_handler
            )
        )

        logger.info("✅ Bot handlers registered")

    async def run_polling(self):
        """Run bot in polling mode"""
        logger.info("Starting bot in polling mode...")

        try:
            # Create application
            application = self.create_telegram_app()

            # Setup handlers
            self.setup_handlers(application)

            # Start polling
            logger.info("🤖 Bot is running! Press Ctrl+C to stop.")
            await application.initialize()
            await application.start()
            await application.updater.start_polling(
                allowed_updates=["message"],
                drop_pending_updates=True
            )

            # Run until stopped
            await asyncio.Event().wait()

        except KeyboardInterrupt:
            logger.info("Received stop signal, shutting down...")
        except Exception as e:
            logger.error(f"Error running bot: {e}")
            raise
        finally:
            # Cleanup
            logger.info("Cleaning up...")
            await application.updater.stop()
            await application.stop()
            await application.shutdown()

            # Close service connections
            if hasattr(self.stt_service, 'close'):
                await self.stt_service.close()
            if hasattr(self.tts_service, 'close'):
                await self.tts_service.close()
            if hasattr(self.nlp_service, 'close'):
                await self.nlp_service.close()
            if hasattr(self.yandex_calendar, 'close'):
                await self.yandex_calendar.close()

            logger.info("✅ Shutdown complete")


def create_bot_application() -> BotApplication:
    """
    Create and configure bot application

    Returns:
        BotApplication instance

    Raises:
        ValueError: If configuration is invalid
    """
    try:
        # Load configuration
        logger.info("Loading configuration...")
        config = Config()
        logger.info("✅ Configuration loaded")

        # Create bot application
        bot_app = BotApplication(config)

        return bot_app

    except Exception as e:
        logger.error(f"Failed to create bot application: {e}")
        raise


async def main():
    """Main entry point"""
    try:
        # Setup logging
        logger.info("=" * 60)
        logger.info("Voice Calendar Telegram Bot")
        logger.info("=" * 60)

        # Create and run bot
        bot_app = create_bot_application()
        await bot_app.run_polling()

    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise


if __name__ == "__main__":
    # Run bot
    asyncio.run(main())
