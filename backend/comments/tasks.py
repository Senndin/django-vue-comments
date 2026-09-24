"""Фонові задачі застосунку коментарів (T7, A17)."""

import logging
from html import unescape
from smtplib import SMTPException

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.utils.html import strip_tags

from comments.models import Comment

logger = logging.getLogger(__name__)

TEXT_PREVIEW_LENGTH = 300


@shared_task(
    # Мережа й поштовий сервер можуть бути тимчасово недоступні — тоді пробуємо ще раз
    # зі зростаючою паузою. Помилки в даних (немає коментаря) повторювати немає сенсу.
    autoretry_for=(SMTPException, OSError),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def notify_parent_author(comment_id: int) -> None:
    """
    Повідомляє автора батьківського коментаря про відповідь.

    Задача отримує `id`, а не сам об'єкт: між постановкою в чергу і виконанням проходить
    час, за який дані могли змінитися, — воркер має читати актуальний стан із БД.
    """
    try:
        reply = Comment.objects.select_related("parent").get(pk=comment_id)
    except Comment.DoesNotExist:
        # Коментар устигли видалити — повторювати марно.
        logger.warning("Comment %s no longer exists, notification skipped", comment_id)
        return

    parent = reply.parent
    if parent is None:
        return
    if parent.email.lower() == reply.email.lower():
        # Відповідь самому собі: сповіщати нема кого.
        return

    body = unescape(strip_tags(reply.text))[:TEXT_PREVIEW_LENGTH]
    send_mail(
        subject=f"New reply to your comment from {reply.user_name}",
        message=f"{reply.user_name} replied to your comment:\n\n{body}\n",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[parent.email],
    )
    logger.info("Notified %s about reply %s", parent.email, reply.id)
