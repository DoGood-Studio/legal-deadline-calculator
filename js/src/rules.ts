/**
 * Legal deadline computation driven by rule packs (rules as data).
 * Mirrors python/src/lexdays/_rules.py; both run the same vectors.
 */
import { type BusinessDayOptions, Calendar, calendar, type Holiday, holidayLabel } from "./calendar.js";
import { RULEPACKS } from "./data.generated.js";
import * as D from "./dates.js";
import type { ISODate } from "./dates.js";
import { DataError, InputError, NotFoundError, OptionError } from "./errors.js";
import { DateParam, DEFAULT_LANG, languages, type LocalizedText, type MessageParam, pick, render } from "./i18n.js";
import { checkKeys, checkName, isObj, type Obj } from "./validate.js";

export type Unit = "day" | "week" | "month" | "year" | "business_day";
export type Direction = "after" | "before";
export const UNITS: readonly Unit[] = ["day", "week", "month", "year", "business_day"];
const DIRECTIONS: readonly Direction[] = ["after", "before"];
const MAX_AMOUNT = 100_000;

const ISO_PERIOD = /^P(\d+)([DWMY])$/i;
const SHORT_PERIOD = /^(\d+)\s*(bd|d|w|m|y)$/i;
const WORD_PERIOD =
  /^(\d+)\s*(business[ _-]?days?|working[ _-]?days?|days?|weeks?|months?|years?|iş günü|gün|hafta|ay|yıl)$/i;
const UNIT_ALIASES: Record<string, Unit> = {
  d: "day", w: "week", m: "month", y: "year", bd: "business_day",
  day: "day", days: "day", week: "week", weeks: "week", month: "month", months: "month",
  year: "year", years: "year", gün: "day", hafta: "week", ay: "month", yıl: "year", "iş günü": "business_day",
};
const TIME = /^(?:[01]\d|2[0-3]):[0-5]\d$/;
const MONTH_DAY = /^(\d{2})-(\d{2})$/;

const PACK_KEYS = new Set([
  "$schema", "id", "name", "description", "jurisdiction", "calendar", "status",
  "non_working", "options", "steps", "citations", "sources", "disclaimer", "notes",
]);
const COMMON_STEP_KEYS = ["type", "when", "cite", "message", "note"];
const STEP_KEYS: Record<string, ReadonlySet<string>> = Object.fromEntries(
  Object.entries({
    shift_trigger: ["days"],
    count: ["exclude_start_day", "clear_days", "business_days"],
    recess: ["name", "periods", "mode", "extension_days", "count_from"],
    roll: ["direction", "half_days", "kinds", "weekend"],
    add_days: ["days"],
    ends_at: ["time"],
    notice: ["code", "text"],
  }).map(([k, v]) => [k, new Set([...COMMON_STEP_KEYS, ...v])]),
);
const CONDITION_KEYS = new Set([
  "option", "equals", "in", "unit", "unit_in", "min_amount", "max_amount",
  "direction", "trigger_from", "trigger_before", "trigger_within", "date_within", "day_has",
  "all", "any", "not",
]);

// ------------------------------------------------------------------- results

/** A legal period such as 2 weeks or 10 working days. */
export class Period {
  constructor(
    readonly amount: number,
    readonly unit: Unit,
  ) {
    if (typeof amount !== "number" || !Number.isInteger(amount)) {
      throw new InputError(`period amount must be an integer, got ${JSON.stringify(amount)}`);
    }
    if (amount < 1 || amount > MAX_AMOUNT) throw new InputError(`period amount must be between 1 and ${MAX_AMOUNT}, got ${amount}`);
    if (!UNITS.includes(unit)) throw new InputError(`period unit must be one of ${UNITS.join(", ")}, got ${JSON.stringify(unit)}`);
  }

