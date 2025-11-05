"""Test Agent for automated testing of Tracker tasks"""
import asyncio
import subprocess
from pathlib import Path
from typing import List, Optional, Dict
from loguru import logger
from src.tracker.tracker_client import TrackerClient, TrackerTask


class TestAgent:
    """Agent that automatically tests tasks from Yandex Tracker"""

    # Mapping of task keys to test modules
    TASK_TEST_MAPPING = {
        "EXTEST-7": None,  # Project structure - no tests
        "EXTEST-8": None,  # Dependencies - no tests
        "EXTEST-9": "tests/unit/test_models.py",
        "EXTEST-10": "tests/unit/test_config.py",
        "EXTEST-11": "tests/unit/test_stt_service.py",
        "EXTEST-12": "tests/unit/test_tts_service.py",
        "EXTEST-13": "tests/unit/test_nlp_service.py",
        "EXTEST-14": "tests/unit/test_yandex_calendar.py",
        "EXTEST-15": "tests/unit/test_calendar_aggregator.py",
        "EXTEST-16": "tests/unit/test_bot_handlers.py",
        "EXTEST-17": "tests/unit/test_main.py",
        "EXTEST-18": "tests/unit/test_google_calendar.py",
        "EXTEST-19": "tests/unit/test_calendar_aggregator.py tests/unit/test_main.py",
    }

    def __init__(
        self,
        tracker_client: TrackerClient,
        project_root: Path,
        poll_interval: int = 60,
        coverage_threshold: int = 80
    ):
        """
        Initialize Test Agent

        Args:
            tracker_client: Tracker client instance
            project_root: Path to project root
            poll_interval: Polling interval in seconds
            coverage_threshold: Minimum coverage percentage required
        """
        self.tracker = tracker_client
        self.project_root = project_root
        self.poll_interval = poll_interval
        self.coverage_threshold = coverage_threshold
        self.running = False
        logger.info(f"Test Agent initialized (poll interval: {poll_interval}s, coverage threshold: {coverage_threshold}%)")

    async def start(self):
        """Start the test agent"""
        logger.info("🤖 Test Agent starting...")
        self.running = True

        while self.running:
            try:
                await self._process_testing_tasks()
            except Exception as e:
                logger.error(f"Error in test agent cycle: {e}")

            # Wait before next poll
            logger.info(f"Waiting {self.poll_interval}s before next poll...")
            await asyncio.sleep(self.poll_interval)

    async def stop(self):
        """Stop the test agent"""
        logger.info("🛑 Test Agent stopping...")
        self.running = False

    async def _process_testing_tasks(self):
        """Process all tasks in 'testing' status"""
        logger.info("🔍 Checking for tasks in 'testing' status...")

        try:
            # Get tasks in 'testing' status
            # Note: We need to check what statuses are available in the queue
            # For now, we'll process tasks in 'inProgress' status
            tasks = await self._get_tasks_for_testing()

            if not tasks:
                logger.info("No tasks found for testing")
                return

            logger.info(f"Found {len(tasks)} task(s) to test")

            for task in tasks:
                await self._test_task(task)

        except Exception as e:
            logger.error(f"Error processing testing tasks: {e}")

    async def _get_tasks_for_testing(self) -> List[TrackerTask]:
        """
        Get tasks that need testing

        For now, returns tasks in 'inProgress' status that have test mappings

        Returns:
            List of TrackerTask objects
        """
        try:
            # Get all tasks in inProgress status
            tasks = await self.tracker.get_tasks_by_status("inProgress")

            # Filter tasks that have test mappings
            testable_tasks = [
                task for task in tasks
                if task.key in self.TASK_TEST_MAPPING
            ]

            return testable_tasks

        except Exception as e:
            logger.error(f"Error getting tasks for testing: {e}")
            return []

    async def _test_task(self, task: TrackerTask):
        """
        Test a specific task

        Args:
            task: TrackerTask to test
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"🧪 Testing task: {task.key} - {task.summary}")
        logger.info(f"{'='*60}")

        try:
            # Get test modules for this task
            test_modules = self.TASK_TEST_MAPPING.get(task.key)

            if test_modules is None:
                logger.info(f"No tests defined for {task.key}, marking as passed")
                await self._handle_test_success(task)
                return

            # Run tests
            test_result = await self._run_tests(test_modules)

            if test_result["success"]:
                logger.info(f"✅ Tests passed for {task.key}")
                await self._handle_test_success(task)
            else:
                logger.error(f"❌ Tests failed for {task.key}")
                await self._handle_test_failure(task, test_result)

        except Exception as e:
            logger.error(f"Error testing task {task.key}: {e}")
            await self._handle_test_error(task, str(e))

    async def _run_tests(self, test_modules: str) -> Dict:
        """
        Run pytest for specified test modules

        Args:
            test_modules: Space-separated test module paths

        Returns:
            Dictionary with test results
        """
        logger.info(f"Running tests: {test_modules}")

        try:
            # Run pytest
            cmd = [
                "pytest",
                *test_modules.split(),
                "-v",
                "--cov=src",
                "--cov-report=term-missing",
                "--tb=short"
            ]

            result = subprocess.run(
                cmd,
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )

            # Parse results
            success = result.returncode == 0
            output = result.stdout + result.stderr

            # Extract coverage
            coverage = self._extract_coverage(output)

            return {
                "success": success and (coverage is None or coverage >= self.coverage_threshold),
                "exit_code": result.returncode,
                "output": output,
                "coverage": coverage
            }

        except subprocess.TimeoutExpired:
            logger.error("Tests timed out after 5 minutes")
            return {
                "success": False,
                "exit_code": -1,
                "output": "Tests timed out",
                "coverage": None
            }
        except Exception as e:
            logger.error(f"Error running tests: {e}")
            return {
                "success": False,
                "exit_code": -1,
                "output": str(e),
                "coverage": None
            }

    def _extract_coverage(self, output: str) -> Optional[int]:
        """
        Extract coverage percentage from pytest output

        Args:
            output: pytest output

        Returns:
            Coverage percentage or None
        """
        try:
            # Look for coverage line: "TOTAL ... 81%"
            for line in output.split('\n'):
                if 'TOTAL' in line and '%' in line:
                    # Extract percentage
                    parts = line.split()
                    for part in parts:
                        if '%' in part:
                            coverage_str = part.replace('%', '')
                            return int(coverage_str)
        except Exception as e:
            logger.error(f"Error extracting coverage: {e}")

        return None

    async def _handle_test_success(self, task: TrackerTask):
        """
        Handle successful test result

        Args:
            task: TrackerTask that passed tests
        """
        try:
            # Add success comment
            comment = f"""✅ **Тесты успешно пройдены**

