"""Кореневі HTTP-маршрути проєкту."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("comments.urls")),
    # Маршрути django-simple-captcha: картинка за ключем (/captcha/image/<key>/).
    path("captcha/", include("captcha.urls")),
]

# Daphne, на відміну від `runserver`, статику сам не роздає. У режимі розробки
# це робить Django, інакше адмінка в контейнері відкривається без стилів.
if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