  /** Accepts `"P2W"`, `"10d"`, `"5bd"`, `"2 weeks"`, `[2, "week"]` or `{amount, unit}`. */
  static parse(value: PeriodLike): Period {
    if (value instanceof Period) return value;
    if (Array.isArray(value) && value.length === 2) return new Period(value[0], value[1]);
    if (isObj(value)) return new Period(value.amount as number, value.unit as Unit);
    if (typeof value === "string") {
      const text = value.trim();
      const iso = ISO_PERIOD.exec(text);
      if (iso) return new Period(Number(iso[1]), UNIT_ALIASES[iso[2]!.toLowerCase()]!);
      const m = SHORT_PERIOD.exec(text) ?? WORD_PERIOD.exec(text);
      if (m) {
        let unit = m[2]!.toLowerCase().replace(/[-_]/g, " ");
        if (unit.startsWith("business") || unit.startsWith("working")) unit = "bd";
        const resolved = UNIT_ALIASES[unit];
        if (resolved) return new Period(Number(m[1]), resolved);
      }
      throw new InputError(`cannot parse period ${JSON.stringify(value)}; try 'P10D', '2w', '1m' or '5bd'`);
    }
    throw new InputError(`cannot use ${typeof value} as a period`);
  }

  toString(): string {
    return this.unit === "business_day" ? `${this.amount}bd` : `P${this.amount}${this.unit[0]!.toUpperCase()}`;
  }

  toJSON(): { amount: number; unit: Unit } {
    return { amount: this.amount, unit: this.unit };
  }
}

export type PeriodLike = Period | string | readonly [number, Unit] | { amount: number; unit: Unit };

export interface Citation {
  readonly id: string;
  readonly label: LocalizedText;
  readonly url: string | null;
  readonly quote: LocalizedText | null;
}

export interface TraceStep {
  readonly step: string;
  readonly before: ISODate;
  readonly after: ISODate;
  readonly changed: boolean;
  readonly message: LocalizedText;
  readonly citation: Citation | null;
}

export interface Notice {
  readonly code: string;
  readonly message: LocalizedText;
  readonly citation: Citation | null;
}

function langOrDefault(lang: string): string {
  return languages().includes(lang) ? lang : DEFAULT_LANG;
}

/** The computed deadline together with the reasoning that produced it. */
export class DeadlineResult {
  constructor(
    readonly deadline: ISODate,
    readonly trigger: ISODate,
    readonly period: Period,
    readonly direction: Direction,
    readonly rulepack: string,
    readonly calendar: string,
    readonly options: Readonly<Record<string, unknown>>,
    readonly trace: readonly TraceStep[],
    readonly notices: readonly Notice[],
    readonly endsAt: string | null,
    readonly timezone: string | null,
  ) {}

  /** Human-readable, numbered explanation in `lang` ("en" or "tr"). */
  explain(lang = "en"): string {
    const l = langOrDefault(lang);
    const lines = this.trace.map((s, i) => {
      let line = `${i + 1}. ${pick(s.message, lang)}`;
      if (s.citation) line += ` [${pick(s.citation.label, lang)}]`;
      return line;
    });
    lines.push(render("explain.deadline", { date: new DateParam(D.parseDate(this.deadline)) })[l]!);
    if (this.endsAt) {
      const time = this.timezone ? `${this.endsAt} (${this.timezone})` : this.endsAt;
      lines.push(render("explain.ends_at", { time })[l]!);
    }
    for (const n of this.notices) lines.push(render("explain.warning", { text: pick(n.message, lang) })[l]!);
    return lines.join("\n");
  }

  /** Same shape as Python's `DeadlineResult.to_dict()`. */
  toJSON(): Record<string, unknown> {
    return {
      deadline: this.deadline,
      ends_at: this.endsAt,
      timezone: this.timezone,
      trigger: this.trigger,
      period: this.period.toJSON(),
      direction: this.direction,
      rulepack: this.rulepack,
      calendar: this.calendar,
      options: { ...this.options },
      trace: this.trace.map((s) => ({ ...s, citation: s.citation && { ...s.citation } })),
      notices: this.notices.map((n) => ({ ...n, citation: n.citation && { ...n.citation } })),
    };
  }
}

// ------------------------------------------------------------------- engine

interface Context {
  trigger: number;
  period: Period;
  direction: Direction;
  options: Readonly<Record<string, unknown>>;
  trace: TraceStep[];
  notices: Notice[];
  endsAt: string | null;
  countStart: number | null;
}

type Step = Obj & { type: string };

function intParam(value: unknown, where: string, lo: number, hi: number): number {
  if (typeof value !== "number" || !Number.isInteger(value) || value < lo || value > hi) {
    throw new DataError(`${where}: expected an integer in [${lo}, ${hi}], got ${JSON.stringify(value)}`);
  }
  return value;
}

