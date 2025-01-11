from contextlib import asynccontextmanager

from fastapi import FastAPI
from app.auth.router import router as auth_router
import uvicorn
from app.database.connection import connection_pool, close_all_connections
from app.cache.redis import redis_client
from app.emloyees.router import employees_router
from app.employers.router import employers_router

app = FastAPI()

app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(employers_router, prefix="/employers", tags=["Employers"])
app.include_router(employees_router, prefix="/employees", tags=["Employees"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handle the application lifespan (startup and shutdown).
    """
    # Startup tasks
    try:
        # Check database connection
        connection = connection_pool.getconn()
        print("Database connection pool initialized.")
        connection_pool.putconn(connection)

        # Check Redis connection
        redis_client.ping()
        print("Redis connection initialized.")

    except Exception as e:
        print(f"Error during startup: {e}")
        raise

    # Yield control to the application
    yield

    # Shutdown tasks
    try:
        close_all_connections()
        print("Database connection pool closed.")
    except Exception as e:
        print(f"Error during shutdown: {e}")


@app.get("/")
def root():
    return {"message": "API is running"}


def main():
    """
    Programmatic entry point to run the FastAPI app.
    """
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)


if __name__ == "__main__":
    main()
