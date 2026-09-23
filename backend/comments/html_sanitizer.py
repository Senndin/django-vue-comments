"""
Перевірка розмітки коментаря і збирання безпечного HTML (R13, R19, R20, A8–A10).

Модуль — єдине джерело правди про дозволену розмітку: ним користується і створення
коментаря, і попередній перегляд. Заборонену розмітку ми не вирізаємо, а відхиляємо
з помилкою, у якій названо проблемний тег чи атрибут (A8).

Результат збирається заново з екранованого тексту й нормалізованих тегів — саме цей
рядок зберігається в базі та віддається в API, тож фронтенд може вставити його через
`v-html` (A10).
"""

import re

from django.core.exceptions import ValidationError

ALLOWED_TAGS = frozenset({"a", "code", "i", "strong"})
# Атрибути має лише <a>: href обов'язковий, title — ні (R19, A9).
REQUIRED_ANCHOR_ATTRIBUTES = frozenset({"href"})
OPTIONAL_ANCHOR_ATTRIBUTES = frozenset({"title"})
ALLOWED_HREF_SCHEMES = ("http://", "https://")

# Початок тега: `<` і одразу літера або `/`. Решта `<` — звичайний текст (A9).
TAG_START_RE = re.compile(r"<(?=[A-Za-z/])")
# Тег цілком. Значення в подвійних лапках пропускаємо як одне ціле, щоб `>` усередині
# title="a > b" не обірвав тег завчасно.
TAG_RE = re.compile(r'<(?:"[^"]*"|[^">])*>')
CLOSING_TAG_RE = re.compile(r"</\s*([A-Za-z][A-Za-z0-9]*)\s*>")
OPENING_TAG_RE = re.compile(r'<([A-Za-z][A-Za-z0-9]*)((?:"[^"]*"|[^">])*)>')
ATTRIBUTE_RE = re.compile(r'\s+([A-Za-z][A-Za-z0-9-]*)\s*=\s*"([^"]*)"')
# Сутності, які створює сам санітайзер, плюс числові. Їх повторно не екрануємо,
# інакше друга обробка збереженого тексту дала б `&amp;amp;` (вимога ідемпотентності).
KNOWN_ENTITY_RE = re.compile(r"&(?:amp|lt|gt|quot|apos|#\d+|#[xX][0-9A-Fa-f]+);")


def escape_text(value: str) -> str:
    """Екранує `&`, `<`, `>` і лапки, не чіпаючи вже наявні HTML-сутності."""
    parts: list[str] = []
    position = 0
    for entity in KNOWN_ENTITY_RE.finditer(value):
        parts.append(_escape_all(value[position : entity.start()]))
        parts.append(entity.group())
        position = entity.end()
    parts.append(_escape_all(value[position:]))
    return "".join(parts)


def _escape_all(value: str) -> str:
    """Екранує всі спецсимволи. `&` першим, інакше екранували б власні ж сутності."""
    return (
        value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
    )


