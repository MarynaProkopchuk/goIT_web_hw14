from datetime import date
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserSchema(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=5, max_length=8)


class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    avatar: Optional[str] | None
    model_config = ConfigDict(from_attributes=True)  # noqa


class TokenSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RequestEmail(BaseModel):
    email: EmailStr
