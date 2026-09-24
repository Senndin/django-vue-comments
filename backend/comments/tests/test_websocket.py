"""Тести WebSocket: нові коментарі приходять клієнтам без перезавантаження (T6, A16)."""

import pytest
from asgiref.sync import sync_to_async
from channels.testing import WebsocketCommunicator
from redis.exceptions import RedisError

from comments.broadcast import broadcast_comment_created
from comments.models import Comment
from config.asgi import application

WS_URL = "/ws/comments/"
RECEIVE_TIMEOUT = 3


async def connect(origin: str = "http://localhost") -> WebsocketCommunicator:
    """
    Підключений клієнт WebSocket.

    Заголовок `Origin` обов'язковий: `AllowedHostsOriginValidator` відхиляє з'єднання
    без нього так само, як і з чужого домену. Браузер цей заголовок надсилає завжди.
    """
    communicator = WebsocketCommunicator(
        application, WS_URL, headers=[(b"origin", origin.encode())]
    )
    connected, _ = await communicator.connect()
    assert connected
    return communicator


async def create_comment(**kwargs) -> Comment:
    """Створює коментар у синхронному потоці — так само, як це робить звичайний запит."""
    fields = {"user_name": "Anonym", "email": "anonym@example.com", "text": "Hello"}
    return await sync_to_async(Comment.objects.create)(**(fields | kwargs))


# `transaction=True`: реакції прив'язані до `on_commit`, тож тесту потрібні справжні коміти,
# які до того ж видно з інших з'єднань — інакше подія не дійшла б до consumer'а.
pytestmark = pytest.mark.django_db(transaction=True)


async def test_client_connects() -> None:
    communicator = await connect()

    await communicator.disconnect()


async def test_connection_from_a_foreign_origin_is_rejected() -> None:
    communicator = WebsocketCommunicator(
        application, WS_URL, headers=[(b"origin", b"http://evil.example")]
    )

    connected, _ = await communicator.connect()

    # Чужа сторінка не відкриє наш WebSocket від імені відвідувача (R13).
    assert not connected
    await communicator.disconnect()


async def test_new_comment_reaches_the_client() -> None:
    communicator = await connect()

    comment = await create_comment(text="live update")
    event = await communicator.receive_json_from(timeout=RECEIVE_TIMEOUT)

    assert event["type"] == "comment.created"
    assert event["comment"]["id"] == comment.id
    assert event["comment"]["text"] == "live update"
    await communicator.disconnect()


async def test_reply_carries_parent_and_thread_root() -> None:
    top = await create_comment()
    communicator = await connect()

    reply = await create_comment(parent=top)
    event = await communicator.receive_json_from(timeout=RECEIVE_TIMEOUT)

    # Клієнт має зрозуміти, у яку гілку покласти відповідь (A16).
    assert event["comment"]["id"] == reply.id
    assert event["comment"]["parent"] == top.id
    assert event["comment"]["root"] == top.id
    await communicator.disconnect()


async def test_every_connected_client_gets_the_event() -> None:
    first = await connect()
    second = await connect()

    await create_comment(text="for everyone")

    assert (await first.receive_json_from(timeout=RECEIVE_TIMEOUT))["type"] == "comment.created"
    assert (await second.receive_json_from(timeout=RECEIVE_TIMEOUT))["type"] == "comment.created"
    await first.disconnect()
    await second.disconnect()


async def test_disconnected_client_stops_receiving_events() -> None:
    communicator = await connect()
    await communicator.disconnect()

    await create_comment()

    # З'єднання закрите — жодних повідомлень, і жодної помилки на стороні сервера.
    assert await communicator.receive_nothing()


async def test_messages_from_the_client_are_ignored() -> None:
    communicator = await connect()

    await communicator.send_json_to({"type": "hack", "text": "<script>alert(1)</script>"})

    # З'єднання живе, сервер нічого не відповідає: канал односторонній.
    assert await communicator.receive_nothing()
    await communicator.disconnect()


async def test_only_new_comments_are_broadcast() -> None:
    comment = await create_comment()
    communicator = await connect()

    await sync_to_async(Comment.objects.filter(pk=comment.pk).update)(user_name="Renamed")

    assert await communicator.receive_nothing()
    await communicator.disconnect()


# --- синхронні перевірки самої розсилки ---


@pytest.mark.django_db
def test_broadcast_survives_a_deleted_comment() -> None:
    # Коментар устигли видалити між комітом і розсилкою — це не має ламати нічого.
    broadcast_comment_created(999999)


@pytest.mark.django_db
def test_broken_channel_layer_does_not_break_comment_creation(
    comment_factory, django_capture_on_commit_callbacks, monkeypatch
) -> None:
    def explode(*args, **kwargs):
        raise RedisError("channel layer is down")

    monkeypatch.setattr("comments.signals.broadcast_comment_created", explode)

    with django_capture_on_commit_callbacks(execute=True):
        comment = comment_factory()

    assert Comment.objects.filter(pk=comment.pk).exists()
