# Voice Calendar Bot - Architecture

## Overview
Telegram bot with voice interface for Yandex Calendar and Google Calendar management using TDD approach and Yandex Tracker integration.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Telegram Bot API                        │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│                   Bot Handler Layer                          │
│  - Voice message handler                                     │
│  - Command router                                            │
│  - Response formatter                                        │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│                  Service Orchestrator                        │
│  - Request processing pipeline                               │
│  - Error handling & logging                                  │
└──┬───────────────┬──────────────────┬───────────────────────┘
   │               │                  │
   ▼               ▼                  ▼
┌─────────┐  ┌──────────┐  ┌────────────────────┐
│  Voice  │  │   NLP    │  │  Calendar Service  │
│ Service │  │ Service  │  │    (Aggregator)    │
└─────────┘  └──────────┘  └──────┬─────────────┘
                                   │
                        ┌──────────┴──────────┐
                        ▼                     ▼
                ┌──────────────┐      ┌─────────────┐
                │    Yandex    │      │   Google    │
                │   Calendar   │      │  Calendar   │
                │   Provider   │      │   Provider  │
                └──────────────┘      └─────────────┘
```

## Core Components

### 1. Bot Handler Layer (`src/bot/`)
**Purpose:** Telegram interaction management

**Components:**
- `handlers.py` - Voice message & command handlers
- `middleware.py` - Authentication, rate limiting
- `responses.py` - Response formatting & voice generation

**Dependencies:** python-telegram-bot

### 2. Voice Service (`src/services/voice/`)
**Purpose:** Speech-to-Text and Text-to-Speech

**Components:**
- `stt_service.py` - OpenAI Whisper integration
- `tts_service.py` - ElevenLabs integration
- `audio_processor.py` - Audio format conversion

**Dependencies:** openai, elevenlabs, pydub

### 3. NLP Service (`src/services/nlp/`)
**Purpose:** Command parsing and intent recognition

**Components:**
- `command_parser.py` - Extract commands from text
- `intent_classifier.py` - Classify user intent (GPT-4)
- `entity_extractor.py` - Extract dates, times, names

**Supported Intents:**
- `GET_TODAY` - "что сегодня"
- `GET_TOMORROW` - "что завтра"
- `GET_UPCOMING` - "ближайшие N часов"
- `FIND_MEETING` - "когда встреча с X"
- `CREATE_EVENT` - "создать встречу"

### 4. Calendar Service (`src/services/calendar/`)
**Purpose:** Unified calendar interface

**Components:**
- `calendar_aggregator.py` - Combine multiple calendars
- `yandex_provider.py` - Yandex Calendar (CalDAV)
- `google_provider.py` - Google Calendar API
- `deduplication.py` - Remove duplicate events
- `models.py` - Common event models

**Key Methods:**
```python
class CalendarAggregator:
    async def get_events(self, start: datetime, end: datetime) -> List[Event]
    async def find_event(self, query: str) -> Optional[Event]
    async def create_event(self, event: Event) -> Event
```

### 5. Yandex Tracker Integration (`src/tracker/`)
**Purpose:** Task management automation

**Components:**
- `tracker_client.py` - API client
- `task_manager.py` - Task CRUD operations
- `workflow.py` - Status transitions

**Workflow:**
1. Create tasks for each feature
2. Link commits to tasks
3. Test Agent monitors "testing" status
4. Auto-update on test results

### 6. Test Agent (`scripts/test_agent.py`)
**Purpose:** Automated testing and status updates

**Workflow:**
```
1. Poll Yandex Tracker for tasks in "testing"
2. Run pytest for related modules
3. Collect coverage reports
4. Update task status:
   - ✅ "closed" if tests pass & coverage >= 80%
   - ❌ "open" with comment if tests fail
5. Sleep 60s, repeat
```

## Data Models

### Event Model
```python
@dataclass
class Event:
    id: str
    title: str
    start: datetime
    end: datetime
    description: Optional[str]
    location: Optional[str]
    attendees: List[str]
    source: str  # 'yandex' | 'google'
    raw_data: dict
```

### Command Model
```python
@dataclass
class Command:
    intent: str
    parameters: dict
    original_text: str
    confidence: float
```

## Configuration Management

### Environment Variables (.env)
```
# Bot
TELEGRAM_BOT_TOKEN=
LOG_LEVEL=INFO

