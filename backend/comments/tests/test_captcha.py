"""Тести CAPTCHA: завдання, видача, одноразова перевірка (R8, A15)."""

from datetime import timedelta
from io import BytesIO

import pytest
from captcha.models import CaptchaStore
from django.core.exceptions import ValidationError
from django.test import Client
from django.utils import timezone
from PIL import Image

from comments.captcha import (
    CAPTCHA_ALPHABET,
    CAPTCHA_LENGTH,
    issue_captcha,
    unambiguous_challenge,
    validate_captcha,
)

pytestmark = pytest.mark.django_db

AMBIGUOUS_CHARACTERS = "0O1lI"


def issue_and_answer() -> tuple[str, str]:
    """Нове завдання: повертає ключ і правильну відповідь."""
    challenge = issue_captcha()
    store = CaptchaStore.objects.get(hashkey=challenge["key"])
    return challenge["key"], store.challenge


# --- генератор завдання (A15) ---


def test_challenge_has_required_length_and_alphabet() -> None:
    for _ in range(50):
        challenge, response = unambiguous_challenge()

        assert len(challenge) == CAPTCHA_LENGTH == 6
        assert set(challenge) <= set(CAPTCHA_ALPHABET)
        # Відповідь збігається із зображеним текстом: математичних прикладів не показуємо.
        assert response == challenge


def test_alphabet_has_no_ambiguous_characters() -> None:
    assert not set(AMBIGUOUS_CHARACTERS) & set(CAPTCHA_ALPHABET)


def test_challenges_are_not_repeated() -> None:
    challenges = {unambiguous_challenge()[0] for _ in range(20)}

    assert len(challenges) > 1


# --- видача (A15) ---


def test_issue_captcha_stores_challenge_and_returns_image_url() -> None:
    challenge = issue_captcha()

    assert CaptchaStore.objects.filter(hashkey=challenge["key"]).exists()
    assert challenge["key"] in challenge["image_url"]


def test_each_request_creates_a_new_challenge() -> None:
    first = issue_captcha()
    second = issue_captcha()

    assert first["key"] != second["key"]


# --- перевірка відповіді (A15) ---


@pytest.mark.parametrize("transform", [str.lower, str.upper, str.title])
def test_correct_answer_is_accepted_ignoring_case(transform) -> None:
    key, answer = issue_and_answer()

    validate_captcha(key, transform(answer))


def test_answer_is_accepted_with_surrounding_spaces() -> None:
    key, answer = issue_and_answer()

    validate_captcha(key, f"  {answer} ")


def test_correct_answer_works_only_once() -> None:
    key, answer = issue_and_answer()
    validate_captcha(key, answer)

    with pytest.raises(ValidationError):
        validate_captcha(key, answer)

    assert not CaptchaStore.objects.filter(hashkey=key).exists()


def test_wrong_answer_is_rejected() -> None:
    key, answer = issue_and_answer()

    with pytest.raises(ValidationError):
        validate_captcha(key, "WRONG7")


def test_wrong_answer_does_not_burn_the_challenge() -> None:
    key, answer = issue_and_answer()
    with pytest.raises(ValidationError):
        validate_captcha(key, "WRONG7")

    # Помилився при введенні — можна спробувати ще раз, не оновлюючи картинку.
    validate_captcha(key, answer)


def test_unknown_key_is_rejected() -> None:
    with pytest.raises(ValidationError):
        validate_captcha("deadbeef" * 5, "ABCDEF")


@pytest.mark.parametrize("value", ["", "   "])
def test_empty_answer_is_rejected(value: str) -> None:
    key, _ = issue_and_answer()

    with pytest.raises(ValidationError):
        validate_captcha(key, value)


def test_expired_challenge_is_rejected() -> None:
    key, answer = issue_and_answer()
    CaptchaStore.objects.filter(hashkey=key).update(
        expiration=timezone.now() - timedelta(seconds=1)
    )

    with pytest.raises(ValidationError):
        validate_captcha(key, answer)


# --- ендпоінт для SPA (files/SPEC.md §3.5) ---


def test_endpoint_returns_key_and_image_url(client: Client) -> None:
    response = client.get("/api/captcha/")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {"key", "image_url"}
    assert CaptchaStore.objects.filter(hashkey=payload["key"]).exists()


def test_endpoint_rejects_other_methods(client: Client) -> None:
    assert client.post("/api/captcha/").status_code == 405


def test_captcha_image_is_served(client: Client) -> None:
    payload = client.get("/api/captcha/").json()

    image = client.get(payload["image_url"])

    assert image.status_code == 200
    assert image["Content-Type"] == "image/png"
    assert image.content[:8] == b"\x89PNG\r\n\x1a\n"


def test_captcha_image_is_large_enough_to_read(client: Client) -> None:
    payload = client.get("/api/captcha/").json()

    width, height = Image.open(BytesIO(client.get(payload["image_url"]).content)).size

    # Типові налаштування бібліотеки дають 105×29 — шість символів там не прочитати.
    assert width >= 150
    assert height >= 40
