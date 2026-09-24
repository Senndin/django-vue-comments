"""Пакет проєкту. Імпорт Celery тут гарантує, що декоратор задач знайде застосунок."""

from config.celery import app as celery_app

__all__ = ("celery_app",)
