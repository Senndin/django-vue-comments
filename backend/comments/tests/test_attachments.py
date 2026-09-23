"""
Тести вкладень: картинка або текстовий файл (R16, R17, R18, A11–A13).

Картинки генеруємо Pillow просто в пам'яті — жодних тестових файлів у репозиторії.
"""

from io import BytesIO

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from comments.attachments import (
    MAX_IMAGE_BYTES,
    MAX_IMAGE_SIZE,
    MAX_TEXT_BYTES,
    AttachmentType,
    process_attachment,
)

FORMAT_EXTENSIONS = {"JPEG": "jpg", "GIF": "gif", "PNG": "png", "BMP": "bmp"}


def make_image_file(
    size: tuple[int, int] = (800, 600),
    image_format: str = "PNG",
    name: str | None = None,
) -> SimpleUploadedFile:
    """Картинка заданого розміру й формату як завантажений файл."""
    buffer = BytesIO()
    Image.new("RGB", size, color="red").save(buffer, format=image_format)
    extension = FORMAT_EXTENSIONS[image_format]
    return SimpleUploadedFile(name or f"photo.{extension}", buffer.getvalue())


def make_text_file(content: bytes = b"hello", name: str = "notes.txt") -> SimpleUploadedFile:
    return SimpleUploadedFile(name, content)


def open_result(uploaded) -> Image.Image:
    uploaded.seek(0)
    return Image.open(BytesIO(uploaded.read()))


# --- картинки (R17, A12) ---


@pytest.mark.parametrize("image_format", ["JPEG", "GIF", "PNG"])
def test_allowed_image_formats_are_accepted(image_format: str) -> None:
    uploaded, attachment_type = process_attachment(make_image_file(image_format=image_format))

    assert attachment_type == AttachmentType.IMAGE
    assert open_result(uploaded).format == image_format


@pytest.mark.parametrize(
    ("original", "expected"),
    [
        ((800, 600), (320, 240)),  # та сама пропорція 4:3
        ((1000, 200), (320, 64)),  # широка картинка обмежується шириною
        ((200, 1000), (48, 240)),  # висока — висотою
        ((321, 241), (320, 240)),  # трохи більша за ліміт
    ],
)
def test_large_image_is_scaled_down_proportionally(
    original: tuple[int, int], expected: tuple[int, int]
) -> None:
    uploaded, _ = process_attachment(make_image_file(size=original))

    assert open_result(uploaded).size == expected


@pytest.mark.parametrize("size", [(320, 240), (100, 50), (1, 1)])
def test_small_image_is_left_untouched(size: tuple[int, int]) -> None:
    original = make_image_file(size=size)
    original_bytes = original.read()
    original.seek(0)

    uploaded, _ = process_attachment(original)

    uploaded.seek(0)
    assert uploaded.read() == original_bytes


def test_animated_gif_becomes_a_single_frame() -> None:
    buffer = BytesIO()
    frames = [Image.new("P", (400, 300), color=index) for index in range(3)]
    frames[0].save(buffer, format="GIF", save_all=True, append_images=frames[1:])
    animated = SimpleUploadedFile("animation.gif", buffer.getvalue())

    uploaded, _ = process_attachment(animated)

    # Зменшення анімованого GIF лишає перший кадр — це узгоджене допущення (A12).
    assert getattr(open_result(uploaded), "n_frames", 1) == 1


def test_unsupported_image_format_is_rejected() -> None:
    with pytest.raises(ValidationError):
        process_attachment(make_image_file(image_format="BMP"))


def test_file_that_only_looks_like_an_image_is_rejected() -> None:
    # Формат визначається за вмістом, а не за розширенням (A12).
    disguised = SimpleUploadedFile("photo.png", b"just plain text, not an image")

    with pytest.raises(ValidationError):
        process_attachment(disguised)


def test_image_larger_than_the_limit_is_rejected() -> None:
    oversized = make_image_file(size=(100, 100))
    oversized.size = MAX_IMAGE_BYTES + 1

    with pytest.raises(ValidationError):
        process_attachment(oversized)


def test_image_limits_match_the_requirements() -> None:
    assert MAX_IMAGE_SIZE == (320, 240)
    assert MAX_IMAGE_BYTES == 5 * 1024 * 1024


# --- текстові файли (R18, A13) ---


def test_text_file_is_accepted() -> None:
    uploaded, attachment_type = process_attachment(make_text_file(b"hello world"))

    assert attachment_type == AttachmentType.TEXT
    uploaded.seek(0)
    assert uploaded.read() == b"hello world"


def test_text_file_of_exactly_the_limit_is_accepted() -> None:
    uploaded, _ = process_attachment(make_text_file(b"x" * MAX_TEXT_BYTES))

    assert uploaded is not None
    assert MAX_TEXT_BYTES == 100 * 1024


def test_text_file_over_the_limit_is_rejected() -> None:
    with pytest.raises(ValidationError):
        process_attachment(make_text_file(b"x" * (MAX_TEXT_BYTES + 1)))


def test_text_file_that_is_not_utf8_is_rejected() -> None:
    with pytest.raises(ValidationError):
        process_attachment(make_text_file(b"\xff\xfe\x00\x81 broken"))


def test_extension_is_case_insensitive() -> None:
    _, attachment_type = process_attachment(make_text_file(b"hello", name="NOTES.TXT"))

    assert attachment_type == AttachmentType.TEXT


def test_utf8_text_with_non_latin_characters_is_accepted() -> None:
    uploaded, _ = process_attachment(make_text_file("Привіт, світ!".encode()))

    uploaded.seek(0)
    assert uploaded.read().decode() == "Привіт, світ!"
