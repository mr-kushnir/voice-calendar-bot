"""Update deployment tasks status in Yandex Tracker"""
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tracker.tracker_client import TrackerClient
from dotenv import load_dotenv

load_dotenv()


async def update_tasks():
    tracker = TrackerClient(
        token=os.getenv('YANDEX_TRACKER_TOKEN'),
        org_id=os.getenv('YANDEX_TRACKER_ORG_ID'),
        queue='EXTEST'
    )

    # Tasks to close (already completed)
    completed_tasks = {
        'EXTEST-27': 'Yandex Cloud Infrastructure Setup - DONE',
        'EXTEST-28': 'Docker Containerization - DONE',
        'EXTEST-29': 'Deployment Automation Scripts - DONE',
        'EXTEST-30': 'Deployment Documentation - DONE'
    }

    print('=== CLOSING COMPLETED TASKS ===\n')

    for task_key, comment in completed_tasks.items():
        try:
            # Add comment
            await tracker.add_comment(task_key, f'''Task completed successfully.

**Status:** DONE
**Commit:** 0ed1133 (feat: Add Yandex Cloud deployment infrastructure)
**GitHub:** https://github.com/mr-kushnir/voice-calendar-bot

All files created and tested.''')

            # Close task
            await tracker.update_task_status(task_key, 'closed')
            print(f'Closed {task_key}: {comment}')
        except Exception as e:
            print(f'Failed to close {task_key}: {str(e)}')

    # Start production deployment task
    print('\n=== STARTING PRODUCTION DEPLOYMENT ===\n')
    try:
        await tracker.add_comment('EXTEST-31', '''Starting production deployment to Yandex Cloud.

**Prerequisites:**
- Yandex Cloud CLI configured
- Folder ID: b1gm1nh37o3isrorujke
- Subnet ID: e9b4i1js8g2tol33omp8
- Docker installed and running
- .env file configured
- SSH keys ready

Ready to deploy!''')

        await tracker.update_task_status('EXTEST-31', 'inProgress')
        print('Started EXTEST-31: Production Deployment')
    except Exception as e:
        print(f'Failed to start EXTEST-31: {str(e)}')


if __name__ == "__main__":
    asyncio.run(update_tasks())