# AI Services
OPENAI_API_KEY=
ELEVENLABS_API_KEY=
ELEVENLABS_VOICE_ID=

# Calendars
YANDEX_CALENDAR_LOGIN=
YANDEX_CALENDAR_PASSWORD=
YANDEX_CALENDAR_URL=https://caldav.yandex.ru

GOOGLE_CALENDAR_CREDENTIALS_PATH=credentials.json
GOOGLE_CALENDAR_TOKEN_PATH=token.json

# Yandex Tracker
YANDEX_TRACKER_TOKEN=
YANDEX_TRACKER_ORG_ID=
YANDEX_TRACKER_QUEUE=VOICEBOT

# Test Agent
TEST_AGENT_POLL_INTERVAL=60
TEST_AGENT_COVERAGE_THRESHOLD=80
```

## Testing Strategy

### Test Structure
```
tests/
├── unit/
│   ├── test_voice_service.py
│   ├── test_nlp_service.py
│   ├── test_calendar_aggregator.py
│   ├── test_yandex_provider.py
│   └── test_google_provider.py
├── integration/
│   ├── test_bot_handlers.py
│   ├── test_calendar_workflow.py
│   └── test_tracker_integration.py
└── fixtures/
    ├── audio_samples/
    ├── calendar_responses.json
    └── mock_events.py
```

### TDD Cycle
1. **RED**: Write failing test
2. **GREEN**: Implement minimal code to pass
3. **REFACTOR**: Improve code quality
4. **COMMIT**: Link to Tracker task

### Coverage Requirements
- Overall: >= 80%
- Critical paths (calendar operations): >= 90%
- Voice/NLP services: >= 75%

## Security Considerations

1. **API Keys**: Store in .env, never commit
2. **User Authentication**: Telegram user ID whitelist
3. **Rate Limiting**: Max 10 requests/minute per user
4. **Data Privacy**: No persistent user data storage
5. **Calendar Tokens**: Encrypted at rest

## Performance Requirements

- Voice recognition: < 3s
- Calendar query: < 2s
- Voice response generation: < 4s
- Total response time: < 10s
- Concurrent users: Up to 50

## Error Handling

### Error Categories
1. **User Errors**: Invalid commands → Helpful voice response
2. **Service Errors**: API failures → Retry with exponential backoff
3. **System Errors**: Critical failures → Alert admin + graceful degradation

### Logging
- Structured JSON logs
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Include: user_id, timestamp, request_id, duration

## Deployment

### Prerequisites
- Python 3.11+
- ffmpeg (for audio processing)
- SSL certificates (for webhook mode)

### Deployment Options
1. **Polling Mode**: Simple, for development
2. **Webhook Mode**: Production, requires HTTPS

### Docker Support
- Multi-stage builds
- Separate containers: bot, test_agent
- Docker Compose for local development

## Future Enhancements (Post-MVP)

1. Natural language event creation
2. Event reminders
3. Multi-user support with permissions
4. Calendar sharing
5. Meeting scheduling assistant
6. Integration with more calendar providers
7. Web dashboard for analytics

## Technology Stack Summary

| Component | Technology | Version |
|-----------|-----------|---------|
| Runtime | Python | 3.11+ |
| Bot Framework | python-telegram-bot | 20.7 |
| STT | OpenAI Whisper | 1.12.0 |
| TTS | ElevenLabs | 0.2.27 |
| NLP | GPT-4 | OpenAI API |
| Yandex Calendar | caldav | 1.3.9 |
| Google Calendar | google-api-python-client | Latest |
| Testing | pytest + pytest-asyncio | Latest |
| Coverage | pytest-cov | Latest |
| HTTP Client | aiohttp | Latest |
| Date/Time | python-dateutil | Latest |

## Development Milestones

### MVP1 (40 min)
- Voice input/output ✓
- Yandex Calendar integration ✓
- Basic commands (today, tomorrow, upcoming, find) ✓
- TDD with 80% coverage ✓

### MVP2 (20 min)
- Google Calendar integration ✓
- Unified calendar service ✓
- Deduplication logic ✓

### Automation
- Yandex Tracker integration ✓
- Test Agent ✓
- CI/CD pipeline ✓

---

**Last Updated:** 2025-11-05
**Status:** DRAFT
**Version:** 1.0
