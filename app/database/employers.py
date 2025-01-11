from typing import List, Dict, Optional, Union
from app.database.connection import get_connection, release_connection
from app.cache.redis import redis_client
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

CACHE_EXPIRATION = 60


class Employer:
    def __init__(self, employer_name: str, government_id: Optional[int] = None):
        self.employer_name = employer_name
        self.government_id = government_id


def create_employer_in_db(employer: Employer) -> Dict[str, Union[int, str]]:
    """
    Insert a new employer into the database.

    Args:
        employer (Employer): An Employer object containing employer_name and government_id.

    Returns:
        Dict[str, Union[int, str]]: A dictionary containing the created employer's details.
    """
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO employers (employer_name, government_id)
            VALUES (%s, %s)
            RETURNING employer_name, government_id;
            """,
            (employer.employer_name, employer.government_id),
        )
        new_employer = cursor.fetchone()
        connection.commit()
        logging.info(f"Employer created: {new_employer}")
        return {"employer_name": new_employer[0], "government_id": new_employer[1]}
    except Exception as e:
        logging.error(f"Error creating employer: {e}")
        raise
    finally:
        release_connection(connection)


def search_employers(search: Optional[str] = None, skip: int = 0, limit: int = 10) -> List[Dict[str, Union[int, str]]]:
    """
    Search employers by name or government_id using a single search term.
    Supports full-text and numeric searches. Results are paginated and cached.

    Args:
        search (Optional[str]): The search term.
        skip (int): Number of records to skip for pagination.
        limit (int): Maximum number of records to return.

    Returns:
        List[Dict[str, Union[int, str]]]: A list of employer dictionaries.
    """
    cache_key = f"search_employers:{search}:{skip}:{limit}"

    cached_results = redis_client.get(cache_key)
    if cached_results:
        logging.info("Returning cached results for search query.")
        return json.loads(cached_results)

    connection = get_connection()
    try:
        cursor = connection.cursor()

        if search:
            search_clean = search.strip()
            is_numeric = search_clean.isdigit()

            if is_numeric:
                query = """
                SELECT employer_name, government_id
                FROM employers
                WHERE government_id::TEXT = %s
                LIMIT %s OFFSET %s;
                """
                query_params = [search_clean, limit, skip]
            else:
                query = """
                SELECT employer_name, government_id
                FROM employers
                WHERE to_tsvector('english', employer_name)
                      @@ plainto_tsquery('english', %s)
                LIMIT %s OFFSET %s;
                """
                query_params = [search_clean, limit, skip]

            logging.info(f"Executing query: {query}")
            logging.info(f"With parameters: {query_params}")
            cursor.execute(query, query_params)
        else:
            query = """
            SELECT employer_name, government_id
            FROM employers
            ORDER BY employer_name ASC
            LIMIT %s OFFSET %s;
            """
            query_params = [limit, skip]

            logging.info(f"Executing default query: {query}")
            logging.info(f"With parameters: {query_params}")
            cursor.execute(query, query_params)

        rows = cursor.fetchall()
        logging.info(f"Raw rows returned: {rows}")

        employers = [
            {
                "employer_name": row[0],
                "government_id": row[1]
            }
            for row in rows
        ]

        redis_client.setex(cache_key, CACHE_EXPIRATION, json.dumps(employers))
        return employers

    except Exception as e:
        logging.error(f"Error querying employers: {e}")
        raise
    finally:
        release_connection(connection)


def get_employer_by_name(employer_name: str) -> Optional[Dict[str, int]]:
    """
    Retrieve an employer by name.

    Args:
        employer_name (str): The employer name to search for.

    Returns:
        Optional[Dict[str, int]]: A dictionary with the employer ID if found, otherwise None.
    """
    connection = get_connection()
    try:
        cursor = connection.cursor()
        query = "SELECT id FROM employers WHERE employer_name = %s;"
        cursor.execute(query, (employer_name,))
        employer = cursor.fetchone()
        logging.info(f"Employer found: {employer}" if employer else "Employer not found.")
        return {"id": employer[0]} if employer else None
    except Exception as e:
        logging.error(f"Error retrieving employer by name: {e}")
        raise
    finally:
        release_connection(connection)
