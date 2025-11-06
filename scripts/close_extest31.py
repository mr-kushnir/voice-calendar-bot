"""Close EXTEST-31"""
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tracker.tracker_client import TrackerClient
from dotenv import load_dotenv

load_dotenv()


async def close_task():
    tracker = TrackerClient(
        token=os.getenv('YANDEX_TRACKER_TOKEN'),
        org_id=os.getenv('YANDEX_TRACKER_ORG_ID'),
        queue='EXTEST'
    )

    task_key = 'EXTEST-31'

    try:
        print(f"Closing {task_key}...")

        # Use update_task_status
        success = await tracker.update_task_status(task_key, 'close')

        if success:
            print(f"Task {task_key} closed successfully!")
        else:
            print(f"Failed to close {task_key}")

    except Exception as e:
        print(f"Error closing {task_key}: {str(e)}")


if __name__ == "__main__":
    asyncio.run(close_task())
