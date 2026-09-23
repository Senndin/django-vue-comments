"""
CAPTCHA: генерація завдання, видача ключа і одноразова перевірка відповіді (R8, A15).

SPA не вміє працювати з формою django-simple-captcha напряму, тож клієнт отримує пару
«ключ + адреса картинки», а разом із коментарем надсилає ключ і те, що прочитав.
"""

import secrets

from captcha.helpers import captcha_image_url
from captcha.models import CaptchaStore
from django.core.exceptions import ValidationError
from django.utils import timezone

# Без 0/O та 1/I/L: у спотвореному шумом зображенні їх майже неможливо розрізнити (A15).
CAPTCHA_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
CAPTCHA_LENGTH = 6


def unambiguous_challenge() -> tuple[str, str]:
    """
    Завдання для django-simple-captcha: що намалювати і що очікувати у відповідь.

    Бібліотека викликає цю функцію через налаштування `CAPTCHA_CHALLENGE_FUNCT`.
    `secrets` замість `random`: це захист від спаму, тож джерело випадковості має бути
    криптографічним, а не передбачуваним.
    """
    challenge = "".join(secrets.choice(CAPTCHA_ALPHABET) for _ in range(CAPTCHA_LENGTH))
    return challenge, challenge


def issue_captcha() -> dict[str, str]:
    """Створює нове завдання і повертає ключ та адресу картинки для клієнта."""
    key = CaptchaStore.generate_key()
    return {"key": key, "image_url": captcha_image_url(key)}


def validate_captcha(key: str, value: str) -> None:
    """
    Перевіряє відповідь і гасить завдання: успішно використаний ключ більше не працює.

    Помилка введення завдання не спалює — користувач може спробувати ще раз, не оновлюючи
    картинку. Перебрати 31⁶ варіантів за п'ять хвилин життя ключа неможливо.
    """
    CaptchaStore.remove_expired()

    answer = value.strip().lower()
    if not answer:
        raise ValidationError("CAPTCHA answer is required.")

    try:
        store = CaptchaStore.objects.get(
            hashkey=key,
            response=answer,
            expiration__gt=timezone.now(),
        )
    except CaptchaStore.DoesNotExist as error:
        raise ValidationError("CAPTCHA answer is wrong or expired.") from error

    store.delete()
