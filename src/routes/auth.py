from fastapi import (
    APIRouter,
    HTTPException,
    Depends,
    status,
    Security,
    BackgroundTasks,
    Request,
)
from fastapi.security import (
    OAuth2PasswordRequestForm,
    HTTPAuthorizationCredentials,
    HTTPBearer,
)

from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db

from src.repository import users as repositories_users
from src.schemas.user import UserSchema, UserResponse, TokenSchema, RequestEmail
from src.services.auth import auth_service
from src.services.email import send_email

router = APIRouter(prefix="/auth", tags=["auth"])
get_refresh_token = HTTPBearer()


@router.post(
    "/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def signup(
    body: UserSchema,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    ''' Signup a user to the application and add it to the database.

    :param body: user information
    :type body: UserSchema
    :param background_tasks: background tasks for sending emails
    :type background_tasks: BackgroundTasks
    :param request: request
    :type request: Request
    :param db: database
    :type db: AsyncSession
    :returns: new user
    :rtype: UserResponse'''
    exist_user = await repositories_users.get_user_by_email(body.email, db)
    if exist_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Account already exists"
        )
    else:
        body.password = auth_service.get_password_hash(body.password)
        new_user = await repositories_users.create_user(body, db)
        background_tasks.add_task(
            send_email, new_user.email, new_user.username, str(request.base_url)
        )
        return new_user


@router.post("/login")
async def login(
    body: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    ''' Login the user with the specified password.

    :param body: user credentials
    :type body: OAuth2PasswordRequestForm
    :param db: database
    :type db: AsyncSession
    :returns: access token and refresh token
    :rtype: TokenSchema'''
    user = await repositories_users.get_user_by_email(body.username, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email"
        )
    if not user.confirmed:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Email not confirmed"
        )
    if not auth_service.verify_password(body.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password"
        )
    # Generate JWT
    access_token = await auth_service.create_access_token(data={"sub": user.email})
    refresh_token = await auth_service.create_refresh_token(data={"sub": user.email})
    await repositories_users.update_token(user, refresh_token, db)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh_token", response_model=TokenSchema)
async def refresh_token(
    credentials: HTTPAuthorizationCredentials = Security(get_refresh_token),
    db: AsyncSession = Depends(get_db),
):
    ''' Refresh token for the given credentials and database connection.

    :param credentials: The credentials to refresh the token for the given credentials
    :type credentials: HTTPAuthorizationCredentials
    :param db: The database connection
    :type db: AsyncSession
    :returns: The new access and refresh tokens
    :rtype: HTTPAuthorizationCredentials'''

    token = credentials.credentials
    try:
        email = await auth_service.decode_refresh_token(token)
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    user = await repositories_users.get_user_by_email(email, db)
    if user is None or user.refresh_token != token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    access_token = await auth_service.create_access_token(data={"sub": email})
    refresh_token = await auth_service.create_refresh_token(data={"sub": email})
    await repositories_users.update_token(user, refresh_token, db)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.get("/confirmed_email/{token}")
async def confirmed_email(token: str, db: AsyncSession = Depends(get_db)):
    ''' Confirm the user's email  address and password from the database.

    :param token: email verification token
    :type token: str
    :param db: database connection
    :type db: AsyncSession
    :returns: confirmation message
    :rtype: str'''
    email = await auth_service.get_email_from_token(token)
    user = await repositories_users.get_user_by_email(email, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error"
        )
    if user.confirmed:
        return {"message": "Your email is already confirmed"}
    await repositories_users.confirmed_email(email, db)
    return {"message": "Email confirmed"}


@router.post("/request_email")
async def request_email(
    body: RequestEmail,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    ''' Send a confirmation email to the user's email address from the database.

    :param body: user email address
    :type body: RequestEmail
    :param background_tasks: background tasks for sending emails
    :type background_tasks: BackgroundTasks
    :param request: request
    :type request: Request
    :param db: database connection
    :type db: AsyncSession
    :returns: confirmation message
    :rtype: str'''
    user = await repositories_users.get_user_by_email(body.email, db)

    if user.confirmed:
        return {"message": "Your email is already confirmed"}
    if user:
        background_tasks.add_task(
            send_email, user.email, user.username, str(request.base_url)
        )
    return {"message": "Check your email for confirmation."}
