"""Close EXTEST-31 using direct API"""
import asyncio
import os
import aiohttp
from dotenv import load_dotenv

load_dotenv()


async def close_task():
    token = os.getenv('YANDEX_TRACKER_TOKEN')
    org_id = os.getenv('YANDEX_TRACKER_ORG_ID')
    task_key = 'EXTEST-31'

    headers = {
        "Authorization": f"OAuth {token}",
        "X-Cloud-Org-Id": org_id,
        "Content-Type": "application/json"
    }

    async with aiohttp.ClientSession() as session:
        # Execute transition to close
        url = f"https://api.tracker.yandex.net/v2/issues/{task_key}/transitions/close/_execute"

        print(f"Closing {task_key}...")

        # Try with resolution string
        payload = {"resolution": "fixed"}

        async with session.post(url, headers=headers, json=payload) as response:
            if response.status in [200, 201]:
                result = await response.json()
                print(f"Task {task_key} closed successfully!")
                print(f"New status: {result.get('status', {}).get('display', 'Unknown')}")
                return True
            else:
                error_text = await response.text()
                print(f"Failed to close {task_key}: HTTP {response.status}")
                print(f"Error: {error_text}")
                return False


if __name__ == "__main__":
    asyncio.run(close_task())
