/** Holiday calendars defined as data, plus business-day arithmetic. */
import { CALENDARS } from "./data.generated.js";
import * as D from "./dates.js";
import type { ISODate, RelativeDirection } from "./dates.js";
import { CoverageError, DataError, InputError, NotFoundError } from "./errors.js";
import { type LocalizedText, pick, render } from "./i18n.js";
import { checkInt, checkKeys, checkName, isObj, type Obj } from "./validate.js";

export type HalfDayPolicy = "working" | "non_working";
export type Kinds = string | readonly string[] | null | undefined;

export interface BusinessDayOptions {
  /** Holiday kinds that make a day non-working. Default `["public"]`. */
  kinds?: Kinds;
  /** `"working"` (default) treats half-day holidays as working days. */
  halfDays?: HalfDayPolicy;
  /** Whether weekend days are non-working. Default `true`. */
  weekend?: boolean;
}

export interface Holiday {
  readonly date: ISODate;
  readonly id: string;
  readonly name: LocalizedText;
  readonly kind: string;
  /** `"13:00"` when the day is non-working only from that time on. */
  readonly halfDayFrom: string | null;
  /** Original date, when this occurrence is an observed/substitute day. */
  readonly observedFrom: ISODate | null;
  readonly source: string | null;
}

/** Holiday name in `lang`, with "(observed)" for substitute days. */
export function holidayLabel(h: Holiday, lang = "en"): string {
  if (h.observedFrom === null) return pick(h.name, lang);
  return pick(render("holiday.observed", { name: h.name }), lang);
}

export function holidayToJSON(h: Holiday): Record<string, unknown> {
  return {
    date: h.date,
    id: h.id,
    name: { ...h.name },
    kind: h.kind,
    half_day_from: h.halfDayFrom,
    observed_from: h.observedFrom,
  };
}

const DEFAULT_KINDS: readonly string[] = ["public"];
const TIME = /^(?:[01]\d|2[0-3]):[0-5]\d$/;
const KIND = /^[a-z][a-z_]*$/;
const DIRECTIONS: readonly RelativeDirection[] = ["on_or_after", "after", "on_or_before", "before"];
const CALENDAR_KEYS = new Set([
  "$schema", "id", "name", "description", "extends", "weekend", "timezone",
  "coverage", "sources", "holidays", "one_off", "remove", "notes",
]);
const HOLIDAY_KEYS = new Set([
  "id", "name", "kind", "rule", "since", "until", "except_years", "half_day", "observed", "source", "note",
]);
const ONE_OFF_KEYS = new Set(["id", "name", "date", "kind", "half_day", "source", "note"]);
const RULE_KEYS: Record<string, ReadonlySet<string>> = {
  fixed: new Set(["type", "month", "day"]),
  nth_weekday: new Set(["type", "month", "weekday", "n"]),
  easter: new Set(["type", "offset", "method"]),
  dates: new Set(["type", "dates"]),
  weekday_relative: new Set(["type", "month", "day", "weekday", "direction"]),
};
const MAX_NON_WORKING_RUN = 1000;

interface HolidaySpec {
  id: string;
  name: LocalizedText;
  kind: string;
  rule: Obj & { type: string };
  since: number | null;
  until: number | null;
  exceptYears: ReadonlySet<number>;
  halfDayFrom: string | null;
  observed: { shift: Record<string, number>; avoidCollision: boolean } | null;
  parsedDates: readonly number[];
  source: string | null;
}

interface Occurrence extends Holiday {
  readonly day: number;
}

function checkHalfDay(value: unknown, where: string): string | null {
  if (value === undefined || value === null) return null;
  const obj = checkKeys(value, new Set(["from"]), `${where}.half_day`);
  if (typeof obj.from !== "string" || !TIME.test(obj.from)) {
    throw new DataError(`${where}.half_day.from: expected HH:MM, got ${JSON.stringify(obj.from)}`);
  }
  return obj.from;
}

