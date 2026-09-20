/**
 * Centralized formatting utilities for Digital Twin AI.
 * Handles currency and date formatting across all application modules.
 */

export type CurrencyCode = 'INR' | 'USD' | 'EUR' | 'GBP';
export type DateFormat = 'YYYY-MM-DD' | 'DD/MM/YYYY' | 'MM/DD/YYYY';

export const CURRENCY_SYMBOLS: Record<CurrencyCode, string> = {
  INR: '₹',
  USD: '$',
  EUR: '€',
  GBP: '£',
};

export const CURRENCY_LOCALES: Record<CurrencyCode, string> = {
  INR: 'en-IN',
  USD: 'en-US',
  EUR: 'de-DE',
  GBP: 'en-GB',
};

/**
 * Formats a numeric monetary value using the user's selected display currency.
 * NOTE: As per product specifications, this formats the value with the selected
 * currency symbol and locale grouping WITHOUT fabricating exchange rate conversions.
 */
export function formatCurrency(
  val: number | string | null | undefined,
  currency: CurrencyCode = 'INR',
  options?: { maximumFractionDigits?: number; minimumFractionDigits?: number }
): string {
  if (val === null || val === undefined || val === '') {
    return `${CURRENCY_SYMBOLS[currency] || '₹'}0`;
  }

  const num = typeof val === 'number' ? val : parseFloat(String(val));
  if (isNaN(num)) {
    return `${CURRENCY_SYMBOLS[currency] || '₹'}0`;
  }

  const symbol = CURRENCY_SYMBOLS[currency] || '₹';
  const locale = CURRENCY_LOCALES[currency] || 'en-US';
  const isNegative = num < 0;
  const absNum = Math.abs(num);

  const formattedNum = absNum.toLocaleString(locale, {
    maximumFractionDigits: options?.maximumFractionDigits ?? 0,
    minimumFractionDigits: options?.minimumFractionDigits ?? 0,
  });

  return isNegative ? `-${symbol}${formattedNum}` : `${symbol}${formattedNum}`;
}

/**
 * Compact currency formatter for chart axis tick labels and compact stat tags.
 * e.g. ₹50k, $1.2M, €450k
 */
export function formatCompactCurrency(
  val: number | null | undefined,
  currency: CurrencyCode = 'INR'
): string {
  if (val === null || val === undefined || isNaN(val)) {
    return `${CURRENCY_SYMBOLS[currency] || '₹'}0`;
  }

  const symbol = CURRENCY_SYMBOLS[currency] || '₹';
  const isNegative = val < 0;
  const absVal = Math.abs(val);

  let formatted: string;
  if (absVal >= 1_000_000) {
    formatted = `${(absVal / 1_000_000).toFixed(1).replace(/\.0$/, '')}M`;
  } else if (absVal >= 1_000) {
    formatted = `${(absVal / 1_000).toFixed(0)}k`;
  } else {
    formatted = `${Math.round(absVal)}`;
  }

  return isNegative ? `-${symbol}${formatted}` : `${symbol}${formatted}`;
}

/**
 * Formats date values according to the user's date format preference:
 * - 'YYYY-MM-DD': e.g. 2026-09-04
 * - 'DD/MM/YYYY': e.g. 04/09/2026
 * - 'MM/DD/YYYY': e.g. 09/04/2026
 *
 * Designed to be immune to UTC midnight timezone drift on ISO date strings.
 */
export function formatDate(
  dateInput: string | number | Date | null | undefined,
  format: DateFormat = 'YYYY-MM-DD'
): string {
  if (!dateInput) return '—';

  let year: number;
  let month: number; // 1-12
  let day: number; // 1-31

  if (typeof dateInput === 'string' && /^\d{4}-\d{2}-\d{2}/.test(dateInput)) {
    const parts = dateInput.substring(0, 10).split('-');
    year = parseInt(parts[0], 10);
    month = parseInt(parts[1], 10);
    day = parseInt(parts[2], 10);
  } else if (dateInput instanceof Date) {
    if (isNaN(dateInput.getTime())) return '—';
    year = dateInput.getFullYear();
    month = dateInput.getMonth() + 1;
    day = dateInput.getDate();
  } else {
    const parsed = new Date(dateInput);
    if (isNaN(parsed.getTime())) return String(dateInput);
    year = parsed.getFullYear();
    month = parsed.getMonth() + 1;
    day = parsed.getDate();
  }

  const yyyy = String(year).padStart(4, '0');
  const mm = String(month).padStart(2, '0');
  const dd = String(day).padStart(2, '0');

  switch (format) {
    case 'DD/MM/YYYY':
      return `${dd}/${mm}/${yyyy}`;
    case 'MM/DD/YYYY':
      return `${mm}/${dd}/${yyyy}`;
    case 'YYYY-MM-DD':
    default:
      return `${yyyy}-${mm}-${dd}`;
  }
}

/**
 * Formats a date with a human-readable month name while respecting order from date format.
 * e.g. "04 Sep 2026" or "Sep 04, 2026"
 */
export function formatFriendlyDate(
  dateInput: string | number | Date | null | undefined,
  format: DateFormat = 'YYYY-MM-DD'
): string {
  if (!dateInput) return '—';

  let year: number;
  let month: number;
  let day: number;

  if (typeof dateInput === 'string' && /^\d{4}-\d{2}-\d{2}/.test(dateInput)) {
    const parts = dateInput.substring(0, 10).split('-');
    year = parseInt(parts[0], 10);
    month = parseInt(parts[1], 10) - 1;
    day = parseInt(parts[2], 10);
  } else {
    const d = new Date(dateInput);
    if (isNaN(d.getTime())) return String(dateInput);
    year = d.getFullYear();
    month = d.getMonth();
    day = d.getDate();
  }

  const dateObj = new Date(year, month, day);
  const monthName = dateObj.toLocaleDateString('en-US', { month: 'short' });
  const dayStr = String(day).padStart(2, '0');

  switch (format) {
    case 'DD/MM/YYYY':
      return `${dayStr} ${monthName} ${year}`;
    case 'MM/DD/YYYY':
      return `${monthName} ${dayStr}, ${year}`;
    case 'YYYY-MM-DD':
    default:
      return `${year}-${String(month + 1).padStart(2, '0')}-${dayStr}`;
  }
}
