"""Delete tasks from Yandex Tracker"""
import os
import sys
from pathlib import Path
import requests
from dotenv import load_dotenv

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent.parent))
load_dotenv()

TOKEN = os.getenv("YANDEX_TRACKER_TOKEN")
ORG_ID = os.getenv("YANDEX_TRACKER_ORG_ID")
QUEUE = os.getenv("YANDEX_TRACKER_QUEUE")


def delete_task(task_key):
    """Delete a task"""
    url = f"https://api.tracker.yandex.net/v2/issues/{task_key}"

    headers = {
        "Authorization": f"OAuth {TOKEN}",
        "X-Cloud-Org-Id": ORG_ID,
        "Content-Type": "application/json"
    }

    try:
        response = requests.delete(url, headers=headers)
        if response.status_code == 204:
            print(f"✅ Удалена задача {task_key}")
            return True
        else:
            print(f"❌ Ошибка удаления {task_key}: {response.status_code}")
            print(f"   {response.text}")
            return False
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print(f"Удаление задач из очереди {QUEUE}")
    print("=" * 60)

    # Delete tasks 1-6
    tasks_to_delete = [f"{QUEUE}-{i}" for i in range(1, 7)]

    for task_key in tasks_to_delete:
        delete_task(task_key)

    print("\n✅ Готово!")
