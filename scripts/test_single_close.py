"""Test closing a single task with detailed diagnostics"""
import asyncio
import os
import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import aiohttp
from dotenv import load_dotenv
from loguru import logger

# Load environment variables
load_dotenv()

# Configuration
TRACKER_TOKEN = os.getenv("YANDEX_TRACKER_TOKEN")
TRACKER_ORG_ID = os.getenv("YANDEX_TRACKER_ORG_ID")
BASE_URL = "https://api.tracker.yandex.net/v2"


async def test_close_task():
    """Test closing EXTEST-7 with detailed diagnostics"""

    headers = {
        "Authorization": f"OAuth {TRACKER_TOKEN}",
        "X-Cloud-Org-Id": TRACKER_ORG_ID,
        "Content-Type": "application/json"
    }

    task_key = "EXTEST-7"
    url = f"{BASE_URL}/issues/{task_key}/transitions/close/_execute"

    logger.info(f"Attempting to close {task_key}...")
    logger.info(f"URL: {url}")
    logger.info(f"Headers: {headers}")

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers) as response:
            status = response.status
            text = await response.text()

            logger.info(f"\nResponse Status: {status}")
            logger.info(f"Response Body:\n{text}")

            if status in [200, 201]:
                logger.info(f"✅ Successfully closed {task_key}!")
                data = json.loads(text)
                logger.info(f"New status: {data.get('status', {}).get('key')}")
            else:
                logger.error(f"❌ Failed to close {task_key}")
                try:
                    error_data = json.loads(text)
                    logger.error(f"Error details: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
                except:
                    logger.error(f"Raw error: {text}")


async def main():
    await test_close_task()


if __name__ == "__main__":
    asyncio.run(main())
