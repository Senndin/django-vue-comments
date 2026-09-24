/** Аватар без зовнішніх сервісів: кружок з ініціалами (A6). */

/** Одна-дві літери з імені — те, що показує аватар. */
export function initials(name) {
  const cleaned = (name ?? '').trim()
  if (!cleaned) return '?'
  return cleaned.slice(0, 2).toUpperCase()
}

/**
 * Колір кружка за іменем: однаковий автор завжди має однаковий колір.
 *
 * Gravatar свідомо не використовуємо (A6): це зовнішній запит і витік хешу e-mail.
 */
export function avatarHue(name) {
  let hash = 0
  for (const character of name ?? '') {
    hash = (hash * 31 + character.codePointAt(0)) % 360
  }
  return hash
}
