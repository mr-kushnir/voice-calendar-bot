# Quick Start - Voice Calendar Bot

## 1. Создание очереди VOICEBOT в Yandex Tracker (1 минута)

Яндекс Tracker API требует создания очереди вручную:

1. Откройте https://tracker.yandex.ru/
2. Войдите в организацию **Regulatrix**
3. Нажмите **"Создать очередь"**
4. Заполните:
   - Ключ: **VOICEBOT**
   - Название: **Voice Calendar Bot**
   - Шаблон: **Разработка**
5. Нажмите **"Создать"**

## 2. Создание задач в Tracker

После создания очереди запустите:

```bash
python scripts/create_tracker_tasks.py
```

Это создаст 19 задач для всех функций проекта.

## 3. Запуск тестов

```bash
# Установка зависимостей
pip install -r requirements.txt

# Запуск всех тестов
pytest

# Запуск с coverage
pytest --cov=src --cov-report=html
```

## 4. Запуск бота

```bash
python src/main.py
```

---

**Примечание:** Очередь VOICEBOT требуется только для автоматизации управления задачами. Бот работает независимо от Tracker.
