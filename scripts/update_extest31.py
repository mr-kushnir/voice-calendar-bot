"""Update EXTEST-31 with deployment progress"""
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

    comment = '''Production Deployment Progress Update

**Status:** 95% Complete

**Completed:**
1. Docker Image Built
   - Image: voice-calendar-bot:latest (468MB)
   - Status: Ready for deployment

2. Yandex Cloud VMs Created
   - VM #1: claude-code-vm
     - IP: 89.169.131.111
     - Status: RUNNING
     - Resources: 2 cores, 2GB RAM

   - VM #2: voice-calendar-bot
     - IP: 158.160.37.42
     - Status: RUNNING
     - Resources: 2 cores, 2GB RAM

3. Infrastructure Files
   - Dockerfile: Optimized (no gcc)
   - docker-compose.yml: Multi-service setup
   - cloud-init.yaml: VM auto-configuration
   - .env: Configured

4. Documentation
   - YANDEX_CLOUD_DEPLOYMENT_REPORT.md created
   - Full deployment instructions provided

**GitHub Commits:**
- 0ed1133: Deployment infrastructure
- cf11c54: Deployment status
- 36df782: Deployment preparation complete

**Current Step:** Finalizing deployment on VM
- Uploading Docker image to VM
- Starting bot with docker-compose
- Configuring systemd auto-start

**Expected Completion:** Within 30 minutes

---
Automated update from deployment script'''

    try:
        await tracker.add_comment(task_key, comment)
        print(f'Updated {task_key} with progress comment')
    except Exception as e:
        print(f'Failed to update {task_key}: {str(e)}')


if __name__ == "__main__":
    asyncio.run(update_task())
