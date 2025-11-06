"""Test Google Calendar ICS access"""
import asyncio
import aiohttp
import os
from dotenv import load_dotenv

load_dotenv()


async def test_google_calendar():
    ics_url = os.getenv('GOOGLE_CALENDAR_ICS_URL')

    print(f"Testing Google Calendar ICS URL...")
    print(f"URL: {ics_url[:50]}...{ics_url[-20:]}")
    print()

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(ics_url) as response:
                print(f"Status: {response.status}")

                if response.status == 200:
                    ics_data = await response.text()
                    print(f"Response length: {len(ics_data)} bytes")
                    print()
                    print("First 500 characters:")
                    print(ics_data[:500])
                    print()

                    # Count events
                    event_count = ics_data.count('BEGIN:VEVENT')
                    print(f"Events found: {event_count}")

                    if event_count > 0:
                        print("\nSample event:")
                        start_idx = ics_data.find('BEGIN:VEVENT')
                        end_idx = ics_data.find('END:VEVENT', start_idx) + len('END:VEVENT')
                        print(ics_data[start_idx:end_idx])
                else:
                    error = await response.text()
                    print(f"Error: {error[:200]}")

    except Exception as e:
        print(f"Exception: {e}")


if __name__ == "__main__":
    asyncio.run(test_google_calendar())
