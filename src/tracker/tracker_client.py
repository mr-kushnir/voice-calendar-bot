"""Yandex Tracker API client"""
from dataclasses import dataclass
from typing import List, Optional
import aiohttp
from loguru import logger


@dataclass
class TrackerTask:
    """Yandex Tracker task model"""
    key: str
    id: str
    summary: str
    status: str
    description: Optional[str] = None
    assignee: Optional[str] = None
    priority: Optional[str] = None


class TrackerClient:
    """Client for Yandex Tracker API"""

    BASE_URL = "https://api.tracker.yandex.net/v2"

    def __init__(self, token: str, org_id: str, queue: str):
        """
        Initialize Tracker client

        Args:
            token: OAuth token for authentication
            org_id: Organization ID
            queue: Queue key (e.g., VOICEBOT)
        """
        self.token = token
        self.org_id = org_id
        self.queue = queue
        self.headers = {
            "Authorization": f"OAuth {token}",
            "X-Cloud-Org-Id": org_id,
            "Content-Type": "application/json"
        }

    async def create_task(
        self,
        summary: str,
        description: str,
        priority: str = "normal",
        assignee: Optional[str] = None
    ) -> TrackerTask:
        """
        Create a new task in Yandex Tracker

        Args:
            summary: Task title
            description: Task description
            priority: Task priority (critical, high, normal, low)
            assignee: Assignee username

        Returns:
            Created TrackerTask

        Raises:
            Exception: If API request fails
        """
        url = f"{self.BASE_URL}/issues"
        payload = {
            "queue": self.queue,
            "summary": summary,
            "description": description,
            "priority": priority
        }

        if assignee:
            payload["assignee"] = assignee

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=self.headers) as response:
                if response.status != 201:
                    error_text = await response.text()
                    logger.error(f"Failed to create task: {error_text}")
                    raise Exception(f"Failed to create task: {error_text}")

                data = await response.json()
                return TrackerTask(
                    key=data["key"],
                    id=data["id"],
                    summary=data["summary"],
                    status=data["status"]["key"],
                    description=description,
                    priority=priority
                )

    async def update_task_status(self, task_key: str, status: str) -> bool:
        """
        Update task status using transitions API

        Args:
            task_key: Task key (e.g., EXTEST-1)
            status: New status (open, inProgress, closed, needInfo)

        Returns:
            True if successful

        Raises:
            Exception: If API request fails
        """
        # Map status names to transition IDs
        status_to_transition = {
            "inProgress": "start_progress",
            "closed": "close",
            "needInfo": "need_info"
        }

        # Get transition ID from status, or use status as-is if not in mapping
        transition_id = status_to_transition.get(status, status)

        # Execute transition to new status
        url = f"{self.BASE_URL}/issues/{task_key}/transitions/{transition_id}/_execute"

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=self.headers) as response:
                if response.status not in [200, 201]:
                    error_text = await response.text()
                    logger.error(f"Failed to update task status: {error_text}")
                    raise Exception(f"Failed to update task status: {error_text}")

                logger.info(f"Task {task_key} transitioned to {status} (via {transition_id})")
                return True

    async def get_task_transitions(self, task_key: str) -> List[dict]:
        """
        Get available transitions for task

        Args:
            task_key: Task key

        Returns:
            List of available transitions

        Raises:
            Exception: If API request fails
        """
        url = f"{self.BASE_URL}/issues/{task_key}/transitions"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as response:
                if response.status == 200:
                    transitions = await response.json()
                    return transitions
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to get transitions: {error_text}")
                    raise Exception(f"Failed to get transitions: {error_text}")

    async def add_comment(self, task_key: str, comment: str) -> bool:
        """
        Add comment to task

        Args:
            task_key: Task key (e.g., VOICEBOT-1)
            comment: Comment text

        Returns:
            True if successful

        Raises:
            Exception: If API request fails
        """
        url = f"{self.BASE_URL}/issues/{task_key}/comments"
        payload = {"text": comment}

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=self.headers) as response:
                if response.status != 201:
                    error_text = await response.text()
                    logger.error(f"Failed to add comment: {error_text}")
                    raise Exception(f"Failed to add comment: {error_text}")

                logger.info(f"Comment added to task {task_key}")
                return True

    async def get_tasks_by_status(self, status: str) -> List[TrackerTask]:
        """
        Get tasks by status

        Args:
            status: Task status to filter by

        Returns:
            List of TrackerTask objects

        Raises:
            Exception: If API request fails
        """
        url = f"{self.BASE_URL}/issues"
        params = {
            "queue": self.queue,
            "filter": {"status": status}
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params={"filter": f"Queue: {self.queue} AND Status: {status}"}, headers=self.headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Failed to get tasks: {error_text}")
                    raise Exception(f"Failed to get tasks: {error_text}")

                data = await response.json()
                tasks = []
                for item in data:
                    tasks.append(TrackerTask(
                        key=item["key"],
                        id=item["id"],
                        summary=item["summary"],
                        status=item["status"]["key"],
                        description=item.get("description"),
                        priority=item.get("priority", {}).get("key")
                    ))

                logger.info(f"Found {len(tasks)} tasks with status {status}")
                return tasks

    async def link_commit(self, task_key: str, commit_hash: str, commit_message: str) -> bool:
        """
        Link commit to task

        Args:
            task_key: Task key (e.g., VOICEBOT-1)
            commit_hash: Git commit hash
            commit_message: Commit message

        Returns:
            True if successful

        Raises:
            Exception: If API request fails
        """
        url = f"{self.BASE_URL}/issues/{task_key}/comments"
        comment = f"Commit: `{commit_hash}`\n\n{commit_message}"

        return await self.add_comment(task_key, comment)

    async def close(self):
        """Close any open connections"""
        # Currently using context managers, so no persistent connections
        pass
