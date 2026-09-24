/** Перетворення безпечного HTML коментаря на звичайний текст. */

/**
 * Витягує текст із розмітки.
 *
 * Використовуємо `textContent`, а не регулярний вираз: нам потрібен саме текст без тегів,
 * і жоден фрагмент розмітки при цьому не може «ожити» в DOM.
 */
export function htmlToText(html) {
  const element = document.createElement('div')
  element.innerHTML = html ?? ''
  return (element.textContent ?? '').replace(/\s+/g, ' ').trim()
}

/** Короткий фрагмент тексту для таблиці (A3). */
export function excerpt(html, length = 120) {
  const text = htmlToText(html)
  return text.length > length ? `${text.slice(0, length).trimEnd()}…` : text
}