function checkKind(value: unknown, where: string): string {
  const kind = value ?? "public";
  if (typeof kind !== "string" || !KIND.test(kind)) throw new DataError(`${where}.kind: invalid kind ${JSON.stringify(kind)}`);
  return kind;
}

function kindsSet(kinds: Kinds): ReadonlySet<string> {
  if (kinds === null || kinds === undefined) return new Set(DEFAULT_KINDS);
  if (typeof kinds === "string") return new Set([kinds]);
  return new Set(kinds);
}

function checkHalfPolicy(policy: unknown): HalfDayPolicy {
  if (policy !== "working" && policy !== "non_working") {
    throw new InputError(`halfDays must be 'working' or 'non_working', got ${JSON.stringify(policy)}`);
  }
  return policy;
}

function checkHolidaySpec(raw: unknown, where: string): HolidaySpec {
  const spec = checkKeys(raw, HOLIDAY_KEYS, `${where}.holidays[]`);
  if (typeof spec.id !== "string" || !spec.id) throw new DataError(`${where}: every holiday needs an 'id'`);
  const here = `${where}.holidays[${spec.id}]`;
  const name = checkName(spec.name, here);
  const kind = checkKind(spec.kind, here);
  const rule = spec.rule;
  if (!isObj(rule) || typeof rule.type !== "string" || !(rule.type in RULE_KEYS)) {
    throw new DataError(`${here}.rule.type must be one of ${JSON.stringify(Object.keys(RULE_KEYS).sort())}`);
  }
  const type = rule.type;
  checkKeys(rule, RULE_KEYS[type]!, `${here}.rule`);
  let parsedDates: number[] = [];
  if (type === "fixed" || type === "weekday_relative") {
    const month = checkInt(rule.month, `${here}.rule.month`, 1, 12);
    const day = checkInt(rule.day, `${here}.rule.day`, 1, 31);
    if (day > D.daysInMonth(2000, month)) throw new DataError(`${here}.rule: ${month}/${day} never exists`);
  }
  if (type === "nth_weekday" || type === "weekday_relative") checkInt(rule.weekday, `${here}.rule.weekday`, 1, 7);
  if (type === "nth_weekday") {
    checkInt(rule.month, `${here}.rule.month`, 1, 12);
    const n = checkInt(rule.n, `${here}.rule.n`, -5, 5);
    if (n === 0) throw new DataError(`${here}.rule.n must not be 0`);
  }
  if (type === "weekday_relative" && !DIRECTIONS.includes(rule.direction as RelativeDirection)) {
    throw new DataError(`${here}.rule.direction must be one of ${DIRECTIONS.join(", ")}`);
  }
  if (type === "easter") {
    checkInt(rule.offset ?? 0, `${here}.rule.offset`, -200, 200);
    if (!["western", "orthodox"].includes((rule.method ?? "western") as string)) {
      throw new DataError(`${here}.rule.method must be 'western' or 'orthodox'`);
    }
  }
  if (type === "dates") {
    if (!Array.isArray(rule.dates) || rule.dates.length === 0) throw new DataError(`${here}.rule.dates must be a non-empty list`);
    parsedDates = rule.dates.map((v) => D.parseDate(v, `${here}.rule.dates`)).sort((a, b) => a - b);
    if (new Set(parsedDates).size !== parsedDates.length) throw new DataError(`${here}.rule.dates contains duplicates`);
  }
  const year = (key: string): number | null =>
    spec[key] === undefined || spec[key] === null ? null : checkInt(spec[key], `${here}.${key}`, D.MIN_YEAR, D.MAX_YEAR);
  const exceptYears = new Set<number>();
  for (const y of (spec.except_years as unknown[] | undefined) ?? []) {
    exceptYears.add(checkInt(y, `${here}.except_years`, D.MIN_YEAR, D.MAX_YEAR));
  }
  let observed: HolidaySpec["observed"] = null;
  if (spec.observed !== undefined && spec.observed !== null) {
    const obs = checkKeys(spec.observed, new Set(["shift", "avoid_collision"]), `${here}.observed`);
    if (!isObj(obs.shift) || Object.keys(obs.shift).length === 0) {
      throw new DataError(`${here}.observed.shift must map ISO weekdays to day offsets`);
    }
    const shift: Record<string, number> = {};
    for (const [wd, offset] of Object.entries(obs.shift)) {
      checkInt(/^\d+$/.test(wd) ? Number(wd) : -1, `${here}.observed.shift key`, 1, 7);
      shift[wd] = checkInt(offset, `${here}.observed.shift[${wd}]`, -6, 6);
    }
    observed = { shift, avoidCollision: Boolean(obs.avoid_collision) };
  }
  return {
    id: spec.id,
    name,
    kind,
    rule: rule as Obj & { type: string },
    since: year("since"),
    until: year("until"),
    exceptYears,
    halfDayFrom: checkHalfDay(spec.half_day, here),
    observed,
    parsedDates,
    source: typeof spec.source === "string" ? spec.source : null,
  };
}

