"""Тести валідаторів полів коментаря (R5, R6, R7, R9, A7, A14)."""

import pytest
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator

from accounts.models import USERNAME_VALIDATOR
from comments.validators import (
    HOME_PAGE_VALIDATOR,
    MAX_TEXT_LENGTH,
    validate_comment_text,
)


@pytest.mark.parametrize("user_name", ["Anonym", "Rum8", "a", "A" * 50, "0"])
def test_user_name_accepts_latin_letters_and_digits(user_name: str) -> None:
    USERNAME_VALIDATOR(user_name)


@pytest.mark.parametrize("user_name", ["", "Rum_8", "Денис", "two words", "a@b", "a-b", "a.b"])
def test_user_name_rejects_everything_else(user_name: str) -> None:
    with pytest.raises(ValidationError):
        USERNAME_VALIDATOR(user_name)


@pytest.mark.parametrize("email", ["user@example.com", "a.b+c@sub.example.co.uk"])
def test_email_accepts_valid_addresses(email: str) -> None:
    EmailValidator()(email)


@pytest.mark.parametrize("email", ["", "user", "user@", "@example.com", "user @example.com"])
def test_email_rejects_invalid_addresses(email: str) -> None:
    with pytest.raises(ValidationError):
        EmailValidator()(email)


@pytest.mark.parametrize("url", ["http://example.com", "https://example.com/path?a=1"])
def test_home_page_accepts_http_and_https(url: str) -> None:
    HOME_PAGE_VALIDATOR(url)


@pytest.mark.parametrize(
    "url",
    ["example.com", "ftp://example.com", "javascript:alert(1)", "/relative", "http://"],
)
def test_home_page_rejects_everything_else(url: str) -> None:
    with pytest.raises(ValidationError):
        HOME_PAGE_VALIDATOR(url)


@pytest.mark.parametrize("text", ["a", "x" * MAX_TEXT_LENGTH, "line\nline"])
def test_comment_text_accepts_reasonable_input(text: str) -> None:
    validate_comment_text(text)


def test_comment_text_rejects_too_long_input() -> None:
    with pytest.raises(ValidationError):
        validate_comment_text("x" * (MAX_TEXT_LENGTH + 1))


@pytest.mark.parametrize("text", ["", "   ", "\n\t "])
def test_comment_text_rejects_blank_input(text: str) -> None:
    with pytest.raises(ValidationError):
        validate_comment_text(text)
