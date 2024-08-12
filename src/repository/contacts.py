from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy import select, update, extract, and_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import Contact, User
from src.schemas.contact import ContactSchema, ContactUpdateSchema


async def get_contacts(limit: int, offset: int, db: AsyncSession, user: User):
    '''
    Get all contacts for a given contact schema.

    :param limit: Limit of contacts to return
    :type limit: int
    :param offset: Offset for pagination
    :type offset: int
    :param db: SQLAlchemy database session
    :type db: AsyncSession
    :param user: Current user
    :type user: User
    :returns: a list of contacts
    :rtype: list[Contact]

    '''
    stmt = select(Contact).filter_by(user=user).offset(offset).limit(limit)
    contacts = await db.execute(stmt)
    return contacts.scalars().all()


async def get_contact(name: str, surname: str, email: str, db: AsyncSession, user: User):
    '''
    Get a contact from the database and return the contact.

    :param name: Name of the contact
    :type name: str
    :param surname: Surname of the contact
    :type surname: str
    :param email: Email of the contact
    :type email: str
    :param db: SQLAlchemy database session
    :type db: AsyncSession
    :param user: User to get the contact
    :type user: User
    :returns: Contact if found, otherwise None
    :rtype: Optional[Contact]

    '''

    query = select(Contact).filter_by(user=user)

    if name:
        query = query.filter(Contact.name.ilike(f"%{name}%"))
    if surname:
        query = query.filter(Contact.surname.ilike(f"%{surname}%"))
    if email:
        query = query.filter(Contact.email.ilike(f"%{email}%"))

    contact = await db.execute(query)
    return contact.scalar_one_or_none()


async def create_contact(body: ContactSchema, db: AsyncSession, user: User):
    '''
    Create a new contact in the database and return the new contact.

    :param body: Contact data
    :type body: ContactSchema
    :param db: SQLAlchemy database session
    :type db: AsyncSession
    :param user: Current user
    :type user: User
    :returns: Newly created contact
    :rtype: Contact

    '''

    contact = Contact(**body.model_dump(exclude_unset=True), user=user)
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return contact


async def update_contact(contact_id: int, body: ContactUpdateSchema, db: AsyncSession, user: User):
    '''
    Update contact information for a contact with a given contact id.

    :param contact_id: ID of the contact to update
    :type contact_id: int
    :param body: Contact update schema
    :type body: ContactUpdateSchema
    :param db: SQLAlchemy database session
    :type db: AsyncSession
    :param user: current user
    :type user: User
    :returns: updated contact information
    :rtype: Optional[Contact]

    '''

    update_data = body.dict(exclude_unset=True)
    stmt = (
        update(Contact)
        .where(Contact.id == contact_id)
        .values(**update_data)
        .execution_options(synchronize_session="fetch")
    )
    try:
        result = await db.execute(stmt)
        await db.commit()
    except SQLAlchemyError as e:
        await db.rollback()
        raise e

    if result.rowcount == 0:
        return None
    stmt = select(Contact).filter_by(id=contact_id, user=user)
    updated_contact = await db.execute(stmt)
    return updated_contact.scalar_one_or_none()


async def delete_contact(contact_id: int, db: AsyncSession, user: User):
    '''
    Delete a contact from the database by contact id.

    :param contact_id: ID of the contact to delete
    :type contact_id: int
    :param db: SQLAlchemy database session
    :type db: AsyncSession
    :param user: Current user
    :type user: User
    :returns: Deleted contact if found, otherwise None
    :rtype: Optional[Contact]

    '''

    stmt = select(Contact).filter_by(id=contact_id, user=user)
    contact = await db.execute(stmt)
    contact = contact.scalar_one_or_none()
    if contact:
        await db.delete(contact)
        await db.commit()
    return contact


async def get_upcoming_birthdays(db: AsyncSession, user: User):
    '''
    Get all contacts with upcoming birthdays for the current week.

    :param db: SQLAlchemy database session
    :type db: AsyncSession
    :param user: Current user
    :type user: User
    :returns: list of upcoming birthdays
    :rtype: list[Contact]

    '''

    today = datetime.today()
    today_month = today.month
    today_day = today.day

    next_week = today + timedelta(days=7)
    next_week_month = next_week.month
    next_week_day = next_week.day

    stmt = select(Contact).filter_by(user=user).where(
        and_(
            (extract("month", Contact.birthday) == today_month)
            & (extract("day", Contact.birthday) >= today_day)
            | (extract("month", Contact.birthday) == next_week_month)
            & (extract("day", Contact.birthday) <= next_week_day)
            | (extract("month", Contact.birthday) > today_month)
            & (extract("month", Contact.birthday) < next_week_month)
        )
    )
    result = await db.execute(stmt)
    return result.scalars().all()
