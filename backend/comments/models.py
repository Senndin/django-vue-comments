"""Модель коментаря — основна сутність проєкту (R1, R2, R10)."""

from django.conf import settings
from django.core.validators import URLValidator
from django.db import models

from accounts.models import USERNAME_VALIDATOR
from comments.attachments import AttachmentType, attachment_upload_to


class Comment(models.Model):
    """
    Коментар або відповідь на нього.

    Дерево зберігаємо двома посиланнями: `parent` — безпосередній батько (для відступів
    і порядку), `root` — заголовний коментар гілки. `root` дозволяє дістати всю гілку
    будь-якої глибини одним запитом, без рекурсії та без додаткових бібліотек.
    """

    # Тип вкладення живе поруч із перевірками файлів (`attachments.py`), а тут лишається
    # псевдонім — щоб звичне `Comment.AttachmentType` працювало як раніше.
    AttachmentType = AttachmentType

    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="replies",
        help_text="Direct parent comment. Empty for a top-level comment.",
    )
    root = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="thread_comments",
        editable=False,
        help_text="Top-level comment of the thread. Empty for a top-level comment itself.",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        # Коментар не зникає разом з акаунтом: текст лишається, автор стає анонімним.
        on_delete=models.SET_NULL,
        related_name="comments",
    )

    user_name = models.CharField(max_length=50, validators=[USERNAME_VALIDATOR])
    email = models.EmailField()
    home_page = models.URLField(blank=True, validators=[URLValidator(schemes=["http", "https"])])

    # Готовий безпечний HTML, зібраний санітайзером на етапі 3 (A10).
    text = models.TextField()

    attachment = models.FileField(upload_to=attachment_upload_to, blank=True)
    attachment_type = models.CharField(max_length=5, choices=AttachmentType, blank=True)

    # Дані, які допомагають ідентифікувати клієнта (R2, A2). Порожні в коментарів,
    # створених в адмінці: там HTTP-запиту від відвідувача немає.
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # `ordering` навмисно не задаємо: порядок різний у таблиці (R11, R14) і в гілці (A5),
        # тож кожен запит вказує його явно.
        indexes = [
            # Поля сортування таблиці заголовних коментарів (R11, R14).
            models.Index(fields=["created_at"]),
            models.Index(fields=["user_name"]),
            models.Index(fields=["email"]),
        ]
        constraints = [
            models.CheckConstraint(
                # Тип вкладення має сенс лише разом із файлом — і навпаки.
                condition=(
                    models.Q(attachment="", attachment_type="")
                    | (~models.Q(attachment="") & ~models.Q(attachment_type=""))
                ),
                name="attachment_and_type_are_set_together",
            )
        ]

    def __str__(self) -> str:
        return f"#{self.pk} by {self.user_name}"

    def save(self, *args, **kwargs) -> None:
        """Проставляє корінь гілки. Робимо це в моделі, щоб інваріант діяв і в адмінці."""
        if self.parent_id and self.root_id is None:
            # У відповіді на відповідь корінь той самий, що в батька; у відповіді на
            # заголовний коментар коренем стає сам батько.
            self.root = self.parent.root or self.parent
        super().save(*args, **kwargs)
