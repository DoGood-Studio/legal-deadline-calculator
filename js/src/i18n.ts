import { MESSAGES } from "./data.generated.js";
import { formatISO, isoWeekday } from "./dates.js";

export type LocalizedText = Readonly<Record<string, string>>;
export const DEFAULT_LANG = "en";

interface MessageTable {
  languages: readonly string[];
  date_format: LocalizedText;
  weekdays: Readonly<Record<string, readonly string[]>>;
  messages: Readonly<Record<string, LocalizedText>>;
}

const table = MESSAGES as unknown as MessageTable;

export function languages(): readonly string[] {
  return table.languages;
}

/** Marks a day number so messages format it as a date. */
export class DateParam {
  constructor(readonly day: number) {}
}

export type MessageParam = string | number | DateParam | LocalizedText;

export function pick(text: LocalizedText | string | null | undefined, lang: string): string {
  if (text == null) return "";
  if (typeof text === "string") return text;
  return text[lang] || text[DEFAULT_LANG] || Object.values(text)[0] || "";
}

export function formatDate(day: number, lang: string): string {
  const iso = formatISO(day);
  const weekdays: Record<string, string> = {};
  for (const [code, names] of Object.entries(table.weekdays)) weekdays[code] = names[isoWeekday(day) - 1]!;
  return fill(pick(table.date_format, lang), {
    iso,
    yyyy: iso.slice(0, 4),
    mm: iso.slice(5, 7),
    dd: iso.slice(8, 10),
    weekday: pick(weekdays, lang),
  });
}

function fill(template: string, values: Readonly<Record<string, string>>): string {
  return template.replace(/\{(\w+)\}/g, (_, name: string) => {
    const value = values[name];
    if (value === undefined) throw new Error(`message parameter missing: ${name}`);
    return value;
  });
}

function asText(value: MessageParam, lang: string): string {
  if (value instanceof DateParam) return formatDate(value.day, lang);
  if (typeof value === "object") return pick(value, lang);
  return String(value);
}

/** Renders message `key` (or an override) in every supported language. */
export function render(
  key: string,
  params: Readonly<Record<string, MessageParam>>,
  override?: LocalizedText,
): Record<string, string> {
  const templates = override ?? table.messages[key];
  if (!templates) throw new Error(`unknown message key ${key}`);
  const out: Record<string, string> = {};
  for (const lang of languages()) {
    const values: Record<string, string> = {};
    for (const [name, value] of Object.entries(params)) values[name] = asText(value, lang);
    out[lang] = fill(pick(templates, lang), values);
  }
  return out;
}
