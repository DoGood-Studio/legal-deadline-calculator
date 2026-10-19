/** Base class for every error thrown by lexdays. */
export class LexdaysError extends Error {
  constructor(message: string) {
    super(message);
    this.name = new.target.name;
  }
}

/** Invalid input such as a malformed date string or period. */
export class InputError extends LexdaysError {}

/** A calendar or rule pack definition is invalid. */
export class DataError extends LexdaysError {}

/**
 * The requested year is outside the years a calendar has verified data for.
 * lexdays refuses to guess: a missing holiday would silently give a wrong deadline.
 */
export class CoverageError extends LexdaysError {}

/** An option passed to a rule pack is unknown or has an invalid value. */
export class OptionError extends LexdaysError {}

/** No bundled calendar or rule pack has the requested id. */
export class NotFoundError extends LexdaysError {}
