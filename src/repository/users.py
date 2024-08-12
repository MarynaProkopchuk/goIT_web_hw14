from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.entity.models import User
from src.schemas.user import UserSchema


async def get_user_by_email(email: str, db: AsyncSession):
    ''' Get a user by email from the database.

    :param email: The email
    :type email: str
    :param db: The database session
    :type db: AsyncSession
    :return: User object if found, None otherwise
     :rtype: User | None'''

    try:
        stmt = select(User).filter_by(email=email)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        return user
    except Exception as e:
        print(f"Error in get_user_by_email: {e}")
        raise


async def create_user(body: UserSchema, db: AsyncSession):
    ''' Create a new user in the database.

    :param body: User data
    :type body: UserSchema
    :param db: The database session
    :type db: AsyncSession
    :return: Created user
    :rtype: UserSchema'''

    avatar = None
    try:
        new_user = User(**body.dict())
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        return new_user
    except Exception as e:
        print(f"Error in create_user: {e}")
        raise


async def update_token(user: User, token: str | None, db: AsyncSession):
    ''' Update user's refresh token.

    :param user: The user
    :type user: User
    :param token: The refresh token
    :type token: str | None
    :param db: The database session
    :type db: AsyncSession
    '''
    user.refresh_token = token
    await db.commit()


async def confirmed_email(email: str, db: AsyncSession) -> None:
    ''' Confirm user's email.

    :param email: The email
    :type email: str
    :param db: The database session
    :type db: AsyncSession'''

    user = await get_user_by_email(email, db)
    user.confirmed = True
    await db.commit()


async def update_avatar(email, url: str, db: AsyncSession) -> User:
    ''' Update user's avatar.

    :param email: users email
    :type email: str
    :param url: The avatar URL
    :type url: str
    :param db: The database session
    :type db: AsyncSession
    :return: The updated user
    :rtype: User'''

    user = await get_user_by_email(email, db)
    user.avatar = url
    await db.commit()
    await db.refresh(user)
    return user
