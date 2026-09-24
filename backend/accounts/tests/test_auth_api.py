"""Тести JWT-аутентифікації: реєстрація, токени, профіль, підпис коментаря (T10, A1, A20)."""

from datetime import timedelta

import pytest
from django.conf import settings

from accounts.models import User
from comments.models import Comment

pytestmark = pytest.mark.django_db

REGISTER_URL = "/api/auth/register/"
TOKEN_URL = "/api/auth/token/"
REFRESH_URL = "/api/auth/token/refresh/"
ME_URL = "/api/auth/me/"
COMMENTS_URL = "/api/comments/"

CREDENTIALS = {"username": "Denis", "email": "denis@example.com", "password": "TestPass123!"}


def register(api_client, **overrides):
    return api_client.post(REGISTER_URL, CREDENTIALS | overrides)


def authenticate(api_client) -> str:
    """Реєструє користувача, отримує токен і підставляє його в клієнт."""
    register(api_client)
    tokens = api_client.post(TOKEN_URL, {k: CREDENTIALS[k] for k in ("username", "password")})
    access = tokens.json()["access"]
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
    return access


# --- реєстрація ---


def test_registration_creates_a_user_with_a_hashed_password(api_client) -> None:
    response = register(api_client)

    assert response.status_code == 201
    user = User.objects.get(username="Denis")
    assert user.check_password(CREDENTIALS["password"])
    # Пароль не повертається клієнту і не зберігається відкритим текстом.
    assert "password" not in response.json()
    assert user.password != CREDENTIALS["password"]


@pytest.mark.parametrize("username", ["Rum_8", "Денис", "with space", ""])
def test_registration_rejects_invalid_username(api_client, username: str) -> None:
    response = register(api_client, username=username)

    assert response.status_code == 400
    assert "username" in response.json()


def test_registration_rejects_duplicate_username(api_client) -> None:
    register(api_client)

    response = register(api_client, email="other@example.com")

    assert response.status_code == 400
    assert "username" in response.json()


@pytest.mark.parametrize("password", ["123", "password", "12345678"])
def test_registration_rejects_weak_password(api_client, password: str) -> None:
    response = register(api_client, password=password)

    assert response.status_code == 400
    assert "password" in response.json()


def test_registration_requires_email(api_client) -> None:
    response = api_client.post(REGISTER_URL, {"username": "Denis", "password": "TestPass123!"})

    assert response.status_code == 400
    assert "email" in response.json()


# --- токени (A20) ---


def test_token_is_issued_for_valid_credentials(api_client) -> None:
    register(api_client)

    response = api_client.post(TOKEN_URL, {"username": "Denis", "password": "TestPass123!"})

    assert response.status_code == 200
    assert set(response.json()) == {"access", "refresh"}


def test_token_is_not_issued_for_wrong_password(api_client) -> None:
    register(api_client)

    response = api_client.post(TOKEN_URL, {"username": "Denis", "password": "WrongPass123!"})

    assert response.status_code == 401


def test_refresh_returns_a_new_access_token(api_client) -> None:
    register(api_client)
    tokens = api_client.post(TOKEN_URL, {"username": "Denis", "password": "TestPass123!"}).json()

    response = api_client.post(REFRESH_URL, {"refresh": tokens["refresh"]})

    assert response.status_code == 200
    assert "access" in response.json()


def test_token_lifetimes_match_the_agreement(api_client) -> None:
    assert settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"] == timedelta(minutes=30)
    assert settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"] == timedelta(days=7)


# --- профіль ---


def test_me_requires_a_token(api_client) -> None:
    assert api_client.get(ME_URL).status_code == 401


def test_me_rejects_a_broken_token(api_client) -> None:
    api_client.credentials(HTTP_AUTHORIZATION="Bearer not-a-real-token")

    assert api_client.get(ME_URL).status_code == 401


def test_me_returns_the_current_user(api_client) -> None:
    authenticate(api_client)

    response = api_client.get(ME_URL)

    assert response.status_code == 200
    assert response.json() == {
        "id": User.objects.get(username="Denis").id,
        "username": "Denis",
        "email": "denis@example.com",
    }


# --- коментар від користувача, що ввійшов (A1) ---


def test_authenticated_comment_is_signed_with_the_account(api_client, captcha_fields) -> None:
    authenticate(api_client)

    response = api_client.post(COMMENTS_URL, {"text": "from account", **captcha_fields()})

    assert response.status_code == 201
    comment = User.objects.get(username="Denis").comments.get()
    assert comment.user_name == "Denis"
    assert comment.email == "denis@example.com"


def test_values_sent_by_an_authenticated_user_are_ignored(api_client, captcha_fields) -> None:
    authenticate(api_client)

    api_client.post(
        COMMENTS_URL,
        {
            "user_name": "Someone",
            "email": "spoofed@example.com",
            "text": "trying to spoof",
            **captcha_fields(),
        },
    )

    comment = User.objects.get(username="Denis").comments.get()
    # Сервер бере підпис лише з акаунта (A1).
    assert comment.user_name == "Denis"
    assert comment.email == "denis@example.com"


def test_captcha_is_required_even_for_authenticated_users(api_client) -> None:
    authenticate(api_client)

    response = api_client.post(COMMENTS_URL, {"text": "no captcha here"})

    assert response.status_code == 400
    assert "captcha_value" in response.json()


def test_anonymous_comment_still_needs_name_and_email(api_client, captcha_fields) -> None:
    response = api_client.post(COMMENTS_URL, {"text": "anonymous", **captcha_fields()})

    assert response.status_code == 400
    assert {"user_name", "email"} <= set(response.json())


def test_anonymous_comment_is_not_linked_to_any_user(api_client, captcha_fields) -> None:
    response = api_client.post(
        COMMENTS_URL,
        {
            "user_name": "Anonym",
            "email": "anonym@example.com",
            "text": "just a visitor",
            **captcha_fields(),
        },
    )

    assert Comment.objects.get(pk=response.json()["id"]).user is None
