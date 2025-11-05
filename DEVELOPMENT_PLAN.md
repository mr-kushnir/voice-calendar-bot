# Voice Calendar Bot - Development Plan

## Project Overview
**Timeline:** MVP1 (40 min) + MVP2 (20 min) + Automation (20 min) = ~80 min
**Approach:** Test-Driven Development (TDD)
**Task Management:** Yandex Tracker (Queue: VOICEBOT)

## Development Workflow

### TDD Cycle for Each Feature
1. **Create Tracker Task** → Set status to "open"
2. **Write Tests** (RED) → Tests must fail initially
3. **Implement Code** (GREEN) → Make tests pass
4. **Refactor** → Improve code quality
5. **Update Tracker** → Set status to "testing"
6. **Commit** → Include Tracker key in message
7. **Test Agent** → Auto-validates and closes/reopens task

## Phase 0: Project Setup (10 min)

### Task 0.1: Project Structure
**Tracker Key:** VOICEBOT-1
**Priority:** Critical
**Estimate:** 5 min

**Structure:**
```
voice-calendar-bot/
├── src/
│   ├── __init__.py
│   ├── bot/
│   │   ├── __init__.py
│   │   ├── handlers.py
│   │   ├── middleware.py
│   │   └── responses.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── voice/
│   │   │   ├── __init__.py
│   │   │   ├── stt_service.py
│   │   │   └── tts_service.py
│   │   ├── nlp/
│   │   │   ├── __init__.py
│   │   │   ├── command_parser.py
│   │   │   └── intent_classifier.py
│   │   └── calendar/
│   │       ├── __init__.py
│   │       ├── calendar_aggregator.py
│   │       ├── yandex_provider.py
│   │       ├── google_provider.py
│   │       └── models.py
│   ├── tracker/
│   │   ├── __init__.py
│   │   ├── tracker_client.py
│   │   └── task_manager.py
│   ├── config.py
│   └── main.py
├── tests/
│   ├── __init__.py
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── scripts/
│   └── test_agent.py
├── .env.example
├── .gitignore
├── requirements.txt
├── pytest.ini
├── README.md
└── Dockerfile
```

**Acceptance Criteria:**
- [ ] All directories created
- [ ] requirements.txt with all dependencies
- [ ] .env.example with all required variables
- [ ] pytest.ini configured

### Task 0.2: Dependencies Setup
**Tracker Key:** VOICEBOT-2
**Priority:** Critical
**Estimate:** 5 min

**requirements.txt:**
```
# Telegram Bot
python-telegram-bot==20.7
python-telegram-bot[webhooks]==20.7

# AI Services
openai==1.12.0
elevenlabs==0.2.27

# Calendar Integration
caldav==1.3.9
google-api-python-client==2.108.0
google-auth-httplib2==0.2.0
google-auth-oauthlib==1.2.0

# HTTP & Async
aiohttp==3.9.1
aiofiles==23.2.1

# Date/Time
python-dateutil==2.8.2
pytz==2023.3

# Configuration
python-dotenv==1.0.0
pydantic==2.5.3
pydantic-settings==2.1.0

# Audio Processing
pydub==0.25.1

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
pytest-mock==3.12.0
fakeredis==2.20.0

# Utilities
loguru==0.7.2
```

**Acceptance Criteria:**
- [ ] All dependencies listed
- [ ] Version pinning for stability
- [ ] requirements.txt tested with pip install

---

## Phase 1: MVP1 - Yandex Calendar + Voice (40 min)

### Task 1.1: Data Models
**Tracker Key:** VOICEBOT-3
**Priority:** High
**Estimate:** 5 min

**Test File:** `tests/unit/test_models.py`

**Tests:**
```python
def test_event_creation()
def test_event_serialization()
def test_command_model()
def test_intent_enum()
```

**Implementation:** `src/services/calendar/models.py`

**Acceptance Criteria:**
- [ ] Event dataclass with all fields
- [ ] Command dataclass
- [ ] Intent enum (GET_TODAY, GET_TOMORROW, etc.)
- [ ] JSON serialization/deserialization
- [ ] 100% test coverage

