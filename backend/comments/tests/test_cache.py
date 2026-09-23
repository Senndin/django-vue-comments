"""Тести кешу списку заголовних коментарів (T8, A18)."""

import warnings

import pytest
from django.core.cache import cache
from django.core.cache.backends.base import CacheKeyWarning

from comments.cache import (
    LIST_CACHE_TIMEOUT,
    LIST_VERSION_KEY,
    invalidate_list,
    list_version,
    page_cache_key,
)

pytestmark = pytest.mark.django_db

LIST_URL = "/api/comments/"


def test_repeated_request_does_not_touch_the_database(
    api_client, comment_factory, django_assert_num_queries
) -> None:
    comment_factory()
    api_client.get(LIST_URL)

    # Жодного SQL: відповідь цілком зібрана з кешу.
    with django_assert_num_queries(0):
        response = api_client.get(LIST_URL)

    assert response.status_code == 200
    assert response.json()["count"] == 1


def test_new_comment_makes_the_list_fresh_again(
    api_client, captcha_fields, comment_factory
) -> None:
    comment_factory()
    api_client.get(LIST_URL)

    api_client.post(
        LIST_URL,
        {
            "user_name": "Anonym",
            "email": "anonym@example.com",
            "text": "brand new",
            **captcha_fields(),
        },
    )

    assert api_client.get(LIST_URL).json()["count"] == 2


def test_pages_are_cached_separately(api_client, comment_factory) -> None:
    for index in range(30):
        comment_factory(user_name=f"User{index}")

    first_page = api_client.get(LIST_URL).json()
    second_page = api_client.get(LIST_URL, {"page": 2}).json()

    assert len(first_page["results"]) == 25
    assert len(second_page["results"]) == 5


def test_orderings_are_cached_separately(api_client, comment_factory) -> None:
    comment_factory(user_name="Anna")
    comment_factory(user_name="Bob")

    ascending = api_client.get(LIST_URL, {"ordering": "user_name"}).json()
    descending = api_client.get(LIST_URL, {"ordering": "-user_name"}).json()

    assert [row["user_name"] for row in ascending["results"]] == ["Anna", "Bob"]
    assert [row["user_name"] for row in descending["results"]] == ["Bob", "Anna"]


def test_unknown_ordering_reuses_the_default_cache_entry(
    api_client, comment_factory, django_assert_num_queries
) -> None:
    comment_factory()
    api_client.get(LIST_URL)

    # Сміття в `ordering` зводиться до сортування за замовчуванням, тож окремого ключа
    # не з'являється — інакше кеш можна було б забити випадковими значеннями.
    with django_assert_num_queries(0):
        response = api_client.get(LIST_URL, {"ordering": "nonsense"})

    assert response.status_code == 200


# --- версія списку (A18) ---


def test_version_starts_at_one_and_grows_on_invalidation() -> None:
    assert list_version() == 1

    invalidate_list()

    assert list_version() == 2


def test_invalidation_works_even_if_the_version_key_is_missing() -> None:
    cache.delete(LIST_VERSION_KEY)

    # `cache.incr` на відсутньому ключі кидає ValueError — цей випадок оброблено.
    invalidate_list()

    assert list_version() == 1


def test_key_changes_with_version_page_ordering_and_host() -> None:
    base = page_cache_key(host="example.com", ordering="-created_at,-id", page="1")

    assert base != page_cache_key(host="other.com", ordering="-created_at,-id", page="1")
    assert base != page_cache_key(host="example.com", ordering="user_name,-id", page="1")
    assert base != page_cache_key(host="example.com", ordering="-created_at,-id", page="2")

    invalidate_list()
    assert base != page_cache_key(host="example.com", ordering="-created_at,-id", page="1")


def test_pages_live_five_minutes() -> None:
    assert LIST_CACHE_TIMEOUT == 5 * 60


def test_broken_page_parameter_never_reaches_the_cache_key(api_client, comment_factory) -> None:
    comment_factory()

    with warnings.catch_warnings():
        # Django попереджає, коли в ключі кешу є пробіли й керуючі символи. Робимо
        # попередження помилкою: сміттєвий `page` не має потрапляти в ключ узагалі.
        warnings.simplefilter("error", CacheKeyWarning)

        assert api_client.get(LIST_URL, {"page": "' OR 1=1 --"}).status_code == 404