class HtmlSanitizer:
    """
    Розбирає текст коментаря на теги й звичайний текст і збирає безпечний HTML.

    Стан розбору — позиція в тексті, зібрані шматки результату і стек відкритих тегів —
    живе в екземплярі, тому клас, а не набір функцій із передаванням стану.
    """

    def __init__(self, text: str) -> None:
        self.text = text
        self._parts: list[str] = []
        # Стек відкритих тегів: закривати можна лише той, що на вершині (R20, A9).
        self._open_tags: list[str] = []

    def build(self) -> str:
        """Повертає безпечний HTML або кидає `ValidationError` із причиною (A8)."""
        position = 0
        while (start := TAG_START_RE.search(self.text, position)) is not None:
            self._parts.append(escape_text(self.text[position : start.start()]))
            position = self._handle_tag(start.start())

        self._parts.append(escape_text(self.text[position:]))

        if self._open_tags:
            raise ValidationError(f"Tag <{self._open_tags[-1]}> is not closed.")

        return "".join(self._parts)

    def _handle_tag(self, start: int) -> int:
        """Обробляє один тег, що починається на позиції `start`; повертає позицію за ним."""
        tag = TAG_RE.match(self.text, start)
        if tag is None:
            raise ValidationError(f'Tag is not closed with ">": {self.text[start : start + 30]!r}')

        if tag.group().startswith("</"):
            self._close_tag(tag.group())
        else:
            self._open_tag(tag.group())
        return tag.end()

    def _open_tag(self, raw_tag: str) -> None:
        match = OPENING_TAG_RE.fullmatch(raw_tag)
        if match is None:
            raise ValidationError(f"Malformed tag: {raw_tag!r}")

        name = match.group(1).lower()
        raw_attributes = match.group(2)

        if raw_attributes.rstrip().endswith("/"):
            # Дозволені теги не бувають порожніми, тож `<i/>` — це помилка, а не скорочення (A9).
            raise ValidationError(f"Tag <{name}> cannot be self-closing.")

        self._check_tag_is_allowed(name)

        if name == "a":
            self._parts.append(self._build_anchor(raw_attributes))
        else:
            if raw_attributes.strip():
                raise ValidationError(f"Tag <{name}> does not accept any attribute.")
            self._parts.append(f"<{name}>")

        self._open_tags.append(name)

    def _close_tag(self, raw_tag: str) -> None:
        match = CLOSING_TAG_RE.fullmatch(raw_tag)
        if match is None:
            raise ValidationError(f"Malformed closing tag: {raw_tag!r}")

        name = match.group(1).lower()
        self._check_tag_is_allowed(name)

        if not self._open_tags:
            raise ValidationError(f"Closing tag </{name}> has no matching opening tag.")
        if self._open_tags[-1] != name:
            raise ValidationError(
                f"Closing tag </{name}> does not match the last opened tag <{self._open_tags[-1]}>."
            )

        self._open_tags.pop()
        self._parts.append(f"</{name}>")

    def _check_tag_is_allowed(self, name: str) -> None:
        if name not in ALLOWED_TAGS:
            allowed = ", ".join(f"<{tag}>" for tag in sorted(ALLOWED_TAGS))
            raise ValidationError(f"Tag <{name}> is not allowed. Allowed tags: {allowed}.")

    def _build_anchor(self, raw_attributes: str) -> str:
        """Перевіряє атрибути `<a>` і збирає тег наново в сталому порядку."""
        if "a" in self._open_tags:
            raise ValidationError("Tag <a> cannot be nested inside another <a>.")

        attributes = self._parse_attributes(raw_attributes)

        for name in attributes:
            if name not in REQUIRED_ANCHOR_ATTRIBUTES | OPTIONAL_ANCHOR_ATTRIBUTES:
                raise ValidationError(f'Attribute "{name}" is not allowed in <a>.')
        for name in REQUIRED_ANCHOR_ATTRIBUTES:
            if name not in attributes:
                raise ValidationError(f'Attribute "{name}" is required in <a>.')

        href = attributes["href"].strip()
        if not href.lower().startswith(ALLOWED_HREF_SCHEMES):
            # Схеми на кшталт `javascript:` і `data:` виконують код у браузері (R13).
            raise ValidationError('Attribute "href" must start with http:// or https://.')

        anchor = f'<a href="{escape_text(href)}"'
        if "title" in attributes:
            anchor += f' title="{escape_text(attributes["title"])}"'
        return anchor + ">"

    def _parse_attributes(self, raw_attributes: str) -> dict[str, str]:
        """Розбирає рядок атрибутів; значення — лише в подвійних лапках (A9)."""
        attributes: dict[str, str] = {}
        position = 0
        while (match := ATTRIBUTE_RE.match(raw_attributes, position)) is not None:
            name = match.group(1).lower()
            if name in attributes:
                raise ValidationError(f'Attribute "{name}" is repeated in <a>.')
            attributes[name] = match.group(2)
            position = match.end()

        if raw_attributes[position:].strip():
            raise ValidationError(
                'Attributes of <a> must look like name="value" with double quotes, got: '
                f"{raw_attributes[position:].strip()!r}"
            )
        return attributes


def build_safe_html(text: str) -> str:
    """Публічна точка входу: перевіряє розмітку й повертає безпечний HTML (A10)."""
    return HtmlSanitizer(text).build()
