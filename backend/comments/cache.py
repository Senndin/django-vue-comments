"""
Кеш сторінок списку заголовних коментарів (T8, A18).

Ідея: кожна сторінка лежить у Redis під ключем, у який входить «версія» списку. Новий
коментар не шукає й не видаляє конкретні ключі — він просто збільшує версію, і всі старі
ключі стають недосяжними, а згодом згасають за TTL. Це дешевше, ніж перебирати комбінації
сторінок і сортувань, і не залежить від того, скільки їх було.
"""

from django.core.cache import cache

# Скільки живе сторінка в кеші. П'ять хвилин — компроміс між навантаженням на БД і тим,
# наскільки застарілими можуть бути дані, якщо інвалідація чомусь не спрацювала.
LIST_CACHE_TIMEOUT = 5 * 60
LIST_VERSION_KEY = "comments:list:version"


def list_version() -> int:
    """Поточна версія списку. Живе без TTL: її скидання лише зайвий раз прогріє кеш."""
    version = cache.get(LIST_VERSION_KEY)
    if version is None:
        version = 1
        cache.set(LIST_VERSION_KEY, version, None)
    return version


def page_cache_key(host: str, ordering: str, page: str) -> str:
    """
    Ключ сторінки списку.

    Хост входить у ключ, бо в кешованій відповіді лежать абсолютні посилання `next`/`previous`:
    сторінка, збережена для одного домену, іншому віддала б чужі адреси.
    """
    return f"comments:list:v{list_version()}:{host}:{ordering}:{page}"


def invalidate_list() -> None:
    """Новий коментар — нова версія списку (A18)."""
    try:
        cache.incr(LIST_VERSION_KEY)
    except ValueError:
        # `incr` працює лише з наявним ключем: якщо версії ще немає (перший запуск або
        # кеш очистили), достатньо просто створити її.
        cache.set(LIST_VERSION_KEY, 1, None)
