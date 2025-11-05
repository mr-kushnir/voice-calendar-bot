"""Unit tests for Google Calendar Provider"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from aioresponses import aioresponses
from src.services.calendar.google_calendar import GoogleCalendarProvider
from src.services.calendar.models import Event


@pytest.fixture
def google_provider():
    """Google Calendar provider fixture"""
    return GoogleCalendarProvider(
        ics_url="https://calendar.google.com/calendar/ical/test/basic.ics"
    )


@pytest.fixture
def sample_ics_data():
    """Sample ICS data for testing"""
    return """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Google Inc//Google Calendar 70.9054//EN
BEGIN:VEVENT
DTSTART:20240115T100000Z
DTEND:20240115T110000Z
DTSTAMP:20240115T080000Z
UID:test-event-1@google.com
SUMMARY:Team Meeting
DESCRIPTION:Weekly team sync
LOCATION:Conference Room A
ATTENDEE:mailto:john@example.com
ATTENDEE:mailto:jane@example.com
END:VEVENT
BEGIN:VEVENT
DTSTART:20240115T140000Z
DTEND:20240115T150000Z
UID:test-event-2@google.com
SUMMARY:Client Call
END:VEVENT
END:VCALENDAR"""


def test_google_calendar_initialization():
    """Test GoogleCalendarProvider initialization"""
    provider = GoogleCalendarProvider(
        ics_url="https://calendar.google.com/calendar/ical/test/basic.ics"
    )

    assert provider.ics_url == "https://calendar.google.com/calendar/ical/test/basic.ics"


@pytest.mark.asyncio
async def test_get_events_success(google_provider, sample_ics_data):
    """Test successful event retrieval"""
    start = datetime(2024, 1, 15, 0, 0, 0)
    end = datetime(2024, 1, 16, 0, 0, 0)

    with aioresponses() as mocked:
        # Mock HTTP GET request
        mocked.get(
            google_provider.ics_url,
            status=200,
            body=sample_ics_data
        )

        events = await google_provider.get_events(start, end)

        assert len(events) == 2
        assert events[0].title == "Team Meeting"
        assert events[0].source == "google"
        assert events[1].title == "Client Call"


@pytest.mark.asyncio
async def test_get_events_http_error(google_provider):
    """Test handling of HTTP errors"""
    start = datetime(2024, 1, 15, 0, 0, 0)
    end = datetime(2024, 1, 16, 0, 0, 0)

    with aioresponses() as mocked:
        # Mock HTTP error
        mocked.get(
            google_provider.ics_url,
            status=404
        )

        with pytest.raises(Exception, match="Failed to fetch ICS"):
            await google_provider.get_events(start, end)


def test_parse_ics(google_provider, sample_ics_data):
    """Test ICS parsing"""
    start = datetime(2024, 1, 15, 0, 0, 0)
    end = datetime(2024, 1, 16, 0, 0, 0)

    events = google_provider._parse_ics(sample_ics_data, start, end)

    assert len(events) == 2

    # Check first event
    assert events[0].id == "test-event-1@google.com"
    assert events[0].title == "Team Meeting"
    assert events[0].description == "Weekly team sync"
    assert events[0].location == "Conference Room A"
    assert len(events[0].attendees) == 2
    assert "john@example.com" in events[0].attendees
    assert "jane@example.com" in events[0].attendees

    # Check second event
    assert events[1].id == "test-event-2@google.com"
    assert events[1].title == "Client Call"


def test_parse_ics_datetime(google_provider):
    """Test ICS datetime parsing"""
    # Test datetime with timezone
    dt1 = google_provider._parse_ics_datetime("20240115T100000Z")
    assert dt1 == datetime(2024, 1, 15, 10, 0, 0)

    # Test datetime without timezone
    dt2 = google_provider._parse_ics_datetime("20240115T140000")
    assert dt2 == datetime(2024, 1, 15, 14, 0, 0)

    # Test date only
    dt3 = google_provider._parse_ics_datetime("VALUE=DATE:20240115")
    assert dt3 == datetime(2024, 1, 15, 0, 0, 0)


def test_parse_ics_datetime_invalid(google_provider):
    """Test ICS datetime parsing with invalid input"""
    result = google_provider._parse_ics_datetime("invalid")
    assert result is None


def test_create_event_from_ics(google_provider):
    """Test creating Event from ICS data"""
    ics_event = {
        'UID': 'test-123',
        'SUMMARY': 'Test Event',
        'DTSTART': '20240115T100000Z',
        'DTEND': '20240115T110000Z',
        'DESCRIPTION': 'Test description',
        'LOCATION': 'Test location',
        'ATTENDEE': 'mailto:test@example.com'
    }

    event = google_provider._create_event_from_ics(ics_event)

    assert event is not None
    assert event.id == 'test-123'
    assert event.title == 'Test Event'
    assert event.description == 'Test description'
    assert event.location == 'Test location'
    assert event.source == 'google'
    assert 'test@example.com' in event.attendees


def test_create_event_from_ics_missing_start(google_provider):
    """Test creating Event with missing start time"""
    ics_event = {
        'UID': 'test-123',
        'SUMMARY': 'Test Event'
    }

    event = google_provider._create_event_from_ics(ics_event)
    assert event is None


def test_create_event_from_ics_default_end_time(google_provider):
    """Test creating Event with default end time"""
    ics_event = {
        'UID': 'test-123',
        'SUMMARY': 'Test Event',
        'DTSTART': '20240115T100000Z'
    }

    event = google_provider._create_event_from_ics(ics_event)

    assert event is not None
    assert event.end == event.start + timedelta(hours=1)


@pytest.mark.asyncio
async def test_close_connection(google_provider):
    """Test closing provider connection"""
    await google_provider.close()
    # Should not raise any errors
    assert True


@pytest.mark.asyncio
async def test_get_events_filters_by_date_range(google_provider):
    """Test that events are filtered by date range"""
    # ICS with event outside the date range
    ics_data = """BEGIN:VCALENDAR
BEGIN:VEVENT
DTSTART:20240110T100000Z
DTEND:20240110T110000Z
UID:old-event
SUMMARY:Old Event
END:VEVENT
BEGIN:VEVENT
DTSTART:20240115T100000Z
DTEND:20240115T110000Z
UID:current-event
SUMMARY:Current Event
END:VEVENT
END:VCALENDAR"""

    start = datetime(2024, 1, 15, 0, 0, 0)
    end = datetime(2024, 1, 16, 0, 0, 0)

    with aioresponses() as mocked:
        # Mock HTTP response
        mocked.get(
            google_provider.ics_url,
            status=200,
            body=ics_data
        )

        events = await google_provider.get_events(start, end)

        # Should only return the event within the date range
        assert len(events) == 1
        assert events[0].title == "Current Event"
