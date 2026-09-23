"""Тести моделі коментаря: дерево гілки, видалення, обмеження на вкладення."""

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction

from comments.models import Comment

pytestmark = pytest.mark.django_db


def make_comment(**kwargs) -> Comment:
    """Коментар із мінімально потрібними полями; будь-яке можна перевизначити."""
    fields = {"user_name": "Anonym", "email": "anonym@example.com", "text": "Hello"}
    return Comment.objects.create(**(fields | kwargs))


def test_top_level_comment_has_no_parent_and_no_root() -> None:
    comment = make_comment()

    assert comment.parent is None
    assert comment.root is None


def test_reply_takes_parent_as_thread_root() -> None:
    top = make_comment()

    reply = make_comment(parent=top)

    assert reply.root == top


def test_deep_reply_keeps_the_same_thread_root() -> None:
    top = make_comment()
    reply = make_comment(parent=top)

    deep_reply = make_comment(parent=reply)

    # Корінь гілки — заголовний коментар, а не безпосередній батько.
    assert deep_reply.parent == reply
    assert deep_reply.root == top


def test_thread_holds_every_reply_of_any_depth() -> None:
    top = make_comment()
    reply = make_comment(parent=top)
    make_comment(parent=reply)

    assert top.thread_comments.count() == 2
    assert top.replies.count() == 1


def test_deleting_top_level_comment_removes_the_whole_thread() -> None:
    top = make_comment()
    reply = make_comment(parent=top)
    make_comment(parent=reply)

    top.delete()

    assert Comment.objects.count() == 0


def test_deleting_author_keeps_the_comment() -> None:
    user = get_user_model().objects.create_user(username="Denis", email="d@example.com")
    comment = make_comment(user=user)

    user.delete()
    comment.refresh_from_db()

    assert comment.user is None
    assert comment.user_name == "Anonym"


def test_attachment_without_type_is_rejected_by_database() -> None:
    with pytest.raises(IntegrityError), transaction.atomic():
        make_comment(attachment="attachments/file.png")


def test_attachment_type_without_file_is_rejected_by_database() -> None:
    with pytest.raises(IntegrityError), transaction.atomic():
        make_comment(attachment_type=Comment.AttachmentType.IMAGE)


def test_attachment_with_type_is_stored() -> None:
    comment = make_comment(
        attachment="attachments/file.png",
        attachment_type=Comment.AttachmentType.IMAGE,
    )

    assert comment.attachment.name == "attachments/file.png"
