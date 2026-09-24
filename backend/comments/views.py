"""HTTP-точки входу застосунку коментарів (files/SPEC.md §3.5)."""

from django.core.cache import cache
from django.db.models import Count, QuerySet
from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_GET
from rest_framework import generics, status
from rest_framework.filters import OrderingFilter
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from comments.cache import LIST_CACHE_TIMEOUT, page_cache_key
from comments.captcha import issue_captcha
from comments.models import Comment
from comments.serializers import (
    CommentCreateSerializer,
    CommentListSerializer,
    CommentPreviewSerializer,
    CommentThreadSerializer,
)

USER_AGENT_MAX_LENGTH = 255


@require_GET
def captcha_challenge(request: HttpRequest) -> JsonResponse:
    """`GET /api/captcha/` — нове завдання CAPTCHA для форми коментаря (R8, A15)."""
    return JsonResponse(issue_captcha())


def client_ip(request: Request) -> str | None:
    """
    IP відвідувача (R2, A2).

    `X-Real-IP` довіряємо лише тому, що його виставляє наш nginx і перезаписує значення
    з боку клієнта. Без проксі (локальний запуск, тести) лишається `REMOTE_ADDR`.
    """
    return request.META.get("HTTP_X_REAL_IP") or request.META.get("REMOTE_ADDR")


class StableOrderingFilter(OrderingFilter):
    """
    Сортування з білим списком полів плюс сталий `-id` наприкінці.

    Без другого ключа рядки з однаковим значенням (два `Anonym`, однакова секунда)
    можуть змінювати порядок між запитами, і при посторінковому виводі коментар
    здатен або зникнути, або з'явитися двічі.
    """

    def get_ordering(self, request: Request, queryset: QuerySet, view: APIView) -> list[str]:
        ordering = super().get_ordering(request, queryset, view)
        if ordering and all(field.lstrip("-") != "id" for field in ordering):
            return [*ordering, "-id"]
        return ordering


class CommentListCreateView(generics.ListCreateAPIView):
    """
    `GET /api/comments/` — заголовні коментарі, 25 на сторінку (R11, R12, R14).
    `POST /api/comments/` — новий коментар або відповідь (R1, R5–R9, R16).
    """

    filter_backends = [StableOrderingFilter]
    # Білий список: усе інше в `ordering` ігнорується, тож підставити довільний SQL
    # у сортування неможливо (R13).
    ordering_fields = ["user_name", "email", "created_at"]
    ordering = ["-created_at"]

    def get_queryset(self) -> QuerySet[Comment]:
        # Таблиця показує лише заголовні коментарі (A3), а кількість відповідей рахує
        # БД одним запитом на сторінку — не по запиту на рядок (N+1).
        return Comment.objects.filter(parent__isnull=True).annotate(
            replies_count=Count("thread_comments")
        )

    def get_serializer_class(self) -> type:
        if self.request.method == "POST":
            return CommentCreateSerializer
        return CommentListSerializer

    def list(self, request: Request, *args, **kwargs) -> Response:
        """Готова сторінка береться з кешу; до БД доходить лише перший запит (T8, A18)."""
        if not self.requested_page(request).isdigit():
            # Такий запит однаково завершиться 404, а сміттєвий параметр у ключі кешу
            # нам не потрібен (у memcached він був би ще й помилкою).
            return super().list(request, *args, **kwargs)

        cache_key = self.page_cache_key(request)
        cached_page = cache.get(cache_key)
        if cached_page is not None:
            return Response(cached_page)

        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, LIST_CACHE_TIMEOUT)
        return response

    def page_cache_key(self, request: Request) -> str:
        """
        Ключ сторінки будується з **нормалізованого** сортування, а не з сирого параметра.

        Інакше довільне значення `ordering` створювало б окремий ключ, і кеш можна було б
        забити сміттям із тисяч неіснуючих сортувань.
        """
        ordering = StableOrderingFilter().get_ordering(request, self.get_queryset(), self) or []
        return page_cache_key(
            host=request.get_host(),
            ordering=",".join(ordering),
            page=self.requested_page(request),
        )

    @staticmethod
    def requested_page(request: Request) -> str:
        return request.query_params.get("page", "1")

    def perform_create(self, serializer: CommentCreateSerializer) -> None:
        serializer.save(
            ip_address=client_ip(self.request),
            user_agent=self.request.META.get("HTTP_USER_AGENT", "")[:USER_AGENT_MAX_LENGTH],
        )


class CommentThreadView(generics.RetrieveAPIView):
    """`GET /api/comments/<id>/thread/` — заголовний коментар з усім деревом (R10, A5)."""

    serializer_class = CommentThreadSerializer
    # Гілка є лише в заголовного коментаря: для відповіді це 404, а не порожнє дерево.
    queryset = Comment.objects.filter(parent__isnull=True)

    def get_object(self) -> Comment:
        root = super().get_object()
        replies = list(root.thread_comments.order_by("created_at", "id"))
        return build_thread(root, replies)


class CommentPreviewView(APIView):
    """`POST /api/comments/preview/` — розмітка без збереження (R22, A29)."""

    def post(self, request: Request) -> Response:
        serializer = CommentPreviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({"html": serializer.validated_data["text"]}, status=status.HTTP_200_OK)


def build_thread(root: Comment, replies: list[Comment]) -> Comment:
    """
    Розвішує відповіді по батьках, перетворюючи плаский список на дерево.

    Усі коментарі гілки приходять одним запитом (`root_id = X`), тому глибина дерева
    не додає жодного звернення до БД. Порядок `replies` хронологічний, тож і діти в
    кожного вузла йдуть за часом (A5).
    """
    by_id: dict[int, Comment] = {root.id: root}
    root.children = []
    for reply in replies:
        reply.children = []
        by_id[reply.id] = reply

    for reply in replies:
        by_id[reply.parent_id].children.append(reply)
    return root