function monthDay(value: unknown, where: string): [number, number] {
  const m = typeof value === "string" ? MONTH_DAY.exec(value) : null;
  if (!m) throw new DataError(`${where}: expected MM-DD, got ${JSON.stringify(value)}`);
  const month = Number(m[1]);
  const day = Number(m[2]);
  if (month < 1 || month > 12 || day < 1 || day > D.daysInMonth(2001, month)) {
    throw new DataError(`${where}: ${JSON.stringify(value)} is not a valid month-day`);
  }
  return [month, day];
}

export interface ComputeOptions {
  direction?: Direction;
  options?: Readonly<Record<string, unknown>>;
}

/** A jurisdiction's deadline rules, loaded from a JSON rule pack. */
export class RulePack {
  readonly id: string;
  readonly name: LocalizedText;
  readonly jurisdiction: string | null;
  readonly status: string;
  readonly description: LocalizedText | null;
  readonly disclaimer: LocalizedText | null;
  readonly sources: readonly unknown[];
  readonly calendar: Calendar;
  readonly citations: Readonly<Record<string, Citation>>;
  readonly options: Readonly<Record<string, { values: unknown[]; default: unknown; description?: LocalizedText }>>;
  readonly nonWorking: Readonly<Obj>;
  readonly steps: readonly Step[];
  private readonly where: string;

  constructor(raw: unknown, calendarOverride: Calendar | null = null) {
    const spec = checkKeys(raw, PACK_KEYS, "rule pack");
    if (typeof spec.id !== "string" || !spec.id) throw new DataError("rule pack: 'id' must be a non-empty string");
    this.where = `rule pack '${spec.id}'`;
    this.id = spec.id;
    this.name = checkName(spec.name, this.where);
    this.jurisdiction = (spec.jurisdiction as string | undefined) ?? null;
    this.status = (spec.status as string | undefined) ?? "experimental";
    this.description = (spec.description as LocalizedText | undefined) ?? null;
    this.disclaimer = (spec.disclaimer as LocalizedText | undefined) ?? null;
    this.sources = (spec.sources as unknown[] | undefined) ?? [];
    if (calendarOverride) this.calendar = calendarOverride;
    else if (spec.calendar !== undefined) this.calendar = calendar(spec.calendar as string | Obj);
    else throw new DataError(`${this.where}: 'calendar' is required`);
    this.citations = this.loadCitations(spec.citations ?? {});
    this.options = this.loadOptions(spec.options ?? {});
    this.nonWorking = this.loadNonWorking(spec.non_working ?? {});
    this.steps = this.loadSteps(spec.steps);
  }

  toString(): string {
    return `RulePack(${this.id})`;
  }

  // ----------------------------------------------------------- validation

  private loadCitations(raw: unknown): Record<string, Citation> {
    if (!isObj(raw)) throw new DataError(`${this.where}: 'citations' must be an object`);
    const out: Record<string, Citation> = {};
    for (const [cid, rawItem] of Object.entries(raw)) {
      const item = checkKeys(rawItem, new Set(["label", "url", "quote"]), `${this.where}.citations[${cid}]`);
      out[cid] = {
        id: cid,
        label: checkName(item.label, `${this.where}.citations[${cid}].label`),
        url: (item.url as string | undefined) ?? null,
        quote: (item.quote as LocalizedText | undefined) ?? null,
      };
    }
    return out;
  }

  private loadOptions(raw: unknown): RulePack["options"] {
    if (!isObj(raw)) throw new DataError(`${this.where}: 'options' must be an object`);
    const out: Record<string, { values: unknown[]; default: unknown }> = {};
    for (const [name, rawItem] of Object.entries(raw)) {
      const here = `${this.where}.options[${name}]`;
      const item = checkKeys(rawItem, new Set(["values", "default", "description"]), here);
      if (!Array.isArray(item.values) || item.values.length === 0) throw new DataError(`${here}.values must be a non-empty list`);
      if (!item.values.includes(item.default)) throw new DataError(`${here}.default must be one of its values`);
      out[name] = item as { values: unknown[]; default: unknown };
    }
    return out;
  }

  private resolve(value: unknown, ctx: Context | null, where: string): unknown {
    if (isObj(value) && Object.keys(value).length === 1 && "$option" in value) {
      const name = value.$option as string;
      if (!(name in this.options)) throw new DataError(`${where}: references unknown option ${JSON.stringify(name)}`);
      return ctx ? ctx.options[name] : this.options[name]!.default;
    }
    return value;
  }

