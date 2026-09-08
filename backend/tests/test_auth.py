import uuid
from app.models.user import User
from app.services.auth import hash_password


def test_register(client):
    response = client.post(
        "/auth/register",
        json={"email": "new@lifeos.app", "password": "pass1234", "name": "New"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "new@lifeos.app"
    assert data["name"] == "New"
    assert "id" in data


def test_register_duplicate_email(client, demo_user):
    response = client.post(
        "/auth/register",
        json={"email": "test@lifeos.app", "password": "pass1234", "name": "Dup"},
    )
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


def test_login_success(client, demo_user):
    response = client.post(
        "/auth/login",
        json={"email": "test@lifeos.app", "password": "test1234"},
    )
    assert response.status_code == 200
    assert response.json()["user"]["email"] == "test@lifeos.app"


def test_login_wrong_password(client, demo_user):
    response = client.post(
        "/auth/login",
        json={"email": "test@lifeos.app", "password": "wrong"},
    )
    assert response.status_code == 401


def test_login_nonexistent_user(client):
    response = client.post(
        "/auth/login",
        json={"email": "nobody@lifeos.app", "password": "pass"},
    )
    assert response.status_code == 401


def test_me_authenticated(client, demo_user, auth_headers):
    response = client.get("/auth/me", **auth_headers)
    assert response.status_code == 200
    assert response.json()["email"] == "test@lifeos.app"


def test_me_unauthenticated(client):
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_logout(client):
    response = client.post("/auth/logout")
    assert response.status_code == 200
