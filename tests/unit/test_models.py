"""Unit tests for data models"""
import pytest
from datetime import datetime
from src.services.calendar.models import Event, Command, Intent


def test_event_creation():
    """Test creating an Event object"""
    event = Event(
        id="evt123",
        title="Team Meeting",
        start=datetime(2025, 11, 5, 10, 0),
        end=datetime(2025, 11, 5, 11, 0),
        description="Discuss project status",
        location="Conference Room A",
        attendees=["alice@example.com", "bob@example.com"],
        source="yandex",
        raw_data={}
    )

    assert event.id == "evt123"
    assert event.title == "Team Meeting"
    assert event.start.hour == 10
    assert event.source == "yandex"
    assert len(event.attendees) == 2


def test_event_with_optional_fields():
    """Test Event with optional fields omitted"""
    event = Event(
        id="evt456",
        title="Quick Call",
        start=datetime(2025, 11, 5, 14, 0),
        end=datetime(2025, 11, 5, 14, 30),
        attendees=[],
        source="google",
        raw_data={}
    )

    assert event.description is None
    assert event.location is None
    assert event.attendees == []


def test_event_to_dict():
    """Test Event serialization to dict"""
    event = Event(
        id="evt789",
        title="Lunch",
        start=datetime(2025, 11, 5, 12, 0),
        end=datetime(2025, 11, 5, 13, 0),
        attendees=[],
        source="yandex",
        raw_data={}
    )

    event_dict = event.to_dict()

    assert event_dict["id"] == "evt789"
    assert event_dict["title"] == "Lunch"
    assert event_dict["source"] == "yandex"
    assert isinstance(event_dict["start"], str)  # ISO format


def test_event_from_dict():
    """Test Event deserialization from dict"""
    data = {
        "id": "evt999",
        "title": "Workshop",
        "start": "2025-11-05T15:00:00",
        "end": "2025-11-05T17:00:00",
        "description": "Python workshop",
        "location": "Room 101",
        "attendees": ["charlie@example.com"],
        "source": "google",
        "raw_data": {}
    }

    event = Event.from_dict(data)

    assert event.id == "evt999"
    assert event.title == "Workshop"
    assert event.start == datetime(2025, 11, 5, 15, 0)
    assert event.description == "Python workshop"


def test_command_creation():
    """Test creating a Command object"""
    command = Command(
        intent=Intent.GET_TODAY,
        parameters={},
        original_text="что сегодня",
        confidence=0.95
    )

    assert command.intent == Intent.GET_TODAY
    assert command.original_text == "что сегодня"
    assert command.confidence == 0.95


def test_command_with_parameters():
    """Test Command with extracted parameters"""
    command = Command(
        intent=Intent.GET_UPCOMING,
        parameters={"hours": 3},
        original_text="ближайшие 3 часа",
        confidence=0.92
    )

    assert command.intent == Intent.GET_UPCOMING
    assert command.parameters["hours"] == 3


def test_command_find_meeting():
    """Test FIND_MEETING command with name parameter"""
    command = Command(
        intent=Intent.FIND_MEETING,
        parameters={"query": "Иван"},
        original_text="когда встреча с Иваном",
        confidence=0.88
    )

    assert command.intent == Intent.FIND_MEETING
    assert command.parameters["query"] == "Иван"


def test_intent_enum():
    """Test Intent enum values"""
    assert Intent.GET_TODAY.value == "get_today"
    assert Intent.GET_TOMORROW.value == "get_tomorrow"
    assert Intent.GET_UPCOMING.value == "get_upcoming"
    assert Intent.FIND_MEETING.value == "find_meeting"
    assert Intent.CREATE_EVENT.value == "create_event"
    assert Intent.UNKNOWN.value == "unknown"


def test_intent_from_string():
    """Test creating Intent from string"""
    intent = Intent("get_today")
    assert intent == Intent.GET_TODAY

    intent2 = Intent("find_meeting")
    assert intent2 == Intent.FIND_MEETING
