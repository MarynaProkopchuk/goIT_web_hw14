import unittest
from unittest.mock import MagicMock, Mock, AsyncMock

from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta


from src.entity.models import Contact, User
from src.schemas.contact import ContactSchema, ContactUpdateSchema, ContactResponse
from src.repository.contacts import (
    get_contacts,
    get_contact,
    create_contact,
    update_contact,
    delete_contact,
    get_upcoming_birthdays,
)


class TestContacts(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.session = MagicMock(spec=AsyncSession)
        self.user = MagicMock(spec=User)
        self.user.id = 1
        self.user._sa_instance_state = MagicMock()

    async def test_get_contacts(self):
        limit = 10
        offset = 0
        contacts = [
            Contact(
                id=1,
                name="user_1",
                surname="sur_user_1",
                email="test@email.com",
            ),
            Contact(
                id=2,
                name="user_2",
                surname="sur_user_2",
                email="test1@email.com",
            ),
        ]
        mocked_contacts = Mock()
        mocked_contacts.scalars.return_value.all.return_value = contacts
        self.session.execute.return_value = mocked_contacts
        result = await get_contacts(limit, offset, self.session, self.user)
        self.assertEqual(result, contacts)

    async def test_get_contact(self):
        contact = Contact(
            id=1,
            name="user_1",
            surname="sur_user_1",
            email="test@email.com",
        )
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = contact
        self.session.execute.return_value = result_mock

        result = await get_contact(
            contact.name,
            contact.surname,
            contact.email,
            user=self.user,
            db=self.session,
        )
        self.assertEqual(result, contact)

    async def test_create_contact(self):
        body = ContactSchema(
            name="user_1",
            surname="sur_user_1",
            email="test@email.com",
            phone="111111111",
            birthday="1986-10-25",
        )
        result = await create_contact(body, self.session, self.user)
        self.assertIsInstance(result, Contact)
        self.assertEqual(result.name, body.name)
        self.assertEqual(result.surname, body.surname)
        self.assertEqual(result.email, body.email)
        self.assertEqual(result.phone, body.phone)
        self.assertEqual(result.birthday, body.birthday)

    async def test_update_contact(self):
        body = ContactUpdateSchema(email="test@email.com", phone="111111111")
        mocked_contact = MagicMock()
        mocked_contact.scalar_one_or_none.return_value = Contact(
            name="user_1",
            surname="sur_user_1",
            email="test@email.com",
            phone="111111111",
            birthday="1986-10-25",
        )
        self.session.execute.return_value = mocked_contact
        result = await update_contact(1, body, self.session, self.user)
        self.assertIsInstance(result, Contact)
        self.assertEqual(result.phone, body.phone)
        self.assertEqual(result.email, body.email)

    async def test_delete_contact(self):
        mocked_contact = MagicMock()
        mocked_contact.scalar_one_or_none.return_value = Contact(
            id=1,
            name="user_1",
            surname="sur_user_1",
            email="test@email.com",
            phone="111111111",
            birthday="1986-10-25",
        )
        self.session.execute.return_value = mocked_contact
        result = await delete_contact(1, self.session, self.user)
        self.session.delete.assert_called_once()
        self.session.commit.assert_called_once()
        self.assertIsInstance(result, Contact)

    async def test_get_upcoming_birthdays(self):
        today = datetime.today()
        contact = Contact(
            id=1,
            name="user_1",
            surname="sur_user_1",
            email="test@email.com",
            phone="1111111111",
            birthday=today + timedelta(days=7),
            user=self.user,
        )
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [contact]
        self.session.execute.return_value = result_mock

        result = await get_upcoming_birthdays(self.session, self.user)

        self.session.execute.assert_called_once()
        self.assertEqual(result, [contact])


if __name__ == "__main__":
    unittest.main()
