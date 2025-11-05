"""Unit tests for Calendar Aggregator"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from src.services.calendar.aggregator import CalendarAggregator
from src.services.calendar.models import Event


@pytest.fixture
def aggregator():
    """CalendarAggregator fixture"""
    return CalendarAggregator()


@pytest.fixture
def sample_events():
    """Sample events for testing"""
    now = datetime.now()
    return [
        Event(
            id="yandex-1",
            title="Team Meeting",
            start=now + timedelta(hours=1),
            end=now + timedelta(hours=2),
            attendees=["alice@example.com"],
            source="yandex",
            raw_data={}
        ),
        Event(
            id="yandex-2",
            title="Lunch",
            start=now + timedelta(hours=3),
            end=now + timedelta(hours=4),
            attendees=[],
            source="yandex",
            raw_data={}
        ),
        Event(
            id="google-1",
            title="Client Call",
            start=now + timedelta(hours=5),
            end=now + timedelta(hours=6),
            attendees=["bob@example.com"],
            source="google",
            raw_data={}
        ),
    ]


@pytest.mark.asyncio
async def test_aggregate_single_provider(aggregator, sample_events):
    """Test aggregating events from single provider"""
    mock_provider = AsyncMock()
    mock_provider.get_events.return_value = sample_events[:2]

    aggregator.add_provider("yandex", mock_provider)

    start = datetime.now()
    end = start + timedelta(days=1)
    events = await aggregator.get_events(start=start, end=end)

    assert len(events) == 2
    assert events[0].title == "Team Meeting"
    assert events[1].title == "Lunch"


@pytest.mark.asyncio
async def test_aggregate_multiple_providers(aggregator, sample_events):
    """Test aggregating events from multiple providers"""
    yandex_provider = AsyncMock()
    yandex_provider.get_events.return_value = sample_events[:2]

    google_provider = AsyncMock()
    google_provider.get_events.return_value = [sample_events[2]]

    aggregator.add_provider("yandex", yandex_provider)
    aggregator.add_provider("google", google_provider)

    start = datetime.now()
    end = start + timedelta(days=1)
    events = await aggregator.get_events(start=start, end=end)

    assert len(events) == 3
    assert any(e.title == "Team Meeting" for e in events)
    assert any(e.title == "Client Call" for e in events)


@pytest.mark.asyncio
async def test_deduplicate_events(aggregator):
    """Test deduplication of same event from different providers"""
    now = datetime.now()

    # Same event from Yandex
    yandex_event = Event(
        id="yandex-123",
        title="Important Meeting",
        start=now + timedelta(hours=1),
        end=now + timedelta(hours=2),
        attendees=["alice@example.com", "bob@example.com"],
        source="yandex",
        raw_data={},
        location="Room 1"
    )

    # Same event from Google (duplicate)
    google_event = Event(
        id="google-456",
        title="Important Meeting",
        start=now + timedelta(hours=1),
        end=now + timedelta(hours=2),
        attendees=["alice@example.com", "bob@example.com"],
        source="google",
        raw_data={},
        location="Room 1"
    )

    yandex_provider = AsyncMock()
    yandex_provider.get_events.return_value = [yandex_event]

    google_provider = AsyncMock()
    google_provider.get_events.return_value = [google_event]

    aggregator.add_provider("yandex", yandex_provider)
    aggregator.add_provider("google", google_provider)

    start = datetime.now()
    end = start + timedelta(days=1)
    events = await aggregator.get_events(start=start, end=end, deduplicate=True)

    # Should have only 1 event after deduplication
    assert len(events) == 1
    assert events[0].title == "Important Meeting"


@pytest.mark.asyncio
async def test_deduplicate_similar_titles(aggregator):
    """Test deduplication with similar titles but different times"""
    now = datetime.now()

    # Event 1 at 10:00
    event1 = Event(
        id="yandex-1",
        title="Daily Standup",
        start=now.replace(hour=10, minute=0),
        end=now.replace(hour=10, minute=30),
        attendees=["alice@example.com"],
        source="yandex",
        raw_data={}
    )

    # Event 2 at 14:00 (different time, should NOT be deduplicated)
    event2 = Event(
        id="google-2",
        title="Daily Standup",
        start=now.replace(hour=14, minute=0),
        end=now.replace(hour=14, minute=30),
        attendees=["alice@example.com"],
        source="google",
        raw_data={}
    )

    yandex_provider = AsyncMock()
    yandex_provider.get_events.return_value = [event1]

    google_provider = AsyncMock()
    google_provider.get_events.return_value = [event2]

    aggregator.add_provider("yandex", yandex_provider)
    aggregator.add_provider("google", google_provider)

    start = datetime.now()
    end = start + timedelta(days=1)
    events = await aggregator.get_events(start=start, end=end, deduplicate=True)

    # Should have 2 events (different times)
    assert len(events) == 2


@pytest.mark.asyncio
async def test_sort_by_start_time(aggregator):
    """Test events are sorted by start time"""
    now = datetime.now()

    # Events in random order
    event1 = Event(
        id="1", title="Event 3",
        start=now + timedelta(hours=6), end=now + timedelta(hours=7),
        attendees=[], source="yandex", raw_data={}
    )
    event2 = Event(
        id="2", title="Event 1",
        start=now + timedelta(hours=2), end=now + timedelta(hours=3),
        attendees=[], source="yandex", raw_data={}
    )
    event3 = Event(
        id="3", title="Event 2",
        start=now + timedelta(hours=4), end=now + timedelta(hours=5),
        attendees=[], source="google", raw_data={}
    )

    yandex_provider = AsyncMock()
    yandex_provider.get_events.return_value = [event1, event2]

    google_provider = AsyncMock()
    google_provider.get_events.return_value = [event3]

    aggregator.add_provider("yandex", yandex_provider)
    aggregator.add_provider("google", google_provider)

    start = datetime.now()
    end = start + timedelta(days=1)
    events = await aggregator.get_events(start=start, end=end)

    # Should be sorted by start time
    assert events[0].title == "Event 1"
    assert events[1].title == "Event 2"
    assert events[2].title == "Event 3"


@pytest.mark.asyncio
async def test_empty_providers(aggregator):
    """Test with no providers added"""
    start = datetime.now()
    end = start + timedelta(days=1)
    events = await aggregator.get_events(start=start, end=end)

    assert events == []


@pytest.mark.asyncio
async def test_provider_error_handling(aggregator):
    """Test handling of provider errors"""
    failing_provider = AsyncMock()
    failing_provider.get_events.side_effect = Exception("Provider failed")

    working_provider = AsyncMock()
    working_provider.get_events.return_value = [
        Event(
            id="1", title="Working Event",
            start=datetime.now(), end=datetime.now() + timedelta(hours=1),
            attendees=[], source="google", raw_data={}
        )
    ]

    aggregator.add_provider("failing", failing_provider)
    aggregator.add_provider("working", working_provider)

    start = datetime.now()
    end = start + timedelta(days=1)

    # Should continue despite one provider failing
    events = await aggregator.get_events(start=start, end=end, skip_errors=True)

    assert len(events) == 1
    assert events[0].title == "Working Event"


@pytest.mark.asyncio
async def test_filter_by_date_range(aggregator):
    """Test filtering events by date range"""
    now = datetime.now()

    # Event within range
    event1 = Event(
        id="1", title="Within Range",
        start=now + timedelta(hours=2), end=now + timedelta(hours=3),
        attendees=[], source="yandex", raw_data={}
    )

    # Event outside range
    event2 = Event(
        id="2", title="Outside Range",
        start=now + timedelta(days=2), end=now + timedelta(days=2, hours=1),
        attendees=[], source="yandex", raw_data={}
    )

    mock_provider = AsyncMock()
    mock_provider.get_events.return_value = [event1, event2]

    aggregator.add_provider("yandex", mock_provider)

    # Query only for today
    start = now
    end = now + timedelta(hours=24)
    events = await aggregator.get_events(start=start, end=end)

    # Provider should be called with correct date range
    mock_provider.get_events.assert_called_once()
    call_args = mock_provider.get_events.call_args[1]
    assert 'start' in call_args
    assert 'end' in call_args


def test_add_provider(aggregator):
    """Test adding providers"""
    mock_provider = Mock()
    aggregator.add_provider("test", mock_provider)

    assert "test" in aggregator.providers
    assert aggregator.providers["test"] == mock_provider


def test_remove_provider(aggregator):
    """Test removing providers"""
    mock_provider = Mock()
    aggregator.add_provider("test", mock_provider)
    aggregator.remove_provider("test")

    assert "test" not in aggregator.providers
