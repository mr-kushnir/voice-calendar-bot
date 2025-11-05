"""Copy configuration from existing queue to create VOICEBOT"""
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


def get_queue_config(queue_key):
    """Get configuration from existing queue"""
    url = f"https://api.tracker.yandex.net/v2/queues/{queue_key}"

    headers = {
        "Authorization": f"OAuth {IAM_TOKEN}",
        "X-Cloud-Org-Id": ORG_ID,
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    return None


def get_user_info():
    """Get current user"""
    url = "https://api.tracker.yandex.net/v2/myself"

    headers = {
        "Authorization": f"OAuth {IAM_TOKEN}",
        "X-Cloud-Org-Id": ORG_ID,
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json().get('uid')
    except:
        pass
    return None


def create_voicebot_queue(template_config):
    """Create VOICEBOT queue based on template"""
    url = "https://api.tracker.yandex.net/v2/queues"

    headers = {
        "Authorization": f"OAuth {IAM_TOKEN}",
        "X-Cloud-Org-Id": ORG_ID,
        "Content-Type": "application/json"
    }

    lead = get_user_info()
    if not lead:
        print("❌ Не удалось получить пользователя")
        return False

    payload = {
        "key": "VOICEBOT",
        "name": "Voice Calendar Bot",
        "lead": lead,
        "defaultType": template_config.get("defaultType", {}).get("key", "task"),
        "defaultPriority": template_config.get("defaultPriority", {}).get("key", "normal"),
        "issueTypesConfig": template_config.get("issueTypesConfig", [])
    }

    print(f"\n📝 Создаю очередь VOICEBOT с конфигурацией:")
    print(f"   Lead: {lead}")
    print(f"   DefaultType: {payload['defaultType']}")
    print(f"   IssueTypes: {len(payload['issueTypesConfig'])}")

    try:
        response = requests.post(url, json=payload, headers=headers)

        if response.status_code == 201:
            print(f"\n✅ Очередь VOICEBOT создана успешно!")
            return True
        else:
            print(f"\n❌ Ошибка создания: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Создание очереди VOICEBOT на основе EXTEST")
    print("=" * 60)

    # Get EXTEST configuration
    print("\n1. Получаю конфигурацию очереди EXTEST...")
    config = get_queue_config("EXTEST")

    if config:
        print(f"✅ Конфигурация получена")
        print(f"   Workflow: {config.get('issueTypesConfig', [{}])[0].get('workflow', {}).get('key') if config.get('issueTypesConfig') else 'N/A'}")

        # Create VOICEBOT
        print("\n2. Создаю очередь VOICEBOT...")
        if create_voicebot_queue(config):
            print("\n✅ Готово! Теперь можно создавать задачи.")
        else:
            print("\n❌ Не удалось создать очередь.")
    else:
        print("❌ Не удалось получить конфигурацию EXTEST")
