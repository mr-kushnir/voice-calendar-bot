"""Task Manager for Yandex Tracker"""
from dataclasses import dataclass
from typing import List
from loguru import logger
from .tracker_client import TrackerClient, TrackerTask


@dataclass
class FeatureTask:
    """Feature task definition"""
    key: str
    title: str
    description: str
    priority: str
    estimate: str


class TaskManager:
    """High-level task management operations"""

    def __init__(self, tracker_client: TrackerClient):
        """
        Initialize Task Manager

        Args:
            tracker_client: TrackerClient instance
        """
        self.client = tracker_client

    async def create_feature_tasks(self) -> List[TrackerTask]:
        """
        Create all MVP feature tasks in Yandex Tracker

        Returns:
            List of created TrackerTask objects
        """
        feature_tasks = self._define_feature_tasks()
        created_tasks = []

        logger.info(f"Creating {len(feature_tasks)} tasks in Yandex Tracker...")

        for feature in feature_tasks:
            try:
                task = await self.client.create_task(
                    summary=feature.title,
                    description=feature.description,
                    priority=feature.priority
                )
                created_tasks.append(task)
                logger.info(f"Created task {task.key}: {task.summary}")
            except Exception as e:
                logger.error(f"Failed to create task {feature.key}: {e}")

        logger.info(f"Successfully created {len(created_tasks)} tasks")
        return created_tasks

    async def get_testing_tasks(self) -> List[TrackerTask]:
        """
        Get all tasks in 'testing' status

        Returns:
            List of TrackerTask objects in testing status
        """
        return await self.client.get_tasks_by_status("testing")

    def extract_module_from_task(self, task: TrackerTask) -> str:
        """
        Extract module path from task summary/description

        Args:
            task: TrackerTask object

        Returns:
            Module path for testing (e.g., 'src/services/voice')
        """
        summary_lower = task.summary.lower()

        # Map task keywords to module paths
        module_mapping = {
            "project structure": "src",
            "dependencies": "src",
            "data models": "src/services/calendar",
            "configuration": "src",
            "stt": "src/services/voice",
            "tts": "src/services/voice",
            "voice": "src/services/voice",
            "nlp": "src/services/nlp",
            "command parser": "src/services/nlp",
            "yandex calendar": "src/services/calendar",
            "google calendar": "src/services/calendar",
            "calendar aggregator": "src/services/calendar",
            "telegram": "src/bot",
            "bot handler": "src/bot",
            "tracker": "src/tracker",
            "test agent": "scripts"
        }

        for keyword, module in module_mapping.items():
            if keyword in summary_lower:
                return module

        # Default fallback
        return "src"

    def _define_feature_tasks(self) -> List[FeatureTask]:
        """
        Define all feature tasks from development plan

        Returns:
            List of FeatureTask objects
        """
        queue_key = self.client.queue
        return [
            # Фаза 0: Настройка проекта
            FeatureTask(
                key=f"{queue_key}-1",
                title="Настройка структуры проекта",
                description="Создание структуры директорий, requirements.txt, .env.example, pytest.ini",
                priority="critical",
                estimate="5 min"
            ),
            FeatureTask(
                key=f"{queue_key}-2",
                title="Установка зависимостей",
                description="Установка и настройка всех зависимостей: telegram bot, OpenAI, ElevenLabs, CalDAV, Google Calendar",
                priority="critical",
                estimate="5 min"
            ),
            # Фаза 1: MVP1
            FeatureTask(
                key=f"{queue_key}-3",
                title="Модели данных",
                description="Реализация моделей Event, Command и Intent с сериализацией",
                priority="critical",
                estimate="5 min"
            ),
            FeatureTask(
                key=f"{queue_key}-4",
                title="Управление конфигурацией",
                description="Реализация Pydantic настроек для типобезопасной конфигурации из .env",
                priority="critical",
                estimate="5 min"
            ),
            FeatureTask(
                key=f"{queue_key}-5",
                title="Сервис распознавания речи (Whisper)",
                description="Интеграция OpenAI Whisper для преобразования речи в текст с конвертацией форматов аудио",
                priority="critical",
                estimate="8 min"
            ),
            FeatureTask(
                key=f"{queue_key}-6",
                title="Сервис синтеза речи (ElevenLabs)",
                description="Интеграция ElevenLabs для преобразования текста в речь с выбором голоса",
                priority="critical",
                estimate="8 min"
            ),
            FeatureTask(
                key=f"{queue_key}-7",
                title="Парсер NLP команд",
                description="Интеграция GPT-4 для классификации намерений и извлечения сущностей (сегодня, завтра, ближайшие, найти)",
                priority="critical",
                estimate="10 min"
            ),
            FeatureTask(
                key=f"{queue_key}-8",
                title="Провайдер Яндекс.Календарь",
                description="Интеграция CalDAV для Яндекс.Календаря с запросами событий и поиском",
                priority="critical",
                estimate="12 min"
            ),
            FeatureTask(
                key=f"{queue_key}-9",
                title="Агрегатор календарей (только Яндекс)",
                description="Высокоуровневые операции с календарем: get_today, get_tomorrow, get_upcoming, find_meeting",
                priority="critical",
                estimate="8 min"
            ),
            FeatureTask(
                key=f"{queue_key}-10",
                title="Обработчики Telegram бота",
                description="Обработчик голосовых сообщений с полным циклом: STT → NLP → Calendar → TTS",
                priority="critical",
                estimate="12 min"
            ),
            FeatureTask(
                key=f"{queue_key}-11",
                title="Главное приложение бота",
                description="Инициализация приложения, внедрение зависимостей, graceful shutdown, логирование",
                priority="critical",
                estimate="5 min"
            ),
            # Фаза 2: MVP2
            FeatureTask(
                key=f"{queue_key}-12",
                title="Провайдер Google Calendar",
                description="Интеграция Google Calendar API v3 с OAuth 2.0 аутентификацией",
                priority="critical",
                estimate="12 min"
            ),
            FeatureTask(
                key=f"{queue_key}-13",
                title="Расширение агрегатора календарей",
                description="Поддержка нескольких календарей с дедупликацией и атрибуцией источника",
                priority="critical",
                estimate="8 min"
            ),
            # Фаза 3: Автоматизация
            FeatureTask(
                key=f"{queue_key}-14",
                title="Клиент Яндекс.Трекера",
                description="Интеграция REST API для CRUD задач, обновления статусов и связывания коммитов",
                priority="critical",
                estimate="10 min"
            ),
            FeatureTask(
                key=f"{queue_key}-15",
                title="Менеджер задач",
                description="Высокоуровневые операции с задачами и управление рабочим процессом",
                priority="critical",
                estimate="5 min"
            ),
            FeatureTask(
                key=f"{queue_key}-16",
                title="Тестовый агент",
                description="Автоматизированный агент тестирования: опрос Трекера, запуск pytest, обновление статусов задач",
                priority="critical",
                estimate="15 min"
            ),
            # Фаза 4: CI/CD
            FeatureTask(
                key=f"{queue_key}-17",
                title="GitHub Actions конвейер",
                description="CI/CD пайплайн с тестами, coverage, линтингом и Docker сборками",
                priority="critical",
                estimate="8 min"
            ),
            FeatureTask(
                key=f"{queue_key}-18",
                title="Документация README",
                description="Полная документация с инструкциями по настройке, использованию и развертыванию",
                priority="critical",
                estimate="10 min"
            ),
            FeatureTask(
                key=f"{queue_key}-19",
                title="Скрипт развертывания",
                description="Скрипт развертывания одной командой с валидацией и проверкой работоспособности",
                priority="critical",
                estimate="5 min"
            )
        ]
