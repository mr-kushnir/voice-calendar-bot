"""Webhook-based Test Agent for Yandex Tracker"""
import asyncio
from pathlib import Path
from typing import Optional
from aiohttp import web
from loguru import logger
from src.tracker.tracker_client import TrackerClient
from src.agents.test_agent import TestAgent


class WebhookTestAgent:
    """Test Agent with webhook support"""

    def __init__(
        self,
        tracker_client: TrackerClient,
        project_root: Path,
        coverage_threshold: int = 80,
        webhook_host: str = "0.0.0.0",
        webhook_port: int = 8080
    ):
        """
        Initialize Webhook Test Agent

        Args:
            tracker_client: Tracker client instance
            project_root: Path to project root
            coverage_threshold: Minimum coverage percentage required
            webhook_host: Webhook server host
            webhook_port: Webhook server port
        """
        self.tracker = tracker_client
        self.project_root = project_root
        self.coverage_threshold = coverage_threshold
        self.webhook_host = webhook_host
        self.webhook_port = webhook_port

        # Create base test agent
        self.test_agent = TestAgent(
            tracker_client=tracker_client,
            project_root=project_root,
            poll_interval=0,  # Not used in webhook mode
            coverage_threshold=coverage_threshold
        )

        # Create web app
        self.app = web.Application()
        self.app.router.add_post('/webhook/tracker', self.handle_webhook)
        self.app.router.add_get('/health', self.health_check)

        logger.info(f"Webhook Test Agent initialized on {webhook_host}:{webhook_port}")

    async def handle_webhook(self, request: web.Request) -> web.Response:
        """
        Handle incoming webhook from Yandex Tracker

        Args:
            request: aiohttp request

        Returns:
            HTTP response
        """
        try:
            # Parse webhook payload
            payload = await request.json()

            logger.info("="*60)
            logger.info("📥 Webhook received from Yandex Tracker")
            logger.info("="*60)

            # Extract task information
            task_key = payload.get('issue', {}).get('key')
            status = payload.get('issue', {}).get('status', {}).get('key')

            if not task_key:
                logger.warning("Webhook without task key, ignoring")
                return web.Response(text="OK", status=200)

            logger.info(f"Task: {task_key}")
            logger.info(f"Status: {status}")

            # Check if status is 'inProgress' (ready for testing)
            if status == 'inProgress':
                logger.info(f"🧪 Task {task_key} moved to 'inProgress', starting tests...")

                # Run tests asynchronously (don't block webhook response)
                asyncio.create_task(self._test_task_async(task_key))

                return web.Response(
                    text=f"Testing task {task_key}",
                    status=202  # Accepted
                )
            else:
                logger.info(f"Task {task_key} status '{status}' - no action needed")
                return web.Response(text="OK", status=200)

        except Exception as e:
            logger.error(f"Error handling webhook: {e}")
            return web.Response(
                text=f"Error: {str(e)}",
                status=500
            )

    async def _test_task_async(self, task_key: str):
        """
        Test task asynchronously

        Args:
            task_key: Task key to test
        """
        try:
            # Get task details
            logger.info(f"Fetching task {task_key}...")

            # For now, create a mock task object
            # In production, would fetch from tracker
            from src.tracker.tracker_client import TrackerTask
            task = TrackerTask(
                key=task_key,
                id=task_key,
                summary=f"Task {task_key}",
                status="inProgress"
            )

            # Run tests
            await self.test_agent._test_task(task)

        except Exception as e:
            logger.error(f"Error testing task {task_key}: {e}")

    async def health_check(self, request: web.Request) -> web.Response:
        """Health check endpoint"""
        return web.Response(
            text="Webhook Test Agent is running",
            status=200
        )

    async def start(self):
        """Start webhook server"""
        logger.info("="*60)
        logger.info("🤖 Webhook Test Agent starting...")
        logger.info("="*60)
        logger.info(f"Listening on http://{self.webhook_host}:{self.webhook_port}")
        logger.info(f"Webhook URL: http://{self.webhook_host}:{self.webhook_port}/webhook/tracker")
        logger.info(f"Health check: http://{self.webhook_host}:{self.webhook_port}/health")
        logger.info("="*60)

        # Run web app
        runner = web.AppRunner(self.app)
        await runner.setup()

        site = web.TCPSite(runner, self.webhook_host, self.webhook_port)
        await site.start()

        logger.info("✅ Webhook Test Agent is running!")
        logger.info("\n📋 Настройте триггер в Yandex Tracker:")
        logger.info("1. Откройте настройки очереди EXTEST")
        logger.info("2. Перейдите в раздел 'Триггеры'")
        logger.info("3. Создайте новый триггер:")
        logger.info("   Условие: Статус изменён → В работе (inProgress)")
        logger.info(f"   Действие: HTTP запрос → POST http://YOUR_SERVER:{self.webhook_port}/webhook/tracker")
        logger.info("   Тело запроса: {{")
        logger.info('     "issue": {')
        logger.info('       "key": "{{issue.key}}",')
        logger.info('       "status": {"key": "{{issue.status.key}}"}')
        logger.info("     }")
        logger.info("   }")
        logger.info("\n⚠️  Замените YOUR_SERVER на ваш публичный IP или используйте ngrok для локальной разработки")

        # Keep running
        while True:
            await asyncio.sleep(3600)

    async def stop(self):
        """Stop webhook server"""
        logger.info("🛑 Webhook Test Agent stopping...")
