"""
Налаштування Celery — черги фонових задач (T7, A17).

Застосунок Celery створюється один раз тут і імпортується в `config/__init__.py`, щоб
існувати до того, як Django почне імпортувати модулі із задачами.
"""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("config")
# Усі налаштування беремо з Django: префікс CELERY_ відокремлює їх від решти.
app.config_from_object("django.conf:settings", namespace="CELERY")
# Шукає `tasks.py` у кожному застосунку з INSTALLED_APPS.
app.autodiscover_tasks()
