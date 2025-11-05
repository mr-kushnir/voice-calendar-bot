"""Script to create all feature tasks in Yandex Tracker"""
import asyncio
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from loguru import logger
from src.tracker.tracker_client import TrackerClient
from src.tracker.task_manager import TaskManager


async def main():
    """Create all feature tasks in Yandex Tracker"""
    # Load environment variables
    load_dotenv()

    # Get credentials
    token = os.getenv("YANDEX_TRACKER_TOKEN")
    org_id = os.getenv("YANDEX_TRACKER_ORG_ID")
    queue = os.getenv("YANDEX_TRACKER_QUEUE", "VOICEBOT")

    if not token or not org_id:
        logger.error("Missing YANDEX_TRACKER_TOKEN or YANDEX_TRACKER_ORG_ID in .env")
        logger.info("Please add these variables to your .env file:")
        logger.info("  YANDEX_TRACKER_TOKEN=your_oauth_token")
        logger.info("  YANDEX_TRACKER_ORG_ID=your_organization_id")
        logger.info("  YANDEX_TRACKER_QUEUE=VOICEBOT")
        sys.exit(1)

    # Initialize clients
    tracker_client = TrackerClient(token=token, org_id=org_id, queue=queue)
    task_manager = TaskManager(tracker_client)

    logger.info("=" * 60)
    logger.info("Creating Voice Calendar Bot tasks in Yandex Tracker")
    logger.info(f"Queue: {queue}")
    logger.info("=" * 60)

    try:
        # Create all feature tasks
        tasks = await task_manager.create_feature_tasks()

        logger.info("\n" + "=" * 60)
        logger.info(f"✅ Successfully created {len(tasks)} tasks!")
        logger.info("=" * 60)

        # Print summary
        logger.info("\nCreated tasks:")
        for task in tasks:
            logger.info(f"  • {task.key}: {task.summary}")

        logger.info("\n" + "=" * 60)
        logger.info("Next steps:")
        logger.info("  1. Review tasks in Yandex Tracker")
        logger.info("  2. Start implementing features using TDD")
        logger.info("  3. Link commits to tasks using format: VOICEBOT-X: <message>")
        logger.info("  4. Set task status to 'testing' after implementation")
        logger.info("  5. Test Agent will automatically validate and close tasks")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Failed to create tasks: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
