"""Розсилання подій про коментарі в канальний шар (T6, T9, A16)."""

import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from comments.consumers import COMMENTS_GROUP
from comments.models import Comment

logger = logging.getLogger(__name__)

COMMENT_CREATED = "comment.created"


def broadcast_comment_created(comment_id: int) -> None:
    """
    Надсилає всім підключеним клієнтам щойно створений коментар.

    Читаємо коментар із БД за `id` з тієї ж причини, що й у задачі черги: подія
    відправляється після коміту, і джерелом правди має бути база, а не об'єкт у пам'яті.
    """
    from comments.serializers import CommentSerializer

    try:
        comment = Comment.objects.get(pk=comment_id)
    except Comment.DoesNotExist:
        logger.warning("Comment %s no longer exists, broadcast skipped", comment_id)
        return

    channel_layer = get_channel_layer()
    if channel_layer is None:
        return

    # `group_send` асинхронний, а сигнали Django — синхронні, тож викликаємо через міст.
    async_to_sync(channel_layer.group_send)(
        COMMENTS_GROUP,
        {"type": COMMENT_CREATED, "comment": CommentSerializer(comment).data},
    )
