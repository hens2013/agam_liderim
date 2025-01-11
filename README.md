
# Project Name

## Overview
This project is a containerized application built using Docker and Docker Compose. It includes modules for authentication, caching, database interactions, and APIs for managing employees and employers.

---

## Table of Contents
1. [Setup Instructions](#setup-instructions)
2. [API Endpoint Documentation](#api-endpoint-documentation)
3. [Database Schema](#database-schema)
4. [Alert Criteria Explanation](#alert-criteria-explanation)

---

## Setup Instructions

### Prerequisites
- [Docker](https://www.docker.com/get-started) installed on your system.
- [Docker Compose](https://docs.docker.com/compose/install/) installed.
- Python 3.11 (if running outside Docker).

### Environment Variables
1. Copy the `.env` file and configure the necessary variables:
   ```bash
   cp .env.example .env
   ```
   Update the variables as needed.

### Build and Run
1. Build and start the containers:
   ```bash
   docker-compose up --build
   ```
2. The application will be available at [http://localhost:8000](http://localhost:8000).

### Running the Application Locally
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the application:
   ```bash
   python app/main.py
   ```

---

## API Endpoint Documentation

### Authentication Endpoints
#### 1. **Login**
   - **URL:** `/auth/login`
   - **Method:** `POST`
   - **Body:**
     ```json
     {
       "username": "string",
       "password": "string"
     }
     ```
   - **Response:**
     ```json
     {
       "access_token": "string",
       "token_type": "bearer"
     }
     ```

#### 2. **Register**
   - **URL:** `/auth/register`
   - **Method:** `POST`
   - **Body:**
     ```json
     {
       "username": "string",
       "password": "string",
       "email": "string"
     }
     ```

---

### Employee Endpoints
#### 1. **Get All Employees**
   - **URL:** `/employees/`
   - **Method:** `GET`
   - **Response:**
     ```json
     [
       {
         "id": "int",
         "name": "string",
         "position": "string"
       }
     ]
     ```

#### 2. **Add Employee**
   - **URL:** `/employees/add`
   - **Method:** `POST`
   - **Body:**
     ```json
     {
       "name": "string",
       "position": "string"
     }
     ```
   - **Response:** Status Code `201 Created`

---

### Employer Endpoints
#### 1. **Get All Employers**
   - **URL:** `/employers/`
   - **Method:** `GET`
   - **Response:**
     ```json
     [
       {
         "id": "int",
         "company_name": "string",
         "industry": "string"
       }
     ]
     ```

#### 2. **Add Employer**
   - **URL:** `/employers/add`
   - **Method:** `POST`
   - **Body:**
     ```json
     {
       "company_name": "string",
       "industry": "string"
     }
     ```
   - **Response:** Status Code `201 Created`

---

## Database Schema

### Tables

#### 1. **users**
- **Columns:**
  - `id`: Serial primary key.
  - `username`: String (max length 50), unique.
  - `password_hash`: Text, stores hashed passwords.
  - `created_at`: Timestamp, records the user creation date.

#### 2. **employees**
- **Columns:**
  - `personal_id`: BigInt, primary key.
  - `first_name`: String (max length 50), employee's first name.
  - `last_name`: String (max length 50), employee's last name.
  - `position`: String (max length 100), job position of the employee.
  - `government_id`: BigInt, foreign key referencing `employers.government_id`.

#### 3. **employers**
- **Columns:**
  - `government_id`: BigInt, primary key.
  - `employer_name`: String (max length 100), name of the employer.

### Relationships
- `employees.government_id` references `employers.government_id`.
- Users table is independent but can be linked via application logic for ownership or role-based access control.

---
