"""Generate Final Report for EXTEST Task Testing"""
import asyncio
import os
import sys
from pathlib import Path
from typing import List, Dict
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from loguru import logger
from src.tracker.tracker_client import TrackerClient

# Load environment variables
load_dotenv()


async def get_task_status(tracker: TrackerClient, task_key: str) -> Dict:
    """Get current task status"""
    try:
        import aiohttp
        url = f"{tracker.BASE_URL}/issues/{task_key}"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=tracker.headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "key": data["key"],
                        "summary": data["summary"],
                        "status": data["status"]["key"],
                        "priority": data.get("priority", {}).get("key", "normal")
                    }
                else:
                    return {
                        "key": task_key,
                        "summary": "ERROR",
                        "status": "ERROR",
                        "priority": "unknown"
                    }
    except Exception as e:
        logger.error(f"Error getting task {task_key}: {e}")
        return {
            "key": task_key,
            "summary": "ERROR",
            "status": "ERROR",
            "priority": "unknown"
        }


async def main():
    """Generate final report"""
    logger.info("=" * 80)
    logger.info("FINAL TESTING AND DEPLOYMENT REPORT")
    logger.info("=" * 80)
    logger.info(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("")

    # Get configuration
    tracker_token = os.getenv("YANDEX_TRACKER_TOKEN")
    tracker_org_id = os.getenv("YANDEX_TRACKER_ORG_ID")
    tracker_queue = os.getenv("YANDEX_TRACKER_QUEUE", "EXTEST")

    if not tracker_token or not tracker_org_id:
        logger.error("Missing Yandex Tracker credentials")
        return

    # Initialize tracker client
    tracker = TrackerClient(
        token=tracker_token,
        org_id=tracker_org_id,
        queue=tracker_queue
    )

    # Tasks to check
    tasks_to_check = [
        "EXTEST-7", "EXTEST-8", "EXTEST-9", "EXTEST-10", "EXTEST-11",
        "EXTEST-12", "EXTEST-13", "EXTEST-14", "EXTEST-15", "EXTEST-16",
        "EXTEST-17", "EXTEST-18", "EXTEST-19", "EXTEST-22", "EXTEST-23",
        "EXTEST-25"
    ]

    # Get current status of all tasks
    logger.info("Querying Yandex Tracker for current task statuses...")
    logger.info("")

    tasks_data = []
    for task_key in tasks_to_check:
        task_data = await get_task_status(tracker, task_key)
        tasks_data.append(task_data)

    # Count by status
    status_counts = {
        "open": 0,
        "inProgress": 0,
        "closed": 0,
        "needInfo": 0,
        "other": 0
    }

    # Print task details
    logger.info("TASK STATUS DETAILS:")
    logger.info("")
    logger.info(f"{'Task Key':<15} {'Status':<15} {'Priority':<12} {'Title'}")
    logger.info("-" * 80)

    for task in tasks_data:
        status = task["status"]
        if status in status_counts:
            status_counts[status] += 1
        else:
            status_counts["other"] += 1

        # Determine status icon
        if status == "closed":
            icon = "[CLOSED]"
        elif status == "open":
            icon = "[OPEN]  "
        elif status == "inProgress":
            icon = "[IN_PROG]"
        elif status == "needInfo":
            icon = "[INFO]  "
        else:
            icon = f"[{status[:7]}]"

        title = task["summary"][:50] + "..." if len(task["summary"]) > 50 else task["summary"]
        logger.info(f"{task['key']:<15} {icon:<15} {task['priority']:<12} {title}")

    logger.info("")
    logger.info("=" * 80)
    logger.info("SUMMARY STATISTICS:")
    logger.info("=" * 80)
    logger.info("")
    logger.info(f"Total Tasks Checked:    {len(tasks_data)}")
    logger.info(f"Closed (Passed):        {status_counts['closed']}")
    logger.info(f"Open (Failed/Returned): {status_counts['open']}")
    logger.info(f"In Progress:            {status_counts['inProgress']}")
    logger.info(f"Need Info:              {status_counts['needInfo']}")
    logger.info(f"Other Status:           {status_counts['other']}")
    logger.info("")

    # Calculate success rate
    successfully_tested = status_counts['closed']
    returned_to_work = status_counts['open']
    total = len(tasks_data)

    success_rate = (successfully_tested / total * 100) if total > 0 else 0

    logger.info("DEPLOYMENT METRICS:")
    logger.info(f"  Success Rate:         {success_rate:.1f}%")
    logger.info(f"  Tasks Ready:          {successfully_tested}/{total}")
    logger.info(f"  Tasks Needing Work:   {returned_to_work}")
    logger.info("")

    # Overall project status
    logger.info("=" * 80)
    logger.info("OVERALL PROJECT STATUS:")
    logger.info("=" * 80)
    logger.info("")

    if status_counts['open'] == 0 and status_counts['inProgress'] == 0:
        logger.info("STATUS: READY FOR DEPLOYMENT")
        logger.info("All tasks have been tested and closed successfully.")
    elif status_counts['open'] > 0:
        logger.info(f"STATUS: {status_counts['open']} TASK(S) NEED FIXES")
        logger.info("Some tasks failed testing and need remediation.")
        logger.info("Review the test failure comments in Yandex Tracker for details.")
    elif status_counts['inProgress'] > 0:
        logger.info(f"STATUS: {status_counts['inProgress']} TASK(S) STILL IN PROGRESS")
        logger.info("Some tasks are still being developed.")
    else:
        logger.info("STATUS: REVIEW REQUIRED")
        logger.info("Mixed status - manual review recommended.")

    logger.info("")
    logger.info("=" * 80)
    logger.info("NEXT STEPS:")
    logger.info("=" * 80)
    logger.info("")

    if returned_to_work > 0:
        logger.info("1. Review failed tasks in Yandex Tracker")
        logger.info("2. Check automated test reports in task comments")
        logger.info("3. Fix failing tests and improve code coverage")
        logger.info("4. Re-run tests after fixes are implemented")
        logger.info("5. Once all tests pass, tasks will be automatically closed")
    else:
        logger.info("1. All tests passed - project is ready for deployment")
        logger.info("2. Review final code and prepare deployment plan")
        logger.info("3. Execute deployment to production environment")
        logger.info("4. Monitor application performance post-deployment")

    logger.info("")
    logger.info("=" * 80)
    logger.info("END OF REPORT")
    logger.info("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
