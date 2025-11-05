"""Check or create VOICEBOT queue in Yandex Tracker"""
import os
import sys
from pathlib import Path
import requests
from dotenv import load_dotenv

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent.parent))
load_dotenv()

IAM_TOKEN = os.getenv("YANDEX_TRACKER_TOKEN")
ORG_ID = os.getenv("YANDEX_TRACKER_ORG_ID")
QUEUE_KEY = os.getenv("YANDEX_TRACKER_QUEUE", "VOICEBOT")


def check_queue_exists():
    """Check if VOICEBOT queue exists"""
    url = f"https://api.tracker.yandex.net/v2/queues/{QUEUE_KEY}"

    headers = {
        "Authorization": f"OAuth {IAM_TOKEN}",
        "X-Cloud-Org-Id": ORG_ID,
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            queue = response.json()
            print(f"✅ Очередь {QUEUE_KEY} существует!")
            print(f"   Название: {queue.get('name')}")
            print(f"   Описание: {queue.get('description', 'Нет описания')}")
            return True
        elif response.status_code == 404:
            print(f"❌ Очередь {QUEUE_KEY} не найдена")
            return False
        else:
            print(f"❌ Ошибка проверки очереди: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


def list_queues():
    """List all available queues"""
    url = "https://api.tracker.yandex.net/v2/queues"

    headers = {
        "Authorization": f"OAuth {IAM_TOKEN}",
        "X-Cloud-Org-Id": ORG_ID,
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            queues = response.json()
            print(f"\n📋 Доступные очереди ({len(queues)}):")
            for queue in queues:
                print(f"  • {queue.get('key')}: {queue.get('name')}")
            return queues
        else:
            print(f"❌ Ошибка получения списка очередей: {response.status_code}")
            print(f"Response: {response.text}")
            return []
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return []


def get_user_info():
    """Get current user info for lead field"""
    url = "https://api.tracker.yandex.net/v2/myself"

    headers = {
        "Authorization": f"OAuth {IAM_TOKEN}",
        "X-Cloud-Org-Id": ORG_ID,
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return data.get('uid')
    except:
        pass
    return None


def create_queue():
    """Create VOICEBOT queue"""
    url = "https://api.tracker.yandex.net/v2/queues"

    headers = {
        "Authorization": f"OAuth {IAM_TOKEN}",
        "X-Cloud-Org-Id": ORG_ID,
        "Content-Type": "application/json"
    }

    # Get current user as lead
    lead = get_user_info()
    if not lead:
        print("❌ Не удалось получить информацию о пользователе")
        return False

    payload = {
        "key": QUEUE_KEY,
        "name": "Voice Calendar Bot",
        "lead": lead,
        "defaultType": "task",
        "defaultPriority": "normal",
        "issueTypesConfig": [
            {"issueType": "task", "workflow": "okmdesimple", "resolutions": ["fixed", "wontFix", "duplicate", "invalid"]}
        ]
    }

    try:
        response = requests.post(url, json=payload, headers=headers)

        if response.status_code == 201:
            queue = response.json()
            print(f"\n✅ Очередь {QUEUE_KEY} создана успешно!")
            print(f"   ID: {queue.get('id')}")
            return True
        else:
            print(f"\n❌ Ошибка создания очереди: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Проверка очереди VOICEBOT в Yandex Tracker")
    print("=" * 60)

    # Check if queue exists
    if not check_queue_exists():
        print("\n🔧 Попытка создания очереди...")

        # List existing queues first
        queues = list_queues()

        # Try to create queue
        if create_queue():
            print("\n✅ Готово! Можно создавать задачи.")
        else:
            print("\n❌ Не удалось создать очередь.")
            print("Создайте очередь вручную на https://tracker.yandex.ru/")
    else:
        print("\n✅ Все готово для создания задач!")
