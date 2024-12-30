import mysql.connector
import os
from dotenv import load_dotenv
import aiomysql

# Load environment variables
load_dotenv()

# MySQL database credentials from .env file
DATABASE_HOST = os.getenv("DATABASE_HOST")
DATABASE_USER = os.getenv("DATABASE_USER")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
DATABASE_NAME = os.getenv("DATABASE_NAME")


# MySQL Connection
# Async MySQL Connection
async def get_db_connection():
    return await aiomysql.connect(
        host=DATABASE_HOST,
        port=3306,  # Default MySQL port
        user=DATABASE_USER,
        password=DATABASE_PASSWORD,
        db=DATABASE_NAME,
        autocommit=True
    )


async def save_user(user_id, username, first_name, last_name, chat_id):
    try:
        connection = await get_db_connection()
        cursor = await connection.cursor()

        # Insert user data into the database
        await cursor.execute(
            "INSERT INTO users (user_id, username, first_name, last_name, chat_id) VALUES (%s, %s, %s, %s, %s)",
            (user_id, username, first_name, last_name, chat_id)
        )

        await cursor.close()
        connection.close()
    except Exception as e:
        # Print the exception (you can log this instead)
        print(f"Failed to save user info to the database: {e}")
        # Don't raise the exception, just print the error
