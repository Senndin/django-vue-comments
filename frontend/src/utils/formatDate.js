/** Дата коментаря у форматі `dd.mm.yy HH:MM` (A6). */

function pad(value) {
  return String(value).padStart(2, '0')
}

/**
 * Перетворює ISO-рядок із API на локальний час читача.
 *
 * Сервер зберігає час у UTC, а `new Date` переводить його в часовий пояс браузера —
 * тому «щойно» виглядає як «щойно» і в Києві, і в Лісабоні.
 */
export function formatDate(isoString) {
  // `new Date(null)` дає 1970 рік, а не помилку, тож порожнє значення відсікаємо окремо.
  if (typeof isoString !== 'string' || !isoString) return ''

  const date = new Date(isoString)
  if (Number.isNaN(date.getTime())) return ''

  const day = pad(date.getDate())
  const month = pad(date.getMonth() + 1)
  const year = pad(date.getFullYear() % 100)
  return `${day}.${month}.${year} ${pad(date.getHours())}:${pad(date.getMinutes())}`
}
