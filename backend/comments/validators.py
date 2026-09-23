"""Валідатори полів коментаря (R9, A14)."""

from django.core.exceptions import ValidationError

# Довжина початкового тексту, до розмітки (A14).
MAX_TEXT_LENGTH = 5000


def validate_comment_text(value: str) -> None:
    """Текст обов'язковий (R9) і не довший за `MAX_TEXT_LENGTH` символів (A14)."""
    if not value.strip():
        raise ValidationError("Text cannot be empty.")
    if len(value) > MAX_TEXT_LENGTH:
        raise ValidationError(f"Text cannot be longer than {MAX_TEXT_LENGTH} characters.")