  private loadNonWorking(raw: unknown): Obj {
    const conf = checkKeys(raw, new Set(["weekend", "kinds", "half_days"]), `${this.where}.non_working`);
    const merged = { weekend: true, kinds: ["public"], half_days: "working", ...conf };
    this.checkNonWorking(merged, `${this.where}.non_working`);
    return merged;
  }

  private checkNonWorking(conf: Obj, where: string): void {
    if ("weekend" in conf && typeof this.resolve(conf.weekend, null, where) !== "boolean") {
      throw new DataError(`${where}.weekend must be true or false`);
    }
    if ("kinds" in conf) {
      const kinds = this.resolve(conf.kinds, null, where);
      if (!Array.isArray(kinds) || !kinds.every((k) => typeof k === "string")) {
        throw new DataError(`${where}.kinds must be a list of strings`);
      }
    }
    if ("half_days" in conf && !["working", "non_working"].includes(this.resolve(conf.half_days, null, where) as string)) {
      throw new DataError(`${where}.half_days must be 'working' or 'non_working'`);
    }
  }

  private checkCondition(raw: unknown, where: string): void {
    const cond = checkKeys(raw, CONDITION_KEYS, where);
    if (Object.keys(cond).length === 0) throw new DataError(`${where}: empty condition`);
    if ("option" in cond) {
      const name = cond.option as string;
      if (!(name in this.options)) throw new DataError(`${where}: unknown option ${JSON.stringify(name)}`);
      if (("equals" in cond) === ("in" in cond)) {
        throw new DataError(`${where}: an option condition needs exactly one of 'equals' or 'in'`);
      }
      const allowed = this.options[name]!.values;
      const tested = "equals" in cond ? [cond.equals] : cond.in;
      if (!Array.isArray(tested) || tested.some((v) => !allowed.includes(v))) {
        throw new DataError(`${where}: tests values that option ${JSON.stringify(name)} can never take`);
      }
    } else if ("equals" in cond || "in" in cond) {
      throw new DataError(`${where}: 'equals'/'in' require 'option'`);
    }
    if ("unit" in cond && !UNITS.includes(cond.unit as Unit)) throw new DataError(`${where}: unknown unit`);
    if ("unit_in" in cond && (!Array.isArray(cond.unit_in) || cond.unit_in.some((u) => !UNITS.includes(u as Unit)))) {
      throw new DataError(`${where}: 'unit_in' must list valid units`);
    }
    for (const key of ["min_amount", "max_amount"]) {
      if (key in cond && !Number.isInteger(cond[key])) throw new DataError(`${where}: ${key} must be an integer`);
    }
    if ("direction" in cond && !DIRECTIONS.includes(cond.direction as Direction)) {
      throw new DataError(`${where}: direction must be one of ${DIRECTIONS.join(", ")}`);
    }
    for (const key of ["trigger_from", "trigger_before"]) if (key in cond) D.parseDate(cond[key], `${where}.${key}`);
    for (const key of ["trigger_within", "date_within"]) {
      if (!(key in cond)) continue;
      const windows = cond[key];
      if (!Array.isArray(windows) || windows.length === 0) throw new DataError(`${where}.${key} must be a non-empty list of windows`);
      windows.forEach((w, i) => {
        const window = checkKeys(w, new Set(["start", "end"]), `${where}.${key}[${i}]`);
        monthDay(window.start, `${where}.${key}[${i}].start`);
        monthDay(window.end, `${where}.${key}[${i}].end`);
      });
    }
    if ("day_has" in cond && typeof cond.day_has !== "string") {
      throw new DataError(`${where}.day_has must be 'half_day' or a holiday kind`);
    }
    for (const key of ["all", "any"]) {
      if (key in cond) {
        const list = cond[key];
        if (!Array.isArray(list) || list.length === 0) throw new DataError(`${where}.${key} must be a non-empty list`);
        list.forEach((sub, i) => this.checkCondition(sub, `${where}.${key}[${i}]`));
      }
    }
    if ("not" in cond) this.checkCondition(cond.not, `${where}.not`);
  }

