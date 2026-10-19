// Property-based tests (fast-check), mirroring python/tests/test_properties.py.
import fc from "fast-check";
import { describe, expect, it } from "vitest";
import { calendar, compute, CoverageError, Period, rulepack, type Unit } from "../src/index.js";
import { addMonths, civilFromDays, daysFromCivil, formatISO, parseDate } from "../src/dates.js";

const CALENDARS = ["tr", "us", "gb-eaw", "de-by-catholic", "eu-cj"];
const ROLLING_PACKS = ["tr/hmk", "tr/iik", "tr/cmk", "tr/iyuk", "tr/vuk", "tr/aym", "eu/cj", "de/zpo"];
const ALL_PACKS = [...ROLLING_PACKS, "us/frcp", "gb-eaw/cpr"];

function datesIn(calId: string): fc.Arbitrary<string> {
  const [lo, hi] = calendar(calId).coverage ?? [2000, 2030];
  const margin = Math.min(400, Math.floor(((hi - lo + 1) * 365) / 4));
  const first = daysFromCivil(lo, 1, 1) + margin;
  const last = daysFromCivil(hi, 12, 31) - margin;
  return fc.integer({ min: first, max: last }).map(formatISO);
}

const calendarAndDate = fc.constantFrom(...CALENDARS).chain((c) => fc.tuple(fc.constant(c), datesIn(c)));
const packAndDate = (packs: string[]) =>
  fc.constantFrom(...packs).chain((p) => fc.tuple(fc.constant(p), datesIn(rulepack(p).calendar.id)));
const periods = fc.oneof(
  fc.tuple(fc.integer({ min: 1, max: 120 }), fc.constant<Unit>("day")),
  fc.tuple(fc.integer({ min: 1, max: 12 }), fc.constant<Unit>("week")),
  fc.tuple(fc.integer({ min: 1, max: 6 }), fc.constant<Unit>("month")),
  fc.tuple(fc.integer({ min: 1, max: 2 }), fc.constant<Unit>("year")),
  fc.tuple(fc.integer({ min: 1, max: 30 }), fc.constant<Unit>("business_day")),
).map(([n, unit]) => new Period(n, unit));

/** Computes, or returns null when the case runs past a calendar's verified years. */
function tryCompute(pack: string, trigger: string, period: Period) {
  try {
    return compute(pack, trigger, period);
  } catch (err) {
    if (err instanceof CoverageError) return null;
    throw err;
  }
}

describe("calendar properties", () => {
  it("addBusinessDays lands on a business day and inverts businessDaysBetween", () => {
    fc.assert(
      fc.property(calendarAndDate, fc.integer({ min: -40, max: 40 }), ([calId, day], n) => {
        const cal = calendar(calId);
        const result = cal.addBusinessDays(day, n);
        if (n === 0) return result === day;
        expect(cal.isBusinessDay(result)).toBe(true);
        expect(n > 0 ? result > day : result < day).toBe(true);
        expect(cal.businessDaysBetween(day, result)).toBe(n);
        return true;
      }),
      { numRuns: 400 },
    );
  });

  it("businessDaysBetween forward and backward agree", () => {
    fc.assert(
      fc.property(calendarAndDate, fc.integer({ min: 0, max: 90 }), ([calId, day], span) => {
        const cal = calendar(calId);
        const other = formatISO(parseDate(day) + span);
        const forward = cal.businessDaysBetween(day, other);
        const backward = cal.businessDaysBetween(other, day);
        expect(forward + backward).toBe(Number(cal.isBusinessDay(other)) - Number(cal.isBusinessDay(day)));
        expect(forward >= 0 && forward <= span).toBe(true);
      }),
      { numRuns: 400 },
    );
  });

  it("nextBusinessDay skips only non-working days", () => {
    fc.assert(
      fc.property(calendarAndDate, ([calId, day]) => {
        const cal = calendar(calId);
        const next = cal.nextBusinessDay(day, { inclusive: true });
        expect(next >= day && cal.isBusinessDay(next)).toBe(true);
        for (let d = parseDate(day); d < parseDate(next); d++) expect(cal.isBusinessDay(formatISO(d))).toBe(false);
      }),
      { numRuns: 400 },
    );
  });
});

describe("deadline properties", () => {
  it("the trace is a consistent chain from trigger to deadline", () => {
    fc.assert(
      fc.property(packAndDate(ALL_PACKS), periods, ([pack, trigger], period) => {
        if (pack === "gb-eaw/cpr" && period.unit === "business_day") return;
        const result = tryCompute(pack, trigger, period);
        if (!result) return;
        expect(result.deadline >= trigger).toBe(true);
        expect(result.trace[0]!.before).toBe(trigger);
        expect(result.trace.at(-1)!.after).toBe(result.deadline);
        for (let i = 1; i < result.trace.length; i++) expect(result.trace[i]!.before).toBe(result.trace[i - 1]!.after);
      }),
      { numRuns: 600 },
    );
  });

  it("rolling packs never end on a non-working day", () => {
    fc.assert(
      fc.property(packAndDate(ROLLING_PACKS), periods, ([packId, trigger], period) => {
        const result = tryCompute(packId, trigger, period);
        if (!result) return;
        const pack = rulepack(packId);
        const halfDays = typeof pack.nonWorking.half_days === "string" ? pack.nonWorking.half_days : "working";
        expect(
          pack.calendar.isBusinessDay(result.deadline, { kinds: pack.nonWorking.kinds as string[], halfDays: halfDays as "working" }),
        ).toBe(true);
      }),
      { numRuns: 600 },
    );
  });

  it("a later trigger never gives an earlier deadline", () => {
    fc.assert(
      fc.property(packAndDate(ALL_PACKS), periods, ([pack, trigger], period) => {
        if (pack === "gb-eaw/cpr" && period.unit === "business_day") return;
        const a = tryCompute(pack, trigger, period);
        const b = tryCompute(pack, formatISO(parseDate(trigger) + 1), period);
        if (!a || !b) return;
        expect(b.deadline >= a.deadline).toBe(true);
      }),
      { numRuns: 500 },
    );
  });
});

describe("date arithmetic properties", () => {
  it("day numbers round-trip through civil dates", () => {
    fc.assert(
      fc.property(fc.integer({ min: daysFromCivil(1, 1, 1), max: daysFromCivil(9999, 12, 31) }), (day) => {
        const [y, m, d] = civilFromDays(day);
        expect(daysFromCivil(y, m, d)).toBe(day);
        expect(parseDate(formatISO(day))).toBe(day);
      }),
    );
  });

  it("addMonths clamps to the end of shorter months", () => {
    fc.assert(
      fc.property(
        fc.integer({ min: daysFromCivil(10, 1, 1), max: daysFromCivil(9990, 12, 31) }),
        fc.integer({ min: -60, max: 60 }),
        (day, months) => {
          const [y, m, d] = civilFromDays(day);
          const [result, clamped] = addMonths(day, months);
          const [ry, rm, rd] = civilFromDays(result);
          expect(ry * 12 + rm - (y * 12 + m)).toBe(months);
          expect(rd === d || (clamped && rd < d)).toBe(true);
        },
      ),
    );
  });

  it("period strings round-trip", () => {
    fc.assert(
      fc.property(periods, (p) => {
        expect(Period.parse(p.toString())).toEqual(p);
      }),
    );
  });
});
