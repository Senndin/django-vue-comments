"""Маршрути застосунку коментарів (префікс `/api/`)."""

from django.urls import path

from comments import views

urlpatterns = [
    path("captcha/", views.captcha_challenge, name="captcha-challenge"),
]