  private loadSteps(raw: unknown): Step[] {
    if (!Array.isArray(raw) || raw.length === 0) throw new DataError(`${this.where}: 'steps' must be a non-empty list`);
    let seenCount = false;
    raw.forEach((step: unknown, index) => {
      const type = isObj(step) ? step.type : undefined;
      const here = `${this.where}.steps[${index}]`;
      if (typeof type !== "string" || !(type in STEP_KEYS)) {
        throw new DataError(`${here}: type must be one of ${Object.keys(STEP_KEYS).sort().join(", ")}`);
      }
      const s = checkKeys(step, STEP_KEYS[type]!, `${here} (${type})`);
      if ("when" in s) this.checkCondition(s.when, `${here}.when`);
      if ("cite" in s && !((s.cite as string) in this.citations)) {
        throw new DataError(`${here}: cites unknown citation ${JSON.stringify(s.cite)}`);
      }
      if ("message" in s) checkName(s.message, `${here}.message`);
      if (type === "count") {
        seenCount = true;
        for (const key of ["exclude_start_day", "clear_days", "business_days"]) {
          if (key in s && typeof this.resolve(s[key], null, here) !== "boolean") throw new DataError(`${here}.${key} must be true or false`);
        }
      } else if (type === "shift_trigger") {
        if (seenCount) throw new DataError(`${here}: shift_trigger must come before the count step`);
        intParam(this.resolve(s.days, null, here), `${here}.days`, -366, 366);
      } else if (type === "add_days") {
        intParam(this.resolve(s.days, null, here), `${here}.days`, -366, 366);
      } else if (type === "recess") {
        this.checkRecess(s, here);
        if (s.mode === "defer_start" && seenCount) throw new DataError(`${here}: a 'defer_start' recess must come before the count step`);
      } else if (type === "roll") {
        if (!["auto", "forward", "backward"].includes((s.direction ?? "auto") as string)) {
          throw new DataError(`${here}.direction must be auto, forward or backward`);
        }
        this.checkNonWorking(s, here);
      } else if (type === "ends_at") {
        const time = this.resolve(s.time, null, here);
        if (typeof time !== "string" || !TIME.test(time)) throw new DataError(`${here}.time must be HH:MM`);
      } else if (type === "notice") {
        if (typeof s.code !== "string") throw new DataError(`${here}.code must be a string`);
        checkName(s.text, `${here}.text`);
      }
    });
    if (!seenCount) throw new DataError(`${this.where}: needs at least one 'count' step`);
    return raw as Step[];
  }

  private checkRecess(step: Obj, here: string): void {
    checkName(step.name, `${here}.name`);
    const mode = step.mode ?? "extend";
    if (mode !== "extend" && mode !== "suspend" && mode !== "defer_start") {
      throw new DataError(`${here}.mode must be 'extend', 'suspend' or 'defer_start'`);
    }
    if (mode === "extend") {
      intParam(step.extension_days, `${here}.extension_days`, 0, 366);
      const from = this.resolve(step.count_from ?? "end", null, here);
      if (from !== "end" && from !== "day_after_end") throw new DataError(`${here}.count_from must be 'end' or 'day_after_end'`);
    }
    const periods = step.periods;
    if (!Array.isArray(periods) || periods.length === 0) throw new DataError(`${here}.periods must be a non-empty list`);
    periods.forEach((p, i) => {
      const period = checkKeys(p, new Set(["start", "end", "since", "until"]), `${here}.periods[${i}]`);
      monthDay(period.start, `${here}.periods[${i}].start`);
      monthDay(period.end, `${here}.periods[${i}].end`);
    });
  }

  private optionValues(options: Readonly<Record<string, unknown>> | undefined): Record<string, unknown> {
    const given = { ...(options ?? {}) };
    const unknown = Object.keys(given).filter((k) => !(k in this.options)).sort();
    if (unknown.length) {
      const known = Object.keys(this.options).sort().join(", ") || "none";
      throw new OptionError(`${this.where}: unknown option(s) ${JSON.stringify(unknown)}; known: ${known}`);
    }
    const resolved: Record<string, unknown> = {};
    for (const [name, spec] of Object.entries(this.options)) {
      const value = name in given ? given[name] : spec.default;
      if (!spec.values.includes(value)) {
        throw new OptionError(`${this.where}: option '${name}' must be one of ${JSON.stringify(spec.values)}, got ${JSON.stringify(value)}`);
      }
      resolved[name] = value;
    }
    return resolved;
  }