function checkOneOff(raw: unknown, where: string): Occurrence {
  const spec = checkKeys(raw, ONE_OFF_KEYS, `${where}.one_off[]`);
  if (typeof spec.id !== "string" || !spec.id) throw new DataError(`${where}: every one-off holiday needs an 'id'`);
  const here = `${where}.one_off[${spec.id}]`;
  const day = D.parseDate(spec.date, `${here}.date`);
  return {
    day,
    date: D.formatISO(day),
    id: spec.id,
    name: checkName(spec.name, here),
    kind: checkKind(spec.kind, here),
    halfDayFrom: checkHalfDay(spec.half_day, here),
    observedFrom: null,
    source: typeof spec.source === "string" ? spec.source : null,
  };
}

function publicHoliday(o: Occurrence): Holiday {
  const { day: _day, ...rest } = o;
  return rest;
}

/**
 * A holiday calendar: weekend days plus holiday rules, all loaded from data.
 * Use {@link calendar} to load a bundled one by id, or pass a spec object.
 */
export class Calendar {
  readonly id: string;
  readonly name: LocalizedText;
  readonly weekend: ReadonlySet<number>;
  readonly timezone: string | null;
  readonly coverage: readonly [number, number] | null;
  readonly sources: readonly unknown[];
  /** @internal */ readonly specs: readonly HolidaySpec[];
  /** @internal */ readonly oneOff: readonly Occurrence[];
  private readonly cache = new Map<number, readonly Occurrence[]>();
  private readonly index = new Map<number, ReadonlyMap<number, readonly Occurrence[]>>();

  constructor(raw: unknown, parent: Calendar | null = null) {
    const spec = checkKeys(raw, CALENDAR_KEYS, "calendar");
    if (typeof spec.id !== "string" || !spec.id) throw new DataError("calendar: 'id' must be a non-empty string");
    const where = `calendar '${spec.id}'`;
    this.id = spec.id;
    this.name = spec.name !== undefined ? checkName(spec.name, where) : (parent?.name ?? { en: spec.id });
    const weekend = spec.weekend ?? (parent ? [...parent.weekend].sort() : [6, 7]);
    if (!Array.isArray(weekend) || weekend.length > 6) {
      throw new DataError(`${where}: 'weekend' must be a list of at most 6 ISO weekdays`);
    }
    this.weekend = new Set(weekend.map((d) => checkInt(d, `${where}.weekend`, 1, 7)));
    this.timezone = (spec.timezone as string | undefined) ?? parent?.timezone ?? null;
    if (spec.coverage !== undefined) {
      const cov = checkKeys(spec.coverage, new Set(["from", "to"]), `${where}.coverage`);
      const lo = checkInt(cov.from, `${where}.coverage.from`, D.MIN_YEAR + 1, D.MAX_YEAR - 1);
      const hi = checkInt(cov.to, `${where}.coverage.to`, lo, D.MAX_YEAR - 1);
      this.coverage = [lo, hi];
    } else {
      this.coverage = parent?.coverage ?? null;
    }
    this.sources = (spec.sources as unknown[] | undefined) ?? [];
    const own = ((spec.holidays as unknown[] | undefined) ?? []).map((h) => checkHolidaySpec(h, where));
    const ids = own.map((h) => h.id);
    if (new Set(ids).size !== ids.length) throw new DataError(`${where}: duplicate holiday ids`);
    const remove = new Set((spec.remove as string[] | undefined) ?? []);
    const inherited = (parent?.specs ?? []).filter((h) => !remove.has(h.id) && !ids.includes(h.id));
    this.specs = [...inherited, ...own];
    this.oneOff = [
      ...(parent?.oneOff ?? []),
      ...((spec.one_off as unknown[] | undefined) ?? []).map((o) => checkOneOff(o, where)),
    ];
  }

