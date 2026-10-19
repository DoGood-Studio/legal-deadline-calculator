/**
 * Pure civil-date arithmetic on the proleptic Gregorian calendar.
 *
 * Dates are handled as day numbers (days since 1970-01-01) and exchanged as
 * `YYYY-MM-DD` strings. JavaScript `Date` objects are never used, so results do
 * not depend on the machine's time zone.
 */
import { InputError } from "./errors.js";

export type ISODate = string;

const ISO_DATE = /^(\d{4})-(\d{2})-(\d{2})$/;
export const MIN_YEAR = 1;
export const MAX_YEAR = 9999;

/** Days since 1970-01-01 (Howard Hinnant's algorithm). */
export function daysFromCivil(year: number, month: number, day: number): number {
  const y = month <= 2 ? year - 1 : year;
  const era = Math.floor(y / 400);
  const yoe = y - era * 400;
  const doy = Math.floor((153 * (month + (month > 2 ? -3 : 9)) + 2) / 5) + day - 1;
  const doe = yoe * 365 + Math.floor(yoe / 4) - Math.floor(yoe / 100) + doy;
  return era * 146097 + doe - 719468;
}

export function civilFromDays(days: number): [number, number, number] {
  const z = days + 719468;
  const era = Math.floor(z / 146097);
  const doe = z - era * 146097;
  const yoe = Math.floor((doe - Math.floor(doe / 1460) + Math.floor(doe / 36524) - Math.floor(doe / 146096)) / 365);
  const doy = doe - (365 * yoe + Math.floor(yoe / 4) - Math.floor(yoe / 100));
  const mp = Math.floor((5 * doy + 2) / 153);
  const day = doy - Math.floor((153 * mp + 2) / 5) + 1;
  const month = mp < 10 ? mp + 3 : mp - 9;
  return [yoe + era * 400 + (month <= 2 ? 1 : 0), month, day];
}

export function isLeapYear(year: number): boolean {
  return (year % 4 === 0 && year % 100 !== 0) || year % 400 === 0;
}

export function daysInMonth(year: number, month: number): number {
  return [31, isLeapYear(year) ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1]!;
}

export function makeDay(year: number, month: number, day: number): number {
  return daysFromCivil(year, month, day);
}

export function yearOf(day: number): number {
  return civilFromDays(day)[0];
}

/** ISO weekday, 1 = Monday ... 7 = Sunday. 1970-01-01 was a Thursday. */
export function isoWeekday(day: number): number {
  return (((day + 3) % 7) + 7) % 7 + 1;
}

export function formatISO(day: number): ISODate {
  const [y, m, d] = civilFromDays(day);
  return `${String(y).padStart(4, "0")}-${String(m).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
}

function checkRange(day: number, what: string): number {
  const year = yearOf(day);
  if (year < MIN_YEAR || year > MAX_YEAR) throw new InputError(`date out of range: ${what}`);
  return day;
}

/** Parses a strict `YYYY-MM-DD` string into a day number. */
export function parseDate(value: unknown, field = "date"): number {
  if (value instanceof Date) {
    throw new InputError(
      `${field}: pass a 'YYYY-MM-DD' string, not a Date. Which calendar day a Date belongs to depends on a time zone.`,
    );
  }
  if (typeof value !== "string") {
    throw new InputError(`${field}: expected a 'YYYY-MM-DD' string, got ${typeof value}`);
  }
  const match = ISO_DATE.exec(value);
  if (!match) throw new InputError(`${field}: expected YYYY-MM-DD, got ${JSON.stringify(value)}`);
  const year = Number(match[1]);
  const month = Number(match[2]);
  const day = Number(match[3]);
  if (year < MIN_YEAR || month < 1 || month > 12 || day < 1 || day > daysInMonth(year, month)) {
    throw new InputError(`${field}: ${JSON.stringify(value)} is not a valid date`);
  }
  return daysFromCivil(year, month, day);
}

export function addDays(day: number, days: number): number {
  return checkRange(day + days, `${formatISO(day)} ${days >= 0 ? "+" : ""}${days} days`);
}

/** Adds calendar months, clamping to the last day of a shorter target month. */
export function addMonths(day: number, months: number): [number, boolean] {
  const [y, m, d] = civilFromDays(day);
  const index = y * 12 + (m - 1) + months;
  const year = Math.floor(index / 12);
  const month = index - year * 12 + 1;
  if (year < MIN_YEAR || year > MAX_YEAR) throw new InputError(`date out of range: ${formatISO(day)} ${months} months`);
  const last = daysInMonth(year, month);
  return d > last ? [daysFromCivil(year, month, last), true] : [daysFromCivil(year, month, d), false];
}

/** Gregorian Easter Sunday (anonymous Gregorian algorithm). */
export function easterWestern(year: number): number {
  const a = year % 19;
  const b = Math.floor(year / 100);
  const c = year % 100;
  const d = Math.floor(b / 4);
  const e = b % 4;
  const f = Math.floor((b + 8) / 25);
  const g = Math.floor((b - f + 1) / 3);
  const h = (19 * a + b - d - g + 15) % 30;
  const i = Math.floor(c / 4);
  const k = c % 4;
  const l = (32 + 2 * e + 2 * i - h - k) % 7;
  const m = Math.floor((a + 11 * h + 22 * l) / 451);
  const n = h + l - 7 * m + 114;
  return daysFromCivil(year, Math.floor(n / 31), (n % 31) + 1);
}

/** Orthodox Easter Sunday as a Gregorian date (Meeus' Julian algorithm). */
export function easterOrthodox(year: number): number {
  const a = year % 4;
  const b = year % 7;
  const c = year % 19;
  const d = (19 * c + 15) % 30;
  const e = (2 * a + 4 * b - d + 34) % 7;
  const n = d + e + 114;
  const julianOffset = Math.floor(year / 100) - Math.floor(year / 400) - 2;
  return daysFromCivil(year, Math.floor(n / 31), (n % 31) + 1) + julianOffset;
}

/** The n-th ISO weekday of a month; negative n counts from the end. */
export function nthWeekday(year: number, month: number, weekday: number, n: number): number | null {
  const last = daysInMonth(year, month);
  let day: number;
  if (n > 0) {
    const first = isoWeekday(daysFromCivil(year, month, 1));
    day = 1 + (((weekday - first) % 7) + 7) % 7 + 7 * (n - 1);
  } else {
    const end = isoWeekday(daysFromCivil(year, month, last));
    day = last - ((((end - weekday) % 7) + 7) % 7) - 7 * (-n - 1);
  }
  return day >= 1 && day <= last ? daysFromCivil(year, month, day) : null;
}

export type RelativeDirection = "on_or_after" | "after" | "on_or_before" | "before";

export function weekdayRelative(anchor: number, weekday: number, direction: RelativeDirection): number {
  const mod = (x: number) => ((x % 7) + 7) % 7;
  switch (direction) {
    case "on_or_after":
      return anchor + mod(weekday - isoWeekday(anchor));
    case "after":
      return weekdayRelative(anchor + 1, weekday, "on_or_after");
    case "on_or_before":
      return anchor - mod(isoWeekday(anchor) - weekday);
    case "before":
      return weekdayRelative(anchor - 1, weekday, "on_or_before");
  }
}