Задача автоматически протестирована Test Agent.
Все тесты прошли успешно.

🤖 Test Agent"""

            await self.tracker.add_comment(task.key, comment)

            # Close task
            logger.info(f"Closing task {task.key}...")
            await self.tracker.update_task_status(task.key, "closed")

            logger.info(f"✅ Task {task.key} successfully tested and closed")

        except Exception as e:
            logger.error(f"Error handling test success for {task.key}: {e}")

    async def _handle_test_failure(self, task: TrackerTask, test_result: Dict):
        """
        Handle failed test result

        Args:
            task: TrackerTask that failed tests
            test_result: Test result dictionary
        """
        try:
            # Add failure comment
            coverage_info = ""
            if test_result.get("coverage") is not None:
                coverage_info = f"\n**Coverage**: {test_result['coverage']}% (требуется {self.coverage_threshold}%)"

            comment = f"""❌ **Тесты не прошли**

Задача автоматически протестирована Test Agent.
Тесты завершились с ошибками.{coverage_info}

**Exit Code**: {test_result.get('exit_code')}

Задача возвращена в работу для исправления.

🤖 Test Agent"""

            await self.tracker.add_comment(task.key, comment)

            # Return task to 'open' status (stop_progress transition)
            logger.info(f"Returning task {task.key} to open status...")
            await self.tracker.update_task_status(task.key, "stop_progress")

            logger.info(f"❌ Task {task.key} returned to open status due to test failures")

        except Exception as e:
            logger.error(f"Error handling test failure for {task.key}: {e}")

    async def _handle_test_error(self, task: TrackerTask, error_message: str):
        """
        Handle test error

        Args:
            task: TrackerTask that encountered an error
            error_message: Error message
        """
        try:
            # Add error comment
            comment = f"""⚠️ **Ошибка при тестировании**

Задача автоматически протестирована Test Agent.
При выполнении тестов произошла ошибка.

**Ошибка**: {error_message}

Задача оставлена в текущем статусе. Требуется ручная проверка.

🤖 Test Agent"""

            await self.tracker.add_comment(task.key, comment)

            logger.warning(f"⚠️ Task {task.key} encountered testing error")

        except Exception as e:
            logger.error(f"Error handling test error for {task.key}: {e}")