  toString(): string {
    return `Calendar(${this.id})`;
  }

  private checkCoverage(year: number): void {
    if (this.coverage && (year < this.coverage[0] || year > this.coverage[1])) {
      throw new CoverageError(
        `calendar '${this.id}' has verified holiday data for ${this.coverage[0]}–${this.coverage[1]} only; ${year} is outside that range`,
      );
    }
  }

  private static rawDays(spec: HolidaySpec, year: number): number[] {
    if (spec.since !== null && year < spec.since) return [];
    if (spec.until !== null && year > spec.until) return [];
    if (spec.exceptYears.has(year)) return [];
    const r = spec.rule;
    switch (r.type) {
      case "fixed":
        if ((r.day as number) > D.daysInMonth(year, r.month as number)) return [];
        return [D.makeDay(year, r.month as number, r.day as number)];
      case "nth_weekday": {
        const found = D.nthWeekday(year, r.month as number, r.weekday as number, r.n as number);
        return found === null ? [] : [found];
      }
      case "easter": {
        const base = r.method === "orthodox" ? D.easterOrthodox(year) : D.easterWestern(year);
        return [base + ((r.offset as number | undefined) ?? 0)];
      }
      case "dates":
        return spec.parsedDates.filter((d) => D.yearOf(d) === year);
      default: {
        if ((r.day as number) > D.daysInMonth(year, r.month as number)) return [];
        const anchor = D.makeDay(year, r.month as number, r.day as number);
        return [D.weekdayRelative(anchor, r.weekday as number, r.direction as RelativeDirection)];
      }
    }
  }

  private year(year: number): readonly Occurrence[] {
    const cached = this.cache.get(year);
    if (cached) return cached;
    const pairs: [Occurrence, HolidaySpec | null][] = [];
    // Neighbouring years are included because observed days can cross 1 January.
    for (const y of [year - 1, year, year + 1]) {
      if (y <= D.MIN_YEAR || y >= D.MAX_YEAR) continue;
      for (const spec of this.specs) {
        for (const day of Calendar.rawDays(spec, y)) {
          pairs.push([
            {
              day,
              date: D.formatISO(day),
              id: spec.id,
              name: spec.name,
              kind: spec.kind,
              halfDayFrom: spec.halfDayFrom,
              observedFrom: null,
              source: spec.source,
            },
            spec,
          ]);
        }
      }
      for (const o of this.oneOff) if (D.yearOf(o.day) === y) pairs.push([o, null]);
    }
    pairs.sort((a, b) => a[0].day - b[0].day || (a[0].id < b[0].id ? -1 : a[0].id > b[0].id ? 1 : 0));
    const taken = new Map<string, Set<number>>();
    for (const [h] of pairs) {
      if (!taken.has(h.kind)) taken.set(h.kind, new Set());
      taken.get(h.kind)!.add(h.day);
    }
    const observed: Occurrence[] = [];
    for (const [h, spec] of pairs) {
      const rule = spec?.observed;
      if (!rule) continue;
      const offset = rule.shift[String(D.isoWeekday(h.day))];
      if (!offset) continue;
      let target = h.day + offset;
      const used = taken.get(h.kind)!;
      if (rule.avoidCollision) {
        const step = offset > 0 ? 1 : -1;
        while (this.weekend.has(D.isoWeekday(target)) || used.has(target)) target += step;
      }
      used.add(target);
      observed.push({ ...h, day: target, date: D.formatISO(target), observedFrom: h.date });
    }
    const result = [...pairs.map((p) => p[0]), ...observed]
      .filter((h) => D.yearOf(h.day) === year)
      .sort(
        (a, b) =>
          a.day - b.day ||
          Number(a.observedFrom !== null) - Number(b.observedFrom !== null) ||
          (a.id < b.id ? -1 : a.id > b.id ? 1 : 0),
      );
    this.cache.set(year, result);
    const index = new Map<number, Occurrence[]>();
    for (const h of result) {
      if (!index.has(h.day)) index.set(h.day, []);
      index.get(h.day)!.push(h);
    }
    this.index.set(year, index);
    return result;
  }

