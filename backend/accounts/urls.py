"""Маршрути акаунтів (префікс `/api/auth/`)."""

from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from accounts import views

urlpatterns = [
    path("register/", views.RegisterView.as_view(), name="auth-register"),
    # Готові в'юхи simplejwt: перша видає пару access+refresh, друга оновлює access.
    path("token/", TokenObtainPairView.as_view(), name="auth-token"),
    path("token/refresh/", TokenRefreshView.as_view(), name="auth-token-refresh"),
    path("me/", views.MeView.as_view(), name="auth-me"),
]
