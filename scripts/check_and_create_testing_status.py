"""Check and create 'testing' status in Yandex Tracker"""
import asyncio
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import aiohttp
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

TRACKER_TOKEN = os.getenv("YANDEX_TRACKER_TOKEN")
TRACKER_ORG_ID = os.getenv("YANDEX_TRACKER_ORG_ID")
TRACKER_QUEUE = os.getenv("YANDEX_TRACKER_QUEUE", "EXTEST")
BASE_URL = "https://api.tracker.yandex.net/v2"


async def check_queue_statuses():
    """Check available statuses in queue"""
    headers = {
        "Authorization": f"OAuth {TRACKER_TOKEN}",
        "X-Cloud-Org-Id": TRACKER_ORG_ID,
        "Content-Type": "application/json"
    }

    url = f"{BASE_URL}/queues/{TRACKER_QUEUE}/statuses"

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                statuses = await response.json()
                logger.info(f"\nДоступные статусы в очереди {TRACKER_QUEUE}:")
                logger.info("="*60)
                for status in statuses:
                    key = status.get('key', 'unknown')
                    display = status.get('display', status.get('name', 'N/A'))
                    logger.info(f"  Key: {key:15} | Display: {display}")
                return statuses
            else:
                error_text = await response.text()
                logger.error(f"Failed to get statuses: {error_text}")
                return []


async def check_workflow():
    """Check workflow for queue"""
    headers = {
        "Authorization": f"OAuth {TRACKER_TOKEN}",
        "X-Cloud-Org-Id": TRACKER_ORG_ID,
        "Content-Type": "application/json"
    }

    url = f"{BASE_URL}/queues/{TRACKER_QUEUE}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                queue_info = await response.json()
                logger.info(f"\nИнформация об очереди {TRACKER_QUEUE}:")
                logger.info("="*60)
                logger.info(f"Name: {queue_info.get('name')}")
                logger.info(f"Key: {queue_info.get('key')}")

                # Check if there's a workflow
                if 'workflow' in queue_info:
                    logger.info(f"Workflow: {queue_info['workflow']}")

                return queue_info
            else:
                error_text = await response.text()
                logger.error(f"Failed to get queue info: {error_text}")
                return None


async def main():
    logger.info("="*60)
    logger.info("Yandex Tracker Status Configuration")
    logger.info("="*60)

    # Check statuses
    await check_queue_statuses()

    # Check workflow
    await check_workflow()

    logger.info("\n" + "="*60)
    logger.info("Рекомендации:")
    logger.info("="*60)
    logger.info("1. Если есть статус 'testing' или 'needInfo' - используем его")
    logger.info("2. Настроим trigger в Yandex Tracker:")
    logger.info("   - Событие: Статус изменён на 'inProgress'")
    logger.info("   - Действие: HTTP request to webhook")
    logger.info("3. Test Agent будет получать webhook и сразу тестировать")


if __name__ == "__main__":
    asyncio.run(main())
