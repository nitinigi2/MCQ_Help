from typing import Final
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from gemini_image_process import get_output
import logging
from concurrent.futures import ThreadPoolExecutor
from telegram.error import TelegramError
import asyncio

total_users_joined = 0  # Counter for total users

load_dotenv()
TOKEN: Final = os.environ.get('BOT_TOKEN')
BOT_USERNAME: Final = os.environ.get('BOT_USERNAME')

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

# Create a thread pool executor
executor = ThreadPoolExecutor(max_workers=5)  # Adjust max_workers as needed


def log_user_info(update: Update, commandName):
    # Get the user's information
    user = update.effective_user
    user_name = user.first_name if user.first_name else "Unknown"
    user_username = user.username if user.username else "No Username"

    # Log the information
    print(f"User joined: Name = {user_name}, Username = {user_username}, ID = {user.id}, commandName = {commandName}")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global total_users_joined

    total_users_joined += 1  # Increment the total count

    log_user_info(update, 'start')

    print(f"Total users joined so far: {total_users_joined}")
    await update.message.reply_text('Hello! Thanks for chatting with me')


async def description_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Hello! I am your Helper bot. Upload your MCQ image to find the answer. Remember '
                                    'image should have 1 MCQ at a time. Dont forget to share it with your friends')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log_user_info(update, 'help')
    await update.message.reply_text('Hello! I am your Helper bot. Upload your MCQ image to find the answer. Remember '
                                    'image should have 1 MCQ at a time. Dont forget to share it with your friends')


async def custom_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('This is custom command')


def handle_response(text: str) -> str:
    processed: str = text.lower()

    if 'hello' in processed:
        return 'Hey there!'
    if 'how are you' in processed:
        return 'I am good!'
    if 'i love python' in processed:
        return 'remember to subscribe'
    return 'I do not understand. Please write something else'


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log_user_info(update, 'custom message')
    message_type: str = update.message.chat.type
    text: str = update.message.text

    print(f'User({update.message.chat.id}) in {message_type}: "{text}"')

    if message_type == 'group':
        if BOT_USERNAME in text:
            new_text: str = text.replace(BOT_USERNAME, '').strip()
            response: str = handle_response(new_text)
        else:
            return
    else:
        response: str = handle_response(text)

    print('Bot: ', response)
    await update.message.reply_text(response)


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update({update}) caused error {context.error}')


async def handle_image(update: Update, context):
    log_user_info(update, 'image')
    """Handles incoming images and processes them using Gemini."""
    try:
        print(f'User({update.message.chat.id}): "username": "{update.message.from_user.first_name}"')
        file = await update.message.effective_attachment[-1].get_file()  # Get the highest resolution image
        await update.message.reply_text("Processing image...")
        # Submit the image processing task to the executor
        asyncio.create_task(process_image(update, file.file_path))
    except Exception or TelegramError as e:
        logger.error(f"Telegram Error: {e}")
        await update.message.reply_text("An error occurred while processing the image. Please try again later.")


async def process_image(update, image_url):
    answer, explanation = get_output(image_url)
    print(f'"answer": {answer}, "explanation: " {explanation}')
    if answer is None or answer == 'error':
        await update.message.reply_text("An error occurred while processing the image. Please try again later")
    else:
        await update.message.reply_text(f"Answer: {answer}\n\nExplanation: {explanation}")


if __name__ == '__main__':
    app = Application.builder().token(TOKEN).build()

    # Command
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('custom', custom_command))
    app.add_handler(MessageHandler(filters.PHOTO, handle_image))

    # Message
    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    # Error
    app.add_error_handler(error)

    # Polls the bot
    print('Polling')
    app.run_polling(10)
