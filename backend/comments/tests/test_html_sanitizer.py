"""
Тести санітайзера HTML — ключового модуля проєкту (R19, R20, A8–A10).

Санітайзер не вирізає заборонену розмітку, а відхиляє текст із зрозумілою помилкою (A8),
а дозволену — перезбирає в нормалізований безпечний HTML, який і потрапляє в базу (A10).
"""

import pytest
from django.core.exceptions import ValidationError

from comments.html_sanitizer import build_safe_html


def assert_rejected(text: str, *expected_fragments: str) -> None:
    """Текст відхилено, і в повідомленні названо проблемний тег чи атрибут (A8)."""
    with pytest.raises(ValidationError) as error:
        build_safe_html(text)

    message = " ".join(error.value.messages).lower()
    for fragment in expected_fragments:
        assert fragment.lower() in message


# --- дозволені теги (R19) ---


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("<i>italic</i>", "<i>italic</i>"),
        ("<strong>bold</strong>", "<strong>bold</strong>"),
        ("<code>print(1)</code>", "<code>print(1)</code>"),
        ('<a href="https://example.com">link</a>', '<a href="https://example.com">link</a>'),
        (
            '<a href="http://example.com" title="Example">link</a>',
            '<a href="http://example.com" title="Example">link</a>',
        ),
        ("<i><strong>both</strong></i>", "<i><strong>both</strong></i>"),
        ("plain text", "plain text"),
        ("", ""),
    ],
)
def test_allowed_markup_is_kept(text: str, expected: str) -> None:
    assert build_safe_html(text) == expected


def test_tag_names_are_normalised_to_lower_case() -> None:
    # Підсумковий HTML має бути валідним XHTML, а там теги лише в нижньому регістрі (A9).
    assert build_safe_html("<STRONG>bold</StRoNg>") == "<strong>bold</strong>"


def test_attribute_order_is_normalised() -> None:
    result = build_safe_html('<a title="Example" href="https://example.com">link</a>')

    assert result == '<a href="https://example.com" title="Example">link</a>'


# --- заборонені теги (R19, A8) ---


@pytest.mark.parametrize(
    ("text", "tag"),
    [
        ("<script>alert(1)</script>", "script"),
        ("<b>bold</b>", "b"),
        ('<img src="x" onerror="alert(1)">', "img"),
        ("<div>block</div>", "div"),
        ("<br>", "br"),
        ("<style>body{}</style>", "style"),
    ],
)
def test_forbidden_tags_are_rejected(text: str, tag: str) -> None:
    assert_rejected(text, tag)


# --- закриття і вкладеність тегів (R20, A9) ---


def test_unclosed_tag_is_rejected() -> None:
    assert_rejected("<i>italic", "i", "not closed")


def test_closing_tag_without_opening_is_rejected() -> None:
    assert_rejected("italic</i>", "i")


def test_crossed_nesting_is_rejected() -> None:
    assert_rejected("<i><strong>text</i></strong>", "strong")


def test_nested_anchor_is_rejected() -> None:
    text = '<a href="https://a.test">outer <a href="https://b.test">inner</a></a>'

    assert_rejected(text, "a")


def test_self_closing_tag_is_rejected() -> None:
    # Дозволені теги не бувають порожніми, тож самозакриття — помилка (A9).
    assert_rejected("<i/>", "i")


def test_tag_without_closing_bracket_is_rejected() -> None:
    assert_rejected('<a href="https://example.com"', "a")


# --- атрибути (R19, A9) ---


def test_anchor_without_href_is_rejected() -> None:
    assert_rejected("<a>link</a>", "href")


@pytest.mark.parametrize(
    "text",
    [
        '<a href="https://example.com" onclick="alert(1)">link</a>',
        '<a href="https://example.com" style="color:red">link</a>',
        '<a href="https://example.com" target="_blank">link</a>',
    ],
)
def test_extra_anchor_attributes_are_rejected(text: str) -> None:
    assert_rejected(text, "a")


