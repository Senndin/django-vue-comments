"""Спільні фікстури для тестів бекенду."""

import pytest
from captcha.models import CaptchaStore
from django.core.cache import cache
from rest_framework.test import APIClient

from comments.captcha import issue_captcha
from comments.models import Comment
from config.celery import app as celery_app


@pytest.fixture(autouse=True)
def eager_celery():
    """У тестах задачі виконуються одразу в тому ж процесі, без воркера й брокера."""
    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True


@pytest.fixture(autouse=True)
def local_cache(settings):
    """Тести не ходять у Redis: кеш у пам'яті, порожній на початку кожного тесту."""
    settings.CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def api_client() -> APIClient:
    """Клієнт DRF: вміє надсилати JSON і multipart, розбирає відповіді API."""
    return APIClient()


@pytest.fixture
def captcha_fields(db):
    """Фабрика полів CAPTCHA: кожен виклик — нове завдання і правильна відповідь до нього."""

    def create() -> dict[str, str]:
        challenge = issue_captcha()
        store = CaptchaStore.objects.get(hashkey=challenge["key"])
        return {"captcha_key": challenge["key"], "captcha_value": store.challenge}

    return create


@pytest.fixture
def comment_factory(db):
    """Фабрика коментарів із мінімально потрібними полями."""

    def create(**kwargs) -> Comment:
        fields = {"user_name": "Anonym", "email": "anonym@example.com", "text": "Hello"}
        return Comment.objects.create(**(fields | kwargs))

    return create
