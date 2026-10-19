# Changelog

All notable changes to this project are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.1.0] - 2026-10-19

First public release.

### Added

- Jurisdiction-agnostic deadline engine driven by JSON rule packs. Steps: deemed service, counting (days, weeks, months, years, business days, clear days), judicial recess (extend, suspend, defer start), roll to a working day, add-on days, end time and notices. Each executed step is recorded in a bilingual (English/Turkish) explanation trace with its citation.
- Holiday calendars as data: fixed dates, nth weekdays, Easter offsets (Western and Orthodox), explicit dates, weekday-relative dates, observed and substitute days, half days with a clock time, holiday kinds, inheritance, and explicit coverage years. Queries outside the coverage raise `CoverageError`.
- Business-day functions: `is_business_day`, `add_business_days`, `business_days_between`, `next_business_day`, `previous_business_day`, `holidays`.
- Rule packs: `tr/hmk`, `tr/iik`, `tr/cmk`, `tr/iyuk`, `tr/vuk`, `tr/aym`, `us/frcp`, `gb-eaw/cpr`, `eu/cj`, `de/zpo`.
- Calendars: `tr` (2000–2035), `us`, `us-ma`, `gb-eaw` (2019–2028), `eu-cj` (2025–2026), `de` and all 16 Länder, `de-by-catholic`, `de-by-augsburg`.
- Python package with a command-line interface, and a typed TypeScript package (ESM and CommonJS) with identical behaviour.
- JSON Schemas for calendars and rule packs.
- Shared conformance vectors, property-based tests, a Python/TypeScript differential test, and calendar cross-checks against python-holidays and the GOV.UK bank holidays feed.

[Unreleased]: https://github.com/DoGood-Studio/lexdays/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/DoGood-Studio/lexdays/releases/tag/v0.1.0
