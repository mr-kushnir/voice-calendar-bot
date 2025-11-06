"""Mark EXTEST-31 as complete"""
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tracker.tracker_client import TrackerClient
from dotenv import load_dotenv

load_dotenv()


async def complete_task():
    tracker = TrackerClient(
        token=os.getenv('YANDEX_TRACKER_TOKEN'),
        org_id=os.getenv('YANDEX_TRACKER_ORG_ID'),
        queue='EXTEST'
    )

    task_key = 'EXTEST-31'

    comment = '''✅ Production Deployment Complete!

**Deployment Method:** Container-Optimized VM

**Details:**
- **VM Name:** voice-bot-container
- **IP Address:** 158.160.48.17
- **Zone:** ru-central1-a
- **Resources:** 2 cores, 2GB RAM, 30GB disk
- **Platform:** standard-v3

**Container Registry:**
- **Registry:** cr.yandex/crpt07fh0n2t32v0otd8
- **Image:** voice-calendar-bot:latest
- **Digest:** sha256:f6a1970e6d48039adce8e709cbcd410219ece3093f3332a6a9f86740c40a256f

**Deployment Process:**
1. ✅ Bot tested locally with Docker - works perfectly
2. ✅ Image pushed to Yandex Container Registry
3. ✅ Container-Optimized VM created
4. ✅ Bot automatically deployed and running

**Testing:**
- Local testing: ✅ PASSED
- All services initialized: ✅ SUCCESS
- Telegram integration: ✅ WORKING

**Next Steps:**
- Bot is now running 24/7 on Yandex Cloud
- Automatic restarts enabled
- Ready for production use

**Cost:** ~1000₽/month (~$10-11/month)

---
🎉 Deployment successfully completed!
Automated update from deployment script'''

    try:
        await tracker.add_comment(task_key, comment)
        print(f'✅ Updated {task_key} with completion status')

        # Try to close the task
        try:
            await tracker.transition_issue(task_key, 'close')
            print(f'✅ Closed {task_key}')
        except Exception as e:
            print(f'⚠️  Could not auto-close {task_key}: {str(e)}')
            print('   Please close manually in Yandex Tracker')
    except Exception as e:
        print(f'❌ Failed to update {task_key}: {str(e)}')


if __name__ == "__main__":
    asyncio.run(complete_task())
