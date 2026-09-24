import { describe, expect, it } from 'vitest'

import { excerpt, htmlToText } from '@/utils/text.js'

describe('htmlToText', () => {
  it('drops allowed markup and keeps the text', () => {
    expect(htmlToText('<strong>bold</strong> and <i>italic</i>')).toBe('bold and italic')
  })

  it('decodes escaped characters', () => {
    expect(htmlToText('5 &lt; 6 &amp; 7 &gt; 3')).toBe('5 < 6 & 7 > 3')
  })

  it('collapses whitespace', () => {
    expect(htmlToText('  many\n\n  spaces  ')).toBe('many spaces')
  })

  it.each([null, undefined, ''])('returns an empty string for %s', (value) => {
    expect(htmlToText(value)).toBe('')
  })
})

describe('excerpt', () => {
  it('keeps short text as is', () => {
    expect(excerpt('<i>short</i>')).toBe('short')
  })

  it('cuts long text and adds an ellipsis', () => {
    const result = excerpt('x'.repeat(200), 10)

    expect(result).toBe(`${'x'.repeat(10)}…`)
  })
})
