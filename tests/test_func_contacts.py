from unittest.mock import Mock, patch, AsyncMock

import pytest
import pytest_asyncio

from src.conf import messages
from src.entity.models import Contact
from tests.conftest import client, test_user, TestingSessionLocal

from src.services.auth import auth_service

contact_data = {
    "name": "test",
    "surname": "test",
    "email": "test@test.com",
    "phone": "111111111",
    "birthday": "1986-08-18",
}


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
        json=contact_data,
        headers=headers,
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["name"] == contact_data["name"]
    assert data["surname"] == contact_data["surname"]
    assert data["email"] == contact_data["email"]
    assert data["phone"] == contact_data["phone"]
    assert data["birthday"] == contact_data["birthday"]


def test_get_contact_by_name(client, get_token):
    token = get_token
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get(
        "/api/contacts/search", params={"name": contact_data["name"]}, headers=headers
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["name"] == contact_data["name"]
    assert data["surname"] == contact_data["surname"]
    assert data["email"] == contact_data["email"]
    assert data["phone"] == contact_data["phone"]
    assert data["birthday"] == contact_data["birthday"]


def test_get_contact_by_email(client, get_token):
    token = get_token
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get(
        "/api/contacts/search", params={"email": contact_data["email"]}, headers=headers
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["name"] == contact_data["name"]
    assert data["surname"] == contact_data["surname"]
    assert data["email"] == contact_data["email"]
    assert data["phone"] == contact_data["phone"]
    assert data["birthday"] == contact_data["birthday"]


def test_get_contact_by_surname(client, get_token):
    token = get_token
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get(
        "/api/contacts/search",
        params={"surname": contact_data["surname"]},
        headers=headers,
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["name"] == contact_data["name"]
    assert data["surname"] == contact_data["surname"]
    assert data["email"] == contact_data["email"]
    assert data["phone"] == contact_data["phone"]
    assert data["birthday"] == contact_data["birthday"]


def test_update_contact(client, get_token):
    token = get_token
    headers = {"Authorization": f"Bearer {token}"}

    updated_contact_data = {
        "email": "test1@test.com",
        "phone": "999999999",
    }
    update_response = client.patch(
        f"/api/contacts/update",
        params={"surname": contact_data["surname"]},
        json=updated_contact_data,
        headers=headers,
    )
    assert update_response.status_code == 200, update_response.text
    updated_contact = update_response.json()
    assert updated_contact["email"] == updated_contact_data["email"]
    assert updated_contact["phone"] == updated_contact_data["phone"]


def test_delete_contact(client, get_token):
    token = get_token
    headers = {"Authorization": f"Bearer {token}"}
    delete_response = client.delete(
        f"/api/contacts/delete",
        params={"name": contact_data["name"]},
        headers=headers,
    )
    assert delete_response.status_code == 204, delete_response.text


def test_get_upcoming_birthday(client, get_token):
    token = get_token
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/contacts/birthdays", headers=headers)
    assert response.status_code == 404, response.text
    data = response.json()
    assert data["detail"] == messages.BIRTHDAYS_NOT_FOUND
