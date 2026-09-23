"""Тести гілки відповідей і попереднього перегляду (R10, R22, A5, A29)."""

import pytest

from comments.models import Comment

pytestmark = pytest.mark.django_db

PREVIEW_URL = "/api/comments/preview/"


def thread_url(comment_id: int) -> str:
    return f"/api/comments/{comment_id}/thread/"


# --- гілка (R10, A5) ---


def test_thread_returns_nested_children(api_client, comment_factory) -> None:
    top = comment_factory(text="top")
    reply = comment_factory(parent=top, text="reply")
    comment_factory(parent=reply, text="deep reply")

    payload = api_client.get(thread_url(top.id)).json()

    assert payload["text"] == "top"
    assert payload["children"][0]["text"] == "reply"
    assert payload["children"][0]["children"][0]["text"] == "deep reply"


def test_children_are_ordered_chronologically(api_client, comment_factory) -> None:
    top = comment_factory()
    first = comment_factory(parent=top)
    second = comment_factory(parent=top)

    payload = api_client.get(thread_url(top.id)).json()

    # У гілці порядок завжди від старіших до новіших, незалежно від сортування таблиці (A5).
    assert [child["id"] for child in payload["children"]] == [first.id, second.id]


def test_thread_without_replies_has_empty_children(api_client, comment_factory) -> None:
    top = comment_factory()

    assert api_client.get(thread_url(top.id)).json()["children"] == []


def test_reply_has_no_thread_of_its_own(api_client, comment_factory) -> None:
    top = comment_factory()
    reply = comment_factory(parent=top)

    # Гілка є лише в заголовного коментаря (files/SPEC.md §3.5).
    assert api_client.get(thread_url(reply.id)).status_code == 404


def test_unknown_comment_returns_404(api_client) -> None:
    assert api_client.get(thread_url(999999)).status_code == 404


def test_deep_thread_costs_a_constant_number_of_queries(
    api_client, comment_factory, django_assert_num_queries
) -> None:
    top = comment_factory()
    parent = top
    for _ in range(10):
        parent = comment_factory(parent=parent)

    # Заголовний коментар і вся гілка — два запити, скільки б рівнів вкладеності не було.
    with django_assert_num_queries(2):
        api_client.get(thread_url(top.id))


# --- попередній перегляд (R22, A29) ---


def test_preview_returns_safe_html(api_client) -> None:
    response = api_client.post(PREVIEW_URL, {"text": "<i>hi</i> & bye"}, format="json")

    assert response.status_code == 200
    assert response.json() == {"html": "<i>hi</i> &amp; bye"}


def test_preview_does_not_save_anything(api_client) -> None:
    api_client.post(PREVIEW_URL, {"text": "just looking"}, format="json")

    assert Comment.objects.count() == 0


@pytest.mark.parametrize("text", ["<script>alert(1)</script>", "<i>unclosed", "", "   "])
def test_preview_reports_the_same_errors_as_saving(api_client, text: str) -> None:
    response = api_client.post(PREVIEW_URL, {"text": text}, format="json")

    assert response.status_code == 400
    assert "text" in response.json()


def test_preview_needs_no_captcha(api_client) -> None:
    # Попередній перегляд нічого не зберігає, тож і захисту від спаму не потребує.
    assert api_client.post(PREVIEW_URL, {"text": "hello"}, format="json").status_code == 200
