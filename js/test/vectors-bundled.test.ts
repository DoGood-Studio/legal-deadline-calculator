// Runs the jurisdiction vectors (vectors/<jurisdiction>/*.json) against the bundled data,
// exactly like python/tests/test_vectors_bundled.py.
import { existsSync, readdirSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { languages } from "../src/i18n.js";
import {
  calendar,
  compute,
  CoverageError,
  DataError,
  InputError,
  listCalendars,
  listRulepacks,
  OptionError,
  rulepack,
} from "../src/index.js";

const root = join(dirname(fileURLToPath(import.meta.url)), "..", "..", "vectors");
const ERRORS: Record<string, readonly (new (...args: never[]) => Error)[]> = {
  CoverageError: [CoverageError],
  DataError: [DataError],
  OptionError: [OptionError],
  ValueError: [InputError, DataError, CoverageError, OptionError],
};

function collect(kind: string): Record<string, any>[] {
  const cases: Record<string, any>[] = [];
  for (const dir of readdirSync(root).sort()) {
    const file = join(root, dir, `${kind}.json`);
    if (dir === "core" || !existsSync(file)) continue;
    for (const c of JSON.parse(readFileSync(file, "utf8")).cases) cases.push({ ...c, _file: dir });
  }
  return cases;
}

function expectError(fn: () => unknown, name: string): void {
  let thrown: unknown;
  try {
    fn();
  } catch (err) {
    thrown = err;
  }
  expect(ERRORS[name]!.some((cls) => thrown instanceof cls), `expected ${name}, got ${String(thrown)}`).toBe(true);
}

function calendarCall(c: Record<string, any>): unknown {
  const cal = calendar(c.calendar);
  const a = c.args;
  const opts = { kinds: a.kinds, halfDays: a.half_days, weekend: a.weekend, inclusive: a.inclusive };
  switch (c.fn) {
    case "holidays":
      return cal.holidays(a.year, a.kinds ? { kinds: a.kinds } : {}).map((h) => [h.date, h.id]);
    case "holiday_ids":
      return cal.holidays(a.year).map((h) => h.id);
    case "add_business_days":
      return cal.addBusinessDays(a.date, a.n, opts);
    case "business_days_between":
      return cal.businessDaysBetween(a.start, a.end, opts);
    case "is_business_day":
      return cal.isBusinessDay(a.date, opts);
    case "next_business_day":
      return cal.nextBusinessDay(a.date, opts);
    case "previous_business_day":
      return cal.previousBusinessDay(a.date, opts);
    default:
      throw new Error(`unknown fn ${c.fn}`);
  }
}

describe("bundled calendar vectors", () => {
  for (const c of collect("calendar")) {
    it(`${c._file}:${c.id}`, () => {
      if (c.error) return expectError(() => calendarCall(c), c.error);
      const result = calendarCall(c) as unknown[];
      if ("expect" in c) expect(result).toEqual(c.expect);
      for (const item of c.expect_contains ?? []) expect(result).toContainEqual(item);
      for (const item of c.expect_absent ?? []) expect(result).not.toContainEqual(item);
    });
  }
});

describe("bundled deadline vectors", () => {
  for (const c of collect("deadline")) {
    it(`${c._file}:${c.id}`, () => {
      const run = () =>
        compute(c.pack, c.trigger, c.period, { direction: c.direction ?? "after", options: c.options, calendar: c.calendar });
      if (c.error) return expectError(run, c.error);
      const result = run();
      const e = c.expect;
      expect(result.deadline, result.explain()).toBe(e.deadline);
      if (e.steps) expect(result.trace.map((s) => s.step)).toEqual(e.steps);
      if ("ends_at" in e) expect(result.endsAt).toBe(e.ends_at);
      if (e.notices) expect(result.notices.map((n) => n.code)).toEqual(e.notices);
      for (const s of result.trace) for (const lang of languages()) expect(s.message[lang]).not.toMatch(/\{\w+\}/);
    });
  }
});

it("every bundled pack and calendar loads", () => {
  for (const id of listCalendars()) calendar(id);
  for (const id of listRulepacks()) {
    const pack = rulepack(id);
    expect(pack.disclaimer, `${id} needs a disclaimer`).toBeTruthy();
  }
});
