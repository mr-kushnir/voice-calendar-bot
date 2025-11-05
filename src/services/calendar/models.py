"""Data models for calendar events and commands"""
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class Intent(Enum):
    """Command intent types"""
    GET_TODAY = "get_today"
    GET_TOMORROW = "get_tomorrow"
    GET_UPCOMING = "get_upcoming"
    FIND_MEETING = "find_meeting"
    CREATE_EVENT = "create_event"
    UNKNOWN = "unknown"


@dataclass
class Event:
    """Calendar event model"""
    id: str
    title: str
    start: datetime
    end: datetime
    attendees: List[str]
    source: str  # 'yandex' or 'google'
    raw_data: Dict[str, Any]
    description: Optional[str] = None
    location: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary with ISO format dates"""
        data = asdict(self)
        data['start'] = self.start.isoformat()
        data['end'] = self.end.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Event':
        """Create Event from dictionary"""
        # Parse datetime strings
        if isinstance(data['start'], str):
            data['start'] = datetime.fromisoformat(data['start'])
        if isinstance(data['end'], str):
            data['end'] = datetime.fromisoformat(data['end'])

        return cls(**data)

    def __str__(self) -> str:
        """String representation of event"""
        time_str = self.start.strftime("%H:%M")
        return f"{time_str} - {self.title}"


@dataclass
class Command:
    """Parsed command from user input"""
    intent: Intent
    parameters: Dict[str, Any]
    original_text: str
    confidence: float

    def __post_init__(self):
        """Validate command after initialization"""
        if not 0 <= self.confidence <= 1:
            raise ValueError("Confidence must be between 0 and 1")

        # Convert intent string to Intent enum if needed
        if isinstance(self.intent, str):
            self.intent = Intent(self.intent)

    def to_dict(self) -> Dict[str, Any]:
        """Convert command to dictionary"""
        return {
            'intent': self.intent.value,
            'parameters': self.parameters,
            'original_text': self.original_text,
            'confidence': self.confidence
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Command':
        """Create Command from dictionary"""
        if isinstance(data['intent'], str):
            data['intent'] = Intent(data['intent'])
        return cls(**data)
