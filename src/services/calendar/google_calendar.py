"""Google Calendar Provider"""
from datetime import datetime, timedelta
from typing import List, Optional
import aiohttp
from loguru import logger
from .models import Event


class GoogleCalendarProvider:
    """Provider for Google Calendar using ICS URL"""

    def __init__(self, ics_url: str):
        """
        Initialize Google Calendar provider

        Args:
            ics_url: ICS URL for Google Calendar
        """
        self.ics_url = ics_url
        logger.info("Google Calendar Provider initialized")

    async def get_events(
        self,
        start: datetime,
        end: datetime
    ) -> List[Event]:
        """
        Get events from Google Calendar

        Args:
            start: Start datetime
            end: End datetime

        Returns:
            List of Event objects
        """
        try:
            logger.info(f"Fetching Google Calendar events from {start} to {end}")

            # Fetch ICS file
            async with aiohttp.ClientSession() as session:
                async with session.get(self.ics_url) as response:
                    if response.status != 200:
                        raise Exception(f"Failed to fetch ICS: {response.status}")

                    ics_data = await response.text()

            # Parse ICS data
            events = self._parse_ics(ics_data, start, end)
            logger.info(f"Found {len(events)} Google Calendar events")

            return events

        except Exception as e:
            logger.error(f"Error fetching Google Calendar events: {e}")
            raise

    def _parse_ics(self, ics_data: str, start: datetime, end: datetime) -> List[Event]:
        """
        Parse ICS data into Event objects

        Args:
            ics_data: ICS file content
            start: Start datetime filter
            end: End datetime filter

        Returns:
            List of Event objects
        """
        events = []
        current_event = {}
        in_event = False

        for line in ics_data.split('\n'):
            line = line.strip()

            if line == 'BEGIN:VEVENT':
                in_event = True
                current_event = {}
            elif line == 'END:VEVENT':
                in_event = False
                # Create Event object
                if current_event:
                    event = self._create_event_from_ics(current_event)
                    if event and start <= event.start <= end:
                        events.append(event)
            elif in_event and ':' in line:
                key, value = line.split(':', 1)
                # Handle multi-line values
                if key.startswith(' '):
                    continue

                # For ATTENDEE, collect all values in a list
                if key.startswith('ATTENDEE'):
                    if key not in current_event:
                        current_event[key] = []
                    if isinstance(current_event[key], list):
                        current_event[key].append(value)
                    else:
                        # Convert to list if it was a string
                        current_event[key] = [current_event[key], value]
                else:
                    current_event[key] = value

        return events

    def _create_event_from_ics(self, ics_event: dict) -> Optional[Event]:
        """
        Create Event object from ICS event data

        Args:
            ics_event: Dictionary with ICS event fields

        Returns:
            Event object or None if parsing fails
        """
        try:
            # Parse UID
            uid = ics_event.get('UID', '')

            # Parse summary (title)
            summary = ics_event.get('SUMMARY', 'Untitled Event')

            # Parse start datetime
            dtstart = ics_event.get('DTSTART')
            if not dtstart:
                return None

            start_dt = self._parse_ics_datetime(dtstart)
            if not start_dt:
                return None

            # Parse end datetime
            dtend = ics_event.get('DTEND')
            if dtend:
                end_dt = self._parse_ics_datetime(dtend)
            else:
                # Default to 1 hour duration
                end_dt = start_dt + timedelta(hours=1)

            # Parse description
            description = ics_event.get('DESCRIPTION', '')

            # Parse location
            location = ics_event.get('LOCATION')

            # Parse attendees
            attendees = []
            for key, value in ics_event.items():
                if key.startswith('ATTENDEE'):
                    # ATTENDEE can be a list or a single string
                    values = value if isinstance(value, list) else [value]
                    for v in values:
                        # Extract email from mailto:
                        if v.startswith('mailto:'):
                            email = v.replace('mailto:', '')
                            attendees.append(email)

            return Event(
                id=uid,
                title=summary,
                start=start_dt,
                end=end_dt,
                description=description,
                location=location,
                attendees=attendees,
                source="google",
                raw_data=ics_event
            )

        except Exception as e:
            logger.error(f"Error creating event from ICS: {e}")
            return None

    def _parse_ics_datetime(self, dt_string: str) -> Optional[datetime]:
        """
        Parse ICS datetime string

        Args:
            dt_string: ICS datetime string (e.g., 20240101T120000Z or VALUE=DATE:20240101)

        Returns:
            datetime object or None
        """
        try:
            # Remove VALUE=DATE: prefix if present
            if 'VALUE=DATE:' in dt_string:
                dt_string = dt_string.split('VALUE=DATE:')[1]

            # Remove timezone info for simplicity
            dt_string = dt_string.replace('Z', '').replace('TZID=', '')

            # Parse different formats
            if 'T' in dt_string:
                # DateTime format: 20240101T120000
                dt = datetime.strptime(dt_string[:15], '%Y%m%dT%H%M%S')
            else:
                # Date only format: 20240101
                dt = datetime.strptime(dt_string[:8], '%Y%m%d')

            return dt

        except Exception as e:
            logger.error(f"Error parsing ICS datetime '{dt_string}': {e}")
            return None

    async def close(self):
        """Close any open connections"""
        # No persistent connections to close
        pass
