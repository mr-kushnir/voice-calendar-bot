"""Check available transitions from inProgress status"""
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


async def check_transitions():
    """Check available transitions from inProgress status"""

    tracker = TrackerClient(
        token=TRACKER_TOKEN,
        org_id=TRACKER_ORG_ID,
        queue=TRACKER_QUEUE
    )

    # Check transitions for EXTEST-7 (currently in inProgress)
    logger.info("Checking available transitions for EXTEST-7...")
    transitions = await tracker.get_task_transitions("EXTEST-7")

    logger.info(f"\nAvailable transitions from 'inProgress' status:")
    logger.info("="*60)

    for transition in transitions:
        transition_id = transition.get("id")
        display = transition.get("display")
        to_status = transition.get("to", {})
        to_status_key = to_status.get("key")
        to_status_display = to_status.get("display")

        logger.info(f"ID: {transition_id}")
        logger.info(f"  Display: {display}")
        logger.info(f"  To Status: {to_status_key} ({to_status_display})")
        logger.info("-"*60)


async def main():
    await check_transitions()


if __name__ == "__main__":
    asyncio.run(main())
