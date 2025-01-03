from telegram import Bot
import time
from typing import Final
import os
from dotenv import load_dotenv
import asyncio

# Load environment variables
load_dotenv()
BOT_TOKEN: Final = os.environ.get('NEW_BOT_TOKEN')

# Create a bot instance
bot = Bot(token=BOT_TOKEN)

# List of user IDs to send the message to
user_ids = [7584]


async def migrate_notification():
    # The message to send
    message = (
        "Hello! 🚀\n\n"
        "We are moving to a new bot with a better username and the same great features.\n"
        "👉 Please start using our new bot here: [@McqSolverBot](https://t.me/McqSolverBot).\n\n"
        "Thank you for your support! ❤️"
    )

    # Send messages to each user
    for user_id in user_ids:
        try:
            await bot.send_message(chat_id=user_id, text=message, parse_mode="Markdown")
            print(f"Message sent to user {user_id}")
        except Exception as e:
            print(f"Failed to send message to {user_id}: {e}")
        # Add a delay after every message
        await asyncio.sleep(0.1)  # 0.1 seconds = 10 messages/second


if __name__ == '__main__':
    asyncio.run(migrate_notification())
