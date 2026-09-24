"""
Події: реакції на появу нового коментаря (T9, A19).

Сигнал спрацьовує на будь-який шлях збереження — API, адмінка, shell, — тому інваліда́ція
кешу й постановка задачі не залежать від того, звідки прийшов коментар.
"""

import logging

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from kombu.exceptions import OperationalError
from redis.exceptions import RedisError

from comments.cache import invalidate_list
from comments.models import Comment
from comments.tasks import notify_parent_author

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Comment)
def on_comment_saved(sender: type[Comment], instance: Comment, created: bool, **kwargs) -> None:
    """Реакції відкладаємо до коміту транзакції: до нього коментаря ще «не існує»."""
    if not created:
        return

    comment_id = instance.id
    has_parent = instance.parent_id is not None
    transaction.on_commit(lambda: react_to_new_comment(comment_id, has_parent))


def react_to_new_comment(comment_id: int, has_parent: bool) -> None:
    """
    Дві реакції на новий коментар. Кожна у власному `try`: збій однієї не має скасовувати
    другу, і жодна не має ламати вже збережений коментар (`CLAUDE.md` §5.2).
    """
    try:
        invalidate_list()
    except RedisError:
        logger.exception("Failed to invalidate comment list cache for comment %s", comment_id)

    if not has_parent:
        return

    try:
        notify_parent_author.delay(comment_id)
    except OperationalError:
        # Брокер недоступний: коментар збережено, лист просто не піде.
        logger.exception("Failed to queue notification for comment %s", comment_id)
