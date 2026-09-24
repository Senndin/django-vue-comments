/**
 * Клієнтська перевірка полів форми (R21).
 *
 * Це дзеркало серверних правил, і воно потрібне лише для зручності: відповідь показується
 * одразу, без запиту. Остаточне рішення завжди за сервером — тут немає нічого, на що
 * можна покластися з точки зору безпеки (`CLAUDE.md` §5.4).
 *
 * Кожна функція повертає текст помилки або `null`, якщо значення підходить.
 */

export const MAX_TEXT_LENGTH = 5000
export const MAX_USER_NAME_LENGTH = 50
export const MAX_IMAGE_BYTES = 5 * 1024 * 1024
export const MAX_TEXT_FILE_BYTES = 100 * 1024

const USER_NAME_PATTERN = /^[A-Za-z0-9]+$/
// Груба перевірка форми адреси: точний розбір робить сервер.
const EMAIL_PATTERN = /^[^\s@]+@[^\s@.]+(\.[^\s@.]+)+$/

export function validateUserName(value) {
  const name = (value ?? '').trim()
  if (!name) return 'User name is required.'
  if (name.length > MAX_USER_NAME_LENGTH) {
    return `User name must be at most ${MAX_USER_NAME_LENGTH} characters.`
  }
  if (!USER_NAME_PATTERN.test(name)) return 'Only latin letters and digits are allowed.'
  return null
}

export function validateEmail(value) {
  const email = (value ?? '').trim()
  if (!email) return 'E-mail is required.'
  if (!EMAIL_PATTERN.test(email)) return 'Enter a valid e-mail address.'
  return null
}

/** Домашня сторінка необов'язкова, але якщо заповнена — лише http/https (R7). */
export function validateHomePage(value) {
  const url = (value ?? '').trim()
  if (!url) return null

  let parsed
  try {
    parsed = new URL(url)
  } catch {
    return 'Enter a valid URL, for example https://example.com.'
  }
  if (!['http:', 'https:'].includes(parsed.protocol))
    return 'Only http and https links are allowed.'
  return null
}

export function validateText(value) {
  const text = value ?? ''
  if (!text.trim()) return 'Message is required.'
  if (text.length > MAX_TEXT_LENGTH) {
    return `Message must be at most ${MAX_TEXT_LENGTH} characters.`
  }
  return validateMarkup(text)
}

export function validateCaptcha(value) {
  return (value ?? '').trim() ? null : 'Enter the code from the image.'
}

/** Вкладення: або картинка, або текстовий файл, кожне зі своїм лімітом (R17, R18, A11). */
export function validateAttachment(file) {
  if (!file) return null

  if (file.name.toLowerCase().endsWith('.txt')) {
    return file.size > MAX_TEXT_FILE_BYTES ? 'Text file must be at most 100 KB.' : null
  }
  if (!/\.(jpe?g|gif|png)$/i.test(file.name)) {
    return 'Attach an image (JPG, GIF, PNG) or a TXT file.'
  }
  return file.size > MAX_IMAGE_BYTES ? 'Image must be at most 5 MB.' : null
}

// --- перевірка розмітки: та сама логіка, що й у санітайзері на сервері (R19, R20) ---

const ALLOWED_TAGS = new Set(['a', 'code', 'i', 'strong'])
const ALLOWED_ANCHOR_ATTRIBUTES = new Set(['href', 'title'])
const TAG_START = /<(?=[A-Za-z/])/g
const TAG = /<(?:"[^"]*"|[^">])*>/y
const CLOSING_TAG = /^<\/\s*([A-Za-z][A-Za-z0-9]*)\s*>$/
const OPENING_TAG = /^<([A-Za-z][A-Za-z0-9]*)((?:"[^"]*"|[^">])*)>$/
const ATTRIBUTE = /\s+([A-Za-z][A-Za-z0-9-]*)\s*=\s*"([^"]*)"/y

