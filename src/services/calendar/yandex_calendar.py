"""Yandex Calendar Provider using CalDAV protocol"""
from typing import List, Optional
from datetime import datetime
import caldav
from icalendar import Calendar
from loguru import logger
import asyncio

from .models import Event


class YandexCalendarProvider:
    """Yandex Calendar provider using CalDAV"""

    def __init__(self, login: str, password: str, caldav_url: str = "https://caldav.yandex.ru"):
        """
        Initialize Yandex Calendar provider

        Args:
            login: Yandex login (email)
            password: App-specific password for CalDAV
            caldav_url: CalDAV server URL
        """
        self.login = login
        self.password = password
        self.caldav_url = caldav_url
        self.client: Optional[caldav.DAVClient] = None

    async def connect(self):
        """Connect to CalDAV server"""
        try:
            logger.info(f"Connecting to Yandex CalDAV: {self.caldav_url}")

            loop = asyncio.get_event_loop()
            self.client = await loop.run_in_executor(
                None,
                lambda: caldav.DAVClient(
                    url=self.caldav_url,
                    username=self.login,
                    password=self.password
                )
            )

            logger.info("Connected to Yandex Calendar")
        except Exception as e:
            logger.error(f"Failed to connect to Yandex Calendar: {e}")
            raise

    async def get_events(
        self,
        start: datetime,
        end: datetime
    ) -> List[Event]:
        """
        Get events from Yandex Calendar

        Args:
            start: Start datetime
            end: End datetime

        Returns:
            List of Event objects

        Raises:
            Exception: If API call fails
        """
        try:
            if not self.client:
                await self.connect()

            logger.info(f"Fetching events from {start} to {end}")

            loop = asyncio.get_event_loop()

            # Get principal and calendars
            principal = await loop.run_in_executor(
                None,
                lambda: self.client.principal()
            )

            calendars = await loop.run_in_executor(
                None,
                lambda: principal.calendars()
            )

            if not calendars:
                logger.warning("No calendars found")
                return []

            # Get events from first calendar
            calendar = calendars[0]

            cal_events = await loop.run_in_executor(
                None,
                lambda: calendar.date_search(start=start, end=end)
            )

            # Parse events
            events = []
            for cal_event in cal_events:
                event = await self._parse_caldav_event(cal_event)
                if event:
                    events.append(event)

            logger.info(f"Found {len(events)} events")
            return events

        except Exception as e:
            logger.error(f"Failed to get events: {e}")
            raise

    async def _parse_caldav_event(self, caldav_event) -> Optional[Event]:
        """
        Parse CalDAV event to Event model

        Args:
            caldav_event: CalDAV event object

        Returns:
            Event object or None if parsing fails
        """
        try:
            # Parse iCalendar data
            cal = Calendar.from_ical(caldav_event.data)

            for component in cal.walk():
                if component.name == "VEVENT":
                    # Extract event data
                    uid = str(component.get('uid', ''))
                    summary = str(component.get('summary', 'No Title'))
                    start = component.get('dtstart').dt
                    end = component.get('dtend').dt
                    description = str(component.get('description', '')) if component.get('description') else None
                    location = str(component.get('location', '')) if component.get('location') else None

                    # Extract attendees
                    attendees = []
                    for attendee in component.get('attendee', []):
                        if isinstance(attendee, str):
                            # Extract email from mailto: format
                            email = attendee.replace('mailto:', '')
                            attendees.append(email)

                    # Handle single attendee
                    if not isinstance(component.get('attendee', []), list):
                        attendee = component.get('attendee')
                        if attendee:
                            email = str(attendee).replace('mailto:', '')
                            attendees = [email]

                    # Convert date to datetime if needed
                    if not isinstance(start, datetime):
                        start = datetime.combine(start, datetime.min.time())
                    if not isinstance(end, datetime):
                        end = datetime.combine(end, datetime.min.time())

                    # Create Event object
                    event = Event(
                        id=uid,
                        title=summary,
                        start=start,
                        end=end,
                        attendees=attendees,
                        source="yandex",
                        raw_data={"icalendar": str(caldav_event.data)},
                        description=description,
                        location=location
                    )

                    return event

            return None

        except Exception as e:
            logger.error(f"Failed to parse CalDAV event: {e}")
            return None

    async def close(self):
        """Close connection to CalDAV server"""
        self.client = None
        logger.info("Disconnected from Yandex Calendar")
