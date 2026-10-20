// Differential test: every random case computed by the Python package
// (vectors/generated/differential.json) must give a byte-identical result here.
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { calendar, compute, LexdaysError, VERSION } from "../src/index.js";

const file = join(dirname(fileURLToPath(import.meta.url)), "..", "..", "vectors", "generated", "differential.json");
const doc = JSON.parse(readFileSync(file, "utf8"));

/** JSON with sorted keys and no spaces: the same bytes as Python's json.dumps(sort_keys=True, separators=(",", ":")). */
function canonical(value: unknown): string {
  if (Array.isArray(value)) return `[${value.map(canonical).join(",")}]`;
  if (value !== null && typeof value === "object") {
    const entries = Object.entries(value as Record<string, unknown>)
      .filter(([, v]) => v !== undefined)
      .sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0));
    return `{${entries.map(([k, v]) => `${JSON.stringify(k)}:${canonical(v)}`).join(",")}}`;
  }
  return JSON.stringify(value);
}

const sha256 = (text: string) => createHash("sha256").update(text, "utf8").digest("hex");

describe("Python ↔ TypeScript differential", () => {
  it(`${doc.deadlines.length} random deadlines match byte for byte`, () => {
    const mismatches: string[] = [];
    for (const c of doc.deadlines) {
      let got: string;
      try {
        const result = compute(c.pack, c.trigger, c.period ?? null, { act: c.act, direction: c.direction, options: c.options, calendar: c.calendar });
        const { version: _, ...data } = result.toJSON();
        got = `${result.deadline} ${sha256(canonical(data))}`;
      } catch (err) {
        got = `error ${err instanceof LexdaysError ? err.name : String(err)}`;
      }
      const want = c.error ? `error ${c.error}` : `${c.deadline} ${c.sha256}`;
      if (got !== want) mismatches.push(`${JSON.stringify(c)} → ${got}`);
    }
    expect(mismatches.slice(0, 5)).toEqual([]);
  });

  // Left out of the hashes above so the vectors survive a version bump; checked here instead,
  // and python/tests/test_metadata.py checks that both packages carry the same version.
  it("results carry the library version", () => {
    expect(compute("tr/hmk", "2026-07-30", "P2W").toJSON().version).toBe(VERSION);
  });

  it(`${doc.calendar.length} random calendar operations match`, () => {
    const mismatches: string[] = [];
    for (const c of doc.calendar) {
      const cal = calendar(c.calendar);
      let got: unknown;
      try {
        if (c.fn === "add_business_days") got = cal.addBusinessDays(c.date, c.n);
        else if (c.fn === "business_days_between") got = cal.businessDaysBetween(c.date, c.end);
        else if (c.fn === "next_business_day") got = cal.nextBusinessDay(c.date);
        else got = cal.previousBusinessDay(c.date);
      } catch (err) {
        got = `error ${err instanceof LexdaysError ? err.name : String(err)}`;
      }
      const want = c.error ? `error ${c.error}` : c.expect;
      if (got !== want) mismatches.push(`${JSON.stringify(c)} → ${String(got)}`);
    }
    expect(mismatches.slice(0, 5)).toEqual([]);
  });
});
