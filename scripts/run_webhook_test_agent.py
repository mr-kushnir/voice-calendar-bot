"""Run Webhook Test Agent"""
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
from src.agents.webhook_test_agent import WebhookTestAgent

# Load environment variables
load_dotenv()


async def main():
    """Main entry point"""
    logger.info("="*60)
    logger.info("🤖 Webhook Test Agent")
    logger.info("="*60)

    # Get configuration from environment
    tracker_token = os.getenv("YANDEX_TRACKER_TOKEN")
    tracker_org_id = os.getenv("YANDEX_TRACKER_ORG_ID")
    tracker_queue = os.getenv("YANDEX_TRACKER_QUEUE", "EXTEST")
    coverage_threshold = int(os.getenv("TEST_AGENT_COVERAGE_THRESHOLD", "80"))
    webhook_host = os.getenv("WEBHOOK_HOST", "0.0.0.0")
    webhook_port = int(os.getenv("WEBHOOK_PORT", "8080"))

    if not tracker_token or not tracker_org_id:
        logger.error("Missing Yandex Tracker credentials in .env")
        logger.error("Please set YANDEX_TRACKER_TOKEN and YANDEX_TRACKER_ORG_ID")
        return

    # Initialize tracker client
    logger.info(f"Connecting to Yandex Tracker (Queue: {tracker_queue})...")
    tracker_client = TrackerClient(
        token=tracker_token,
        org_id=tracker_org_id,
        queue=tracker_queue
    )

    # Initialize webhook test agent
    webhook_agent = WebhookTestAgent(
        tracker_client=tracker_client,
        project_root=project_root,
        coverage_threshold=coverage_threshold,
        webhook_host=webhook_host,
        webhook_port=webhook_port
    )

    try:
        # Start webhook test agent
        await webhook_agent.start()
    except KeyboardInterrupt:
        logger.info("\n\nReceived interrupt signal...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise
    finally:
        # Stop webhook test agent
        await webhook_agent.stop()
        logger.info("✅ Webhook Test Agent stopped")


if __name__ == "__main__":
    asyncio.run(main())
