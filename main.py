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
from db_operation import save_user, can_upload_image

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

    user = update.effective_user
    chat = update.effective_chat

    # Store user information asynchronously in the MySQL database
    asyncio.create_task(save_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        chat_id=chat.id,
    ))

    # Log the information
    print(f"User joined: Name = {user_name}, Username = {user_username}, ID = {user.id}, commandName = {commandName}")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global total_users_joined

    total_users_joined += 1  # Increment the total count

    log_user_info(update, 'start')

    print(f"Total users joined so far: {total_users_joined}")
    await update.message.reply_text('Hello! Thanks for chatting with me. \nUpload your MCQ image to find the answer. '
                                    '\nRemember image should have 1 MCQ at a time. Dont forget to share it with your '
                                    'friends')


async def description_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Hello! I am your Helper bot. Upload your MCQ image to find the answer. Remember '
                                    'image should have 1 MCQ at a time. Dont forget to share it with your friends')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log_user_info(update, 'help')
    await update.message.reply_text('Hello! I am your Helper bot. \nUpload your MCQ image to find the answer. Remember '
                                    'image should have 1 MCQ at a time. Dont forget to share it with your friends')


async def custom_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('This is custom command')


hello_messages = ["hi", "hello", "who are you", "what can yo do", "what can you do", "who are you", "can you help me", "hii", "hey"]
other_messages = ["no", "yes", "wrong", "wrong answer", ]


def handle_response(text: str) -> str:
    processed: str = text.lower()

    if processed in hello_messages:
        return 'Hey there! \nPlease upload your MCQ image to find the answer. Remember image should have 1 MCQ at a ' \
               'time. Dont forget to share it with your friends '
    if 'how are you' in processed:
        return 'I am good!'
    if 'i love python' in processed:
        return 'remember to subscribe'
    if processed in other_messages:
        return 'I am still learning. Please upload your next MCQ image.'
    return 'I do not understand. \nPlease upload your MCQ image to find the answer. Remember image should have 1 MCQ ' \
           'at a time. Dont forget to share it with your friends '


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log_user_info(update, 'custom message')
    message_type: str = update.message.chat.type
    text: str = update.message.text

    print(f'User({update.message.chat.id}) in {message_type}: "{text}"')

    if message_type == 'group' or message_type == 'supergroup':
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
    user = update.effective_user
    log_user_info(update, 'image')
    """Handles incoming images and processes them using Gemini."""
    try:
        print(f'User({update.message.chat.id}): "username": "{update.message.from_user.first_name}"')
        #Check if the user can upload more images
        if not await can_upload_image(user.id):
            await update.message.reply_text("You have reached your daily limit of 10 uploads. Try again tomorrow!")
            return
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
        full_message = f"Answer: {answer}\n\nExplanation: {explanation}"
        # Telegram's max message length
        MAX_MESSAGE_LENGTH = 4096
        # Split the message into smaller chunks if it's too long
        if len(full_message) > MAX_MESSAGE_LENGTH:
            for i in range(0, len(full_message), MAX_MESSAGE_LENGTH):
                await update.message.reply_text(full_message[i:i + MAX_MESSAGE_LENGTH])
        else:
            await update.message.reply_text(full_message)


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
