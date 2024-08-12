import cloudinary
import cloudinary.uploader
from fastapi import (
    APIRouter,
    Depends,
    UploadFile,
    File,
)

from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.entity.models import User
from src.schemas.user import UserResponse
from src.services.auth import auth_service
from src.conf.config import config
from src.repository import users as repositories_users

router = APIRouter(prefix="/users", tags=["users"])
cloudinary.config(
    cloud_name=config.CLOUDINARY_NAME,
    api_key=config.CLOUDINARY_IP_KEY,
    api_secret=config.CLOUDINARY_IP_SECRET,
    secure=True,
)


@router.get("/me/", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(auth_service.get_current_user)):
    '''Read user information from the database.

    :param current_user: user
    :type current_user: User
    :return: user information
    :rtype: UserResponse'''
    return current_user


@router.patch("/avatar", response_model=UserResponse)
async def update_avatar_user(
    file: UploadFile = File(),
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db),
):
    '''Update user avatar.

    :param file: uploaded file
    :type file: UploadFile
    :param current_user: user
    :type current_user: User
    :param db: database session
    :type db: AsyncSession
    :return: updated user information
    :rtype: UserResponse'''

    r = cloudinary.uploader.upload(
        file.file, public_id=f"NotesApp/{current_user.username}", overwrite=True
    )
    src_url = cloudinary.CloudinaryImage(f"NotesApp/{current_user.username}").build_url(
        width=250, height=250, crop="fill", version=r.get("version")
    )
    user = await repositories_users.update_avatar(current_user.email, src_url, db)
    return user
