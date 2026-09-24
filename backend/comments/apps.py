from django.apps import AppConfig


class CommentsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "comments"

    def ready(self) -> None:
        """Імпорт реєструє обробники сигналів; без нього вони не спрацюють."""
        from comments import signals  # noqa: F401  (імпорт потрібен саме заради реєстрації)