  // ------------------------------------------------------------- execution

  /** Computes the deadline for `period` counted from `trigger` (a `YYYY-MM-DD` string). */
  compute(trigger: ISODate, period: PeriodLike, opts: ComputeOptions = {}): DeadlineResult {
    const start = D.parseDate(trigger, "trigger");
    const parsed = Period.parse(period);
    const direction = opts.direction ?? "after";
    if (!DIRECTIONS.includes(direction)) throw new InputError(`direction must be one of ${DIRECTIONS.join(", ")}, got ${JSON.stringify(direction)}`);
    const ctx: Context = {
      trigger: start,
      period: parsed,
      direction,
      options: this.optionValues(opts.options),
      trace: [],
      notices: [],
      endsAt: null,
      countStart: null,
    };
    let current = start;
    let counted = false;
    for (const step of this.steps) {
      if ("when" in step && !this.evaluate(step.when as Obj, ctx, current)) continue;
      if (step.type === "count") {
        if (counted) throw new DataError(`${this.where}: more than one count step matched ${parsed}`);
        counted = true;
      }
      current = this.run(step, current, ctx);
    }
    if (!counted) throw new DataError(`${this.where}: no count step applies to ${parsed} (${direction})`);
    return new DeadlineResult(
      D.formatISO(current),
      D.formatISO(start),
      parsed,
      direction,
      this.id,
      this.calendar.id,
      ctx.options,
      ctx.trace,
      ctx.notices,
      ctx.endsAt,
      this.calendar.timezone,
    );
  }

  private evaluate(cond: Obj, ctx: Context, current: number): boolean {
    if ("option" in cond) {
      const value = ctx.options[cond.option as string];
      if ("equals" in cond && value !== cond.equals) return false;
      if ("in" in cond && !(cond.in as unknown[]).includes(value)) return false;
    }
    if ("unit" in cond && ctx.period.unit !== cond.unit) return false;
    if ("unit_in" in cond && !(cond.unit_in as string[]).includes(ctx.period.unit)) return false;
    if ("min_amount" in cond && ctx.period.amount < (cond.min_amount as number)) return false;
    if ("max_amount" in cond && ctx.period.amount > (cond.max_amount as number)) return false;
    if ("direction" in cond && ctx.direction !== cond.direction) return false;
    if ("trigger_from" in cond && ctx.trigger < D.parseDate(cond.trigger_from)) return false;
    if ("trigger_before" in cond && ctx.trigger >= D.parseDate(cond.trigger_before)) return false;
    // "trigger_within" tests the date counting starts from (e.g. the deemed date of service).
    const served = ctx.countStart ?? current;
    if ("trigger_within" in cond && !(cond.trigger_within as Obj[]).some((w) => this.inWindow(w, served))) return false;
    if ("date_within" in cond && !(cond.date_within as Obj[]).some((w) => this.inWindow(w, current))) return false;
    if ("day_has" in cond && !this.dayHas(current, cond.day_has as string, ctx)) return false;
    if ("all" in cond && !(cond.all as Obj[]).every((c) => this.evaluate(c, ctx, current))) return false;
    if ("any" in cond && !(cond.any as Obj[]).some((c) => this.evaluate(c, ctx, current))) return false;
    return !("not" in cond && this.evaluate(cond.not as Obj, ctx, current));
  }

  private dayHas(day: number, what: string, ctx: Context): boolean {
    const iso = D.formatISO(day);
    if (what === "half_day") {
      const kinds = this.resolve(this.nonWorking.kinds, ctx, this.where) as string[];
      return this.calendar.holidaysOn(iso, { kinds }).some((h) => h.halfDayFrom !== null);
    }
    return this.calendar.holidaysOn(iso).some((h) => h.kind === what);
  }

  private inWindow(window: Obj, day: number): boolean {
    const year = D.yearOf(day);
    for (const y of [year - 1, year]) {
      const span = this.recessWindow(window, y);
      if (span && span[0] <= day && day <= span[1]) return true;
    }
    return false;
  }

  private nonWorkingFor(step: Step, ctx: Context): BusinessDayOptions {
    const conf: Obj = { ...this.nonWorking };
    for (const key of ["weekend", "kinds", "half_days"]) if (key in step) conf[key] = step[key];
    return {
      weekend: this.resolve(conf.weekend, ctx, this.where) as boolean,
      kinds: this.resolve(conf.kinds, ctx, this.where) as string[],
      halfDays: this.resolve(conf.half_days, ctx, this.where) as "working" | "non_working",
    };
  }

