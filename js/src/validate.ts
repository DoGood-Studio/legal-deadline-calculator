import { DataError } from "./errors.js";
import type { LocalizedText } from "./i18n.js";

export type Json = null | boolean | number | string | Json[] | { [key: string]: Json };
export type Obj = Record<string, unknown>;

export function isObj(value: unknown): value is Obj {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

export function checkKeys(value: unknown, allowed: ReadonlySet<string>, where: string): Obj {
  if (!isObj(value)) throw new DataError(`${where}: expected an object`);
  const unknown = Object.keys(value).filter((k) => !allowed.has(k)).sort();
  if (unknown.length) throw new DataError(`${where}: unknown field(s) ${JSON.stringify(unknown)}`);
  return value;
}

export function checkInt(value: unknown, where: string, lo: number, hi: number): number {
  if (typeof value !== "number" || !Number.isInteger(value) || value < lo || value > hi) {
    throw new DataError(`${where}: expected an integer in [${lo}, ${hi}], got ${JSON.stringify(value)}`);
  }
  return value;
}

export function checkName(value: unknown, where: string): LocalizedText {
  if (!isObj(value) || Object.keys(value).length === 0 || !Object.values(value).every((v) => typeof v === "string" && v)) {
    throw new DataError(`${where}: 'name' must be a non-empty {lang: text} object`);
  }
  return value as LocalizedText;
}