/**
 * Перевіряє теги повідомлення: білий список, атрибути, порядок закриття.
 *
 * Регулярний вираз розбирає окремий тег, а стек стежить за вкладеністю — самими лише
 * регулярними виразами збалансованість тегів не перевіряється.
 */
export function validateMarkup(text) {
  const openTags = []

  TAG_START.lastIndex = 0
  let start = TAG_START.exec(text)
  while (start) {
    TAG.lastIndex = start.index
    const match = TAG.exec(text)
    if (!match) return 'A tag is not closed with ">".'

    const error = handleTag(match[0], openTags)
    if (error) return error

    // Наступний тег шукаємо одразу за поточним, інакше `<a href="<b>">` дав би зайвий збіг.
    TAG_START.lastIndex = start.index + match[0].length
    start = TAG_START.exec(text)
  }

  return openTags.length ? `Tag <${openTags.at(-1)}> is not closed.` : null
}

function handleTag(rawTag, openTags) {
  return rawTag.startsWith('</') ? closeTag(rawTag, openTags) : openTag(rawTag, openTags)
}

function openTag(rawTag, openTags) {
  const match = OPENING_TAG.exec(rawTag)
  if (!match) return `Malformed tag: ${rawTag}`

  const name = match[1].toLowerCase()
  const rawAttributes = match[2]

  if (rawAttributes.trimEnd().endsWith('/')) return `Tag <${name}> cannot be self-closing.`

  const notAllowed = checkTagIsAllowed(name)
  if (notAllowed) return notAllowed

  if (name !== 'a') {
    if (rawAttributes.trim()) return `Tag <${name}> does not accept any attribute.`
    openTags.push(name)
    return null
  }

  if (openTags.includes('a')) return 'Tag <a> cannot be nested inside another <a>.'

  const attributes = parseAttributes(rawAttributes)
  if (typeof attributes === 'string') return attributes

  for (const attribute of attributes.keys()) {
    if (!ALLOWED_ANCHOR_ATTRIBUTES.has(attribute)) {
      return `Attribute "${attribute}" is not allowed in <a>.`
    }
  }
  if (!attributes.has('href')) return 'Attribute "href" is required in <a>.'

  const href = attributes.get('href').trim().toLowerCase()
  if (!href.startsWith('http://') && !href.startsWith('https://')) {
    return 'Attribute "href" must start with http:// or https://.'
  }

  openTags.push(name)
  return null
}

function closeTag(rawTag, openTags) {
  const match = CLOSING_TAG.exec(rawTag)
  if (!match) return `Malformed closing tag: ${rawTag}`

  const name = match[1].toLowerCase()
  const notAllowed = checkTagIsAllowed(name)
  if (notAllowed) return notAllowed

  if (!openTags.length) return `Closing tag </${name}> has no matching opening tag.`
  if (openTags.at(-1) !== name) {
    return `Closing tag </${name}> does not match the last opened tag <${openTags.at(-1)}>.`
  }

  openTags.pop()
  return null
}

function checkTagIsAllowed(name) {
  if (ALLOWED_TAGS.has(name)) return null
  const allowed = [...ALLOWED_TAGS].sort().map((tag) => `<${tag}>`)
  return `Tag <${name}> is not allowed. Allowed tags: ${allowed.join(', ')}.`
}

/** Повертає розібрані атрибути або текст помилки. */
function parseAttributes(rawAttributes) {
  const attributes = new Map()
  let position = 0

  ATTRIBUTE.lastIndex = 0
  let match = ATTRIBUTE.exec(rawAttributes)
  while (match) {
    const name = match[1].toLowerCase()
    if (attributes.has(name)) return `Attribute "${name}" is repeated in <a>.`
    attributes.set(name, match[2])
    position = ATTRIBUTE.lastIndex
    match = ATTRIBUTE.exec(rawAttributes)
  }

  if (rawAttributes.slice(position).trim()) {
    return 'Attributes of <a> must look like name="value" with double quotes.'
  }
  return attributes
}
