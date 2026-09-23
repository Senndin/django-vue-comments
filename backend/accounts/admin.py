"""Реєстрація користувачів у Django admin — адмін модерує коментарі й користувачів (A27)."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from accounts.models import User

admin.site.register(User, UserAdmin)