@pytest.mark.parametrize(
    "text",
    [
        '<i class="big">italic</i>',
        '<strong id="x">bold</strong>',
        '<code lang="py">print(1)</code>',
    ],
)
def test_attributes_are_not_allowed_on_other_tags(text: str) -> None:
    assert_rejected(text, "attribute")


@pytest.mark.parametrize(
    "text",
    [
        "<a href='https://example.com'>link</a>",
        "<a href=https://example.com>link</a>",
        '<a href="https://a.test" href="https://b.test">link</a>',
    ],
)
def test_malformed_attribute_syntax_is_rejected(text: str) -> None:
    assert_rejected(text, "a")


@pytest.mark.parametrize(
    "href",
    [
        "javascript:alert(1)",
        "JavaScript:alert(1)",
        "data:text/html;base64,PHNjcmlwdD4=",
        "ftp://example.com/file",
        "/relative/path",
        "//example.com",
        "&#104;ttps://example.com",
    ],
)
def test_only_http_and_https_links_are_allowed(href: str) -> None:
    assert_rejected(f'<a href="{href}">link</a>', "href")


# --- екранування (R13, A9, A10) ---


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("a < b", "a &lt; b"),
        ("a > b", "a &gt; b"),
        ("Tom & Jerry", "Tom &amp; Jerry"),
        ('say "hi"', "say &quot;hi&quot;"),
        ("5 < 6 && 7 > 3", "5 &lt; 6 &amp;&amp; 7 &gt; 3"),
    ],
)
def test_special_characters_in_plain_text_are_escaped(text: str, expected: str) -> None:
    assert build_safe_html(text) == expected


def test_escaped_characters_are_not_escaped_twice() -> None:
    assert build_safe_html("Tom &amp; Jerry") == "Tom &amp; Jerry"


def test_special_characters_in_attribute_values_are_escaped() -> None:
    result = build_safe_html('<a href="https://example.com/?a=1&b=2" title="A & B">link</a>')

    assert result == '<a href="https://example.com/?a=1&amp;b=2" title="A &amp; B">link</a>'


def test_quote_in_attribute_value_cannot_break_out_of_the_tag() -> None:
    result = build_safe_html('<a href="https://example.com" title="&quot;">link</a>')

    assert result == '<a href="https://example.com" title="&quot;">link</a>'


def test_script_written_as_text_stays_text() -> None:
    result = build_safe_html("Use &lt;script&gt; carefully")

    assert result == "Use &lt;script&gt; carefully"


# --- ідемпотентність: збережений текст можна прогнати ще раз (A10) ---


@pytest.mark.parametrize(
    "text",
    [
        "plain text",
        "a < b & c > d",
        'say "hi"',
        "<i>italic</i> and <strong>bold</strong>",
        '<a href="https://example.com/?a=1&b=2" title="A & B">link</a>',
        "<code>if (a &lt; b) {}</code>",
    ],
)
def test_sanitising_is_idempotent(text: str) -> None:
    once = build_safe_html(text)

    assert build_safe_html(once) == once


# --- межові випадки, які фіксують прийняті рішення ---


def test_less_than_followed_by_letter_is_treated_as_a_tag() -> None:
    # A9: усе, що схоже на тег, перевіряється як тег. Щоб написати «a<b», потрібен пробіл
    # («a < b») або сутність («a &lt; b») — обидва варіанти проходять.
    assert_rejected("a<b", "not closed")
    assert build_safe_html("a < b") == "a &lt; b"


def test_less_than_before_non_letter_stays_text() -> None:
    assert build_safe_html("<3 love") == "&lt;3 love"


def test_same_tag_may_be_nested_except_anchor() -> None:
    assert build_safe_html("<i><i>double</i></i>") == "<i><i>double</i></i>"


def test_empty_title_is_allowed() -> None:
    result = build_safe_html('<a href="https://example.com" title="">link</a>')

    assert result == '<a href="https://example.com" title="">link</a>'
