import mysql.connector
from dotenv import load_dotenv
from mysql.connector import Error
import os

# Load environment variables
load_dotenv()

# MySQL database credentials from .env file
DATABASE_HOST = os.getenv("DATABASE_HOST")
DATABASE_USER = os.getenv("DATABASE_USER")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
DATABASE_NAME = os.getenv("DATABASE_NAME")


def kill_user_connections(target_user):
    try:
        # Connect to the database as an admin user
        connection = mysql.connector.connect(
            host=DATABASE_HOST,
            user=DATABASE_USER,
            password=DATABASE_PASSWORD,
            database=DATABASE_NAME
        )

        if connection.is_connected():
            cursor = connection.cursor()

            # Query to get the connection IDs for the target user
            cursor.execute(f"""
                SELECT id FROM information_schema.processlist WHERE user = '{target_user}';
            """)
            connection_ids = cursor.fetchall()

            # Kill each connection for the target user
            for conn_id in connection_ids:
                cursor.execute(f"KILL {conn_id[0]};")
                print(f"Connection {conn_id[0]} for user '{target_user}' has been terminated.")

            print("All open connections for the user have been cleared.")
    except Error as e:
        print(f"Error while clearing connections: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection closed.")


# Replace 'noman' with the target username
kill_user_connections("nitinigi2")
