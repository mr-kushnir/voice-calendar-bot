"""Calendar Aggregator for combining multiple calendar sources"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from loguru import logger

from .models import Event


class CalendarAggregator:
    """Aggregates events from multiple calendar providers with deduplication"""

    def __init__(self):
        """Initialize calendar aggregator"""
        self.providers: Dict[str, Any] = {}

    def add_provider(self, name: str, provider: Any):
        """
        Add calendar provider

        Args:
            name: Provider name (e.g., 'yandex', 'google')
            provider: Provider instance with get_events method
        """
        self.providers[name] = provider
        logger.info(f"Added calendar provider: {name}")

    def remove_provider(self, name: str):
        """
        Remove calendar provider

        Args:
            name: Provider name to remove
        """
        if name in self.providers:
            del self.providers[name]
            logger.info(f"Removed calendar provider: {name}")

    async def get_events(
        self,
        start: datetime,
        end: datetime,
        deduplicate: bool = True,
        skip_errors: bool = False
    ) -> List[Event]:
        """
        Get aggregated events from all providers

        Args:
            start: Start datetime
            end: End datetime
            deduplicate: Whether to deduplicate events (default: True)
            skip_errors: Skip providers that fail (default: False)

        Returns:
            List of aggregated Event objects sorted by start time

        Raises:
            Exception: If any provider fails and skip_errors=False
        """
        logger.info(f"Aggregating events from {len(self.providers)} providers")

        all_events = []

        # Collect events from all providers
        for provider_name, provider in self.providers.items():
            try:
                logger.debug(f"Fetching events from {provider_name}")
                events = await provider.get_events(start=start, end=end)
                all_events.extend(events)
                logger.debug(f"Got {len(events)} events from {provider_name}")
            except Exception as e:
                logger.error(f"Failed to get events from {provider_name}: {e}")
                if not skip_errors:
                    raise

        logger.info(f"Collected {len(all_events)} total events")

        # Deduplicate if requested
        if deduplicate and len(all_events) > 0:
            all_events = self._deduplicate_events(all_events)
            logger.info(f"After deduplication: {len(all_events)} events")

        # Sort by start time
        all_events.sort(key=lambda e: e.start)

        return all_events

    def _deduplicate_events(self, events: List[Event]) -> List[Event]:
        """
        Deduplicate events based on title, time, and attendees

        Args:
            events: List of events to deduplicate

        Returns:
            List of unique events
        """
        if not events:
            return []

        unique_events = []
        seen_signatures = set()

        for event in events:
            signature = self._event_signature(event)

            if signature not in seen_signatures:
                unique_events.append(event)
                seen_signatures.add(signature)
            else:
                logger.debug(f"Duplicate event detected: {event.title} at {event.start}")

        return unique_events

    def _event_signature(self, event: Event) -> str:
        """
        Create unique signature for event

        Signature includes:
        - Normalized title (lowercase, stripped)
        - Start time rounded to nearest 5 minutes
        - Sorted attendees (normalized emails)
        - Location (if present)

        Args:
            event: Event to create signature for

        Returns:
            Unique signature string
        """
        # Normalize title
        title = event.title.lower().strip()

        # Round start time to nearest 5 minutes for fuzzy matching
        start_rounded = self._round_to_minutes(event.start, 5)

        # Sort and normalize attendees
        attendees = sorted([a.lower().strip() for a in event.attendees])
        attendees_str = ",".join(attendees)

        # Include location if present
        location = event.location.lower().strip() if event.location else ""

        # Create signature
        signature = f"{title}|{start_rounded.isoformat()}|{attendees_str}|{location}"

        return signature

    def _round_to_minutes(self, dt: datetime, minutes: int) -> datetime:
        """
        Round datetime to nearest N minutes

        Args:
            dt: Datetime to round
            minutes: Number of minutes to round to

        Returns:
            Rounded datetime
        """
        # Round to nearest N minutes
        discard = timedelta(
            minutes=dt.minute % minutes,
            seconds=dt.second,
            microseconds=dt.microsecond
        )
        dt = dt - discard
        if discard >= timedelta(minutes=minutes / 2):
            dt = dt + timedelta(minutes=minutes)
        return dt

    async def get_today_events(self) -> List[Event]:
        """
        Get events for today

        Returns:
            List of today's events
        """
        now = datetime.now()
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
        return await self.get_events(start=start, end=end)

    async def get_tomorrow_events(self) -> List[Event]:
        """
        Get events for tomorrow

        Returns:
            List of tomorrow's events
        """
        now = datetime.now()
        start = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
        return await self.get_events(start=start, end=end)

    async def get_upcoming_events(self, hours: int = 24) -> List[Event]:
        """
        Get upcoming events in next N hours

        Args:
            hours: Number of hours to look ahead

        Returns:
            List of upcoming events
        """
        now = datetime.now()
        end = now + timedelta(hours=hours)
        return await self.get_events(start=now, end=end)

    async def find_meetings_with_person(
        self,
        person: str,
        days_ahead: int = 7
    ) -> List[Event]:
        """
        Find meetings with specific person

        Args:
            person: Person name or email to search for
            days_ahead: Number of days to search ahead

        Returns:
            List of meetings with the person
        """
        now = datetime.now()
        end = now + timedelta(days=days_ahead)
        all_events = await self.get_events(start=now, end=end)

        # Filter events that contain person in title or attendees
        person_lower = person.lower()
        matching_events = []

        for event in all_events:
            # Check title
            if person_lower in event.title.lower():
                matching_events.append(event)
                continue

            # Check attendees
            for attendee in event.attendees:
                if person_lower in attendee.lower():
                    matching_events.append(event)
                    break

        logger.info(f"Found {len(matching_events)} meetings with {person}")
        return matching_events
