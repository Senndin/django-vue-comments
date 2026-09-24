"""WebSocket-маршрути застосунку коментарів."""

from django.urls import path

from comments.consumers import CommentConsumer

websocket_urlpatterns = [
    path("ws/comments/", CommentConsumer.as_asgi()),
]
