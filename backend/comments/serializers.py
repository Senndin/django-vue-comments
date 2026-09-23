"""
Серіалізатори коментарів: перетворення між моделлю і JSON плюс уся валідація вводу.

Саме тут сходяться перевірки етапів 3–5: CAPTCHA (R8), текст із дозволеною розміткою
(R9, R19, R20) і вкладення (R16–R18). View лишається тонким (`CLAUDE.md` §5.1).
"""

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from comments.attachments import process_attachment
from comments.captcha import validate_captcha
from comments.html_sanitizer import build_safe_html
from comments.models import Comment
from comments.validators import HOME_PAGE_VALIDATOR, validate_comment_text


def build_text_html(value: str) -> str:
    """Перевіряє довжину вихідного тексту (A14) і повертає безпечний HTML (A10)."""
    validate_comment_text(value)
    return build_safe_html(value)


class CommentSerializer(serializers.ModelSerializer):
    """Загальний вигляд коментаря у відповідях API."""

    class Meta:
        model = Comment
        fields = (
            "id",
            "parent",
            "user_name",
            "email",
            "home_page",
            "text",
            "attachment",
            "attachment_type",
            "created_at",
        )
        read_only_fields = fields


class CommentListSerializer(CommentSerializer):
    """Рядок таблиці заголовних коментарів: додається кількість відповідей у гілці (A3)."""

    # Значення приходить з `annotate` у queryset — окремого запиту на рядок немає.
    replies_count = serializers.IntegerField(read_only=True)

    class Meta(CommentSerializer.Meta):
        fields = (*CommentSerializer.Meta.fields, "replies_count")
        read_only_fields = fields


class CommentThreadSerializer(CommentSerializer):
    """Вузол дерева відповідей: рекурсивно віддає власних нащадків (R10)."""

    children = serializers.SerializerMethodField()

    class Meta(CommentSerializer.Meta):
        fields = (*CommentSerializer.Meta.fields, "children")
        read_only_fields = fields

    def get_children(self, comment: Comment) -> list[dict]:
        # `children` складає view — дерево будується в пам'яті з одного запиту до БД.
        return CommentThreadSerializer(comment.children, many=True, context=self.context).data


class CommentCreateSerializer(serializers.ModelSerializer):
    """Створення коментаря або відповіді: перевіряє все, що надіслав відвідувач."""

    # DRF викидає валідатор `URLField` з моделі й ставить власний, який пропускає ftp,
    # тож обмеження схем доводиться оголошувати тут ще раз (R7).
    home_page = serializers.URLField(
        required=False, allow_blank=True, validators=[HOME_PAGE_VALIDATOR]
    )
    captcha_key = serializers.CharField(write_only=True)
    captcha_value = serializers.CharField(write_only=True, trim_whitespace=False)

    class Meta:
        model = Comment
        fields = (
            "id",
            "parent",
            "user_name",
            "email",
            "home_page",
            "text",
            "attachment",
            "attachment_type",
            "created_at",
            "captcha_key",
            "captcha_value",
        )
        read_only_fields = ("id", "attachment_type", "created_at")

    def validate_text(self, value: str) -> str:
        """У базу лягає вже зібраний безпечний HTML, а не те, що надіслав клієнт (A10)."""
        return build_text_html(value)

    def validate(self, attrs: dict) -> dict:
        """Перевірки, яким потрібно більше ніж одне поле."""
        self._check_captcha(attrs)
        self._check_attachment(attrs)
        return attrs

    def _check_captcha(self, attrs: dict) -> None:
        try:
            validate_captcha(attrs.pop("captcha_key"), attrs.pop("captcha_value"))
        except DjangoValidationError as error:
            # Прив'язуємо помилку до поля вводу, а не до форми загалом.
            raise serializers.ValidationError({"captcha_value": error.messages}) from error

    def _check_attachment(self, attrs: dict) -> None:
        attachment = attrs.get("attachment")
        if not attachment:
            return
        try:
            attrs["attachment"], attrs["attachment_type"] = process_attachment(attachment)
        except DjangoValidationError as error:
            raise serializers.ValidationError({"attachment": error.messages}) from error


class CommentPreviewSerializer(serializers.Serializer):
    """Попередній перегляд (R22): той самий санітайзер, що й при збереженні (A29)."""

    text = serializers.CharField()

    def validate_text(self, value: str) -> str:
        return build_text_html(value)