  private record(ctx: Context, step: Step, key: string, before: number, after: number, params: Record<string, MessageParam>): void {
    const message = render(key, { from: new DateParam(before), to: new DateParam(after), ...params }, step.message as LocalizedText | undefined);
    const citation = "cite" in step ? (this.citations[step.cite as string] ?? null) : null;
    ctx.trace.push({
      step: step.type,
      before: D.formatISO(before),
      after: D.formatISO(after),
      changed: before !== after,
      message,
      citation,
    });
  }

  private run(step: Step, current: number, ctx: Context): number {
    switch (step.type) {
      case "shift_trigger": {
        const days = this.resolve(step.days, ctx, this.where) as number;
        const next = D.addDays(current, days);
        this.record(ctx, step, "shift_trigger", current, next, { days });
        return next;
      }
      case "count":
        return this.count(step, current, ctx);
      case "recess":
        return this.recess(step, current, ctx);
      case "roll":
        return this.roll(step, current, ctx);
      case "add_days": {
        const days = this.resolve(step.days, ctx, this.where) as number;
        const next = D.addDays(current, days);
        this.record(ctx, step, "add_days", current, next, { days });
        return next;
      }
      case "ends_at":
        ctx.endsAt = this.resolve(step.time, ctx, this.where) as string;
        this.record(ctx, step, "ends_at", current, current, { time: ctx.endsAt });
        return current;
      default: {
        const citation = "cite" in step ? (this.citations[step.cite as string] ?? null) : null;
        ctx.notices.push({ code: step.code as string, message: step.text as LocalizedText, citation });
        return current;
      }
    }
  }

  private count(step: Step, current: number, ctx: Context): number {
    ctx.countStart = current;
    const { amount: n, unit } = ctx.period;
    const before = ctx.direction === "before";
    const sign = before ? -1 : 1;
    const suffix = before ? ".before" : "";
    const businessFlag = Boolean(this.resolve(step.business_days ?? false, ctx, this.where));
    let next: number;
    let key: string;
    if (unit === "business_day" || (businessFlag && unit === "day")) {
      next = this.calendar.addBusinessDaysRaw(current, sign * n, this.nonWorkingFor(step, ctx));
      key = `count.business_day${suffix}`;
    } else if (unit === "day") {
      const clear = Boolean(this.resolve(step.clear_days ?? false, ctx, this.where));
      const exclude = Boolean(this.resolve(step.exclude_start_day ?? true, ctx, this.where));
      let delta: number;
      if (clear) [delta, key] = [n + 1, `count.day${suffix}.clear`];
      else if (exclude || before) [delta, key] = [n, `count.day${suffix}`];
      else [delta, key] = [n - 1, "count.day.inclusive"];
      next = D.addDays(current, sign * delta);
    } else if (unit === "week") {
      next = D.addDays(current, sign * 7 * n);
      key = `count.week${suffix}`;
    } else {
      const months = n * (unit === "year" ? 12 : 1);
      const [moved, clamped] = D.addMonths(current, sign * months);
      next = moved;
      key = `count.${unit}${clamped && !before ? ".clamped" : suffix}`;
    }
    this.record(ctx, step, key, current, next, { n });
    return next;
  }

  private recessWindow(period: Obj, year: number): [number, number] | null {
    if (period.since != null && year < (period.since as number)) return null;
    if (period.until != null && year > (period.until as number)) return null;
    const [sm, sd] = monthDay(period.start, "");
    const [em, ed] = monthDay(period.end, "");
    const endYear = em < sm || (em === sm && ed < sd) ? year + 1 : year;
    return [D.makeDay(year, sm, sd), D.makeDay(endYear, em, ed)];
  }

  private windows(step: Step, lo: number, hi: number): [number, number][] {
    const found = new Map<string, [number, number]>();
    for (let year = D.yearOf(lo) - 1; year <= D.yearOf(hi); year++) {
      for (const period of step.periods as Obj[]) {
        const w = this.recessWindow(period, year);
        if (w && w[1] >= lo && w[0] <= hi) found.set(`${w[0]}:${w[1]}`, w);
      }
    }
    return [...found.values()].sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  }

