"""Тести створення коментаря: валідація полів, CAPTCHA, вкладення, XSS і SQLi (R5–R9, R13, R16)."""

from io import BytesIO

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from comments.models import Comment
from comments.validators import MAX_TEXT_LENGTH

pytestmark = pytest.mark.django_db

LIST_URL = "/api/comments/"


def payload(captcha: dict[str, str], **overrides) -> dict:
    """Коректні поля форми; будь-яке можна перевизначити для перевірки помилки."""
    fields = {
        "user_name": "Anonym",
        "email": "anonym@example.com",
        "home_page": "",
        "text": "Hello, world",
        **captcha,
    }
    return fields | overrides


def image_file(size: tuple[int, int] = (800, 600), name: str = "photo.png") -> SimpleUploadedFile:
    buffer = BytesIO()
    Image.new("RGB", size, "red").save(buffer, format="PNG")
    return SimpleUploadedFile(name, buffer.getvalue())


# --- успішне створення ---


def test_creates_top_level_comment(api_client, captcha_fields) -> None:
    response = api_client.post(LIST_URL, payload(captcha_fields()))

    assert response.status_code == 201
    comment = Comment.objects.get(pk=response.json()["id"])
    assert comment.user_name == "Anonym"
    assert comment.parent is None and comment.root is None


def test_creates_reply_and_fills_thread_root(api_client, captcha_fields, comment_factory) -> None:
    top = comment_factory()

    reply = api_client.post(LIST_URL, payload(captcha_fields(), parent=top.id)).json()
    deep = api_client.post(LIST_URL, payload(captcha_fields(), parent=reply["id"])).json()

    assert Comment.objects.get(pk=reply["id"]).root == top
    # Відповідь на відповідь лишається в тій самій гілці (R10).
    assert Comment.objects.get(pk=deep["id"]).root == top


def test_stores_client_data(api_client, captcha_fields) -> None:
    response = api_client.post(
        LIST_URL,
        payload(captcha_fields()),
        HTTP_X_REAL_IP="203.0.113.7",
        HTTP_USER_AGENT="Mozilla/5.0 (Test)",
        REMOTE_ADDR="10.0.0.1",
    )

    comment = Comment.objects.get(pk=response.json()["id"])
    # Заголовок від нашого nginx має пріоритет над адресою з'єднання (A2).
    assert comment.ip_address == "203.0.113.7"
    assert comment.user_agent == "Mozilla/5.0 (Test)"


def test_falls_back_to_connection_address_without_proxy(api_client, captcha_fields) -> None:
    response = api_client.post(LIST_URL, payload(captcha_fields()), REMOTE_ADDR="10.0.0.1")

    assert Comment.objects.get(pk=response.json()["id"]).ip_address == "10.0.0.1"


def test_home_page_is_optional(api_client, captcha_fields) -> None:
    response = api_client.post(LIST_URL, payload(captcha_fields(), home_page="https://example.com"))

    assert response.status_code == 201
    assert Comment.objects.get(pk=response.json()["id"]).home_page == "https://example.com"


# --- CAPTCHA (R8, A15) ---


def test_wrong_captcha_is_rejected(api_client, captcha_fields) -> None:
    response = api_client.post(LIST_URL, payload(captcha_fields(), captcha_value="WRONG7"))

    assert response.status_code == 400
    assert "captcha_value" in response.json()
    assert Comment.objects.count() == 0


def test_captcha_cannot_be_used_twice(api_client, captcha_fields) -> None:
    captcha = captcha_fields()
    api_client.post(LIST_URL, payload(captcha))

    response = api_client.post(LIST_URL, payload(captcha, text="second try"))

    assert response.status_code == 400
    assert Comment.objects.count() == 1


def test_captcha_is_required(api_client, captcha_fields) -> None:
    fields = payload(captcha_fields())
    del fields["captcha_value"]

    response = api_client.post(LIST_URL, fields)

    assert response.status_code == 400
    assert "captcha_value" in response.json()


# --- валідація полів (R5–R7, R9) ---


@pytest.mark.parametrize("user_name", ["", "Rum_8", "Денис", "two words", "a@b"])
def test_invalid_user_name_is_rejected(api_client, captcha_fields, user_name: str) -> None:
    response = api_client.post(LIST_URL, payload(captcha_fields(), user_name=user_name))

    assert response.status_code == 400
    assert "user_name" in response.json()


@pytest.mark.parametrize("email", ["", "user", "user@", "@example.com"])
def test_invalid_email_is_rejected(api_client, captcha_fields, email: str) -> None:
    response = api_client.post(LIST_URL, payload(captcha_fields(), email=email))

    assert response.status_code == 400
    assert "email" in response.json()


