from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field, ConfigDict


from src.schemas.user import UserResponse


class ContactSchema(BaseModel):
    name: str = Field(min_length=3, max_length=50)
    surname: str = Field(min_length=3, max_length=50)
    email: EmailStr
    phone: str = Field(max_length=10)
    birthday: date


class ContactUpdateSchema(BaseModel):
    email: EmailStr | None = None
    phone: str | None = Field(max_length=10, default=None)
    model_config = ConfigDict(from_attributes=True)  # noqa


class ContactResponse(BaseModel):
    id: int
    name: str
    surname: str
    email: EmailStr
    phone: str
    birthday: date
    created_at: datetime | None
    updated_at: datetime | None
    user: UserResponse | None
    model_config = ConfigDict(from_attributes=True)  # noqa
