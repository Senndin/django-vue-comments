"""
Точка входу ASGI: HTTP обробляє Django, WebSocket — Channels (T6).

Один процес Daphne обслуговує обидва протоколи, тому окремого сервера для WebSocket
не потрібно.
"""

import os

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# Django-застосунок створюємо першим: він ініціалізує налаштування та застосунки,
# без чого не можна імпортувати consumer'и (вони тягнуть моделі).
django_asgi_application = get_asgi_application()

from comments.routing import websocket_urlpatterns  # noqa: E402  (тільки після ініціалізації)

application = ProtocolTypeRouter(
    {
        "http": django_asgi_application,
        # Перевірка заголовка Origin за ALLOWED_HOSTS: чужа сторінка не відкриє
        # з'єднання до нашого WebSocket від імені відвідувача.
        "websocket": AllowedHostsOriginValidator(URLRouter(websocket_urlpatterns)),
    }
)
