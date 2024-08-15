from unittest.mock import Mock

import pytest
from sqlalchemy import select
from fastapi import status

from src.conf import messages
from src.entity.models import User
from src.services.auth import auth_service
from tests.conftest import TestingSessionLocal


user_data = {
    "username": "testuser1",
    "email": "testuser1@example.com",
    "password": "secret",
}


def test_signup(client, monkeypatch):
    mock_send_email = Mock()
    monkeypatch.setattr("src.routes.auth.send_email", mock_send_email)
    response = client.post("api/auth/signup", json=user_data)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["username"] == user_data["username"]
    assert data["email"] == user_data["email"]
    assert "password" not in data


def test_signup_existing_user(client, monkeypatch):
    response = client.post("api/auth/signup", json=user_data)
    assert response.status_code == 409, response.text
    data = response.json()
    assert data["detail"] == messages.ACCOUNT_EXIST


def test_not_confirmed_login(client):
    response = client.post(
        "api/auth/login",
        data={
            "username": user_data.get("email"),
            "password": user_data.get("password"),
        },
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == messages.UNCONFIRMED_EMAIL


@pytest.mark.asyncio
async def test_login(client):
    async with TestingSessionLocal() as session:
        current_user = await session.execute(
            select(User).where(User.email == user_data.get("email"))
        )
        current_user = current_user.scalar_one_or_none()
        if current_user:
            current_user.confirmed = True
            await session.commit()
    response = client.post(
        "api/auth/login",
        data={
            "username": user_data.get("email"),
            "password": user_data.get("password"),
        },
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_login_wrong_password(client):
    response = client.post(
        "api/auth/login",
        data={
            "username": user_data.get("email"),
            "password": "wrong_password",
        },
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == messages.INVALID_PASSWORD


def test_login_wrong_email(client):
    response = client.post(
        "api/auth/login",
        data={
            "username": "wrong_email",
            "password": user_data.get("password"),
        },
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == messages.INVALID_EMAIL


def test_refresh_token(client):
    response = client.post(
        "api/auth/refresh_token",
        headers={"Authorization": "Bearer token"},
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == messages.INVALID_REFRESH_TOKEN
