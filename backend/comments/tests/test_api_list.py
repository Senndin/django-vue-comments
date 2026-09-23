"""Тести списку заголовних коментарів: пагінація, сортування, кількість запитів (R11–R14)."""

import pytest
from django.core.cache import cache

from comments.models import Comment

pytestmark = pytest.mark.django_db

LIST_URL = "/api/comments/"


def test_returns_only_top_level_comments(api_client, comment_factory) -> None:
    top = comment_factory()
    comment_factory(parent=top)
    comment_factory(parent=top)

    payload = api_client.get(LIST_URL).json()

    assert payload["count"] == 1
    assert payload["results"][0]["id"] == top.id


def test_each_row_carries_the_number_of_replies_in_the_thread(api_client, comment_factory) -> None:
    top = comment_factory()
    reply = comment_factory(parent=top)
    comment_factory(parent=reply)
    comment_factory()

    results = {
        row["id"]: row["replies_count"] for row in api_client.get(LIST_URL).json()["results"]
    }

    # Рахуються всі відповіді гілки, а не лише прямі діти.
    assert results[top.id] == 2


def test_page_holds_25_comments(api_client, comment_factory) -> None:
    for index in range(30):
        comment_factory(user_name=f"User{index}")

    first_page = api_client.get(LIST_URL).json()
    second_page = api_client.get(LIST_URL, {"page": 2}).json()

    assert first_page["count"] == 30
    assert len(first_page["results"]) == 25
    assert len(second_page["results"]) == 5
    assert first_page["next"] is not None


def test_newest_comments_come_first_by_default(api_client, comment_factory) -> None:
    first = comment_factory(user_name="First")
    second = comment_factory(user_name="Second")

    results = api_client.get(LIST_URL).json()["results"]

    # LIFO: останній доданий — найперший (R14).
    assert [row["id"] for row in results] == [second.id, first.id]


@pytest.mark.parametrize(
    ("ordering", "expected"),
    [
        ("user_name", ["Anna", "Bob", "Cecil"]),
        ("-user_name", ["Cecil", "Bob", "Anna"]),
        ("email", ["Cecil", "Anna", "Bob"]),
        ("-email", ["Bob", "Anna", "Cecil"]),
    ],
)
def test_sorting_by_name_and_email_works_both_ways(
    api_client, comment_factory, ordering: str, expected: list[str]
) -> None:
    comment_factory(user_name="Bob", email="c@example.com")
    comment_factory(user_name="Anna", email="b@example.com")
    comment_factory(user_name="Cecil", email="a@example.com")

    results = api_client.get(LIST_URL, {"ordering": ordering}).json()["results"]

    assert [row["user_name"] for row in results] == expected


def test_sorting_by_date_works_both_ways(api_client, comment_factory) -> None:
    first = comment_factory()
    second = comment_factory()

    ascending = api_client.get(LIST_URL, {"ordering": "created_at"}).json()["results"]
    descending = api_client.get(LIST_URL, {"ordering": "-created_at"}).json()["results"]

    assert [row["id"] for row in ascending] == [first.id, second.id]
    assert [row["id"] for row in descending] == [second.id, first.id]


@pytest.mark.parametrize(
    "ordering",
    ["password", "user__password", "id", "' OR 1=1 --", "created_at; DROP TABLE comments_comment"],
)
def test_unknown_ordering_falls_back_to_the_default(api_client, comment_factory, ordering) -> None:
    first = comment_factory()
    second = comment_factory()

    response = api_client.get(LIST_URL, {"ordering": ordering})

    # Поле не з білого списку просто ігнорується: ані помилки, ані виконаного SQL (R13).
    assert response.status_code == 200
    assert [row["id"] for row in response.json()["results"]] == [second.id, first.id]
    assert Comment.objects.count() == 2


@pytest.mark.parametrize("page", ["abc", "' OR 1=1 --", "999"])
def test_broken_page_parameter_returns_404_not_an_error(api_client, comment_factory, page) -> None:
    comment_factory()

    assert api_client.get(LIST_URL, {"page": page}).status_code == 404


def test_query_count_does_not_grow_with_the_number_of_comments(
    api_client, comment_factory, django_assert_num_queries
) -> None:
    for _ in range(5):
        top = comment_factory()
        comment_factory(parent=top)

    with django_assert_num_queries(2) as captured:
        api_client.get(LIST_URL)

    for _ in range(20):
        top = comment_factory()
        comment_factory(parent=top)

    # Коментарі створені напряму в БД, повз API, тож кеш про них не знає — чистимо його
    # вручну, інакше замість запитів до БД порахували б попадання в кеш (етап 7).
    cache.clear()

    # Стільки ж запитів, скільки й на п'яти рядках: кількість відповідей рахує `annotate`,
    # а не окремий запит на кожен коментар (N+1).
    with django_assert_num_queries(len(captured)):
        api_client.get(LIST_URL)
