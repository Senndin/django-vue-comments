"""Адмінка коментарів: модерація силами адміністратора (A27)."""

from django.contrib import admin

from comments.models import Comment


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """Список коментарів із пошуком і фільтрами; дерево видно через колонку `parent`."""

    list_display = ("id", "user_name", "email", "created_at", "parent", "attachment_type")
    list_filter = ("attachment_type", "created_at")
    search_fields = ("user_name", "email", "text")
    date_hierarchy = "created_at"
    # Коментарів можуть бути тисячі, тож батька й автора обираємо за id, а не з випадного списку.
    raw_id_fields = ("parent", "user")
    readonly_fields = ("root", "created_at")
    # `parent` є в списку: без цього кожен рядок робив би окремий запит (N+1).
    list_select_related = ("parent",)
