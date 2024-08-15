from unittest.mock import Mock, patch, AsyncMock

import pytest

from src.entity.models import Contact
from tests.conftest import client, test_user, TestingSessionLocal

from src.services.auth import auth_service


def test_get_contacts(client, get_token):
    token = get_token
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("api/contacts", headers=headers)
    assert response.status_code == 200, response.text
    data = response.json()
    assert len(data) == 0


def test_create_contact(client, get_token, monkeypatch):
    monkeypatch.setattr("fastapi_limiter.FastAPILimiter.redis", AsyncMock())
    monkeypatch.setattr("fastapi_limiter.FastAPILimiter.identifier", AsyncMock())
    monkeypatch.setattr("fastapi_limiter.FastAPILimiter.http_callback", AsyncMock())
    token = get_token
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post(
        "api/contacts",
        json={
            "name": "test",
            "surname": "test",
            "email": "test@test.com",
            "phone": "111111111",
            "birthday": "1986-10-25",
        },
        headers=headers,
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["name"] == "test"
    assert data["surname"] == "test"
    assert data["email"] == "test@test.com"
    assert data["phone"] == "111111111"
    assert data["birthday"] == "1986-10-25"
