"""Create deployment tasks in Yandex Tracker"""
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tracker.tracker_client import TrackerClient
from dotenv import load_dotenv

load_dotenv()


async def create_deployment_tasks():
    tracker = TrackerClient(
        token=os.getenv('YANDEX_TRACKER_TOKEN'),
        org_id=os.getenv('YANDEX_TRACKER_ORG_ID'),
        queue='EXTEST'
    )

    # New tasks for deployment phase
    tasks = [
        {
            'summary': 'EXTEST-26: Yandex Cloud Infrastructure Setup',
            'description': '''Настройка инфраструктуры Yandex Cloud для развертывания бота

**Задачи:**
- Установить Yandex Cloud CLI
- Настроить конфигурацию (folder, subnet)
- Создать сеть и подсети
- Настроить SSH ключи

**Результат:**
- Yandex Cloud CLI v0.169.0
- Folder ID: b1gm1nh37o3isrorujke
- Subnet ID: e9b4i1js8g2tol33omp8
- Zone: ru-central1-a''',
            'priority': 'critical'
        },
        {
            'summary': 'EXTEST-27: Docker Containerization',
            'description': '''Контейнеризация приложения с помощью Docker

**Файлы:**
- Dockerfile (Python 3.11-slim)
- docker-compose.yml (multi-service)
- .dockerignore

**Сервисы:**
- bot: Основной Telegram бот
- test-agent: Агент тестирования (polling)
- webhook-test-agent: Агент тестирования (webhook)

**Результат:**
- Docker образ voice-calendar-bot:latest
- Готов к развертыванию на VM''',
            'priority': 'critical'
        },
        {
            'summary': 'EXTEST-28: Deployment Automation Scripts',
            'description': '''Создание скриптов автоматического развертывания

**Скрипты:**
- scripts/deploy_yandex_cloud.sh (Bash)
- scripts/deploy_yandex_cloud.py (Python, кроссплатформенный)

**Функции:**
- Сборка Docker образа
- Создание VM в Yandex Cloud
- Копирование файлов на VM
- Настройка systemd сервиса
- Автоматический запуск

**Результат:**
- Полностью автоматизированный деплой в один клик''',
            'priority': 'critical'
        },
        {
            'summary': 'EXTEST-29: Deployment Documentation',
            'description': '''Документация по развертыванию на Yandex Cloud

**Документы:**
- docs/YANDEX_CLOUD_DEPLOYMENT.md (350+ строк)
- DEPLOYMENT_STATUS.md
- README.md (обновлен с инструкциями)

**Содержание:**
- Настройка Yandex Cloud CLI
- Создание сети и VM
- 3 варианта развертывания
- Мониторинг и управление
- Troubleshooting
- Оценка стоимости (~900-1200р/мес)

**Результат:**
- Полное руководство для развертывания''',
            'priority': 'normal'
        },
        {
            'summary': 'EXTEST-30: Production Deployment to Yandex Cloud',
            'description': '''Развертывание бота на production в Yandex Cloud

**Задачи:**
- Собрать Docker образ
- Создать VM instance (2 vCPU, 2GB RAM, 20GB disk)
- Развернуть приложение на VM
- Настроить автозапуск через systemd
- Проверить работоспособность

**Параметры VM:**
- Name: voice-calendar-bot
- Zone: ru-central1-a
- Platform: standard-v3
- Resources: 2 cores, 2GB memory, 20GB disk
- Network: default (enpa3gbb6lddvdaihjil)
- Subnet: e9b4i1js8g2tol33omp8

**Проверка:**
- Бот отвечает на команды
- Логи доступны
- Systemd service работает
- Health checks проходят''',
            'priority': 'critical'
        }
    ]

    print('=== CREATING DEPLOYMENT TASKS ===\n')

    for task_data in tasks:
        try:
            task = await tracker.create_task(
                summary=task_data['summary'],
                description=task_data['description'],
                priority=task_data['priority']
            )
            print(f'Created {task.key}: {task.summary}')
            print(f'  Status: {task.status}')
            print()
        except Exception as e:
            print(f'Failed to create task: {task_data["summary"]}')
            print(f'  Error: {str(e)}')
            print()


if __name__ == "__main__":
    asyncio.run(create_deployment_tasks())
