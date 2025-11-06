"""Test bot functionality"""
import asyncio
import os
from dotenv import load_dotenv
from telegram import Bot

load_dotenv()

async def test_bot():
    """Test bot basic functionality"""
    bot = Bot(token=os.getenv('TELEGRAM_BOT_TOKEN'))

    print("Testing bot connection...")

    try:
        # Get bot info
        me = await bot.get_me()
        print(f"[OK] Bot connected: @{me.username}")
        print(f"   Name: {me.first_name}")
        print(f"   ID: {me.id}")
        print(f"   Can read all group messages: {me.can_read_all_group_messages}")

        # Get webhook info
        webhook_info = await bot.get_webhook_info()
        print(f"\nWebhook status:")
        print(f"   URL: {webhook_info.url or 'Not set (polling mode)'}")
        print(f"   Pending updates: {webhook_info.pending_update_count}")

        # Get updates to see if bot is receiving messages
        updates = await bot.get_updates(limit=5)
        print(f"\nRecent updates: {len(updates)}")

        if updates:
            print("\nLast messages:")
            for update in updates[-3:]:
                if update.message:
                    msg = update.message
                    user = msg.from_user
                    print(f"   - From @{user.username}: {msg.text or '[voice/media]'}")

        print("\n[OK] Bot is operational!")
        print("\nTo test:")
        print(f"1. Open Telegram and find @{me.username}")
        print("2. Send /start command")
        print("3. Try text command: 'Что у меня сегодня в календаре?'")
        print("4. Try voice message with calendar request")

        return True

    except Exception as e:
        print(f"[ERROR] Bot test failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_bot())
