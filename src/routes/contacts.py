from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.conf import messages
from src.database.db import get_db
from src.entity.models import User
from fastapi_limiter.depends import RateLimiter

from src.repository import contacts as repositories_contacts
from src.schemas.contact import ContactSchema, ContactResponse, ContactUpdateSchema
from src.services.auth import auth_service

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.get("/", response_model=list[ContactResponse])
async def get_contacts(
    limit: int = Query(10, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(auth_service.get_current_user),
):
    """Get contacts for a given user.

    :param limit: Limit of contacts to return
    :type limit: int
    :param offset: Offset of contacts to skip
    :type offset: int
    :param db: database connection
    :type db: AsyncSession
    :param user: current authenticated user
    :type user: User
    :return: List of contacts for the user
    :rtype: List[ContactResponse]"""
    contacts = await repositories_contacts.get_contacts(limit, offset, db, user)
    return contacts


@router.get("/search", response_model=ContactResponse)
async def search_contact(
    name: str = Query(None, min_length=1, max_length=50),
    surname: str = Query(None, min_length=1, max_length=50),
    email: str = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(auth_service.get_current_user),
):
    """Search for a contact by name, surname or email.

    :param name: Name of the contact
    :type name: str
    :param surname: Surname of the contact
    :type surname: str
    :param email: Email of the contact
    :type email: str
    :param db: database connection
    :type db: AsyncSession
    :param user: current authenticated user
    :type user: User
    :return: Contact matching the search criteria
    :rtype: ContactResponse"""
    if not any([name, surname, email]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one search parameter must be provided",
        )

    contact = await repositories_contacts.get_contact(name, surname, email, db, user)
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=messages.NO_CONTACT_FOUND
        )
    return contact


@router.post(
    "/",
    response_model=ContactResponse,
    dependencies=[Depends(RateLimiter(times=1, seconds=30))],
    status_code=status.HTTP_201_CREATED,
)
async def create_contact(
    body: ContactSchema,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(auth_service.get_current_user),
):
    """Create a new contact.

    :param body: Contact data
    :type body: ContactSchema
    :param db: database connection
    :type db: AsyncSession
    :param user: current authenticated user
    :type user: User
    :return: Created contact
    :rtype: ContactResponse"""
    contact = await repositories_contacts.create_contact(body, db, user)
    return contact


@router.patch("/update", response_model=ContactResponse)
async def update_contact(
    body: ContactUpdateSchema,
    name: str = Query(None, min_length=1, max_length=50),
    surname: str = Query(None, min_length=1, max_length=50),
    email: str = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(auth_service.get_current_user),
):
    """Update contact by name, surname or email.

    :param body: Contact data to update
    :type body: ContactUpdateSchema
    :param name: Name of the contact
    :type name: str
    :param surname: Surname of the contact
    :type surname: str
    :param email: Email of the contact
    :type email: str
    :param db: database connection
    :type db: AsyncSession
    :param user: current authenticated user
    :type user: User
    :return: Updated contact
    :rtype: ContactResponse"""
    if not any([name, surname, email]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one search parameter must be provided",
        )

    contact = await repositories_contacts.get_contact(name, surname, email, db, user)
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No contact found"
        )

    updated_contact = await repositories_contacts.update_contact(
        contact.id, body, db, user
    )
    if not updated_contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found"
        )
    return updated_contact


@router.delete("/delete", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    name: str = Query(None, min_length=1, max_length=50),
    surname: str = Query(None, min_length=1, max_length=50),
    email: str = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(auth_service.get_current_user),
):
    """Delete contact by name, surname or email.

    :param name: Name of the contact
    :type name: str
    :param surname: Surname of the contact
    :type surname: str
    :param email: Email of the contact
    :type email: str
    :param db: database connection
    :type db: AsyncSession
    :param user: current authenticated user
    :type user: User"""
    if not any([name, surname, email]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one search parameter must be provided",
        )
    contact = await repositories_contacts.get_contact(name, surname, email, db, user)
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No contact found"
        )
    await repositories_contacts.delete_contact(contact.id, db, user)
    return None


@router.get("/birthdays", response_model=list[ContactResponse])
async def get_upcoming_birthdays(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(auth_service.get_current_user),
):
    """Get contacts with upcoming birthdays.

    :param db: database connection
    :type db: AsyncSession
    :param user: current authenticated user
    :type user: User
    :return: List of contacts with upcoming birthdays
    :rtype: List[ContactResponse]"""
    contacts = await repositories_contacts.get_upcoming_birthdays(db, user)
    if not contacts:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=messages.BIRTHDAYS_NOT_FOUND,
        )
    return contacts
