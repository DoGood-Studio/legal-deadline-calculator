// Runs the shared engine conformance vectors (vectors/core/*.json) — the
// same files the Python test-suite runs.
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import {
  Calendar,
  CoverageError,
  DataError,
  type Holiday,
  InputError,
  OptionError,
  RulePack,
} from "../src/index.js";

const root = join(dirname(fileURLToPath(import.meta.url)), "..", "..", "vectors", "core");
const load = (name: string) => JSON.parse(readFileSync(join(root, name), "utf8"));
const CAL = load("calendar.json");
const DL = load("deadline.json");

// Python's ValueError family maps to these TypeScript errors.
const ERRORS: Record<string, readonly (new (...args: never[]) => Error)[]> = {
  CoverageError: [CoverageError],
  DataError: [DataError],
  OptionError: [OptionError],
  ValueError: [InputError, DataError, CoverageError, OptionError],
  TypeError: [InputError],
};

const calendars: Record<string, Calendar> = {};
for (const [id, spec] of Object.entries(CAL.calendars as Record<string, { extends?: string }>)) {
  calendars[id] = new Calendar(spec, spec.extends ? calendars[spec.extends]! : null);
}

function rows(holidays: Holiday[]): string[][] {
  return holidays.map((h) => (h.observedFrom ? [h.date, h.id, h.observedFrom] : [h.date, h.id]));
}

function bizOptions(args: Record<string, unknown>) {
  return { kinds: args.kinds as string[] | undefined, halfDays: args.half_days as "working" | "non_working" | undefined, weekend: args.weekend as boolean | undefined, inclusive: args.inclusive as boolean | undefined };
}

function runCalendarCase(c: Record<string, any>): unknown {
  if (c.fn === "load") return new Calendar(c.spec);
  const cal = calendars[c.calendar]!;
  const a = c.args;
  switch (c.fn) {
    case "holidays":
      return rows(cal.holidays(a.year, a.kinds ? { kinds: a.kinds } : {}));
    case "holiday_ids":
      return cal.holidays(a.year).map((h) => h.id);
    case "is_business_day":
      return cal.isBusinessDay(a.date, bizOptions(a));
    case "next_business_day":
      return cal.nextBusinessDay(a.date, bizOptions(a));
    case "previous_business_day":
      return cal.previousBusinessDay(a.date, bizOptions(a));
    case "add_business_days":
      return cal.addBusinessDays(a.date, a.n, bizOptions(a));
    case "business_days_between":
      return cal.businessDaysBetween(a.start, a.end, bizOptions(a));
    default:
      throw new Error(`unknown fn ${c.fn}`);
  }
}

function expectError(fn: () => unknown, name: string): void {
  let thrown: unknown;
  try {
    fn();
  } catch (err) {
    thrown = err;
  }
  expect(thrown, `expected ${name}`).toBeDefined();
  expect(ERRORS[name]!.some((cls) => thrown instanceof cls), `got ${String(thrown)}`).toBe(true);
}

describe("calendar vectors", () => {
  for (const c of CAL.cases) {
    it(c.id, () => {
      if (c.error) expectError(() => runCalendarCase(c), c.error);
      else expect(runCalendarCase(c)).toEqual(c.expect);
    });
  }
});

function runDeadlineCase(c: Record<string, any>) {
  const spec = c.pack_spec ?? DL.rulepacks[c.pack];
  const pack = new RulePack(spec, calendars[spec.calendar]!);
  return pack.compute(c.trigger, c.period, { direction: c.direction ?? "after", options: c.options });
}

describe("deadline vectors", () => {
  for (const c of DL.cases) {
    it(c.id, () => {
      if (c.error) {
        expectError(() => runDeadlineCase(c), c.error);
        return;
      }
      const result = runDeadlineCase(c);
      const e = c.expect;
      expect(result.deadline).toBe(e.deadline);
      if (e.steps) expect(result.trace.map((s) => s.step)).toEqual(e.steps);
      if (e.changed) expect(result.trace.map((s) => s.changed)).toEqual(e.changed);
      if (e.ends_at) expect(result.endsAt).toBe(e.ends_at);
      expect(result.notices.map((n) => n.code)).toEqual(e.notices ?? []);
      for (const step of result.trace) {
        for (const lang of ["en", "tr"]) {
          expect(step.message[lang]).toBeTruthy();
          expect(step.message[lang]).not.toMatch(/\{\w+\}/);
        }
      }
      expect(result.explain("tr")).toBeTruthy();
    });
  }
});
