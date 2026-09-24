import { describe, expect, it } from 'vitest'

import { formatDate } from '@/utils/formatDate.js'

describe('formatDate', () => {
  it('formats a date as dd.mm.yy HH:MM', () => {
    // Локальний час: беремо дату без зсуву, щоб тест не залежав від часового поясу.
    const date = new Date(2022, 4, 22, 22, 30)

    expect(formatDate(date.toISOString())).toBe('22.05.22 22:30')
  })

  it('pads single digits with zeros', () => {
    const date = new Date(2024, 0, 5, 9, 7)

    expect(formatDate(date.toISOString())).toBe('05.01.24 09:07')
  })

  it.each([null, undefined, '', 'not a date'])('returns an empty string for %s', (value) => {
    expect(formatDate(value)).toBe('')
  })
})
