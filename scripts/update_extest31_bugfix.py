"""Update EXTEST-31 with bugfix information and close it"""
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tracker.tracker_client import TrackerClient
from dotenv import load_dotenv

load_dotenv()


async def update_task():
    tracker = TrackerClient(
        token=os.getenv('YANDEX_TRACKER_TOKEN'),
        org_id=os.getenv('YANDEX_TRACKER_ORG_ID'),
        queue='EXTEST'
    )

    task_key = 'EXTEST-31'

    comment = '''## Bot Fix & Cloud Update

**Issue Fixed:** Voice message sending error (Voice_messages_forbidden)

**Solution:**
- Added fallback mechanism: if voice sending fails, bot sends text response
- User always gets an answer, regardless of voice API restrictions

**Cloud Deployment Updated:**
- New Docker image built with fix
- Image pushed to Yandex Container Registry
- Digest: sha256:5ba631d398d6dcce5747cd73089f49404cd688b69aff54ebbcf648613490b236
- VM voice-bot-container restarted with new image

**Testing Results:**
- Local: PASSED - Bot responds with text when voice fails
- Cloud: VM restarted successfully (158.160.48.17)
- Status: HEALTHY

**Git:**
- Commit: 118866f "fix: Add fallback to text response when voice message sending fails"
- Pushed to GitHub

---
Bot now handles voice API restrictions gracefully!

Deployment completed and tested.'''

    try:
        print(f"Adding comment to {task_key}...")
        await tracker.add_comment(task_key, comment)
        print(f"Comment added successfully!")

        # Try to close the task
        print(f"\nAttempting to close {task_key}...")
        try:
            # Get available transitions
            transitions = await tracker.get_task_transitions(task_key)
            print(f"Available transitions: {[t.get('id') for t in transitions]}")

            # Try to find "close" transition
            close_transition = None
            for t in transitions:
                if 'close' in t.get('id', '').lower() or 'закрыт' in t.get('display', '').lower():
                    close_transition = t.get('id')
                    break

            if close_transition:
                await tracker.transition_issue(task_key, close_transition)
                print(f"Task {task_key} closed successfully!")
            else:
                print(f"No close transition found. Please close manually.")
                print(f"Available: {transitions}")

        except Exception as e:
            print(f"Could not auto-close {task_key}: {str(e)}")
            print("Please close manually in Yandex Tracker")

    except Exception as e:
        print(f"Failed to update {task_key}: {str(e)}")


if __name__ == "__main__":
    asyncio.run(update_task())
