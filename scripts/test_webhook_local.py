"""Test webhook locally by sending a mock request"""
import requests
import json
from loguru import logger


def test_webhook():
    """Send test webhook request to local agent"""

    webhook_url = "http://localhost:8080/webhook/tracker"

    # Mock payload from Yandex Tracker
    payload = {
        "issue": {
            "key": "EXTEST-11",
            "summary": "Сервис распознавания речи (Whisper)",
            "status": {
                "key": "inProgress",
                "display": "В работе"
            }
        }
    }

    logger.info("="*60)
    logger.info("🧪 Testing Webhook locally")
    logger.info("="*60)
    logger.info(f"URL: {webhook_url}")
    logger.info(f"Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")

    try:
        # Check health first
        logger.info("\n1. Checking health endpoint...")
        health_response = requests.get("http://localhost:8080/health", timeout=5)

        if health_response.status_code == 200:
            logger.info(f"✅ Health check OK: {health_response.text}")
        else:
            logger.error(f"❌ Health check failed: {health_response.status_code}")
            return

        # Send webhook
        logger.info("\n2. Sending webhook request...")
        response = requests.post(
            webhook_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=5
        )

        logger.info(f"\nResponse status: {response.status_code}")
        logger.info(f"Response body: {response.text}")

        if response.status_code == 202:
            logger.info("\n✅ Webhook accepted! Test Agent should start testing...")
            logger.info("Check webhook agent logs for test results")
        else:
            logger.warning(f"\n⚠️  Unexpected status code: {response.status_code}")

    except requests.exceptions.ConnectionError:
        logger.error("\n❌ Connection error!")
        logger.error("Make sure Webhook Test Agent is running:")
        logger.error("  python scripts/run_webhook_test_agent.py")

    except Exception as e:
        logger.error(f"\n❌ Error: {e}")


if __name__ == "__main__":
    test_webhook()
