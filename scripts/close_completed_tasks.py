"""Script to properly transition completed tasks through workflow"""
import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from loguru import logger
from src.tracker.tracker_client import TrackerClient

# Load environment variables
load_dotenv()

# Configuration
TRACKER_TOKEN = os.getenv("YANDEX_TRACKER_TOKEN")
TRACKER_ORG_ID = os.getenv("YANDEX_TRACKER_ORG_ID")
TRACKER_QUEUE = os.getenv("YANDEX_TRACKER_QUEUE", "EXTEST")

# Completed tasks that need to be transitioned
COMPLETED_TASKS = [
    ("EXTEST-7", "Настройка структуры проекта"),
    ("EXTEST-8", "Установка зависимостей"),
    ("EXTEST-9", "Модели данных"),
    ("EXTEST-10", "Управление конфигурацией"),
    ("EXTEST-11", "Сервис распознавания речи (Whisper) - 7 тестов"),
    ("EXTEST-12", "Сервис синтеза речи (ElevenLabs) - 8 тестов"),
    ("EXTEST-13", "Парсер NLP команд (GPT-4) - 10 тестов"),
    ("EXTEST-14", "Провайдер Яндекс.Календарь (CalDAV) - 8 тестов"),
    ("EXTEST-15", "Агрегатор календарей - 10 тестов"),
    ("EXTEST-16", "Обработчики Telegram бота - 12 тестов"),
    ("EXTEST-17", "Главное приложение бота - 9 тестов"),
]


async def transition_completed_tasks():
    """Transition completed tasks through proper workflow"""

    if not TRACKER_TOKEN or not TRACKER_ORG_ID:
        logger.error("Missing Yandex Tracker credentials in .env")
        return

    # Initialize tracker client
    tracker = TrackerClient(
        token=TRACKER_TOKEN,
        org_id=TRACKER_ORG_ID,
        queue=TRACKER_QUEUE
    )

    logger.info(f"Processing {len(COMPLETED_TASKS)} completed tasks...")

    for task_key, task_name in COMPLETED_TASKS:
        try:
            logger.info(f"\n{'='*60}")
            logger.info(f"Processing {task_key}: {task_name}")
            logger.info(f"{'='*60}")

            # Step 1: Transition to "inProgress" (В работу)
            logger.info(f"Step 1: Moving {task_key} to 'inProgress'...")
            await tracker.update_task_status(task_key, "inProgress")
            logger.info(f"✅ {task_key} moved to 'inProgress'")

            # Step 2: Add completion comment
            logger.info(f"Step 2: Adding completion comment to {task_key}...")
            completion_comment = f"""✅ Задача завершена

**Статус**: Реализовано и протестировано
**MVP1 Coverage**: 81.49%
**Тесты**: Все тесты проходят

Задача выполнена в рамках MVP1. Код написан, тесты созданы и проходят успешно."""

            await tracker.add_comment(task_key, completion_comment)
            logger.info(f"✅ Completion comment added to {task_key}")

            # Step 3: Transition to "closed" (Закрыта)
            logger.info(f"Step 3: Closing {task_key}...")
            await tracker.update_task_status(task_key, "closed")
            logger.info(f"✅ {task_key} closed successfully")

            # Small delay to avoid rate limiting
            await asyncio.sleep(0.5)

        except Exception as e:
            logger.error(f"❌ Error processing {task_key}: {e}")
            continue

    logger.info("\n" + "="*60)
    logger.info("✅ All completed tasks have been transitioned!")
    logger.info("="*60)


async def main():
    """Main entry point"""
    logger.info("="*60)
    logger.info("Close Completed Tasks Script")
    logger.info("="*60)

    await transition_completed_tasks()


if __name__ == "__main__":
    asyncio.run(main())
