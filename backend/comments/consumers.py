"""
WebSocket-consumer: віддає клієнтам нові коментарі в реальному часі (T6, A16).

З'єднання одностороннє за змістом: сервер надсилає події, клієнт нічого не пише. Усе,
що приходить від клієнта, ігнорується — так у нас немає ще однієї точки вводу, яку
довелося б валідувати.
"""

import logging

from channels.generic.websocket import AsyncJsonWebsocketConsumer

logger = logging.getLogger(__name__)

# Одна група на всіх: кожен відкритий клієнт бачить усі нові коментарі.
COMMENTS_GROUP = "comments"


class CommentConsumer(AsyncJsonWebsocketConsumer):
    """Підписує клієнта на групу `comments` і пересилає йому події про нові коментарі."""

    async def connect(self) -> None:
        await self.channel_layer.group_add(COMMENTS_GROUP, self.channel_name)
        await self.accept()

    async def disconnect(self, code: int) -> None:
        await self.channel_layer.group_discard(COMMENTS_GROUP, self.channel_name)

    async def receive_json(self, content: dict, **kwargs) -> None:
        """Клієнт нічого не надсилає; повідомлення від нього просто ігноруємо."""

    async def comment_created(self, event: dict) -> None:
        """
        Обробник події `comment.created` із канального шару.

        Ім'я методу — це тип події з крапками, заміненими на підкреслення: саме так
        Channels зіставляє повідомлення групи з методом consumer'а.
        """
        await self.send_json({"type": event["type"], "comment": event["comment"]})
