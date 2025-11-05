"""Get IAM token from Yandex Cloud using API key"""
import os
import sys
from pathlib import Path
import requests
from dotenv import load_dotenv

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv()


def get_iam_token_from_api_key():
    """Get IAM token using Yandex Cloud API key"""
    api_key = os.getenv("YANDEX_KEY_ID")

    if not api_key:
        print("❌ YANDEX_KEY_ID not found in .env")
        return None

    # Yandex IAM API endpoint
    url = "https://iam.api.cloud.yandex.net/iam/v1/tokens"

    headers = {
        "Content-Type": "application/json"
    }

    payload = {
        "yandexPassportOauthToken": api_key
    }

    try:
        response = requests.post(url, json=payload, headers=headers)

        if response.status_code == 200:
            data = response.json()
            iam_token = data.get("iamToken")
            print(f"✅ IAM Token получен: {iam_token[:20]}...")
            return iam_token
        else:
            print(f"❌ Ошибка получения токена: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None


def check_tracker_access(iam_token):
    """Check if we can access Yandex Tracker with IAM token"""
    url = "https://api.tracker.yandex.net/v2/myself"

    headers = {
        "Authorization": f"Bearer {iam_token}",
        "X-Cloud-Org-ID": os.getenv("YANDEX_CLOUD_ID", ""),
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Доступ к Tracker есть!")
            print(f"User: {data.get('display', 'Unknown')}")
            return True
        else:
            print(f"❌ Нет доступа к Tracker: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Ошибка проверки: {e}")
        return False


def get_tracker_organizations(iam_token):
    """Get list of organizations in Tracker"""
    url = "https://api.tracker.yandex.net/v2/organizations"

    headers = {
        "Authorization": f"Bearer {iam_token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            orgs = response.json()
            print(f"\n✅ Найдено организаций: {len(orgs)}")
            for org in orgs:
                print(f"  • ID: {org.get('id')} | Name: {org.get('name')}")
            return orgs
        else:
            print(f"❌ Ошибка получения организаций: {response.status_code}")
            print(f"Response: {response.text}")
            return []
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return []


if __name__ == "__main__":
    print("=" * 60)
    print("Получение IAM токена для Yandex Tracker")
    print("=" * 60)

    # Try to get IAM token
    iam_token = get_iam_token_from_api_key()

    if iam_token:
        # Check Tracker access
        print("\nПроверка доступа к Tracker...")
        if check_tracker_access(iam_token):
            # Get organizations
            orgs = get_tracker_organizations(iam_token)

            if orgs:
                print("\n" + "=" * 60)
                print("Добавьте в .env:")
                print(f"YANDEX_TRACKER_TOKEN={iam_token}")
                print(f"YANDEX_TRACKER_ORG_ID={orgs[0].get('id')}")
                print("=" * 60)
    else:
        print("\n❌ Не удалось получить IAM токен")
        print("\nВозможные решения:")
        print("1. Проверьте YANDEX_KEY_ID в .env")
        print("2. Получите OAuth токен на https://oauth.yandex.ru/authorize?response_type=token&client_id=<YOUR_CLIENT_ID>")
        print("3. Или используйте CLI: yc iam create-token")
