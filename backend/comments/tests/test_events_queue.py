"""Тести подій і черги: реакції на новий коментар (T7, T9, A17, A19)."""

import pytest
from kombu.exceptions import OperationalError

from comments.cache import list_version
from comments.models import Comment
from comments.tasks import notify_parent_author

pytestmark = pytest.mark.django_db

LIST_URL = "/api/comments/"


# --- події: коли саме спрацьовують реакції (A19) ---


def test_reactions_wait_for_the_transaction_to_commit(
    comment_factory, django_capture_on_commit_callbacks
) -> None:
    version_before = list_version()

    with django_capture_on_commit_callbacks(execute=False) as callbacks:
        comment_factory()
        # Транзакція ще не завершилася: нічого не сталося.
        assert list_version() == version_before

    assert len(callbacks) == 1


def test_comment_created_outside_the_api_also_refreshes_the_list(
    api_client, comment_factory, django_capture_on_commit_callbacks
) -> None:
    comment_factory()
    api_client.get(LIST_URL)

    with django_capture_on_commit_callbacks(execute=True):
        # Так коментар створюється в адмінці чи в shell — повз наш ендпоінт.
        comment_factory(user_name="FromAdmin")

    assert api_client.get(LIST_URL).json()["count"] == 2


def test_editing_a_comment_does_not_trigger_reactions(
    comment_factory, django_capture_on_commit_callbacks
) -> None:
    comment = comment_factory()

    with django_capture_on_commit_callbacks(execute=False) as callbacks:
        comment.user_name = "Renamed"
        comment.save()

    assert callbacks == []


def test_broken_broker_does_not_break_comment_creation(
    comment_factory, django_capture_on_commit_callbacks, monkeypatch
) -> None:
    top = comment_factory()

    def explode(*args, **kwargs):
        raise OperationalError("broker is down")

    monkeypatch.setattr(notify_parent_author, "delay", explode)

    with django_capture_on_commit_callbacks(execute=True):
        reply = comment_factory(parent=top)

    # Коментар на місці, помилка черги лише записана в лог.
    assert Comment.objects.filter(pk=reply.pk).exists()


# --- черга: лист автору батьківського коментаря (A17) ---


def test_reply_notifies_the_parent_author(
    comment_factory, django_capture_on_commit_callbacks, mailoutbox
) -> None:
    top = comment_factory(email="author@example.com")

    with django_capture_on_commit_callbacks(execute=True):
        comment_factory(parent=top, user_name="Replier", email="replier@example.com")

    assert len(mailoutbox) == 1
    assert mailoutbox[0].to == ["author@example.com"]
    assert "Replier" in mailoutbox[0].subject


def test_top_level_comment_notifies_nobody(
    comment_factory, django_capture_on_commit_callbacks, mailoutbox
) -> None:
    with django_capture_on_commit_callbacks(execute=True):
        comment_factory()

    assert mailoutbox == []


def test_reply_to_yourself_notifies_nobody(
    comment_factory, django_capture_on_commit_callbacks, mailoutbox
) -> None:
    top = comment_factory(email="author@example.com")

    with django_capture_on_commit_callbacks(execute=True):
        comment_factory(parent=top, email="AUTHOR@example.com")

    # Той самий автор (регістр адреси не має значення) — сповіщати нема кого.
    assert mailoutbox == []


def test_notification_body_has_no_markup(
    comment_factory, django_capture_on_commit_callbacks, mailoutbox
) -> None:
    top = comment_factory(email="author@example.com")

    with django_capture_on_commit_callbacks(execute=True):
        comment_factory(
            parent=top,
            email="replier@example.com",
            text="<strong>bold</strong> and 5 &lt; 6",
        )

    body = mailoutbox[0].body
    assert "<strong>" not in body
    assert "bold and 5 < 6" in body


def test_task_survives_a_deleted_comment(mailoutbox) -> None:
    # Коментар устигли видалити між постановкою задачі і її виконанням.
    notify_parent_author(999999)

    assert mailoutbox == []


def test_task_reads_fresh_data_by_id(
    comment_factory, django_capture_on_commit_callbacks, mailoutbox
) -> None:
    top = comment_factory(email="author@example.com")
    reply = comment_factory(parent=top, email="replier@example.com")
    Comment.objects.filter(pk=reply.pk).update(user_name="RenamedLater")

    notify_parent_author(reply.pk)

    # Задача отримує id і читає стан із БД, тому бачить нове ім'я.
    assert "RenamedLater" in mailoutbox[0].subject
