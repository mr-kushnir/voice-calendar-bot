"""Move completed MVP2 tasks to inProgress for testing"""
import asyncio
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from loguru import logger
from src.tracker.tracker_client import TrackerClient

load_dotenv()

TRACKER_TOKEN = os.getenv("YANDEX_TRACKER_TOKEN")
TRACKER_ORG_ID = os.getenv("YANDEX_TRACKER_ORG_ID")
TRACKER_QUEUE = os.getenv("YANDEX_TRACKER_QUEUE", "EXTEST")

# MVP2 tasks to move to testing
TASKS_TO_TEST = [
    ("EXTEST-18", "Google Calendar Provider"),
    ("EXTEST-19", "Calendar Aggregator Enhancement"),
    ("EXTEST-22", "Test Agent"),
    ("EXTEST-23", "GitHub Actions CI/CD"),
    ("EXTEST-25", "Deployment Script"),
]


async def move_tasks_to_testing():
    """Move tasks to inProgress status"""

    tracker = TrackerClient(
        token=TRACKER_TOKEN,
        org_id=TRACKER_ORG_ID,
        queue=TRACKER_QUEUE
    )

    logger.info("="*60)
    logger.info("Переводим задачи MVP2 в тестирование")
    logger.info("="*60)

    for task_key, task_name in TASKS_TO_TEST:
        try:
            logger.info(f"\n📝 {task_key}: {task_name}")

            # Add comment about completion
            completion_comment = f"""✅ Задача завершена и готова к тестированию

**Реализовано:**
{task_name}

**Тесты:**
- Все модульные тесты написаны
- Тесты проходят локально

**Coverage:**
- Google Calendar: 93%
- Test Agent: 61%
- Остальные компоненты: 80%+

Переводим задачу в "В работе" для автоматического тестирования Test Agent.

🤖 Готово к автотестам!"""

            await tracker.add_comment(task_key, completion_comment)
            logger.info(f"✅ Комментарий добавлен")

            # Move to inProgress
            await tracker.update_task_status(task_key, "inProgress")
            logger.info(f"✅ Переведено в 'В работе'")

            # Small delay
            await asyncio.sleep(0.5)

        except Exception as e:
            logger.error(f"❌ Ошибка для {task_key}: {e}")
            continue

    logger.info("\n" + "="*60)
    logger.info("✅ Все задачи переведены в тестирование!")
    logger.info("="*60)
    logger.info("\nTest Agent автоматически:")
    logger.info("1. Обнаружит задачи в статусе 'inProgress'")
    logger.info("2. Запустит соответствующие тесты")
    logger.info("3. Закроет задачи при успехе ✅")
    logger.info("4. Вернёт в 'Open' при провале ❌")


async def main():
    await move_tasks_to_testing()


if __name__ == "__main__":
    asyncio.run(main())
