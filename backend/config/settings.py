"""
Налаштування Django-проєкту.

Один файл на всі оточення: відмінності (DEBUG, хости, доступ до БД) приходять
зі змінних оточення. Локально їх задає файл `.env`, у Docker — сервіс у compose.
"""

import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent


def env(name: str, default: str | None = None) -> str:
    """Повертає змінну оточення; без значення і без default — падає ще на старті."""
    value = os.environ.get(name, default)
    if value is None:
        raise ImproperlyConfigured(f"Environment variable {name} is required")
    return value


def env_bool(name: str, default: str = "False") -> bool:
    """Читає булеву змінну оточення: `1`, `true`, `yes` (будь-який регістр) — це True."""
    return env(name, default).strip().lower() in {"1", "true", "yes"}


# Безпека. Значення за замовчуванням безпечні: на проді DEBUG треба вмикати свідомо.
SECRET_KEY = env("DJANGO_SECRET_KEY", "django-insecure-local-development-key")
DEBUG = env_bool("DJANGO_DEBUG")
ALLOWED_HOSTS = [
    host.strip()
    for host in env("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host.strip()
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "captcha",
    "rest_framework",
    "accounts",
    "comments",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB", "comments"),
        "USER": env("POSTGRES_USER", "comments"),
        "PASSWORD": env("POSTGRES_PASSWORD", "comments"),
        "HOST": env("POSTGRES_HOST", "localhost"),
        "PORT": env("POSTGRES_PORT", "5432"),
    }
}

# Власна модель користувача підключається до першої міграції (потім її не змінити).
AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
# Куди `collectstatic` збирає статику; у production її віддає nginx (етап 16).
STATIC_ROOT = BASE_DIR / "staticfiles"

# Файли, які завантажують користувачі (R16). У production їх віддає nginx (етап 16).
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# Поля форми коментаря невеликі (текст — до 5000 символів), тож тіло запиту без файлів
# обмежуємо 1 МБ: усе більше Django відхилить ще до наших перевірок (R13).
DATA_UPLOAD_MAX_MEMORY_SIZE = 1 * 1024 * 1024
# Вкладення важить щонайбільше 5 МБ (A12) — такий файл тримаємо в пам'яті цілком,
# без тимчасового файлу на диску. Сам ліміт перевіряє `comments/attachments.py`.
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024

# CAPTCHA (R8, A15). Малюнок і сховище — django-simple-captcha, завдання — наше:
# 6 символів без 0/O та 1/I/L. Час життя ключа — 5 хвилин.
CAPTCHA_CHALLENGE_FUNCT = "comments.captcha.unambiguous_challenge"
CAPTCHA_TIMEOUT = 5
# Типовий розмір шрифту (22) дає картинку 105×29 — шість символів на ній майже не
# читаються. Більший шрифт і менший нахил лишають шум, але роблять текст розбірливим.
CAPTCHA_FONT_SIZE = 36
CAPTCHA_LETTER_ROTATION = (-20, 20)

# Redis: одна інфраструктура на три задачі — кеш (БД 0), черга Celery (БД 1)
# і канальний шар WebSocket (БД 2). Зараз використовується лише кеш.
REDIS_URL = env("REDIS_URL", "redis://localhost:6379")
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": f"{REDIS_URL}/0",
    }
}

REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    # 25 повідомлень на сторінку (R12).
    "PAGE_SIZE": 25,
    # Порожній список навмисно: API не користується сесіями, тож і CSRF йому не потрібен.
    # Аутентифікацію за JWT додамо на етапі 10 (§5.3).
    "DEFAULT_AUTHENTICATION_CLASSES": [],
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
