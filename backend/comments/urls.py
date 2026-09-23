"""Маршрути застосунку коментарів (префікс `/api/`)."""

from django.urls import path

from comments import views

urlpatterns = [
    path("captcha/", views.captcha_challenge, name="captcha-challenge"),
    path("comments/", views.CommentListCreateView.as_view(), name="comment-list"),
    path("comments/preview/", views.CommentPreviewView.as_view(), name="comment-preview"),
    path("comments/<int:pk>/thread/", views.CommentThreadView.as_view(), name="comment-thread"),
]
