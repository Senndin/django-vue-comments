"""Смоук-тести етапу 0: проєкт зібрано і власна модель користувача активна."""

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from accounts.models import USERNAME_VALIDATOR, User


def test_project_uses_custom_user_model() -> None:
    assert get_user_model() is User


@pytest.mark.parametrize("username", ["Anonym", "Rum8", "a", "A" * 50])
def test_username_validator_accepts_latin_and_digits(username: str) -> None:
    USERNAME_VALIDATOR(username)


# Rum_8 з картинки завдання не проходить — пріоритет у тексту вимоги R5 (A7).
@pytest.mark.parametrize("username", ["Rum_8", "Денис", "with space", "a@b", ""])
def test_username_validator_rejects_everything_else(username: str) -> None:
    with pytest.raises(ValidationError):
        USERNAME_VALIDATOR(username)
