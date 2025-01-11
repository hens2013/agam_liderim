from fastapi import APIRouter, HTTPException
from app.schemas.auth import UserCreate, Token
from app.auth.hashing import hash_password, verify_password
from app.auth.jwt import create_access_token
from app.database.users import get_user, create_user_in_db

router = APIRouter()


@router.post("/create-user", response_model=Token)
def create_user(user: UserCreate) -> Token:
    """
    Create a new user in the database and return a JWT token.

    Args:
        user (UserCreate): The user details (username and password).

    Returns:
        Token: An access token for the newly created user.

    Raises:
        HTTPException: If the user already exists in the database.
    """
    if get_user(user.username):  # Check if user already exists
        raise HTTPException(status_code=400, detail="User already exists")

    hashed_password = hash_password(user.password)
    result = create_user_in_db(user.username, hashed_password)

    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])

    # Generate JWT token
    access_token = create_access_token({"sub": user.username})

    return Token(access_token=access_token, token_type="bearer")


@router.post("/token", response_model=Token)
def login(user: UserCreate) -> dict[str, str]:
    """
    Authenticate a user and generate an access token.

    Args:
        user (UserCreate): The user credentials (username and password).

    Returns:
        Token: An access token if authentication is successful.

    Raises:
        HTTPException: If the username or password is invalid.
    """

    db_user = get_user(user.username)

    # Verify the user's credentials
    if not db_user or not verify_password(user.password, db_user["password_hash"]):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    access_token = create_access_token({"sub": user.username})

    # Return the token as a response
    return {"access_token": access_token, "token_type": "bearer"}