  private static checkYear(year: unknown): number {
    if (typeof year !== "number" || !Number.isInteger(year) || year <= D.MIN_YEAR || year >= D.MAX_YEAR) {
      throw new InputError(`year: expected an integer in [${D.MIN_YEAR + 1}, ${D.MAX_YEAR - 1}], got ${JSON.stringify(year)}`);
    }
    return year;
  }

  /** All holidays in `year`. `kinds: "all"` (default) includes every kind. */
  holidays(year: number, options: { kinds?: Kinds | "all" } = {}): Holiday[] {
    const y = Calendar.checkYear(year);
    this.checkCoverage(y);
    const items = this.year(y);
    const kinds = options.kinds ?? "all";
    const wanted = kinds === "all" ? null : kindsSet(kinds);
    return items.filter((h) => !wanted || wanted.has(h.kind)).map(publicHoliday);
  }

  private occurrencesOn(day: number, wanted: ReadonlySet<string> | null): readonly Occurrence[] {
    const year = D.yearOf(day);
    this.checkCoverage(year);
    this.year(year);
    const items = this.index.get(year)!.get(day) ?? [];
    return wanted ? items.filter((h) => wanted.has(h.kind)) : items;
  }

  holidaysOn(date: ISODate, options: { kinds?: Kinds | "all" } = {}): Holiday[] {
    const kinds = options.kinds ?? "all";
    return this.occurrencesOn(D.parseDate(date), kinds === "all" ? null : kindsSet(kinds)).map(publicHoliday);
  }

  isWeekend(date: ISODate): boolean {
    return this.weekend.has(D.isoWeekday(D.parseDate(date)));
  }

  /** @internal Works on day numbers. */
  reasonOn(day: number, options: BusinessDayOptions = {}): Holiday | "weekend" | null {
    const policy = checkHalfPolicy(options.halfDays ?? "working");
    for (const h of this.occurrencesOn(day, kindsSet(options.kinds))) {
      if (h.halfDayFrom === null || policy === "non_working") return publicHoliday(h);
    }
    if ((options.weekend ?? true) && this.weekend.has(D.isoWeekday(day))) return "weekend";
    return null;
  }

  /** Why `date` is not a working day: a {@link Holiday}, `"weekend"`, or `null`. */
  nonWorkingReason(date: ISODate, options: BusinessDayOptions = {}): Holiday | "weekend" | null {
    return this.reasonOn(D.parseDate(date), options);
  }

  /** `true` unless `date` is a weekend day or a holiday of one of `kinds`. */
  isBusinessDay(date: ISODate, options: BusinessDayOptions = {}): boolean {
    return this.reasonOn(D.parseDate(date), options) === null;
  }

