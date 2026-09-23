"""Кореневі HTTP-маршрути проєкту."""

from django.conf import settings
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import path

urlpatterns = [
    path("admin/", admin.site.urls),
]

# Daphne, на відміну від `runserver`, статику сам не роздає. У режимі розробки
# це робить Django, інакше адмінка в контейнері відкривається без стилів.
if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
