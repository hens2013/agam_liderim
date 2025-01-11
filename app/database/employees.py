from typing import Optional, List, Dict, Union, Tuple
from app.database.connection import get_connection, release_connection
from app.cache.redis import redis_client, CACHE_EXPIRATION
from app.schemas.employees import EmployeeCreate
import json
import re
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def search_employees_in_db(
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 10
) -> List[Dict[str, Union[int, str, None]]]:
    """
    Search employees across multiple fields, including personal_id, using a single search term.
    Supports numeric and text-based searches. Results are sorted by similarity,
    paginated, and cached for 1 minute.

    Args:
        search (Optional[str]): The search term.
        skip (int): Number of records to skip for pagination.
        limit (int): Maximum number of records to return.

    Returns:
        List[Dict[str, Union[int, str, None]]]: A list of employee dictionaries.
    """
    cache_key = f"search_employees:{search}:{skip}:{limit}"
    cached_results = redis_client.get(cache_key)
    if cached_results:
        logging.info("Returning cached results for search query.")
        return json.loads(cached_results)

    connection = get_connection()
    try:
        cursor = connection.cursor()

        if search:
            search_clean = search.strip()
            ts_query = re.sub(r"[^\w\s]", "", search_clean)
            is_numeric = search_clean.isdigit()

            if is_numeric:
                query = """
                    SELECT
                        personal_id,
                        first_name,
                        last_name,
                        position,
                        government_id,
                        ts_rank_cd(
                            setweight(to_tsvector('english', first_name), 'A') ||
                            setweight(to_tsvector('english', last_name), 'A') ||
                            setweight(to_tsvector('english', position), 'B') ||
                            setweight(to_tsvector('english', COALESCE(government_id::TEXT, '')), 'C'),
                            plainto_tsquery('english', %s)
                        ) AS rank
                    FROM employees
                    WHERE
                        personal_id::TEXT = %s OR
                        government_id::TEXT = %s OR
                        to_tsvector('english', first_name || ' ' || last_name || ' ' || position || ' ' || COALESCE(government_id::TEXT, ''))
                        @@ plainto_tsquery('english', %s)
                    ORDER BY rank DESC
                    LIMIT %s OFFSET %s;
                """
                query_params = [ts_query, search_clean, search_clean, ts_query, limit, skip]
            else:
                query = """
                    SELECT
                        personal_id,
                        first_name,
                        last_name,
                        position,
                        government_id,
                        ts_rank_cd(
                            setweight(to_tsvector('english', first_name), 'A') ||
                            setweight(to_tsvector('english', last_name), 'A') ||
                            setweight(to_tsvector('english', position), 'B') ||
                            setweight(to_tsvector('english', COALESCE(government_id::TEXT, '')), 'C'),
                            plainto_tsquery('english', %s)
                        ) AS rank
                    FROM employees
                    WHERE
                        to_tsvector('english', first_name || ' ' || last_name || ' ' || position || ' ' || COALESCE(government_id::TEXT, ''))
                        @@ plainto_tsquery('english', %s)
                    ORDER BY rank DESC
                    LIMIT %s OFFSET %s;
                """
                query_params = [ts_query, ts_query, limit, skip]

            logging.info(f"Executing query: {query}")
            logging.info(f"With parameters: {query_params}")
            cursor.execute(query, query_params)
        else:
            query = """
                SELECT
                    personal_id,
                    first_name,
                    last_name,
                    position,
                    government_id
                FROM employees
                ORDER BY first_name ASC
                LIMIT %s OFFSET %s;
            """
            query_params = [limit, skip]

            logging.info(f"Executing default query: {query}")
            logging.info(f"With parameters: {query_params}")
            cursor.execute(query, query_params)

        rows = cursor.fetchall()
        logging.info(f"Raw rows returned: {rows}")

        employees = []

        for row in rows:
            if len(row) < 5:
                logging.warning(f"Skipping malformed row: {row}")
                continue

            employees.append({
                "personal_id": row[0],
                "first_name": row[1],
                "last_name": row[2],
                "position": row[3],
                "government_id": row[4] if row[4] is not None else None
            })

        redis_client.setex(cache_key, CACHE_EXPIRATION, json.dumps(employees))
        return employees

    except Exception as e:
        logging.error(f"Error querying employees: {e}")
        raise
    finally:
        release_connection(connection)


def create_employee_in_db(employeeCreate: EmployeeCreate) -> Dict[str, Union[int, str]]:
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO employees (personal_id, first_name, last_name, position)
            VALUES (%s, %s, %s, %s) RETURNING personal_id, first_name, last_name, position;
            """,
            (employeeCreate.personal_id, employeeCreate.first_name, employeeCreate.last_name, employeeCreate.position)
        )
        new_employee = cursor.fetchone()
        connection.commit()
        logging.info(f"Employee created: {new_employee}")
        return {
            "personal_id": new_employee[0],
            "first_name": new_employee[1],
            "last_name": new_employee[2],
            "position": new_employee[3]
        }
    except Exception as e:
        connection.rollback()
        logging.error(f"Error creating employee: {e}")
        raise
    finally:
        release_connection(connection)


def attach_employee_to_employer(
    employee_personal_id: int,
    employer_government_id: int
) -> Tuple[Optional[Dict[str, Optional[str]]], Optional[str]]:
    connection = get_connection()
    try:
        cursor = connection.cursor()

        update_query = """
            UPDATE employees
            SET government_id = %s
            WHERE personal_id = %s
            RETURNING personal_id;
        """
        cursor.execute(update_query, (employer_government_id, employee_personal_id))
        updated_employee_id = cursor.fetchone()

        if not updated_employee_id:
            return None, f"Employee with personal ID {employee_personal_id} not found"

        fetch_query = """
            SELECT personal_id, first_name, last_name, position, government_id
            FROM employees
            WHERE personal_id = %s;
        """
        cursor.execute(fetch_query, (employee_personal_id,))
        updated_employee = cursor.fetchone()

        connection.commit()

        if updated_employee:
            return {
                "personal_id": updated_employee[0],
                "first_name": updated_employee[1],
                "last_name": updated_employee[2],
                "position": updated_employee[3],
                "government_id": updated_employee[4]
            }, None

        return None, "Error retrieving updated employee data"

    except Exception as e:
        connection.rollback()
        logging.error(f"Error attaching employee to employer: {e}")
        return None, str(e)
    finally:
        release_connection(connection)
