# Use the official Python 3.11 image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies for PostgreSQL
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the application files to the container
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the init scripts and data files to the container
COPY scripts/employers.csv /docker-entrypoint-initdb.d/employers.csv
COPY scripts/employees.csv /docker-entrypoint-initdb.d/employees.csv
COPY scripts/load_data.py /app/load_data.py

# Run the Python script to initialize the database
CMD ["bash", "-c", "python /app/load_data.py && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"]