  /** @internal */
  stepDay(day: number, direction: 1 | -1, inclusive: boolean, options: BusinessDayOptions): number {
    let current = inclusive ? day : D.addDays(day, direction);
    for (let i = 0; i < MAX_NON_WORKING_RUN; i++) {
      if (this.reasonOn(current, options) === null) return current;
      current = D.addDays(current, direction);
    }
    throw new DataError(`calendar '${this.id}': no working day within ${MAX_NON_WORKING_RUN} days of ${D.formatISO(day)}`);
  }

  /** First working day after `date` (or on it, with `inclusive: true`). */
  nextBusinessDay(date: ISODate, options: BusinessDayOptions & { inclusive?: boolean } = {}): ISODate {
    return D.formatISO(this.stepDay(D.parseDate(date), 1, options.inclusive ?? false, options));
  }

  /** Last working day before `date` (or on it, with `inclusive: true`). */
  previousBusinessDay(date: ISODate, options: BusinessDayOptions & { inclusive?: boolean } = {}): ISODate {
    return D.formatISO(this.stepDay(D.parseDate(date), -1, options.inclusive ?? false, options));
  }

  /** @internal */
  addBusinessDaysRaw(day: number, n: number, options: BusinessDayOptions): number {
    if (!Number.isInteger(n)) throw new InputError(`n must be an integer, got ${JSON.stringify(n)}`);
    const direction = n > 0 ? 1 : -1;
    let current = day;
    for (let i = 0; i < Math.abs(n); i++) current = this.stepDay(current, direction, false, options);
    return current;
  }

  /** Moves `n` working days from `date` (negative `n` moves backwards). The start day never counts. */
  addBusinessDays(date: ISODate, n: number, options: BusinessDayOptions = {}): ISODate {
    return D.formatISO(this.addBusinessDaysRaw(D.parseDate(date), n, options));
  }

  /** Number of working days `d` with `start < d <= end` (negative when `end < start`). */
  businessDaysBetween(start: ISODate, end: ISODate, options: BusinessDayOptions = {}): number {
    let a = D.parseDate(start, "start");
    let b = D.parseDate(end, "end");
    let sign = 1;
    if (b < a) [a, b, sign] = [b, a, -1];
    let count = 0;
    for (let day = a + 1; day <= b; day++) if (this.reasonOn(day, options) === null) count++;
    return sign * count;
  }
}

const loaded = new Map<string, Calendar>();
const ID = /^[a-z0-9]+(?:[-_/][a-z0-9]+)*$/;

export function loadCalendar(id: string, chain: readonly string[] = []): Calendar {
  const hit = loaded.get(id);
  if (hit) return hit;
  if (chain.includes(id)) throw new DataError(`calendar inheritance cycle: ${[...chain, id].join(" -> ")}`);
  if (typeof id !== "string" || !ID.test(id) || !Object.hasOwn(CALENDARS, id)) {
    throw new NotFoundError(`unknown calendar: ${JSON.stringify(id)} (see listCalendars())`);
  }
  const spec = CALENDARS[id] as Obj;
  const parentId = spec.extends as string | undefined;
  const cal = new Calendar(spec, parentId ? loadCalendar(parentId, [...chain, id]) : null);
  loaded.set(id, cal);
  return cal;
}

/** Returns a {@link Calendar} from an id, a spec object, or a calendar. */
export function calendar(value: string | Obj | Calendar): Calendar {
  if (value instanceof Calendar) return value;
  if (typeof value === "string") return loadCalendar(value);
  if (isObj(value)) {
    const parentId = value.extends as string | undefined;
    return new Calendar(value, parentId ? loadCalendar(parentId) : null);
  }
  throw new InputError(`expected a calendar id, spec or Calendar`);
}

/** Ids of all bundled calendars. */
export function listCalendars(): string[] {
  return Object.keys(CALENDARS).sort();
}
