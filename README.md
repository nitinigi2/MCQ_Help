## This is a Telegram bot that solves a given MCQ question from an image

Setup steps:
1. pip install google-generativeai Pillow requests python-dotenv
2. pip install python-dotenv python-telegram-bot
3. pip install mysql-connector-python aiomysql
3. Create a .env file and add below things
```
BOT_TOKEN={TELEGRAM_BOT_TOKEN}
BOT_USERNAME={TELEGRAM_BOT_USERNAME}
GEMINI_API_KEY={GEMINI_API_KEY}
```

Run the main.py file

This telegram bot is live at ```@helpmcq_bot``` on Telegram