@pytest.mark.parametrize("home_page", ["example.com", "javascript:alert(1)", "ftp://example.com"])
def test_invalid_home_page_is_rejected(api_client, captcha_fields, home_page: str) -> None:
    response = api_client.post(LIST_URL, payload(captcha_fields(), home_page=home_page))

    assert response.status_code == 400
    assert "home_page" in response.json()


@pytest.mark.parametrize("text", ["", "   ", "x" * (MAX_TEXT_LENGTH + 1)])
def test_invalid_text_is_rejected(api_client, captcha_fields, text: str) -> None:
    response = api_client.post(LIST_URL, payload(captcha_fields(), text=text))

    assert response.status_code == 400
    assert "text" in response.json()


def test_reply_to_unknown_comment_is_rejected(api_client, captcha_fields) -> None:
    response = api_client.post(LIST_URL, payload(captcha_fields(), parent=999999))

    assert response.status_code == 400
    assert "parent" in response.json()


# --- розмітка, XSS і SQLi (R13, R19, R20) ---


def test_allowed_markup_is_stored(api_client, captcha_fields) -> None:
    text = '<strong>bold</strong> <a href="https://example.com" title="T">link</a>'

    response = api_client.post(LIST_URL, payload(captcha_fields(), text=text))

    assert response.status_code == 201
    assert Comment.objects.get(pk=response.json()["id"]).text == text


@pytest.mark.parametrize(
    "text",
    [
        "<script>alert(1)</script>",
        '<img src="x" onerror="alert(1)">',
        "<b>bold</b>",
        '<a href="javascript:alert(1)">link</a>',
        "<i>unclosed",
        "<i><strong>crossed</i></strong>",
    ],
)
def test_dangerous_or_broken_markup_is_rejected(api_client, captcha_fields, text: str) -> None:
    response = api_client.post(LIST_URL, payload(captcha_fields(), text=text))

    assert response.status_code == 400
    assert "text" in response.json()
    assert Comment.objects.count() == 0


def test_special_characters_are_stored_escaped(api_client, captcha_fields) -> None:
    response = api_client.post(LIST_URL, payload(captcha_fields(), text='5 < 6 & "quoted"'))

    stored = Comment.objects.get(pk=response.json()["id"]).text
    assert stored == "5 &lt; 6 &amp; &quot;quoted&quot;"


@pytest.mark.parametrize(
    "injection",
    ["' OR 1=1 --", "'; DROP TABLE comments_comment; --", "1' UNION SELECT NULL --"],
)
def test_sql_injection_strings_are_plain_text(api_client, captcha_fields, injection: str) -> None:
    response = api_client.post(LIST_URL, payload(captcha_fields(), text=injection))

    assert response.status_code == 201
    # Рядок зберігся як текст, таблиця на місці: ORM параметризує запити (R13).
    assert Comment.objects.count() == 1
    assert injection.replace('"', "&quot;") in Comment.objects.get().text


# --- вкладення (R16–R18) ---


def test_image_attachment_is_resized_and_typed(api_client, captcha_fields) -> None:
    response = api_client.post(
        LIST_URL,
        payload(captcha_fields(), attachment=image_file((800, 600))),
        format="multipart",
    )

    assert response.status_code == 201
    comment = Comment.objects.get(pk=response.json()["id"])
    assert comment.attachment_type == Comment.AttachmentType.IMAGE
    assert Image.open(comment.attachment).size == (320, 240)
    comment.attachment.delete(save=False)


def test_text_attachment_is_accepted(api_client, captcha_fields) -> None:
    attachment = SimpleUploadedFile("notes.txt", "Привіт".encode())

    response = api_client.post(
        LIST_URL, payload(captcha_fields(), attachment=attachment), format="multipart"
    )

    assert response.status_code == 201
    comment = Comment.objects.get(pk=response.json()["id"])
    assert comment.attachment_type == Comment.AttachmentType.TEXT
    comment.attachment.delete(save=False)


@pytest.mark.parametrize(
    "attachment",
    [
        SimpleUploadedFile("fake.png", b"not an image at all"),
        SimpleUploadedFile("big.txt", b"x" * (100 * 1024 + 1)),
    ],
)
def test_invalid_attachment_is_rejected(api_client, captcha_fields, attachment) -> None:
    response = api_client.post(
        LIST_URL, payload(captcha_fields(), attachment=attachment), format="multipart"
    )

    assert response.status_code == 400
    assert "attachment" in response.json()
    assert Comment.objects.count() == 0
