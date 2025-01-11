import psycopg2
import os
from dotenv import load_dotenv
import logging

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Database connection details
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PORT = os.getenv("DB_PORT")

EMPLOYERS_CSV_FILE_PATH = "/docker-entrypoint-initdb.d/employers.csv"
EMPLOYEES_CSV_FILE_PATH = "/docker-entrypoint-initdb.d/employees.csv"


def main():
    connection = None
    try:
        # Connect to the database
        logging.info("Connecting to the database...")
        connection = psycopg2.connect(
            host=DB_HOST,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT,
        )
        cursor = connection.cursor()

        # Step 1: Create employers and employees tables
        logging.info("Creating employers and employees tables...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS employers (
                government_id BIGINT PRIMARY KEY,
                employer_name VARCHAR(100) NOT NULL
            );
        """)

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(50) NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
            );

            """
        )
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS employees (
                personal_id BIGINT PRIMARY KEY,
                first_name VARCHAR(50),
                last_name VARCHAR(50),
                position VARCHAR(100),
                government_id BIGINT REFERENCES employers(government_id)
            );
        """)

        # Step 2: Create temporary tables
        logging.info("Creating temporary tables...")
        cursor.execute("""
            CREATE TEMP TABLE tmp_employers AS SELECT * FROM employers WITH NO DATA;
        """)
        cursor.execute("""
            CREATE TEMP TABLE tmp_employees AS SELECT * FROM employees WITH NO DATA;
        """)

        # Step 3: Load data into the temporary tables
        logging.info("Loading data into tmp_employers from the CSV file...")
        with open(EMPLOYERS_CSV_FILE_PATH, 'r') as employers_file:
            cursor.copy_expert("""
                COPY tmp_employers (government_id, employer_name)
                FROM STDIN
                DELIMITER ';'
                CSV HEADER;
            """, employers_file)

        logging.info("Loading data into tmp_employees from the CSV file...")
        with open(EMPLOYEES_CSV_FILE_PATH, 'r') as employees_file:
            cursor.copy_expert("""
                COPY tmp_employees (personal_id, first_name, last_name, position, government_id)
                FROM STDIN
                DELIMITER ';'
                CSV HEADER;
            """, employees_file)

        # Step 4: Upsert data from the temporary tables
        logging.info("Upserting data from tmp_employers to employers...")
        cursor.execute("""
            INSERT INTO employers (government_id, employer_name)
            SELECT DISTINCT government_id, employer_name FROM tmp_employers
            ON CONFLICT (government_id)
            DO UPDATE SET employer_name = EXCLUDED.employer_name;
        """)

        logging.info("Upserting data from tmp_employees to employees...")
        cursor.execute("""
            INSERT INTO employees (personal_id, first_name, last_name, position, government_id)
            SELECT DISTINCT personal_id, first_name, last_name, position, government_id FROM tmp_employees
            ON CONFLICT (personal_id)
            DO UPDATE SET
                first_name = EXCLUDED.first_name,
                last_name = EXCLUDED.last_name,
                position = EXCLUDED.position,
                government_id = EXCLUDED.government_id;
        """)

        # Step 5: Drop the temporary tables
        logging.info("Dropping temporary tables...")
        cursor.execute("DROP TABLE tmp_employers;")
        cursor.execute("DROP TABLE tmp_employees;")

        # Commit the changes
        connection.commit()
        logging.info("Data successfully loaded into the employers and employees tables.")

    except Exception as e:
        if connection:
            connection.rollback()
        logging.error(f"An error occurred: {e}")
    finally:
        if connection:
            cursor.close()
            connection.close()
            logging.info("Database connection closed.")


if __name__ == "__main__":
    main()
