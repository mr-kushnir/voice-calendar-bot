"""Check all tasks in Yandex Tracker"""
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tracker.tracker_client import TrackerClient
from dotenv import load_dotenv

load_dotenv()


async def check_tasks():
    import aiohttp

    token = os.getenv('YANDEX_TRACKER_TOKEN')
    org_id = os.getenv('YANDEX_TRACKER_ORG_ID')

    print("=" * 60)
    print("Yandex Tracker Tasks Status")
    print("=" * 60)
    print()

    # Get all deployment tasks (EXTEST-27 to EXTEST-31)
    task_keys = ['EXTEST-27', 'EXTEST-28', 'EXTEST-29', 'EXTEST-30', 'EXTEST-31']

    headers = {
        "Authorization": f"OAuth {token}",
        "X-Cloud-Org-Id": org_id
    }

    async with aiohttp.ClientSession() as session:
        for task_key in task_keys:
            try:
                url = f"https://api.tracker.yandex.net/v2/issues/{task_key}"
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        task = await response.json()

                        status = task.get('status', {}).get('display', 'Unknown')
                        summary = task.get('summary', 'No summary')
                        assignee_info = task.get('assignee', {})
                        assignee = assignee_info.get('display', 'Unassigned') if assignee_info else 'Unassigned'

                        print(f"[{task_key}] {summary}")
                        print(f"  Status: {status}")
                        print(f"  Assignee: {assignee}")
                        print()
                    else:
                        error_text = await response.text()
                        print(f"[{task_key}] ERROR: HTTP {response.status} - {error_text[:100]}")
                        print()

            except Exception as e:
                print(f"[{task_key}] ERROR: {e}")
                print()

    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(check_tasks())
