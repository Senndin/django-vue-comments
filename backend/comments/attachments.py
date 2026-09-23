"""
Вкладення коментаря: перевірка файлу і підготовка його до збереження (R16–R18, A11–A13).

До коментаря можна додати рівно один файл — картинку або текстовий файл (A11). Тип
визначається за **вмістом**, а не за розширенням: файл `photo.png`, усередині якого текст,
буде відхилено (A12). Завелика картинка зменшується пропорційно до 320×240 (R17).
"""

import uuid
from io import BytesIO
from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile, File
from django.db import models
from PIL import Image, UnidentifiedImageError

MAX_IMAGE_SIZE = (320, 240)
MAX_IMAGE_BYTES = 5 * 1024 * 1024
MAX_TEXT_BYTES = 100 * 1024
ALLOWED_IMAGE_FORMATS = frozenset({"JPEG", "GIF", "PNG"})
TEXT_EXTENSION = ".txt"


class AttachmentType(models.TextChoices):
    """Тип вкладення: або картинка, або текстовий файл (R16, A11)."""

    IMAGE = "image", "Image"
    TEXT = "text", "Text file"


def attachment_upload_to(instance: object, filename: str) -> str:
    """
    Дає файлу ім'я з UUID і кладе його в теку `attachments/`.

    Оригінальне ім'я в шлях не потрапляє: воно приходить від користувача і могло б містити
    шлях (`../`), керуючі символи чи просто повторитися й перетерти чужий файл (R13).
    Розширення зберігаємо в нижньому регістрі — воно потрібне, щоб браузер відкрив файл
    із правильним типом вмісту.
    """
    suffix = Path(filename).suffix.lower()
    return f"attachments/{uuid.uuid4().hex}{suffix}"


def process_attachment(uploaded: File) -> tuple[File, str]:
    """
    Перевіряє вкладення і повертає пару «файл для збереження, тип вкладення».

    Розширення `.txt` — єдина підказка, за якою ми вибираємо гілку перевірки; далі все
    вирішує вміст файлу. Тому текст під виглядом картинки і картинка під виглядом тексту
    однаково не пройдуть.
    """
    if Path(uploaded.name or "").suffix.lower() == TEXT_EXTENSION:
        return _check_text_file(uploaded), AttachmentType.TEXT
    return _process_image(uploaded), AttachmentType.IMAGE


def _check_text_file(uploaded: File) -> File:
    """Текстовий файл: не більший за 100 КБ і читається як UTF-8 (R18, A13)."""
    if uploaded.size > MAX_TEXT_BYTES:
        raise ValidationError(f"Text file must not be larger than {MAX_TEXT_BYTES // 1024} KB.")

    uploaded.seek(0)
    try:
        uploaded.read().decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValidationError("Text file must be encoded in UTF-8.") from error

    # Файл ще читатиме Django при збереженні, тож повертаємо курсор на початок.
    uploaded.seek(0)
    return uploaded


def _process_image(uploaded: File) -> File:
    """Картинка: дозволений формат, розмір до 320×240, зменшення зі збереженням пропорцій."""
    if uploaded.size > MAX_IMAGE_BYTES:
        raise ValidationError(
            f"Image must not be larger than {MAX_IMAGE_BYTES // 1024 // 1024} MB."
        )

    uploaded.seek(0)
    try:
        with Image.open(uploaded) as image:
            # `format` Pillow визначає за сигнатурою файлу, а не за іменем (A12).
            if image.format not in ALLOWED_IMAGE_FORMATS:
                raise ValidationError("Image must be a JPG, GIF or PNG file.")

            image_format = image.format
            # Повне читання пікселів: тут виявляються обрізані й пошкоджені файли.
            image.load()

            if image.width <= MAX_IMAGE_SIZE[0] and image.height <= MAX_IMAGE_SIZE[1]:
                # Менші за ліміт не чіпаємо взагалі — жодної втрати якості (R17).
                uploaded.seek(0)
                return uploaded

            # `thumbnail` зменшує на місці й сам зберігає пропорції; анімований GIF після
            # цього лишається одним кадром (A12).
            image.thumbnail(MAX_IMAGE_SIZE)
            resized = BytesIO()
            image.save(resized, format=image_format)
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError) as error:
        # Захист Pillow від «бомб стиснення» лишаємо ввімкненим — він і кидає ці помилки (R13).
        raise ValidationError("Image must be a valid JPG, GIF or PNG file.") from error

    return ContentFile(resized.getvalue(), name=uploaded.name)
