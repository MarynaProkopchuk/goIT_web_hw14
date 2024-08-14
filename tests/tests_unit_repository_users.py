import unittest
from unittest.mock import MagicMock, Mock, AsyncMock, patch

from sqlalchemy.ext.asyncio import AsyncSession


from src.entity.models import User
from src.schemas.user import UserSchema
from src.repository.users import (
    get_user_by_email,
    create_user,
    update_token,
    confirmed_email,
    update_avatar,
)


class TestUsers(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.session = MagicMock(spec=AsyncSession)
        self.user = MagicMock(spec=User)

    async def test_get_user_by_email(self):
        user = User(email="test@email.com")
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = user
        self.session.execute.return_value = result_mock

        result = await get_user_by_email(user.email, db=self.session)
        self.assertEqual(result, user)

    async def test_create_user(self):
        body = UserSchema(
            username="test_user", email="test@email.com", password="secret"
        )
        result = await create_user(body, self.session)
        self.assertIsInstance(result, User)
        self.assertEqual(result.email, body.email)
        self.assertEqual(result.password, body.password)

    async def test_update_token(self):
        token = "new_refresh_token"
        self.user.refresh_token = None
        await update_token(self.user, token, self.session)
        self.assertEqual(self.user.refresh_token, token)
        self.session.commit.assert_awaited_once()

    @patch("src.repository.users.get_user_by_email")
    async def test_confirmed_email(self, mock_get_user_by_email):
        email = "test@email.com"
        mock_get_user_by_email.return_value = self.user
        await confirmed_email(email, self.session)
        self.assertTrue(self.user.confirmed)
        self.session.commit.assert_awaited_once()

    @patch("src.repository.users.get_user_by_email")
    async def test_update_avatar(self, mock_get_user_by_email):
        email = "test@email.com"
        avatar = "test_avatar_url"
        mock_get_user_by_email.return_value = self.user
        result = await update_avatar(email, avatar, self.session)
        self.assertEqual(self.user.avatar, avatar)
        self.session.commit.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
