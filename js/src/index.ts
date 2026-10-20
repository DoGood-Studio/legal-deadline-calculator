/**
 * lexdays — explainable legal deadlines and business days.
 *
 * @example
 * import { calendar, compute } from "lexdays";
 * calendar("us").addBusinessDays("2026-07-02", 1); // "2026-07-06"
 */
export {
  type BusinessDayOptions,
  Calendar,
  calendar,
  type HalfDayPolicy,
  type Holiday,
  holidayLabel,
  holidayToJSON,
  type Kinds,
  listCalendars,
} from "./calendar.js";
export type { ISODate } from "./dates.js";
export { CoverageError, DataError, InputError, LexdaysError, NotFoundError, OptionError } from "./errors.js";
export type { LocalizedText } from "./i18n.js";
export {
  type Citation,
  compute,
  type ComputeOptions,
  DeadlineResult,
  type Direction,
  listRulepacks,
  type Notice,
  Period,
  type PeriodLike,
  RulePack,
  rulepack,
  type TraceStep,
  type Unit,
} from "./rules.js";

export { VERSION } from "./version.js";
