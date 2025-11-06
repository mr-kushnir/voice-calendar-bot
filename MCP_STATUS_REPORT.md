# Статус MCP Сервера Яндекс Трекера

## Проблема

MCP сервер Яндекс Трекера использует SSE (Server-Sent Events) транспорт, который держит долгоживущие HTTP соединения открытыми. Это создает проблемы с простым stdio proxy для Claude Code.

**URL:** https://db8ss12906fjgalcbbtf.5p9km096.mcpgw.serverless.yandexcloud.net/sse

**Статус сервера:** ✅ Работает
**Статус интеграции:** ⚠️ Требует доработки

## Что было сделано

1. ✅ Создан MCP proxy (`mcp_tracker_proxy.py`)
2. ✅ Настроена конфигурация MCP (`C:\Users\ak\.claude-code\mcp.json`)
3. ✅ Добавлены токены доступа
4. ⚠️ Proxy блокируется при подключении к SSE endpoint

## Техническая проблема

SSE (Server-Sent Events) - это протокол для push-уведомлений, где:
- Клиент открывает HTTP соединение
- Сервер держит его открытым
- Сервер отправляет события по мере их возникновения

Это несовместимо с простой моделью request/response, которую ожидает stdio транспорт MCP.

## Рабочие альтернативы

### Вариант 1: TrackerClient (✅ РАБОТАЕТ СЕЙЧАС)

Используйте существующий `TrackerClient` из `src/tracker/tracker_client.py`:

```python
from src.tracker.tracker_client import TrackerClient

tracker = TrackerClient(
    token=os.getenv('YANDEX_TRACKER_TOKEN'),
    org_id=os.getenv('YANDEX_TRACKER_ORG_ID'),
    queue='EXTEST'
)

# Создать задачу
issue = await tracker.create_issue(
    summary="Новая задача",
    description="Описание",
    type="task"
)

# Добавить комментарий
await tracker.add_comment("EXTEST-31", "Комментарий")

# Получить задачу
task = await tracker.get_issue("EXTEST-31")
```

**Преимущества:**
- ✅ Работает прямо сейчас
- ✅ Простой API
- ✅ Все функции трекера доступны
- ✅ Уже используется в проекте

### Вариант 2: Python скрипты

Используйте готовые скрипты из `scripts/`:
- `scripts/create_deployment_tasks.py` - создание задач
- `scripts/update_extest31.py` - обновление задач
- `scripts/update_extest31_complete.py` - закрытие задач

### Вариант 3: Переделать MCP сервер (требует времени)

Чтобы MCP сервер работал через Claude Code, нужно:

1. **Изменить транспорт на SSE сервере** - добавить поддержку обычных HTTP запросов вместо/вместе с SSE
2. **Или создать WebSocket proxy** - преобразовывать stdio ↔ WebSocket ↔ SSE
3. **Или использовать готовую MCP библиотеку** для SSE транспорта

## Рекомендация

**Используйте TrackerClient** - он работает отлично и покрывает все нужды проекта.

MCP сервер можно доработать позже, если понадобится интеграция на уровне Claude Code UI.

## Что работает прямо сейчас

### Создание задач в Яндекс Трекере

```bash
python scripts/create_deployment_tasks.py
```

### Обновление задач

```bash
python scripts/update_extest31_complete.py
```

### Использование в коде

```python
from src.tracker.tracker_client import TrackerClient
# ... см. примеры выше
```

## Следующие шаги

Если нужна интеграция MCP:

1. Связаться с владельцем SSE сервера
2. Добавить HTTP endpoint для JSON-RPC запросов
3. Или использовать другой транспорт (WebSocket, HTTP POST)

Если нужен просто доступ к трекеру:
- ✅ Используйте TrackerClient - он уже работает!

## Файлы конфигурации

- `C:\Users\ak\.claude-code\mcp.json` - конфигурация MCP (готова)
- `mcp_tracker_proxy.py` - proxy (требует доработки)
- `src/tracker/tracker_client.py` - рабочий клиент (✅)
- `MCP_SETUP.md` - инструкция по настройке

