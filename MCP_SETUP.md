# Настройка MCP сервера Яндекс Трекера

## Что сделано

### 1. Создан MCP Proxy (mcp_tracker_proxy.py)
Proxy сервер на Python, который:
- Подключается к SSE серверу Яндекс Трекера
- Преобразует stdio транспорт в HTTP/SSE запросы
- Обеспечивает совместимость с Claude Code

### 2. Конфигурация MCP
Файл: `C:\Users\ak\.claude-code\mcp.json`

```json
{
  "mcpServers": {
    "yandex-tracker": {
      "command": "python",
      "args": [
        "D:\\claude projects\\exam\\mcp_tracker_proxy.py"
      ],
      "env": {
        "YANDEX_TRACKER_TOKEN": "",
        "YANDEX_TRACKER_ORG_ID": ""
      }
    }
  }
}
```

## Как использовать

### Шаг 1: Перезапустить Claude Code
После создания конфигурации нужно перезапустить Claude Code, чтобы он загрузил новый MCP сервер.

### Шаг 2: Проверить подключение
После перезапуска MCP сервер "yandex-tracker" должен появиться в списке доступных инструментов.

### Шаг 3: Использовать инструменты
Теперь вы можете использовать MCP инструменты для работы с Яндекс Трекером напрямую через Claude Code.

## Ручное тестирование proxy

Для тестирования proxy можно использовать:

```bash
# Запустить proxy
python mcp_tracker_proxy.py

# В другом терминале отправить JSON-RPC запрос:
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' | python mcp_tracker_proxy.py
```

## SSE сервер

**URL:** https://db8ss12906fjgalcbbtf.5p9km096.mcpgw.serverless.yandexcloud.net/sse

**Статус:** ✅ Работает

**Транспорт:** Server-Sent Events (SSE)

## Доступные инструменты (после подключения)

MCP сервер предоставляет инструменты для:
- Получения списка задач
- Создания новых задач
- Обновления статуса задач
- Добавления комментариев
- И другие операции с Яндекс Трекером

## Альтернативный вариант

Если MCP не подключается автоматически, вы можете:

1. **Использовать TrackerClient напрямую** (текущий подход):
   ```python
   from src.tracker.tracker_client import TrackerClient
   tracker = TrackerClient(token=..., org_id=..., queue='EXTEST')
   await tracker.create_issue(...)
   ```

2. **Создать слэш-команду** для работы с трекером через MCP

3. **Использовать Python скрипты** из директории `scripts/`

## Troubleshooting

### MCP сервер не подключается
- Проверьте путь к proxy в mcp.json
- Убедитесь, что Python установлен и доступен в PATH
- Проверьте логи Claude Code

### Таймауты при запросах
- SSE сервер может иметь cold start delay
- Увеличьте timeout в proxy (по умолчанию 30 секунд)

### Отсутствуют переменные окружения
- Добавьте YANDEX_TRACKER_TOKEN и YANDEX_TRACKER_ORG_ID в .env
- Или укажите их напрямую в mcp.json (не рекомендуется для безопасности)

## См. также

- `test_mcp_tracker.py` - скрипт для тестирования MCP сервера
- `src/tracker/tracker_client.py` - прямой клиент Яндекс Трекера
- `.env` - переменные окружения для токенов