### Task 1.2: Configuration Management
**Tracker Key:** VOICEBOT-4
**Priority:** High
**Estimate:** 5 min

**Test File:** `tests/unit/test_config.py`

**Tests:**
```python
def test_config_loads_from_env()
def test_config_validation()
def test_missing_required_fields_raises_error()
```

**Implementation:** `src/config.py`

**Acceptance Criteria:**
- [ ] Pydantic Settings for type-safe config
- [ ] Environment variable loading
- [ ] Validation of required fields
- [ ] Sensible defaults
- [ ] 100% test coverage

### Task 1.3: Voice STT Service (Whisper)
**Tracker Key:** VOICEBOT-5
**Priority:** High
**Estimate:** 8 min

**Test File:** `tests/unit/test_stt_service.py`

**Tests:**
```python
@pytest.mark.asyncio
async def test_transcribe_audio_file()
async def test_transcribe_handles_invalid_file()
async def test_transcribe_api_error_handling()
async def test_audio_format_conversion()
```

**Implementation:** `src/services/voice/stt_service.py`

**Features:**
- OpenAI Whisper API integration
- Audio format conversion (ogg → mp3)
- Error handling and retries
- Async operations

**Acceptance Criteria:**
- [ ] Accepts audio file path/bytes
- [ ] Returns transcribed text
- [ ] Handles API errors gracefully
- [ ] >= 85% test coverage

### Task 1.4: Voice TTS Service (ElevenLabs)
**Tracker Key:** VOICEBOT-6
**Priority:** High
**Estimate:** 8 min

**Test File:** `tests/unit/test_tts_service.py`

**Tests:**
```python
@pytest.mark.asyncio
async def test_synthesize_speech()
async def test_voice_selection()
async def test_api_error_handling()
async def test_audio_output_format()
```

**Implementation:** `src/services/voice/tts_service.py`

**Features:**
- ElevenLabs API integration
- Voice selection
- Audio streaming
- Caching for common responses

**Acceptance Criteria:**
- [ ] Accepts text input
- [ ] Returns audio bytes (MP3)
- [ ] Configurable voice ID
- [ ] >= 85% test coverage

### Task 1.5: NLP Command Parser
**Tracker Key:** VOICEBOT-7
**Priority:** High
**Estimate:** 10 min

**Test File:** `tests/unit/test_command_parser.py`

**Tests:**
```python
@pytest.mark.asyncio
async def test_parse_today_command()
async def test_parse_tomorrow_command()
async def test_parse_upcoming_hours()
async def test_parse_find_meeting()
async def test_ambiguous_command_handling()
```

**Implementation:** `src/services/nlp/command_parser.py`

**Features:**
- GPT-4 for intent classification
- Entity extraction (dates, times, names)
- Confidence scoring
- Fallback to clarification

**Supported Commands:**
- "что сегодня" → GET_TODAY
- "что завтра" → GET_TOMORROW
- "ближайшие 3 часа" → GET_UPCOMING (hours: 3)
- "когда встреча с Иваном" → FIND_MEETING (name: "Иван")

**Acceptance Criteria:**
- [ ] Parses all 4 command types
- [ ] Extracts parameters correctly
- [ ] Returns Command object
- [ ] >= 80% test coverage

### Task 1.6: Yandex Calendar Provider
**Tracker Key:** VOICEBOT-8
**Priority:** Critical
**Estimate:** 12 min

**Test File:** `tests/unit/test_yandex_provider.py`

**Tests:**
```python
@pytest.mark.asyncio
async def test_connect_to_caldav()
async def test_get_events_today()
async def test_get_events_date_range()
async def test_find_event_by_title()
async def test_handle_connection_errors()
```

**Implementation:** `src/services/calendar/yandex_provider.py`

**Features:**
- CalDAV protocol integration
- Event querying with date ranges
- Event search by title/attendee
- Connection pooling
- Error handling

