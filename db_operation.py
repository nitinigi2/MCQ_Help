import mysql.connector
import os
from dotenv import load_dotenv
import aiomysql
from datetime import date

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


# Function to check and update daily upload limit
async def can_upload_image(user_id):
    conn = await get_db_connection()
    try:
        today = date.today()

        async with conn.cursor() as cursor:
            # Check the user's upload count for today
            await cursor.execute(
                "SELECT upload_count FROM user_uploads WHERE user_id=%s AND upload_date=%s",
                (user_id, today)
            )
            result = await cursor.fetchone()

            if result:
                upload_count = result[0]
                if upload_count >= 10:
                    return False  # Limit reached

                # Increment the upload count
                await cursor.execute(
                    "UPDATE user_uploads SET upload_count=upload_count+1 WHERE user_id=%s AND upload_date=%s",
                    (user_id, today)
                )
            else:
                # Insert a new record for today
                await cursor.execute(
                    "INSERT INTO user_uploads (user_id, upload_date, upload_count) VALUES (%s, %s, %s)",
                    (user_id, today, 1)
                )

            # Commit the changes
            await conn.commit()
    except Exception as e:
        # Print the exception (you can log this instead)
        print(f"Failed to save upload count info to the database: {e}")
        # Don't raise the exception, just print the error
        conn.close()
    return True  # User can upload
