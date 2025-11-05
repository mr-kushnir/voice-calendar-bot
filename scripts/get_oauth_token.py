"""Get OAuth token for Yandex Tracker using Client ID and Secret"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent.parent))
load_dotenv()

CLIENT_ID = os.getenv("YANDEX_TRACKER_CLIENT_ID")
CLIENT_SECRET = os.getenv("YANDEX_TRACKER_CLIENT_SECRET")


def get_auth_url():
    """Generate OAuth authorization URL"""
    auth_url = (
        f"https://oauth.yandex.ru/authorize"
        f"?response_type=token"
        f"&client_id={CLIENT_ID}"
    )
    return auth_url


if __name__ == "__main__":
    print("=" * 70)
    print("Получение OAuth токена для Yandex Tracker")
    print("=" * 70)

    if not CLIENT_ID or not CLIENT_SECRET:
        print("❌ Client ID или Client Secret не найдены в .env")
        sys.exit(1)

    print(f"\nClient ID: {CLIENT_ID}")
    print(f"Client Secret: {CLIENT_SECRET[:10]}...")

    print("\n" + "=" * 70)
    print("ИНСТРУКЦИЯ:")
    print("=" * 70)
    print("\n1. Откройте эту ссылку в браузере:\n")
    print(f"   {get_auth_url()}\n")
    print("2. Войдите в аккаунт Яндекса (если требуется)")
    print("3. Разрешите доступ приложению")
    print("4. Скопируйте токен из URL после редиректа")
    print("   (будет после #access_token=)")
    print("\n5. Обновите .env файл:")
    print("   YANDEX_TRACKER_TOKEN=ваш_скопированный_токен")
    print("\n" + "=" * 70)

    # Try to open in browser
    try:
        import webbrowser
        print("\n🌐 Открываю браузер...")
        webbrowser.open(get_auth_url())
    except:
        print("\n⚠️  Не удалось открыть браузер автоматически")
        print("   Скопируйте ссылку вручную")