**Acceptance Criteria:**
- [ ] Connects to Yandex Calendar via CalDAV
- [ ] Retrieves events for date range
- [ ] Finds events by query
- [ ] Converts to common Event model
- [ ] >= 90% test coverage

### Task 1.7: Calendar Aggregator (Yandex only)
**Tracker Key:** VOICEBOT-9
**Priority:** High
**Estimate:** 8 min

**Test File:** `tests/unit/test_calendar_aggregator.py`

**Tests:**
```python
@pytest.mark.asyncio
async def test_get_today_events()
async def test_get_tomorrow_events()
async def test_get_upcoming_hours()
async def test_find_meeting_by_attendee()
```

**Implementation:** `src/services/calendar/calendar_aggregator.py`

**Features:**
- High-level calendar operations
- Date/time calculations
- Event filtering
- Natural language queries

**Acceptance Criteria:**
- [ ] get_today() returns today's events
- [ ] get_tomorrow() returns tomorrow's events
- [ ] get_upcoming(hours) returns events in next N hours
- [ ] find_meeting(query) searches by title/attendee
- [ ] >= 85% test coverage

### Task 1.8: Telegram Bot Handlers
**Tracker Key:** VOICEBOT-10
**Priority:** Critical
**Estimate:** 12 min

**Test File:** `tests/integration/test_bot_handlers.py`

**Tests:**
```python
@pytest.mark.asyncio
async def test_voice_message_handler()
async def test_start_command()
async def test_help_command()
async def test_end_to_end_voice_flow()
```

**Implementation:** `src/bot/handlers.py`

**Features:**
- Voice message handler
- Command routing
- Error handling
- Response formatting

**Flow:**
1. Receive voice message
2. Download audio → STT
3. Parse command → NLP
4. Query calendar
5. Format response
6. TTS → Send voice

**Acceptance Criteria:**
- [ ] Handles voice messages
- [ ] Processes all 4 command types
- [ ] Sends voice responses
- [ ] Handles errors gracefully
- [ ] >= 80% test coverage

### Task 1.9: Main Bot Application
**Tracker Key:** VOICEBOT-11
**Priority:** Critical
**Estimate:** 5 min

**Test File:** `tests/integration/test_main.py`

**Implementation:** `src/main.py`

**Features:**
- Application bootstrap
- Dependency injection
- Graceful shutdown
- Logging setup

**Acceptance Criteria:**
- [ ] Starts bot in polling mode
- [ ] Initializes all services
- [ ] Handles SIGINT/SIGTERM
- [ ] Structured logging
- [ ] >= 70% test coverage

---

## Phase 2: MVP2 - Google Calendar (20 min)

### Task 2.1: Google Calendar Provider
**Tracker Key:** VOICEBOT-12
**Priority:** High
**Estimate:** 12 min

**Test File:** `tests/unit/test_google_provider.py`

**Tests:**
```python
@pytest.mark.asyncio
async def test_authenticate_with_oauth()
async def test_get_events_date_range()
async def test_find_event()
async def test_token_refresh()
```

**Implementation:** `src/services/calendar/google_provider.py`

**Features:**
- OAuth 2.0 authentication
- Google Calendar API v3
- Event querying
- Token refresh

**Acceptance Criteria:**
- [ ] OAuth flow working
- [ ] Retrieves events
- [ ] Converts to common Event model
- [ ] >= 90% test coverage

### Task 2.2: Calendar Aggregator Enhancement
**Tracker Key:** VOICEBOT-13
**Priority:** High
**Estimate:** 8 min

**Test File:** `tests/unit/test_calendar_aggregator_multi.py`

**Tests:**
```python
@pytest.mark.asyncio
async def test_aggregate_multiple_calendars()
async def test_deduplication_logic()
async def test_event_merging()
async def test_source_attribution()
```

**Implementation:** Update `src/services/calendar/calendar_aggregator.py`

**Features:**
- Query both calendars concurrently
- Merge results by datetime
- Deduplicate based on title + time
- Attribute source to each event

