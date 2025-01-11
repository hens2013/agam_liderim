from datetime import datetime, timedelta
from typing import Optional, Callable, Dict, Any
import time
from fastapi.security import OAuth2PasswordBearer
from fastapi import HTTPException, Request, status, Depends
from functools import wraps
import jwt
from jose import JWTError


import os

from dotenv import load_dotenv

load_dotenv()
# Constants for JWT configuration
SECRET_KEY: str = os.getenv("SECRET_KEY")
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
JWT_SECRET: str =  os.getenv("JWT_SECRET")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data (Dict[str, Any]): The payload data to include in the token.
        expires_delta (Optional[timedelta]): Custom expiration time for the token.
            Defaults to ACCESS_TOKEN_EXPIRE_MINUTES.

    Returns:
        str: The encoded JWT token.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_jwt(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and validate a JWT token.

    Args:
        token (str): The JWT token to decode.

    Returns:
        Optional[Dict[str, Any]]: The decoded token payload if valid, None if expired or invalid.

    Raises:
        HTTPException: If the token has expired or is invalid.
    """
    try:
        # Decode the token and validate its signature
        decoded_token = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])

        # Check if the token has expired
        if decoded_token.get("exp", 0) < time.time():
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")

        return decoded_token  # Return the decoded payload
    except jwt.ExpiredSignatureError:
        # Raised if the token's 'exp' claim has expired
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    except jwt.InvalidTokenError:
        # Raised for any other issues with the token
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


def requires_auth(func: Callable) -> Callable:
    """
    Decorator to require authentication for an endpoint.

    Args:
        func (Callable): The function to wrap with authentication.

    Returns:
        Callable: The wrapped function.

    Raises:
        HTTPException: If the token is invalid or missing.
    """
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs) -> Any:
        try:
            # Extract the token using the OAuth2 scheme
            token: str = await oauth2_scheme(request)

            # Decode the JWT token
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username = payload.get("sub")
            if not username:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials",
                )
            # Pass the username to the wrapped function
            return await func(request, *args, **kwargs)  # Forward all arguments
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )
    return wrapper
