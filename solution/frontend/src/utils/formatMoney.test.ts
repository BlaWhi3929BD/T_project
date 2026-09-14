import { describe, expect, it } from 'vitest';
import { formatMoney, parseMoney } from './formatMoney';

describe('formatMoney', () => {
  it('formats positive and negative decimal strings consistently', () => {
    expect(formatMoney('1234.5')).toBe('1,234.50');
    expect(formatMoney('-12.345')).toBe('-12.35');
    expect(formatMoney('0')).toBe('0.00');
  });

  it('uses a visible placeholder for missing values', () => {
    expect(formatMoney(null)).toBe('—');
    expect(formatMoney(undefined)).toBe('—');
    expect(formatMoney('')).toBe('—');
  });

  it('does not expose invalid numeric output', () => {
    expect(formatMoney('not-a-number')).toBe('0.00');
    expect(formatMoney(Infinity)).toBe('0.00');
  });
});

describe('parseMoney', () => {
  it('returns finite numbers for chart and CSS comparisons', () => {
    expect(parseMoney('10.25')).toBe(10.25);
    expect(parseMoney('-3.5')).toBe(-3.5);
    expect(parseMoney('invalid')).toBe(0);
    expect(parseMoney(null)).toBe(0);
  });
});
