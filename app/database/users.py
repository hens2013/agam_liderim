import psycopg2
from psycopg2.extras import RealDictCursor
from app.database.connection import get_connection, release_connection
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

def get_user(username: str):
    """
    Check if a user exists in the database by username.

    Args:
        username (str): The username to check.

    Returns:
        dict: User data if found, None otherwise.
    """
    connection = get_connection()
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM users WHERE username = %s;", (username,))
        user = cursor.fetchone()
        if user:
            logging.info(f"User '{username}' found in the database.")
        else:
            logging.warning(f"User '{username}' not found in the database.")
        return user
    except Exception as e:
        logging.error(f"Error fetching user '{username}': {e}")
        raise
    finally:
        release_connection(connection)


def create_user_in_db(username: str, hashed_password: str):
    """
    Insert a new user into the database and return success or error messages.

    Args:
        username (str): The username to create.
        hashed_password (str): The hashed password for the user.

    Returns:
        dict: A dictionary containing the status and message of the operation.
    """
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO users (username, password_hash)
            VALUES (%s, %s);
            """,
            (username, hashed_password),
        )
        connection.commit()
        logging.info(f"User '{username}' created successfully.")
        return {"status": "success", "message": f"User '{username}' created successfully."}
    except Exception as e:
        logging.error(f"Error creating user '{username}': {e}")
        return {"status": "error", "message": str(e)}
    finally:
        release_connection(connection)
