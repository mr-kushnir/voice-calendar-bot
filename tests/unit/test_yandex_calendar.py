"""Unit tests for Yandex Calendar Provider"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
from src.services.calendar.yandex_calendar import YandexCalendarProvider
from src.services.calendar.models import Event


@pytest.fixture
def yandex_calendar():
    """YandexCalendarProvider fixture"""
    return YandexCalendarProvider(
        login="test@example.com",
        password="test_password",
        caldav_url="https://caldav.yandex.ru"
    )


@pytest.mark.asyncio
async def test_get_events_today(yandex_calendar):
    """Test getting events for today"""
    with patch('caldav.DAVClient') as mock_client:
        # Mock CalDAV client
        mock_dav = MagicMock()
        mock_client.return_value = mock_dav

        mock_principal = MagicMock()
        mock_dav.principal.return_value = mock_principal

        mock_calendar = MagicMock()
        mock_principal.calendars.return_value = [mock_calendar]

        # Mock event
        mock_event = MagicMock()
        mock_event.data = """BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
UID:test-event-1
SUMMARY:Test Meeting
DTSTART:20251105T100000Z
DTEND:20251105T110000Z
END:VEVENT
END:VCALENDAR"""
        mock_calendar.date_search.return_value = [mock_event]

        yandex_calendar.client = mock_dav

        # Test getting events
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)
        events = await yandex_calendar.get_events(start=today, end=tomorrow)

        assert len(events) > 0
        assert events[0].title == "Test Meeting"
        assert events[0].source == "yandex"


@pytest.mark.asyncio
async def test_get_events_empty(yandex_calendar):
    """Test getting events when calendar is empty"""
    with patch('caldav.DAVClient') as mock_client:
        mock_dav = MagicMock()
        mock_client.return_value = mock_dav

        mock_principal = MagicMock()
        mock_dav.principal.return_value = mock_principal

        mock_calendar = MagicMock()
        mock_principal.calendars.return_value = [mock_calendar]
        mock_calendar.date_search.return_value = []

        yandex_calendar.client = mock_dav

        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)
        events = await yandex_calendar.get_events(start=today, end=tomorrow)

        assert events == []


@pytest.mark.asyncio
async def test_get_events_with_attendees(yandex_calendar):
    """Test getting events with attendees"""
    with patch('caldav.DAVClient') as mock_client:
        mock_dav = MagicMock()
        mock_client.return_value = mock_dav

        mock_principal = MagicMock()
        mock_dav.principal.return_value = mock_principal

        mock_calendar = MagicMock()
        mock_principal.calendars.return_value = [mock_calendar]

        mock_event = MagicMock()
        mock_event.data = """BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
UID:test-event-2
SUMMARY:Team Meeting
DTSTART:20251105T140000Z
DTEND:20251105T150000Z
ATTENDEE:mailto:ivan@example.com
ATTENDEE:mailto:maria@example.com
DESCRIPTION:Weekly sync
LOCATION:Conference Room A
END:VEVENT
END:VCALENDAR"""
        mock_calendar.date_search.return_value = [mock_event]

        yandex_calendar.client = mock_dav

        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)
        events = await yandex_calendar.get_events(start=today, end=tomorrow)

        assert len(events) == 1
        assert events[0].title == "Team Meeting"
        assert "ivan@example.com" in events[0].attendees
        assert "maria@example.com" in events[0].attendees
        assert events[0].description == "Weekly sync"
        assert events[0].location == "Conference Room A"


@pytest.mark.asyncio
async def test_find_meeting_with_person(yandex_calendar):
    """Test finding meeting with specific person"""
    with patch('caldav.DAVClient') as mock_client:
        mock_dav = MagicMock()
        mock_client.return_value = mock_dav

        mock_principal = MagicMock()
        mock_dav.principal.return_value = mock_principal

        mock_calendar = MagicMock()
        mock_principal.calendars.return_value = [mock_calendar]

        mock_event = MagicMock()
        mock_event.data = """BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
UID:test-event-3
SUMMARY:Meeting with Sergey
DTSTART:20251106T120000Z
DTEND:20251106T130000Z
ATTENDEE:mailto:sergey@example.com
END:VEVENT
END:VCALENDAR"""
        mock_calendar.date_search.return_value = [mock_event]

        yandex_calendar.client = mock_dav

        # Search for upcoming events
        start = datetime.now()
        end = start + timedelta(days=7)
        events = await yandex_calendar.get_events(start=start, end=end)

        # Find meeting with Sergey
        sergey_meetings = [e for e in events if "Sergey" in e.title or "sergey@example.com" in e.attendees]
        assert len(sergey_meetings) > 0
        assert "Sergey" in sergey_meetings[0].title


@pytest.mark.asyncio
async def test_connection_error(yandex_calendar):
    """Test handling connection errors"""
    with patch('caldav.DAVClient') as mock_client:
        mock_client.side_effect = Exception("Connection failed")

        with pytest.raises(Exception, match="Connection failed"):
            await yandex_calendar.connect()


@pytest.mark.asyncio
async def test_invalid_credentials(yandex_calendar):
    """Test handling invalid credentials"""
    with patch('caldav.DAVClient') as mock_client:
        mock_dav = MagicMock()
        mock_client.return_value = mock_dav
        mock_dav.principal.side_effect = Exception("Unauthorized")

        yandex_calendar.client = mock_dav

        with pytest.raises(Exception, match="Unauthorized"):
            today = datetime.now()
            tomorrow = today + timedelta(days=1)
            await yandex_calendar.get_events(start=today, end=tomorrow)


def test_yandex_calendar_initialization():
    """Test YandexCalendarProvider initialization"""
    provider = YandexCalendarProvider(
        login="user@example.com",
        password="password123",
        caldav_url="https://caldav.yandex.ru"
    )
    assert provider.login == "user@example.com"
    assert provider.password == "password123"
    assert provider.caldav_url == "https://caldav.yandex.ru"


@pytest.mark.asyncio
async def test_parse_icalendar_format(yandex_calendar):
    """Test parsing iCalendar format correctly"""
    with patch('caldav.DAVClient') as mock_client:
        mock_dav = MagicMock()
        mock_client.return_value = mock_dav

        mock_principal = MagicMock()
        mock_dav.principal.return_value = mock_principal

        mock_calendar = MagicMock()
        mock_principal.calendars.return_value = [mock_calendar]

        # Test with complex iCalendar format
        mock_event = MagicMock()
        mock_event.data = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Yandex LLC//Yandex Calendar//EN
BEGIN:VEVENT
UID:unique-event-id-123
DTSTAMP:20251105T080000Z
DTSTART:20251105T090000Z
DTEND:20251105T100000Z
SUMMARY:Важная встреча
DESCRIPTION:Обсуждение проекта
LOCATION:Офис
STATUS:CONFIRMED
ATTENDEE;CN=Ivan Ivanov:mailto:ivan@example.com
ORGANIZER:mailto:organizer@example.com
END:VEVENT
END:VCALENDAR"""
        mock_calendar.date_search.return_value = [mock_event]

        yandex_calendar.client = mock_dav

        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)
        events = await yandex_calendar.get_events(start=today, end=tomorrow)

        assert len(events) == 1
        assert events[0].title == "Важная встреча"
        assert events[0].id == "unique-event-id-123"
