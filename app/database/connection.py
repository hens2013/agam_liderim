import psycopg2
from psycopg2 import pool
import os
from dotenv import load_dotenv
from typing import Optional, Any
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

load_dotenv()

# Database configuration
connection_pool: Optional[pool.SimpleConnectionPool] = None
DB_CONFIG: dict[str, Optional[str]] = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
}

try:
    connection_pool = psycopg2.pool.SimpleConnectionPool(
        1, 20,  # Minimum and maximum connections
        dbname=DB_CONFIG["dbname"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"]
    )

    if connection_pool:
        logging.info("Connection pool created successfully!")

except Exception as e:
    logging.error("Error while creating the connection pool: %s", e)


def get_connection() -> Optional[Any]:
    """
    Get a connection from the pool.

    Returns:
        Optional[Any]: A connection object from the pool or None if an error occurs.
    """
    try:
        connection = connection_pool.getconn() if connection_pool else None
        if connection:
            logging.info("Connection retrieved from pool")
        return connection
    except Exception as e:
        logging.error("Error while getting connection: %s", e)
        return None


def release_connection(connection: Optional[Any]) -> None:
    """
    Release a connection back to the pool.

    Args:
        connection (Optional[Any]): The connection object to be released.
    """
    try:
        if connection and connection_pool:
            connection_pool.putconn(connection)
            logging.info("Connection released back to pool")
    except Exception as e:
        logging.error("Error while releasing connection: %s", e)


def close_all_connections() -> None:
    """
    Close all connections in the pool.
    """
    try:
        if connection_pool:
            connection_pool.closeall()
            logging.info("All connections closed successfully!")
    except Exception as e:
        logging.error("Error while closing connections: %s", e)