  private recess(step: Step, current: number, ctx: Context): number {
    const name = step.name as LocalizedText;
    if (step.mode === "defer_start") {
      for (const [start, end] of this.windows(step, current, current)) {
        if (start <= current && current <= end) {
          this.record(ctx, step, "recess.defer_start", current, end, { recess: name, start: new DateParam(start), end: new DateParam(end) });
          return end;
        }
      }
      this.record(ctx, step, "recess.outside", current, current, { recess: name });
      return current;
    }
    if ((step.mode ?? "extend") === "extend") {
      for (const [start, end] of this.windows(step, current, current)) {
        if (start <= current && current <= end) {
          const days = step.extension_days as number;
          const countFrom = this.resolve(step.count_from ?? "end", ctx, this.where);
          const base = countFrom === "end" ? end : D.addDays(end, 1);
          const next = D.addDays(base, days);
          const key = countFrom === "end" ? "recess.extend" : "recess.extend.next_day";
          this.record(ctx, step, key, current, next, {
            recess: name, start: new DateParam(start), end: new DateParam(end), days, next: new DateParam(base),
          });
          return next;
        }
      }
      this.record(ctx, step, "recess.outside", current, current, { recess: name });
      return current;
    }
    if (ctx.direction === "before") throw new DataError(`${this.where}: recess mode 'suspend' does not support counting backwards`);
    const origin = ctx.countStart ?? ctx.trigger;
    let suspended = 0;
    let next = current;
    for (;;) {
      let overlap = 0;
      for (const [start, end] of this.windows(step, origin, next)) {
        const first = Math.max(start, origin + 1);
        const last = Math.min(end, next);
        overlap += Math.max(0, last - first + 1);
      }
      if (overlap === suspended) break;
      suspended = overlap;
      next = D.addDays(current, suspended);
    }
    if (suspended) this.record(ctx, step, "recess.suspend", current, next, { recess: name, days: suspended });
    else this.record(ctx, step, "recess.outside", current, current, { recess: name });
    return next;
  }

  private reason(why: Holiday | "weekend"): LocalizedText {
    if (why === "weekend") return render("reason.weekend", {});
    if (why.halfDayFrom !== null) return render("reason.half_day", { holiday: why.name, time: why.halfDayFrom });
    return Object.fromEntries(languages().map((l) => [l, holidayLabel(why, l)]));
  }

  private roll(step: Step, current: number, ctx: Context): number {
    const conf = this.nonWorkingFor(step, ctx);
    let direction = (step.direction ?? "auto") as string;
    if (direction === "auto") direction = ctx.direction === "before" ? "backward" : "forward";
    const why = this.calendar.reasonOn(current, conf);
    if (why === null) {
      this.record(ctx, step, "roll.none", current, current, {});
      return current;
    }
    const next = this.calendar.stepDay(current, direction === "forward" ? 1 : -1, false, conf);
    this.record(ctx, step, `roll.${direction}`, current, next, { reason: this.reason(why) });
    return next;
  }
}

// ------------------------------------------------------------------ registry

const loaded = new Map<string, RulePack>();

/** Returns a {@link RulePack} from an id (e.g. `"tr/hmk"`), a spec object, or a pack. */
export function rulepack(value: string | Obj | RulePack): RulePack {
  if (value instanceof RulePack) return value;
  if (typeof value === "string") {
    let pack = loaded.get(value);
    if (!pack) {
      if (!Object.hasOwn(RULEPACKS, value)) throw new NotFoundError(`unknown rule pack: ${JSON.stringify(value)} (see listRulepacks())`);
      pack = new RulePack(RULEPACKS[value]);
      loaded.set(value, pack);
    }
    return pack;
  }
  if (isObj(value)) return new RulePack(value);
  throw new InputError("expected a rule pack id, spec or RulePack");
}

/** Computes a deadline: `compute("tr/hmk", "2026-07-10", "P2W")`. */
export function compute(pack: string | Obj | RulePack, trigger: ISODate, period: PeriodLike, opts: ComputeOptions = {}): DeadlineResult {
  return rulepack(pack).compute(trigger, period, opts);
}

/** Ids of all bundled rule packs. */
export function listRulepacks(): string[] {
  return Object.keys(RULEPACKS).sort();
}
