/**
 * Клієнтські валідатори повторюють серверні правила (R21), тому й випадки тут ті самі,
 * що в тестах санітайзера й валідаторів бекенда.
 */
import { describe, expect, it } from 'vitest'

import {
  MAX_TEXT_LENGTH,
  validateAttachment,
  validateEmail,
  validateHomePage,
  validateMarkup,
  validateText,
  validateUserName,
} from '@/utils/validators.js'

function file(name, size) {
  return { name, size }
}

describe('validateUserName', () => {
  it.each(['Anonym', 'Rum8', 'a', 'A'.repeat(50), '0'])('accepts %s', (value) => {
    expect(validateUserName(value)).toBeNull()
  })

  it.each(['', '   ', 'Rum_8', 'Денис', 'two words', 'a@b', 'a-b', 'A'.repeat(51)])(
    'rejects %s',
    (value) => {
      expect(validateUserName(value)).toBeTruthy()
    },
  )
})

describe('validateEmail', () => {
  it.each(['user@example.com', 'a.b+c@sub.example.co.uk'])('accepts %s', (value) => {
    expect(validateEmail(value)).toBeNull()
  })

  it.each(['', 'user', 'user@', '@example.com', 'user @example.com', 'user@example'])(
    'rejects %s',
    (value) => {
      expect(validateEmail(value)).toBeTruthy()
    },
  )
})

describe('validateHomePage', () => {
  it('treats an empty value as valid: the field is optional', () => {
    expect(validateHomePage('')).toBeNull()
  })

  it.each(['http://example.com', 'https://example.com/path?a=1'])('accepts %s', (value) => {
    expect(validateHomePage(value)).toBeNull()
  })

  it.each(['example.com', 'ftp://example.com', 'javascript:alert(1)', '/relative'])(
    'rejects %s',
    (value) => {
      expect(validateHomePage(value)).toBeTruthy()
    },
  )
})

describe('validateText', () => {
  it.each(['hello', 'x'.repeat(MAX_TEXT_LENGTH), '<i>markup</i> is fine'])(
    'accepts valid text',
    (value) => {
      expect(validateText(value)).toBeNull()
    },
  )

  it.each(['', '   ', 'x'.repeat(MAX_TEXT_LENGTH + 1)])('rejects %s', (value) => {
    expect(validateText(value)).toBeTruthy()
  })
})

describe('validateMarkup', () => {
  it.each([
    '<i>italic</i>',
    '<strong>bold</strong>',
    '<code>print(1)</code>',
    '<a href="https://example.com">link</a>',
    '<a href="http://example.com" title="Example">link</a>',
    '<i><strong>both</strong></i>',
    'plain text without tags',
    'a < b',
  ])('accepts %s', (value) => {
    expect(validateMarkup(value)).toBeNull()
  })

  it.each([
    ['<script>alert(1)</script>', 'script'],
    ['<b>bold</b>', 'b'],
    ['<img src="x" onerror="alert(1)">', 'img'],
    ['<div>block</div>', 'div'],
  ])('rejects the forbidden tag in %s', (value, tag) => {
    expect(validateMarkup(value)).toContain(tag)
  })

  it.each([
    '<i>unclosed',
    'italic</i>',
    '<i><strong>text</i></strong>',
    '<i/>',
    '<a href="https://a.test">outer <a href="https://b.test">inner</a></a>',
  ])('rejects broken nesting in %s', (value) => {
    expect(validateMarkup(value)).toBeTruthy()
  })

  it.each([
    '<a>link</a>',
    '<a href="javascript:alert(1)">link</a>',
    '<a href="data:text/html,x">link</a>',
    '<a href="/relative">link</a>',
    '<a href="https://example.com" onclick="alert(1)">link</a>',
    "<a href='https://example.com'>link</a>",
    '<a href=https://example.com>link</a>',
    '<i class="big">italic</i>',
  ])('rejects bad attributes in %s', (value) => {
    expect(validateMarkup(value)).toBeTruthy()
  })

  it('reports the same problem as the server for a forbidden tag', () => {
    expect(validateMarkup('<b>x</b>')).toBe(
      'Tag <b> is not allowed. Allowed tags: <a>, <code>, <i>, <strong>.',
    )
  })
})

describe('validateAttachment', () => {
  it('treats no file as valid: the field is optional', () => {
    expect(validateAttachment(null)).toBeNull()
  })

  it.each([
    ['photo.png', 1024],
    ['photo.JPG', 5 * 1024 * 1024],
    ['animation.gif', 10],
    ['notes.txt', 100 * 1024],
  ])('accepts %s', (name, size) => {
    expect(validateAttachment(file(name, size))).toBeNull()
  })

  it.each([
    ['photo.bmp', 1024],
    ['archive.zip', 1024],
    ['photo.png', 5 * 1024 * 1024 + 1],
    ['notes.txt', 100 * 1024 + 1],
  ])('rejects %s of %i bytes', (name, size) => {
    expect(validateAttachment(file(name, size))).toBeTruthy()
  })
})
