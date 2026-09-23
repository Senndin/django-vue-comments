"""Модель користувача. Власна з самого початку — щоб її можна було розширювати далі (A1)."""

from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models

# R5/A7: у завданні ім'я — тільки латиниця й цифри. Те саме правило діє для username
# при реєстрації, тому валідатор живе поруч із моделлю і перевикористовується.
USERNAME_VALIDATOR = RegexValidator(
    regex=r"^[A-Za-z0-9]+$",
    message="Username may contain only latin letters and digits.",
)


class User(AbstractUser):
    """Користувач сайту: стандартний Django-користувач із суворішим правилом для username."""

    username = models.CharField(
        max_length=50,
        unique=True,
        validators=[USERNAME_VALIDATOR],
        help_text="Latin letters and digits only, up to 50 characters.",
        error_messages={"unique": "A user with that username already exists."},
    )
    # E-mail обов'язковий: після входу ім'я та e-mail підставляються у форму коментаря (A1).
    email = models.EmailField()
