from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.security import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from app.db.database import get_db
from app.db.crud import (
    authenticate_user, create_user,
    get_user_by_email, get_user_by_username
)
from app.schemas.user import Token, UserCreate, UserResponse

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post(
    "/register", response_model=UserResponse,
    status_code=status.HTTP_201_CREATED)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user.

    Parameters:
    - **user**: User information including username, email, and password

    Returns:
    - **User information**: Created user details (excluding password)

    Raises:
    - **400 Bad Request**: When username or email is already registered

    Example:
    ```
    {
      "username": "johndoe",
      "email": "john@example.com",
      "password": "securepassword123"
    }
    ```
    """
    # Check if username already exists
    db_user = get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    # Check if email already exists
    db_user = get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create new user
    return create_user(db=db, user=user)


@router.post("/login", response_model=Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    OAuth2 compatible token login, get an access token for future requests.

    Parameters:
    - **username**: User's username
    - **password**: User's password

    Returns:
    - **access_token**: JWT token to be used for authenticated endpoints
    - **token_type**: Type of the token (bearer)

    Raises:
    - **401 Unauthorized**: When credentials are invalid

    Example request (form-data):
    ```
    username=johndoe&password=securepassword123
    ```

    Example response:
    ```
    {
      "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "token_type": "bearer"
    }
    ```
    """
    # Authenticate user
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}