**Deduplication Algorithm:**
```python
def are_duplicates(e1: Event, e2: Event) -> bool:
    return (
        e1.title.lower() == e2.title.lower() and
        abs((e1.start - e2.start).total_seconds()) < 300  # 5 min tolerance
    )
```

**Acceptance Criteria:**
- [ ] Queries both calendars
- [ ] Deduplicates events
- [ ] Maintains source attribution
- [ ] >= 85% test coverage

---

## Phase 3: Automation - Yandex Tracker + Test Agent (20 min)

### Task 3.1: Yandex Tracker Client
**Tracker Key:** VOICEBOT-14
**Priority:** High
**Estimate:** 10 min

**Test File:** `tests/unit/test_tracker_client.py`

**Tests:**
```python
@pytest.mark.asyncio
async def test_create_task()
async def test_update_task_status()
async def test_add_comment()
async def test_get_tasks_by_status()
async def test_link_commits()
```

**Implementation:** `src/tracker/tracker_client.py`

**Features:**
- REST API integration
- Task CRUD operations
- Status transitions
- Comment management
- Commit linking

**API Endpoints:**
- POST `/v2/issues` - Create task
- PATCH `/v2/issues/{key}` - Update task
- GET `/v2/issues` - List tasks
- POST `/v2/issues/{key}/comments` - Add comment

**Acceptance Criteria:**
- [ ] Creates tasks with title, description, priority
- [ ] Updates task status
- [ ] Queries tasks by status
- [ ] Adds comments
- [ ] >= 85% test coverage

### Task 3.2: Task Manager
**Tracker Key:** VOICEBOT-15
**Priority:** Medium
**Estimate:** 5 min

**Test File:** `tests/unit/test_task_manager.py`

**Implementation:** `src/tracker/task_manager.py`

**Features:**
- High-level task operations
- Workflow management
- Batch operations

**Acceptance Criteria:**
- [ ] create_feature_tasks() creates all MVP tasks
- [ ] get_testing_tasks() filters by status
- [ ] >= 80% test coverage

### Task 3.3: Test Agent
**Tracker Key:** VOICEBOT-16
**Priority:** Critical
**Estimate:** 15 min

**Test File:** `tests/unit/test_test_agent.py`

**Implementation:** `scripts/test_agent.py`

**Features:**
- Poll Tracker every 60s
- Detect tasks in "testing"
- Run pytest with coverage
- Update task status based on results
- Add detailed comments

**Algorithm:**
```python
while True:
    tasks = get_tasks_in_testing()
    for task in tasks:
        module = extract_module_from_task(task)
        result = run_pytest(module)
        if result.passed and result.coverage >= 80:
            update_status(task, "closed")
            add_comment(task, f"✅ All tests passed. Coverage: {result.coverage}%")
        else:
            update_status(task, "open")
            add_comment(task, f"❌ Tests failed:\n{result.failures}")
    sleep(60)
```

**Acceptance Criteria:**
- [ ] Polls Tracker continuously
- [ ] Runs tests for relevant modules
- [ ] Updates status correctly
- [ ] Adds informative comments
- [ ] Handles errors gracefully
- [ ] >= 75% test coverage

---

## Phase 4: CI/CD & Documentation (15 min)

### Task 4.1: GitHub Actions Workflow
**Tracker Key:** VOICEBOT-17
**Priority:** Medium
**Estimate:** 8 min

**File:** `.github/workflows/ci.yml`

**Features:**
- Run tests on push/PR
- Coverage reporting
- Lint checks (flake8, black)
- Type checking (mypy)
- Security scan (bandit)

**Stages:**
1. Lint & Type Check
2. Unit Tests
3. Integration Tests
4. Coverage Report (upload to Codecov)
5. Build Docker Image

**Acceptance Criteria:**
- [ ] CI runs on every push
- [ ] Coverage reports generated
- [ ] Docker image builds successfully

### Task 4.2: README Documentation
**Tracker Key:** VOICEBOT-18
**Priority:** High
**Estimate:** 10 min

**File:** `README.md`

