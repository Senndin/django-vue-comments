"""HTTP-точки входу застосунку коментарів."""

from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_GET

from comments.captcha import issue_captcha


@require_GET
def captcha_challenge(request: HttpRequest) -> JsonResponse:
    """`GET /api/captcha/` — нове завдання CAPTCHA для форми коментаря (R8, A15)."""
    return JsonResponse(issue_captcha())