**Sections:**
1. Project Overview
2. Features
3. Architecture Diagram
4. Prerequisites
5. Installation
6. Configuration (.env setup)
7. Running Locally
8. Running Tests
9. Deployment
10. Usage Examples
11. Yandex Tracker Integration
12. Test Agent Setup
13. Troubleshooting
14. Contributing
15. License

**Acceptance Criteria:**
- [ ] Comprehensive setup instructions
- [ ] Code examples for all commands
- [ ] Deployment guide
- [ ] Architecture diagram

### Task 4.3: Deployment Script
**Tracker Key:** VOICEBOT-19
**Priority:** Medium
**Estimate:** 5 min

**File:** `deploy.sh`

**Features:**
- Environment validation
- Dependency installation
- Database migration (if needed)
- Service restart
- Health check

**Acceptance Criteria:**
- [ ] One-command deployment
- [ ] Error handling
- [ ] Rollback capability

---

## Testing Strategy

### Coverage Targets
- **Overall:** >= 80%
- **Critical Paths:** >= 90%
  - Calendar providers
  - Tracker client
- **Services:** >= 85%
  - Voice services
  - NLP services
  - Aggregator
- **Handlers:** >= 80%

### Test Types
1. **Unit Tests:** Mock external dependencies
2. **Integration Tests:** Test component interactions
3. **E2E Tests:** Full flow with mocked Telegram

### Fixtures
- `tests/fixtures/audio_samples/` - Sample voice messages
- `tests/fixtures/calendar_responses.json` - Mock calendar data
- `tests/fixtures/mock_events.py` - Event factories

---

## Git Workflow

### Branch Strategy
- `main` - Production-ready code
- `develop` - Integration branch
- `feature/VOICEBOT-X` - Feature branches

### Commit Message Format
```
VOICEBOT-X: <type>: <subject>

<body>

<footer>
```

**Types:** feat, fix, test, refactor, docs, chore

**Example:**
```
VOICEBOT-5: feat: Implement Whisper STT service

- Add OpenAI Whisper integration
- Support audio format conversion
- Implement error handling and retries

Tests: tests/unit/test_stt_service.py
Coverage: 87%
```

---

## Risk Management

### High-Risk Areas
1. **API Rate Limits**
   - Mitigation: Implement caching, request throttling
2. **Audio Processing Latency**
   - Mitigation: Optimize file sizes, use streaming
3. **Calendar API Failures**
   - Mitigation: Retry logic, graceful degradation
4. **Test Agent False Positives**
   - Mitigation: Manual review step, detailed logging

---

## Success Criteria

### MVP1 Complete When:
- [ ] All 11 tasks (VOICEBOT-1 to VOICEBOT-11) closed
- [ ] Voice input/output working
- [ ] All 4 commands functional with Yandex Calendar
- [ ] Test coverage >= 80%
- [ ] No critical bugs

### MVP2 Complete When:
- [ ] Tasks VOICEBOT-12, VOICEBOT-13 closed
- [ ] Google Calendar integrated
- [ ] Deduplication working
- [ ] Test coverage >= 80%

### Project Complete When:
- [ ] All 19 tasks closed
- [ ] Test Agent running
- [ ] CI/CD operational
- [ ] Documentation complete
- [ ] Deployment script working

---

## Timeline Summary

| Phase | Tasks | Estimate | Cumulative |
|-------|-------|----------|------------|
| Phase 0: Setup | 2 | 10 min | 10 min |
| Phase 1: MVP1 | 9 | 40 min | 50 min |
| Phase 2: MVP2 | 2 | 20 min | 70 min |
| Phase 3: Automation | 3 | 20 min | 90 min |
| Phase 4: CI/CD | 3 | 15 min | 105 min |

**Total Estimate:** ~105 min (including buffer)

---

## Next Steps

1. ✅ Review and approve architecture
2. ✅ Review and approve development plan
3. → **Create Yandex Tracker tasks** (all 19 tasks)
4. → Start Phase 0: Project setup
5. → Begin TDD cycle for each task

---

**Last Updated:** 2025-11-05
**Status:** APPROVED
**Version:** 1.0
